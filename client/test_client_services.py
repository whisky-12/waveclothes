"""
测试Client层服务
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.basic_compose_service import BasicComposeService
from services.advanced_compose_service import AdvancedComposeService
from services.service_factory import ServiceFactory


def test_basic_service():
    """测试基础构图服务"""
    print("=" * 60)
    print("测试基础构图服务")
    print("=" * 60)
    
    service = BasicComposeService()
    
    # 测试队列名称
    print("\n[测试1] 获取队列名称")
    queue_info = service.get_queue_names()
    print(f"任务队列: {queue_info['task_queue']}")
    print(f"结果队列: {queue_info['result_queue']}")
    
    # 测试异步提交
    print("\n[测试2] 异步提交任务")
    result = service.submit_task_async(
        prompt="Test image",
        image_url="https://example.com/image.jpg",
        width=512,
        height=512
    )
    print(f"提交结果: {result} (应为 True)")


def test_advanced_service():
    """测试高级构图服务"""
    print("\n" + "=" * 60)
    print("测试高级构图服务")
    print("=" * 60)
    
    service = AdvancedComposeService()
    
    # 测试队列名称
    print("\n[测试1] 获取队列名称")
    queue_info = service.get_queue_names()
    print(f"任务队列: {queue_info['task_queue']}")
    print(f"结果队列: {queue_info['result_queue']}")
    
    # 测试异步提交
    print("\n[测试2] 异步提交任务")
    images = [
        {'url': 'https://example.com/img1.jpg', 'weight': 1.0},
        {'url': 'https://example.com/img2.jpg', 'weight': 1.5}
    ]
    result = service.submit_task_async(
        prompt="Advanced composition",
        images=images,
        composition_type='grid'
    )
    print(f"提交结果: {result} (应为 True)")


def test_service_factory():
    """测试服务工厂"""
    print("\n" + "=" * 60)
    print("测试服务工厂")
    print("=" * 60)
    
    # 测试获取服务
    print("\n[测试1] 获取服务实例")
    basic_service = ServiceFactory.get_service('basic')
    print(f"基础服务类型: {type(basic_service).__name__}")
    
    advanced_service = ServiceFactory.get_service('advanced')
    print(f"高级服务类型: {type(advanced_service).__name__}")
    
    # 测试异常处理
    print("\n[测试2] 不支持的服务类型")
    try:
        ServiceFactory.get_service('unknown')
    except ValueError as e:
        print(f"异常捕获: {e}")
    
    # 测试快捷方法
    print("\n[测试3] 快捷方法获取队列信息")
    queue_info = ServiceFactory.get_all_queue_info()
    print(f"队列信息:")
    for service_name, queues in queue_info.items():
        print(f"  {service_name}:")
        print(f"    任务队列: {queues['task_queue']}")
        print(f"    结果队列: {queues['result_queue']}")


if __name__ == '__main__':
    try:
        test_basic_service()
        test_advanced_service()
        test_service_factory()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        print("\n注意：同步任务测试需要RabbitMQ服务器运行中")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
