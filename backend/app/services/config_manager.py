"""大模型配置管理器：支持读取、更新、持久化 API 配置，支持热更新。"""
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'llm_config.json')

DEFAULT_CONFIG = {
    'api_key': '',
    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'model_name': 'qwen-plus',
    'vision_model': 'qwen3-vl-plus',
}


class ConfigManager:
    """管理大模型 API 配置，支持热更新和持久化。"""

    def __init__(self, config_file: str = CONFIG_FILE_PATH):
        self._config_file = config_file
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """从 JSON 文件加载配置，文件不存在时返回默认配置。"""
        if not os.path.exists(self._config_file):
            logger.info('配置文件不存在，使用默认配置')
            return DEFAULT_CONFIG.copy()
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(loaded)
            logger.info('配置加载成功，模型: %s', merged['model_name'])
            return merged
        except (json.JSONDecodeError, IOError) as e:
            logger.error('配置文件读取失败: %s，使用默认配置', e)
            return DEFAULT_CONFIG.copy()

    def _save_config(self) -> None:
        """将当前配置持久化到 JSON 文件。"""
        os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            logger.info('配置已保存')
        except IOError as e:
            logger.error('配置保存失败: %s', e)
            raise

    def get_config(self) -> dict:
        """获取当前配置的副本。"""
        return self._config.copy()

    def update_config(self, api_key: Optional[str] = None,
                      base_url: Optional[str] = None,
                      model_name: Optional[str] = None,
                      vision_model: Optional[str] = None) -> dict:
        """更新配置并持久化，返回更新后的配置。"""
        if api_key is not None:
            self._config['api_key'] = api_key.strip()
        if base_url is not None:
            self._config['base_url'] = base_url.strip()
        if model_name is not None:
            self._config['model_name'] = model_name.strip()
        if vision_model is not None:
            self._config['vision_model'] = vision_model.strip()
        self._save_config()
        logger.info('配置已更新，模型: %s', self._config['model_name'])
        return self.get_config()

    def is_configured(self) -> bool:
        """检查是否已配置有效的 API Key。"""
        return bool(self._config.get('api_key'))


_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器单例。"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
