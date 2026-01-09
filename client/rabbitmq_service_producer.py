"""
RabbitMQ服务生产者 - Client层
支持多个构图服务的任务发送和结果接收
"""

import pika
import json
import logging
import uuid
import time
from typing import Dict, Any, Optional
from config import Config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQServiceProducer:
    """
    RabbitMQ服务生产者类
    
    功能：
    1. 发送任务到指定服务的任务队列
    2. 从对应的结果队列接收处理结果
    3. 支持同步和异步模式
    """
    
    def __init__(self):
        """初始化生产者"""
        self.config = Config()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.response = None
        self.task_id = None
        self.current_service_type = None
        
    def connect(self) -> bool:
        """连接到RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                self.config.RABBITMQ_USER,
                self.config.RABBITMQ_PASSWORD
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config.RABBITMQ_HOST,
                port=self.config.RABBITMQ_PORT,
                virtual_host=self.config.RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info(f"生产者连接成功: {self.config.RABBITMQ_HOST}:{self.config.RABBITMQ_PORT}")
            return True
            
        except Exception as e:
            logger.error(f"生产者连接失败: {e}")
            return False
    
    def _on_result(self, ch, method, props, body):
        """处理结果消息"""
        result = json.loads(body.decode('utf-8'))
        logger.info(f"收到结果: {result.get('task_id')}")
        
        # 检查是否是我们等待的任务结果
        if self.task_id and result.get('task_id') == self.task_id:
            self.response = result
    
    def _declare_result_queue(self, result_queue: str) -> bool:
        """声明结果队列并开始消费"""
        try:
            self.channel.queue_declare(
                queue=result_queue,
                durable=True
            )
            
            self.channel.basic_consume(
                queue=result_queue,
                on_message_callback=self._on_result,
                auto_ack=True
            )
            return True
        except Exception as e:
            logger.error(f"声明结果队列失败: {e}")
            return False
    
    def send_task(self, service_type: str, task_data: Dict[str, Any], 
                  timeout: int = 120) -> Optional[Dict[str, Any]]:
        """
        发送任务到指定服务并等待结果（同步）
        
        Args:
            service_type: 服务类型 (basic, advanced)
            task_data: 任务数据
            timeout: 超时时间（秒）
        
        Returns:
            Dict: 任务结果
        """
        if service_type not in self.config.QUEUE_CONFIG:
            logger.error(f"不支持的服务类型: {service_type}")
            return None
        
        if not self.connect():
            return None
        
        queue_config = self.config.QUEUE_CONFIG[service_type]
        task_queue = queue_config['task_queue']
        result_queue = queue_config['result_queue']
        
        self.response = None
        self.task_id = task_data.get('task_id')
        self.current_service_type = service_type
        
        # 声明并订阅结果队列
        if not self._declare_result_queue(result_queue):
            self.close()
            return None
        
        try:
            # 发送任务到任务队列
            self.channel.basic_publish(
                exchange='',
                routing_key=task_queue,
                properties=pika.BasicProperties(
                    delivery_mode=2
                ),
                body=json.dumps(task_data)
            )
            
            logger.info(f"任务已发送到 {service_type} 服务队列: {task_queue}, task_id: {self.task_id}")
            
            # 等待结果
            start_time = time.time()
            while self.response is None:
                self.connection.process_data_events(time_limit=1)
                if time.time() - start_time > timeout:
                    logger.warning("等待结果超时")
                    self.close()
                    return None
            
            self.close()
            return self.response
            
        except Exception as e:
            logger.error(f"发送任务失败: {e}")
            self.close()
            return None
    
    def send_task_async(self, service_type: str, task_data: Dict[str, Any]) -> bool:
        """
        发送任务（异步，不等待结果）
        
        Args:
            service_type: 服务类型
            task_data: 任务数据
        
        Returns:
            bool: 是否发送成功
        """
        if service_type not in self.config.QUEUE_CONFIG:
            logger.error(f"不支持的服务类型: {service_type}")
            return False
        
        if not self.connect():
            return False
        
        queue_config = self.config.QUEUE_CONFIG[service_type]
        task_queue = queue_config['task_queue']
        
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=task_queue,
                properties=pika.BasicProperties(
                    delivery_mode=2
                ),
                body=json.dumps(task_data)
            )
            
            logger.info(f"任务已发送（异步）到 {service_type} 服务: {task_data.get('task_id')}")
            self.close()
            return True
            
        except Exception as e:
            logger.error(f"发送任务失败: {e}")
            self.close()
            return False
    
    def close(self):
        """关闭连接"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.debug("生产者连接已关闭")
