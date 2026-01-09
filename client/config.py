import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Client层配置"""

    # RabbitMQ配置
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')

    # 构图服务队列配置
    # 服务1: 基础构图服务
    COMPOSE_SERVICE_1_QUEUE = os.getenv('COMPOSE_SERVICE_1_QUEUE', 'compose.service.basic')
    COMPOSE_SERVICE_1_RESULT_QUEUE = os.getenv('COMPOSE_SERVICE_1_RESULT_QUEUE', 'compose.service.basic.result')

    # 服务2: 高级构图服务
    COMPOSE_SERVICE_2_QUEUE = os.getenv('COMPOSE_SERVICE_2_QUEUE', 'compose.service.advanced')
    COMPOSE_SERVICE_2_RESULT_QUEUE = os.getenv('COMPOSE_SERVICE_2_RESULT_QUEUE', 'compose.service.advanced.result')

    # 队列映射配置
    QUEUE_CONFIG = {
        'basic': {
            'task_queue': COMPOSE_SERVICE_1_QUEUE,
            'result_queue': COMPOSE_SERVICE_1_RESULT_QUEUE
        },
        'advanced': {
            'task_queue': COMPOSE_SERVICE_2_QUEUE,
            'result_queue': COMPOSE_SERVICE_2_RESULT_QUEUE
        }
    }

    # FastAPI配置
    APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
    APP_PORT = 8005

    # 任务超时配置
    TASK_TIMEOUT = 120  # 秒
