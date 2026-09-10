import json
import os
import re
import logging
import statistics
from typing import List, Dict, Optional, Tuple
from collections import Counter

from app.config import (
    CONDITION_FACTORS,
    DEFAULT_CONDITION_FACTOR,
    CONFIDENCE_THRESHOLDS,
)

logger = logging.getLogger(__name__)

DATA_DIR = os.getenv('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data'))
DATA_FILE = os.path.join(DATA_DIR, 'mercari_cleaned.json')


class PricingEngine:
    def __init__(self):
        self.products = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
            logger.info('加载 %d 条商品数据', len(self.products))
        else:
            logger.warning('数据文件不存在: %s', DATA_FILE)

    def _tokenize(self, text: str) -> List[str]:
        """简单分词：提取英文单词和中文词组"""
        text = text.lower()
        words = re.findall(r'[a-z0-9]+', text)
        chinese_segments = re.findall(r'[\u4e00-\u9fff]+', text)
        for segment in chinese_segments:
            for i in range(len(segment) - 1):
                words.append(segment[i:i+2])
        return [w for w in words if len(w) >= 2]

    def _score_product(self, query_tokens: List[str], product: Dict) -> float:
        """计算商品与查询的匹配分数"""
        name_tokens = set(self._tokenize(product['name']))
        desc_tokens = set(self._tokenize(product.get('description', '')))
        brand_tokens = set(self._tokenize(product.get('brand', '')))
        all_tokens = name_tokens | desc_tokens | brand_tokens

        if not all_tokens:
            return 0.0

        matches = sum(1 for token in query_tokens if token in all_tokens)
        return matches / len(query_tokens) if query_tokens else 0.0

    def search_similar(self, product_name: str, category: Optional[str] = None,
                       condition: Optional[str] = None, top_k: int = 20) -> List[Dict]:
        """检索同类商品"""
        if not self.products:
            return []

        query_tokens = self._tokenize(product_name)

        candidates = self.products
        if category and category != '其他':
            candidates = [p for p in candidates if p['category'] == category]

        if len(candidates) < 5:
            candidates = self.products

        scored = []
        for product in candidates:
            score = self._score_product(query_tokens, product)
            if score > 0:
                scored.append((score, product))

        scored.sort(key=lambda x: -x[0])

        if condition:
            same_condition = [(s, p) for s, p in scored if p['condition'] == condition]
            other_condition = [(s, p) for s, p in scored if p['condition'] != condition]
            scored = same_condition + other_condition

        return [product for _, product in scored[:top_k]]

    def _calculate_price_range(self, prices: List[float], condition_factor: float) -> Tuple[float, float]:
        """基于价格分布计算价格区间"""
        if len(prices) >= 4:
            quantiles = statistics.quantiles(prices, n=4)
            price_min = round(quantiles[0] * condition_factor, 0)
            price_max = round(quantiles[2] * condition_factor, 0)
        else:
            median_price = statistics.median(prices)
            suggested = round(median_price * condition_factor, 0)
            price_min = round(suggested * 0.85, 0)
            price_max = round(suggested * 1.15, 0)
        return price_min, price_max

    def _determine_confidence(self, match_count: int) -> str:
        """根据匹配数量确定置信度"""
        if match_count >= CONFIDENCE_THRESHOLDS['high']:
            return 'high'
        if match_count >= CONFIDENCE_THRESHOLDS['medium']:
            return 'medium'
        return 'low'

    def calculate_price(self, product_name: str, category: Optional[str] = None,
                        condition: Optional[str] = None) -> Tuple[float, float, float, str, List[Dict]]:
        """
        计算建议价格
        返回: (suggested_price, price_min, price_max, confidence, comparables)
        """
        comparables = self.search_similar(product_name, category, condition, top_k=20)

        if not comparables:
            base_price = 100.0
            return base_price, base_price * 0.7, base_price * 1.3, 'low', []

        prices = [p['price_cny'] for p in comparables]
        condition_factor = CONDITION_FACTORS.get(condition, DEFAULT_CONDITION_FACTOR)

        median_price = statistics.median(prices)
        suggested_price = round(median_price * condition_factor, 0)

        price_min, price_max = self._calculate_price_range(prices, condition_factor)
        confidence = self._determine_confidence(len(comparables))

        return suggested_price, price_min, price_max, confidence, comparables

    def get_category_stats(self) -> Dict[str, int]:
        """获取各品类数据量统计"""
        if not self.products:
            return {}
        counter = Counter(p['category'] for p in self.products)
        return dict(counter)


_pricing_engine = None


def get_pricing_engine() -> PricingEngine:
    global _pricing_engine
    if _pricing_engine is None:
        _pricing_engine = PricingEngine()
    return _pricing_engine
