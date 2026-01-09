"""
基础服务类
定义所有构图服务的基类接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pika
import json
import time
import logging


logger = logging.getLogger(__name__)


class BaseComposeService(ABC):
    """构图服务基类"""
    
    def __init__(self, queue_name: str, result_queue_name: str):
        """
        初始化服务
        
        Args:
            queue_name: 任务队列名称
            result_queue_name: 结果队列名称
        """
        self.queue_name = queue_name
        self.result_queue_name = result_queue_name
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.response = None
        self.task_id = None
    
    @abstractmethod
    def get_queue_names(self) -> Dict[str, str]:
        """
        获取队列名称
        
        Returns:
            Dict: 包含 task_queue 和 result_queue
        """
        pass
    
    def connect(self) -> bool:
        """连接到RabbitMQ"""
        from config import Config
        config = Config()
        
        try:
            credentials = pika.PlainCredentials(
                config.RABBITMQ_USER,
                config.RABBITMQ_PASSWORD
            )
            
            parameters = pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
                port=config.RABBITMQ_PORT,
                virtual_host=config.RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info(f"[{self.queue_name}] 连接成功")
            return True
            
        except Exception as e:
            logger.error(f"[{self.queue_name}] 连接失败: {e}")
            return False
    
    def _declare_result_queue(self) -> bool:
        """声明结果队列并开始消费"""
        try:
            # 声明结果队列
            self.channel.queue_declare(
                queue=self.result_queue_name,
                durable=True
            )
            logger.info(f"[{self.queue_name}] 结果队列已声明: {self.result_queue_name}")
            
            # 设置预取数量为1，确保公平分配
            self.channel.basic_qos(prefetch_count=1)
            
            # 开始消费结果队列
            self.channel.basic_consume(
                queue=self.result_queue_name,
                on_message_callback=self._on_result,
                auto_ack=False  # 手动确认，避免消息丢失
            )
            logger.info(f"[{self.queue_name}] 开始监听结果队列")
            return True
        except Exception as e:
            logger.error(f"[{self.queue_name}] 声明结果队列失败: {e}")
            return False
    
    def _on_result(self, ch, method, props, body):
        """处理结果消息"""
        try:
            result = json.loads(body.decode('utf-8'))
            result_task_id = result.get('task_id')
            logger.info(f"[{self.queue_name}] 收到结果: task_id={result_task_id}, 期望的task_id={self.task_id}")
            
            if self.task_id and result_task_id == self.task_id:
                self.response = result
                logger.info(f"[{self.queue_name}] 结果匹配成功，设置响应")
            
            # 手动确认消息
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"[{self.queue_name}] 消息已确认")
        except Exception as e:
            logger.error(f"[{self.queue_name}] 处理结果时出错: {e}")
    
    def send_task(self, task_data: Dict[str, Any], timeout: int = 120) -> Optional[Dict[str, Any]]:
        """
        发送任务并等待结果（同步）
        
        Args:
            task_data: 任务数据
            timeout: 超时时间（秒）
        
        Returns:
            Dict: 任务结果
        """
        if not self.connect():
            return None
        
        self.response = None
        self.task_id = task_data.get('task_id')
        
        # 声明并订阅结果队列
        if not self._declare_result_queue():
            self.close()
            return None
        
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                properties=pika.BasicProperties(
                    delivery_mode=2
                ),
                body=json.dumps(task_data)
            )
            
            logger.info(f"[{self.queue_name}] 任务已发送: {self.task_id}")
            
            # 等待结果
            start_time = time.time()
            while self.response is None:
                self.connection.process_data_events(time_limit=1)
                if time.time() - start_time > timeout:
                    logger.warning(f"[{self.queue_name}] 等待结果超时")
                    self.close()
                    return None
            
            self.close()
            return self.response
            
        except Exception as e:
            logger.error(f"[{self.queue_name}] 发送任务失败: {e}")
            self.close()
            return None
    
    def send_task_async(self, task_data: Dict[str, Any]) -> bool:
        """
        发送任务（异步，不等待结果）
        
        Args:
            task_data: 任务数据
        
        Returns:
            bool: 是否发送成功
        """
        if not self.connect():
            return False
        
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                properties=pika.BasicProperties(
                    delivery_mode=2
                ),
                body=json.dumps(task_data)
            )
            
            logger.info(f"[{self.queue_name}] 任务已发送（异步）: {task_data.get('task_id')}")
            self.close()
            return True
            
        except Exception as e:
            logger.error(f"[{self.queue_name}] 发送任务失败: {e}")
            self.close()
            return False
    
    def close(self):
        """关闭连接"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.debug(f"[{self.queue_name}] 连接已关闭")
