"""
基础构图服务
提供基础构图功能
"""

import time
from typing import Dict, Any
from config import Config
from .base_service import BaseComposeService


class BasicComposeService(BaseComposeService):
    """基础构图服务"""
    
    def __init__(self):
        """初始化基础构图服务"""
        config = Config()
        super().__init__(
            queue_name=config.COMPOSE_SERVICE_1_QUEUE,
            result_queue_name=config.COMPOSE_SERVICE_1_RESULT_QUEUE
        )
        self.service_name = "basic_compose"
    
    def get_queue_names(self) -> Dict[str, str]:
        """获取队列名称"""
        return {
            'task_queue': self.queue_name,
            'result_queue': self.result_queue_name
        }
    
    def submit_task(self, prompt: str, image_url: str,
                  example_image_url: str = None,
                  user_id: str = 'anonymous') -> Dict[str, Any]:
        """
        提交基础构图任务

        Args:
            prompt: 提示词
            image_url: 基础图像URL
            example_image_url: 示例图像URL（可选）
            user_id: 用户ID

        Returns:
            Dict: 任务结果
        """
        task_id = f"basic_{int(time.time() * 1000)}"

        task_data = {
            'task_id': task_id,
            'prompt': prompt,
            'image_url': image_url,
            'example_image_url': example_image_url,
            'user_id': user_id
        }

        return self.send_task(task_data)

    def submit_task_async(self, prompt: str, image_url: str,
                       example_image_url: str = None,
                       user_id: str = 'anonymous') -> bool:
        """
        异步提交基础构图任务

        Args:
            prompt: 提示词
            image_url: 基础图像URL
            example_image_url: 示例图像URL（可选）
            user_id: 用户ID

        Returns:
            bool: 是否提交成功
        """
        task_id = f"basic_{int(time.time() * 1000)}"

        task_data = {
            'task_id': task_id,
            'prompt': prompt,
            'image_url': image_url,
            'example_image_url': example_image_url,
            'user_id': user_id
        }

        return self.send_task_async(task_data)
