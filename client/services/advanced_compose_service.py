"""
高级构图服务
提供高级构图功能
"""

import time
from typing import Dict, Any, List
from config import Config
from .base_service import BaseComposeService


class AdvancedComposeService(BaseComposeService):
    """高级构图服务"""
    
    def __init__(self):
        """初始化高级构图服务"""
        config = Config()
        super().__init__(
            queue_name=config.COMPOSE_SERVICE_2_QUEUE,
            result_queue_name=config.COMPOSE_SERVICE_2_RESULT_QUEUE
        )
        self.service_name = "advanced_compose"
    
    def get_queue_names(self) -> Dict[str, str]:
        """获取队列名称"""
        return {
            'task_queue': self.queue_name,
            'result_queue': self.result_queue_name
        }
    
    def submit_task(self, prompt: str, images: List[Dict[str, Any]] = None,
                  image_url: str = None,
                  composition_type: str = 'grid', layout: Dict = None,
                  example_image_url: str = None,
                  user_id: str = 'anonymous') -> Dict[str, Any]:
        """
        提交高级构图任务

        Args:
            prompt: 提示词
            images: 图像列表，每个元素包含 url 和 weight (可选)
            image_url: 单张图像URL (可选，与images二选一)
            composition_type: 构图类型 (grid, collage, blend, overlay, stitch)
            layout: 布局参数
            example_image_url: 示例图像URL（可选）
            user_id: 用户ID

        Returns:
            Dict: 任务结果
        """
        task_id = f"advanced_{int(time.time() * 1000)}"

        task_data = {
            'task_id': task_id,
            'prompt': prompt,
            'images': images if images else [],
            'image_url': image_url,
            'composition_type': composition_type,
            'layout': layout or {},
            'example_image_url': example_image_url,
            'user_id': user_id
        }

        return self.send_task(task_data)

    def submit_task_async(self, prompt: str, images: List[Dict[str, Any]] = None,
                       image_url: str = None,
                       composition_type: str = 'grid', layout: Dict = None,
                       example_image_url: str = None,
                       user_id: str = 'anonymous') -> bool:
        """
        异步提交高级构图任务

        Args:
            prompt: 提示词
            images: 图像列表，每个元素包含 url 和 weight (可选)
            image_url: 单张图像URL (可选，与images二选一)
            composition_type: 构图类型 (grid, collage, blend, overlay, stitch)
            layout: 布局参数
            example_image_url: 示例图像URL（可选）
            user_id: 用户ID

        Returns:
            bool: 是否提交成功
        """
        task_id = f"advanced_{int(time.time() * 1000)}"

        task_data = {
            'task_id': task_id,
            'prompt': prompt,
            'images': images if images else [],
            'image_url': image_url,
            'composition_type': composition_type,
            'layout': layout or {},
            'example_image_url': example_image_url,
            'user_id': user_id
        }

        return self.send_task_async(task_data)
