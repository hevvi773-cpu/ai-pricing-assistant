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
from app.services.risk_engine import get_risk_engine
from app.services.config_manager import get_config_manager

app = FastAPI(title="AI Pricing Assistant API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 请求/响应模型 ============

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


class RiskCheckResult(BaseModel):
    risk_level: str
    risk_type: Optional[str] = None
    matched_words: List[str] = []
    message: str = ''


class PricingResult(BaseModel):
    suggested_price: float
    price_min: float
    price_max: float
    confidence: str
    reasoning: str
    comparables: Optional[List[Comparable]] = None
    risk_check: Optional[RiskCheckResult] = None


class AdjustRequest(BaseModel):
    product_name: str
    category: Optional[str] = None
    condition: Optional[str] = None
    current_price: float
    message: str


class RiskCheckRequest(BaseModel):
    product_name: str
    description: Optional[str] = ''


class RecognizeRequest(BaseModel):
    image: str


class RecognizeResult(BaseModel):
    success: bool = False
    product_name: str = ''
    category: str = ''
    condition: str = ''
    brand: str = ''
    notes: str = ''
    message: str = ''


class LLMConfigUpdate(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    vision_model: Optional[str] = None


class LLMConfigResponse(BaseModel):
    api_key: str
    base_url: str
    model_name: str
    is_configured: bool


# ============ 服务初始化 ============

pricing_engine = get_pricing_engine()
llm_service = get_llm_service()
risk_engine = get_risk_engine()
config_manager = get_config_manager()


# ============ 基础接口 ============

@app.get("/")
async def root():
    config = config_manager.get_config()
    return {
        "message": "AI Pricing Assistant API",
        "version": "0.3.0",
        "data_loaded": len(pricing_engine.products),
        "llm_enabled": config_manager.is_configured(),
        "llm_model": config.get('model_name', ''),
        "category_stats": pricing_engine.get_category_stats(),
    }


# ============ 定价接口 ============

@app.post("/api/price", response_model=PricingResult)
async def get_price(request: PricingRequest):
    """AI 智能估价：输入商品信息，返回价格区间、置信度和定价理由。
    定价前先进行风控检测，高风险商品不返回价格。"""
    risk_result = risk_engine.check_content(request.product_name)

    if risk_result['risk_level'] == 'high':
        logger.info('高风险商品，拦截定价: %s', request.product_name)
        return PricingResult(
            suggested_price=0,
            price_min=0,
            price_max=0,
            confidence='low',
            reasoning=risk_result['message'],
            comparables=[],
            risk_check=RiskCheckResult(**risk_result),
        )

    suggested_price, price_min, price_max, confidence, comparables = pricing_engine.calculate_price(
        request.product_name,
        request.category,
        request.condition,
    )

    # 匹配不到数据时，用大模型估算价格
    if not comparables:
        logger.info('无匹配数据，调用大模型估算: %s', request.product_name)
        suggested_price, price_min, price_max, reasoning = llm_service.estimate_price(
            request.product_name,
            request.category or '未分类',
            request.condition or '几乎全新',
        )
        confidence = 'low'
    else:
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
        risk_check=RiskCheckResult(**risk_result),
    )


@app.post("/api/price/adjust", response_model=PricingResult)
async def adjust_price(request: AdjustRequest):
    """对话式微调：根据用户反馈调整价格。"""
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


# ============ 风控接口 ============

@app.post("/api/risk/check", response_model=RiskCheckResult)
async def check_risk(request: RiskCheckRequest):
    """风控检测：输入商品名称和描述，返回风险等级和命中的关键词。"""
    result = risk_engine.check_content(request.product_name, request.description or '')
    return RiskCheckResult(**result)


# ============ 视觉识别接口 ============

@app.post("/api/recognize", response_model=RecognizeResult)
async def recognize_product(request: RecognizeRequest):
    """图片识别：从商品图片中识别名称、品类、成色，供前端回填表单。"""
    result = llm_service.recognize_product(request.image)

    if not result:
        return RecognizeResult(
            success=False,
            message='识别失败，请确认已配置有效的 API Key，或手动填写商品信息',
        )

    if not result.get('product_name'):
        return RecognizeResult(
            success=False,
            message='没能从图片里认出商品，请手动填写商品信息',
        )

    return RecognizeResult(
        success=True,
        product_name=result.get('product_name', ''),
        category=result.get('category', ''),
        condition=result.get('condition', ''),
        brand=result.get('brand', ''),
        notes=result.get('notes', ''),
        message='识别成功',
    )


# ============ 大模型配置管理接口 ============

@app.get("/api/config/llm", response_model=LLMConfigResponse)
async def get_llm_config():
    """获取当前大模型配置（api_key 脱敏显示）。"""
    config = config_manager.get_config()
    raw_key = config.get('api_key', '')
    masked_key = _mask_api_key(raw_key) if raw_key else ''
    return LLMConfigResponse(
        api_key=masked_key,
        base_url=config.get('base_url', ''),
        model_name=config.get('model_name', ''),
        is_configured=config_manager.is_configured(),
    )


@app.put("/api/config/llm", response_model=LLMConfigResponse)
async def update_llm_config(request: LLMConfigUpdate):
    """更新大模型配置，支持 api_key、base_url、model_name 单独或组合更新。"""
    updated = config_manager.update_config(
        api_key=request.api_key,
        base_url=request.base_url,
        model_name=request.model_name,
        vision_model=request.vision_model,
    )
    raw_key = updated.get('api_key', '')
    masked_key = _mask_api_key(raw_key) if raw_key else ''
    logger.info('大模型配置已更新，模型: %s', updated.get('model_name'))
    return LLMConfigResponse(
        api_key=masked_key,
        base_url=updated.get('base_url', ''),
        model_name=updated.get('model_name', ''),
        is_configured=bool(updated.get('api_key')),
    )


def _mask_api_key(api_key: str) -> str:
    """脱敏 API Key，只显示前4位和后4位。"""
    if len(api_key) <= 8:
        return '*' * len(api_key)
    return f'{api_key[:4]}...{api_key[-4:]}'


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
