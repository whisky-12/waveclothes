"""
服务工厂类
统一管理所有构图服务
"""

from typing import Dict, Any, List
from .basic_compose_service import BasicComposeService
from .advanced_compose_service import AdvancedComposeService
import logging


logger = logging.getLogger(__name__)


class ServiceFactory:
    """服务工厂类"""
    
    _services = None
    
    @classmethod
    def get_service(cls, service_type: str):
        """
        获取指定类型的服务实例
        
        Args:
            service_type: 服务类型 (basic, advanced)
        
        Returns:
            服务实例
        """
        if service_type == 'basic':
            return BasicComposeService()
        elif service_type == 'advanced':
            return AdvancedComposeService()
        else:
            raise ValueError(f"不支持的服务类型: {service_type}")
    
    @classmethod
    def submit_basic_task(cls, prompt: str, image_url: str,
                       example_image_url: str = None,
                       user_id: str = 'anonymous') -> Dict[str, Any]:
        """
        快捷方法：提交基础构图任务

        Args:
            prompt: 提示词
            image_url: 基础图像URL
            example_image_url: 示例图像URL（可选）
            user_id: 用户ID

        Returns:
            Dict: 任务结果
        """
        service = BasicComposeService()
        return service.submit_task(prompt, image_url, example_image_url, user_id)

    @classmethod
    def submit_advanced_task(cls, prompt: str, images: List[Dict[str, Any]] = None,
                          image_url: str = None,
                          composition_type: str = 'grid', layout: Dict = None,
                          example_image_url: str = None,
                          user_id: str = 'anonymous') -> Dict[str, Any]:
        """
        快捷方法：提交高级构图任务

        Args:
            prompt: 提示词
            images: 图像列表 (可选)
            image_url: 单张图像URL (可选，与images二选一)
            composition_type: 构图类型
            layout: 布局参数
            example_image_url: 示例图像URL（可选）
            user_id: 用户ID

        Returns:
            Dict: 任务结果
        """
        service = AdvancedComposeService()
        return service.submit_task(prompt, images, image_url, composition_type, layout, example_image_url, user_id)
    
    @classmethod
    def get_all_queue_info(cls) -> Dict[str, Dict[str, str]]:
        """
        获取所有服务的队列信息
        
        Returns:
            Dict: 服务队列信息
        """
        return {
            'basic': BasicComposeService().get_queue_names(),
            'advanced': AdvancedComposeService().get_queue_names()
        }
