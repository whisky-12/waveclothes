"""
配置管理器
用于读取和管理系统配置文件
"""

import os
import yaml
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器类"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            # 获取配置文件路径
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config',
                'system_config.yaml'
            )
            
            # 如果配置文件不存在，使用默认配置
            if not os.path.exists(config_path):
                logger.warning(f"配置文件不存在: {config_path}")
                self._config = self._get_default_config()
                return
            
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
            
            logger.info("配置文件加载成功")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'cloud': {
                'tencent': {
                    'cos': {
                        'secret_id': '',
                        'secret_key': '',
                        'region': 'ap-guangzhou',
                        'bucket': 'crush-temp-1384444369',
                        'domain': 'https://crush-temp-1384444369.cos.ap-guangzhou.myqcloud.com',
                        'upload_folder': 'crush-temp-1384444369/uploads'
                    }
                }
            },
            'upload': {
                'allowed_extensions': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
                'max_file_size': 10485760,  # 10MB
                'image_processing': {
                    'auto_compress': True,
                    'quality': 85,
                    'max_width': 4096,
                    'max_height': 4096
                },
                'naming': {
                    'use_timestamp': True,
                    'use_uuid': True,
                    'prefix': 'upload'
                }
            },
            'api': {
                'version': 'v1',
                'prefix': '/api/core'
            },
            'security': {
                'validate_file_type': True,
                'rate_limit': {
                    'enabled': True,
                    'max_requests_per_minute': 60
                }
            },
            'logging': {
                'log_uploads': True,
                'level': 'INFO'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'cloud.tencent.cos.secret_id'
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"获取配置失败 {key}: {e}")
            return default
    
    def get_cos_config(self) -> Dict[str, Any]:
        """获取腾讯云COS配置"""
        return self.get('cloud.tencent.cos', {})
    
    def get_upload_config(self) -> Dict[str, Any]:
        """获取上传配置"""
        return self.get('upload', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.get('api', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get('security', {})
    
    def reload_config(self):
        """重新加载配置文件"""
        self._config = None
        self._load_config()
        logger.info("配置文件已重新加载")


# 创建全局配置管理器实例
config_manager = ConfigManager()