import os
import json
import logging
from typing import Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from app.config import CONDITION_DESCRIPTIONS, DEFAULT_CONDITION_DESCRIPTION, CONFIDENCE_DESCRIPTIONS

logger = logging.getLogger(__name__)

DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
DASHSCOPE_BASE_URL = os.getenv('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
MODEL_NAME = os.getenv('LLM_MODEL', 'qwen-plus')


class LLMService:
    def __init__(self):
        self.client = None
        if DASHSCOPE_API_KEY and HAS_OPENAI:
            self.client = OpenAI(
                api_key=DASHSCOPE_API_KEY,
                base_url=DASHSCOPE_BASE_URL,
            )
            logger.info('已初始化，模型: %s', MODEL_NAME)
        else:
            logger.warning('未配置 API Key，使用模板生成理由')

    def _build_comparables_summary(self, comparables: list) -> str:
        """构建参考商品摘要"""
        if not comparables:
            return ''
        prices = [f"¥{p['price_cny']}" for p in comparables[:5]]
        return f"参考了{len(comparables)}条同类成交记录，近期成交价包括：{', '.join(prices)}。"

    def generate_reasoning(self, product_name: str, category: str, condition: str,
                            suggested_price: float, price_min: float, price_max: float,
                            confidence: str, comparables: list) -> str:
        """生成定价理由"""
        if not self.client:
            return self._template_reasoning(product_name, category, condition,
                                             suggested_price, price_min, price_max,
                                             confidence, comparables)

        try:
            comparables_summary = self._build_comparables_summary(comparables)
            prompt = f"""你是一个二手商品定价专家。请根据以下信息，用中文生成一段简洁的定价理由（50-100字）。

商品信息：
- 名称：{product_name}
- 品类：{category}
- 成色：{condition}

定价结果：
- 建议价格：¥{suggested_price}
- 价格区间：¥{price_min} ~ ¥{price_max}
- 置信度：{confidence}

{comparables_summary}

请说明：
1. 这个价格是基于什么得出的
2. 成色对价格的影响
3. 为什么是这个区间

只输出理由正文，不要输出标题或额外解释。"""

            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error('大模型调用失败: %s', e, exc_info=True)
            return self._template_reasoning(product_name, category, condition,
                                             suggested_price, price_min, price_max,
                                             confidence, comparables)

    def adjust_price(self, product_name: str, current_price: float, message: str,
                     category: str, condition: str) -> tuple:
        """对话式价格调整，返回 (new_price, reasoning)"""
        if not self.client:
            return self._template_adjust(product_name, current_price, message, category, condition)

        try:
            prompt = f"""你是一个二手商品定价专家。用户希望根据以下反馈调整价格。

商品：{product_name}
品类：{category}
成色：{condition}
当前价格：¥{current_price}
用户反馈：{message}

请分析用户意图，给出调整后的价格和理由。
输出JSON格式：{{"new_price": 数字, "reasoning": "调整理由"}}

调整规则：
- 急售/便宜/降价：下调 5%-15%
- 配件齐全/成色好/涨价：上调 5%-15%
- 其他情况：微调 0%-5%"""

            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.5,
                max_tokens=150,
                response_format={'type': 'json_object'},
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            new_price = float(result.get('new_price', current_price))
            reasoning = result.get('reasoning', '根据您的反馈调整价格。')
            return new_price, reasoning
        except Exception as e:
            logger.error('价格调整失败: %s', e, exc_info=True)
            return self._template_adjust(product_name, current_price, message, category, condition)

    def _template_reasoning(self, product_name, category, condition,
                             suggested_price, price_min, price_max, confidence, comparables):
        """模板生成理由（无大模型时使用）"""
        comparables_text = ''
        if comparables:
            avg_price = sum(p['price_cny'] for p in comparables) / len(comparables)
            comparables_text = f'基于{len(comparables)}条同类商品历史成交数据（均价¥{avg_price:.0f}），'

        condition_text = CONDITION_DESCRIPTIONS.get(condition, DEFAULT_CONDITION_DESCRIPTION)
        confidence_text = CONFIDENCE_DESCRIPTIONS.get(confidence, '')

        return f'{comparables_text}{condition_text}，综合得出建议价格¥{suggested_price}。价格区间¥{price_min}~¥{price_max}反映市场波动。{confidence_text}。'

    def _template_adjust(self, product_name, current_price, message, category, condition):
        """模板调整价格（无大模型时使用）"""
        adjustment = self._detect_adjustment_intent(message)
        new_price = round(current_price * (1 + adjustment), 0)

        if adjustment < 0:
            reasoning = f'根据您的反馈「{message}」，识别为急售/降价意图，价格下调{abs(adjustment)*100:.0f}%至¥{new_price}。'
        elif adjustment > 0:
            reasoning = f'根据您的反馈「{message}」，识别为溢价因素，价格上调{adjustment*100:.0f}%至¥{new_price}。'
        else:
            reasoning = f'根据您的反馈「{message}」，价格微调至¥{new_price}。'
        return new_price, reasoning

    def _detect_adjustment_intent(self, message: str) -> float:
        """识别调整意图，返回调整比例"""
        decrease_keywords = ['急', '便宜', '低', '降', '快', '甩']
        increase_keywords = ['贵', '高', '涨', '齐全', '好', '新']

        if any(word in message for word in decrease_keywords):
            return -0.1
        if any(word in message for word in increase_keywords):
            return 0.08
        return 0.0


_llm_service = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
