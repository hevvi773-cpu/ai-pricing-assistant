from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.pricing_engine import get_pricing_engine
from app.services.llm_service import get_llm_service

app = FastAPI(title="AI Pricing Assistant API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PricingRequest(BaseModel):
    product_name: str
    category: Optional[str] = None
    condition: Optional[str] = None
    image: Optional[str] = None

class Comparable(BaseModel):
    name: str
    price: float
    condition: str
    category: str

class PricingResult(BaseModel):
    suggested_price: float
    price_min: float
    price_max: float
    confidence: str
    reasoning: str
    comparables: Optional[List[Comparable]] = None

class AdjustRequest(BaseModel):
    product_name: str
    category: Optional[str] = None
    condition: Optional[str] = None
    current_price: float
    message: str

# 启动时初始化
pricing_engine = get_pricing_engine()
llm_service = get_llm_service()

@app.get("/")
async def root():
    return {
        "message": "AI Pricing Assistant API",
        "version": "0.2.0",
        "data_loaded": len(pricing_engine.products),
        "llm_enabled": llm_service.client is not None,
        "category_stats": pricing_engine.get_category_stats(),
    }

@app.post("/api/price", response_model=PricingResult)
async def get_price(request: PricingRequest):
    """AI 智能估价：输入商品信息，返回价格区间、置信度和定价理由"""
    # RAG 检索 + 价格计算
    suggested_price, price_min, price_max, confidence, comparables = pricing_engine.calculate_price(
        request.product_name,
        request.category,
        request.condition,
    )

    # 大模型生成理由
    reasoning = llm_service.generate_reasoning(
        request.product_name,
        request.category or '未分类',
        request.condition or '几乎全新',
        suggested_price,
        price_min,
        price_max,
        confidence,
        comparables,
    )

    # 构建参考商品列表
    comparable_list = [
        Comparable(
            name=p['name'],
            price=p['price_cny'],
            condition=p['condition'],
            category=p['category'],
        )
        for p in comparables[:5]
    ]

    return PricingResult(
        suggested_price=suggested_price,
        price_min=price_min,
        price_max=price_max,
        confidence=confidence,
        reasoning=reasoning,
        comparables=comparable_list,
    )

@app.post("/api/price/adjust", response_model=PricingResult)
async def adjust_price(request: AdjustRequest):
    """对话式微调：根据用户反馈调整价格"""
    # 大模型调整价格
    new_price, reasoning = llm_service.adjust_price(
        request.product_name,
        request.current_price,
        request.message,
        request.category or '未分类',
        request.condition or '几乎全新',
    )

    price_min = round(new_price * 0.85, 0)
    price_max = round(new_price * 1.15, 0)

    return PricingResult(
        suggested_price=new_price,
        price_min=price_min,
        price_max=price_max,
        confidence='medium',
        reasoning=reasoning,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
