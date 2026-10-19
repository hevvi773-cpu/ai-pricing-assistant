"""风控引擎：违禁品检测、引流检测、三级风险分级。"""
import re
import logging
from typing import List, Tuple

from app.config import BANNED_WORDS, DIVERSION_WORDS, RISK_LEVELS

logger = logging.getLogger(__name__)


class RiskEngine:
    """内容风控引擎，基于关键词匹配进行风险检测和分级。"""

    def __init__(self):
        self._banned_patterns = self._compile_patterns(BANNED_WORDS)
        self._diversion_patterns = self._compile_patterns(DIVERSION_WORDS)

    def _compile_patterns(self, word_list: List[str]) -> List[re.Pattern]:
        """将关键词列表编译为正则表达式，忽略大小写。"""
        patterns = []
        for word in word_list:
            try:
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                patterns.append(pattern)
            except re.error as e:
                logger.warning('关键词编译失败: %s, %s', word, e)
        return patterns

    def _find_matches(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """在文本中查找所有匹配的关键词，去重后返回。"""
        matches = set()
        for pattern in patterns:
            found = pattern.findall(text)
            matches.update(found)
        return list(matches)

    def check_content(self, product_name: str, description: str = '') -> dict:
        """
        检测商品内容的风险等级。

        返回:
            {
                'risk_level': 'high' | 'medium' | 'low',
                'risk_type': '违禁品' | '引流站外' | None,
                'matched_words': [...],
                'message': '提示信息'
            }
        """
        full_text = f'{product_name} {description}'.strip()
        if not full_text:
            return self._build_result(RISK_LEVELS['low'], None, [], '')

        banned_matches = self._find_matches(full_text, self._banned_patterns)
        if banned_matches:
            message = f'检测到违禁品关键词：{", ".join(banned_matches[:5])}，无法提供定价服务'
            logger.info('违禁品检测命中: %s', banned_matches)
            return self._build_result(RISK_LEVELS['high'], '违禁品', banned_matches, message)

        diversion_matches = self._find_matches(full_text, self._diversion_patterns)
        if diversion_matches:
            message = f'检测到站外引流关键词：{", ".join(diversion_matches[:5])}，请注意交易安全'
            logger.info('引流检测命中: %s', diversion_matches)
            return self._build_result(RISK_LEVELS['medium'], '引流站外', diversion_matches, message)

        return self._build_result(RISK_LEVELS['low'], None, [], '')

    def _build_result(self, risk_level: str, risk_type: str,
                      matched_words: List[str], message: str) -> dict:
        """构建标准化的风控检测结果。"""
        return {
            'risk_level': risk_level,
            'risk_type': risk_type,
            'matched_words': matched_words,
            'message': message,
        }


_risk_engine = None


def get_risk_engine() -> RiskEngine:
    """获取风控引擎单例。"""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine
