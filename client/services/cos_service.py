"""
腾讯云COS上传服务
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Optional, Any
import logging
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError, CosClientError
from PIL import Image
import io
import mimetypes

from .config_manager import config_manager

logger = logging.getLogger(__name__)


class COSService:
    """腾讯云COS上传服务"""
    
    def __init__(self):
        """初始化COS服务"""
        self.cos_config = config_manager.get_cos_config()
        self.upload_config = config_manager.get_upload_config()
        self.client = self._init_client()
    
    def _init_client(self) -> CosS3Client:
        """初始化COS客户端"""
        try:
            required_fields = ['secret_id', 'secret_key', 'region']
            for field in required_fields:
                if not self.cos_config.get(field):
                    raise ValueError(f"COS配置缺少必要字段: {field}")
            
            config = CosConfig(
                Region=self.cos_config['region'],
                SecretId=self.cos_config['secret_id'],
                SecretKey=self.cos_config['secret_key']
            )
            return CosS3Client(config)
        except Exception as e:
            logger.error(f"初始化COS客户端失败: {e}")
            raise
    
    def generate_filename(self, original_filename: str) -> str:
        """生成新的文件名"""
        # 获取文件扩展名
        name, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        
        # 配置文件名生成规则
        naming_config = self.upload_config.get('naming', {})
        prefix = naming_config.get('prefix', 'upload')
        
        parts = [prefix]
        
        if naming_config.get('use_timestamp', True):
            parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        if naming_config.get('use_uuid', True):
            parts.append(str(uuid.uuid4())[:8])
        
        parts.append(f"{name[:20]}")  # 保留原文件名前20个字符
        
        filename = "_".join(parts) + ext
        return filename
    
    def validate_file(self, file) -> Dict[str, Any]:
        """验证文件"""
        result = {
            'valid': True,
            'error': None,
            'file_size': 0,
            'is_image': False
        }

        try:
            # 获取底层文件对象（兼容FastAPI的UploadFile）
            actual_file = file.file if hasattr(file, 'file') else file

            # 检查文件大小
            actual_file.seek(0, os.SEEK_END)
            file_size = actual_file.tell()
            actual_file.seek(0)

            result['file_size'] = file_size
            max_size = self.upload_config.get('max_file_size', 10 * 1024 * 1024)

            if file_size > max_size:
                result['valid'] = False
                result['error'] = f"文件大小超过限制 ({max_size} 字节)"
                return result

            # 检查文件扩展名
            original_filename = getattr(file, 'filename', None) or getattr(file, 'name', None) or 'unknown.jpg'
            if not original_filename:
                result['valid'] = False
                result['error'] = "文件名不能为空"
                return result

            name, ext = os.path.splitext(original_filename)
            ext = ext[1:].lower() if ext else ''

            allowed_extensions = self.upload_config.get('allowed_extensions', [])
            if ext not in allowed_extensions:
                result['valid'] = False
                result['error'] = f"不支持的文件类型: {ext}"
                return result

            # 检查是否为图片
            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
            result['is_image'] = ext in image_extensions

            # 如果是图片，验证图片格式
            if result['is_image']:
                try:
                    actual_file.seek(0)
                    img = Image.open(actual_file)
                    img.verify()  # 验证图片文件

                    # 检查图片尺寸
                    actual_file.seek(0)
                    img = Image.open(actual_file)
                    width, height = img.size

                    max_width = self.upload_config.get('image_processing', {}).get('max_width', 4096)
                    max_height = self.upload_config.get('image_processing', {}).get('max_height', 4096)

                    if width > max_width or height > max_height:
                        result['valid'] = False
                        result['error'] = f"图片尺寸超过限制 ({max_width}x{max_height})"
                        return result

                    actual_file.seek(0)

                except Exception as e:
                    result['valid'] = False
                    result['error'] = f"无效的图片文件: {str(e)}"
                    return result

            actual_file.seek(0)

        except Exception as e:
            result['valid'] = False
            result['error'] = f"文件验证失败: {str(e)}"

        return result
    
    def process_image(self, file, filename: str) -> bytes:
        """处理图片（压缩等）"""
        # 获取底层文件对象（兼容FastAPI的UploadFile）
        actual_file = file.file if hasattr(file, 'file') else file

        if not self.upload_config.get('image_processing', {}).get('auto_compress', False):
            actual_file.seek(0)
            return actual_file.read()

        try:
            actual_file.seek(0)
            img = Image.open(actual_file)

            # 转换为RGB模式（处理RGBA等）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 获取配置
            quality = self.upload_config.get('image_processing', {}).get('quality', 85)

            # 压缩图片
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)

            logger.info(f"图片压缩完成: {filename}")
            return output.read()

        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            actual_file.seek(0)
            return actual_file.read()
    
    def upload_file(self, file, folder: Optional[str] = None) -> Dict[str, Any]:
        """
        上传文件到COS
        
        Args:
            file: 上传的文件对象
            folder: 目标文件夹（可选）
            
        Returns:
            上传结果字典
        """
        try:
            # 验证文件
            validation_result = self.validate_file(file)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'code': 'INVALID_FILE'
                }
            
            # 获取文件信息
            original_filename = getattr(file, 'filename', None) or getattr(file, 'name', None) or 'unknown.jpg'
            file_size = validation_result['file_size']
            
            # 生成新文件名
            new_filename = self.generate_filename(original_filename)
            
            # 处理文件内容
            if validation_result['is_image']:
                file_content = self.process_image(file, new_filename)
            else:
                actual_file = file.file if hasattr(file, 'file') else file
                actual_file.seek(0)
                file_content = actual_file.read()
            
            # 构建远程路径
            upload_folder = folder or self.cos_config.get('upload_folder', 'uploads')
            remote_key = f"{upload_folder}/{new_filename}"
            
            # 上传到COS
            # no-cache 确保每次请求都验证最新 header
            cache_control = "no-cache, max-age=0, must-revalidate"

            # 自动根据扩展名猜 Content-Type
            content_type, _ = mimetypes.guess_type(new_filename)
            if not content_type:
                # 如果无法猜测，默认用二进制流
                content_type = "application/octet-stream"
            # 执行上传
            response = self.client.put_object(
                Bucket=self.cos_config["bucket"],
                Key=remote_key,
                Body=file_content,
                StorageClass="STANDARD",
                EnableMD5=True,

                ContentType=content_type,
                ContentDisposition="inline",  # 明确告诉浏览器这是展示内容
                CacheControl=cache_control  # 避免错误 header 缓存
            )
            
            # 生成访问URL
            file_url = f"{self.cos_config['domain']}/{remote_key}"
            
            # 计算文件MD5
            md5_hash = hashlib.md5(file_content).hexdigest()
            
            # 记录日志
            logger.info(f"文件上传成功: {original_filename} -> {remote_key}")
            
            return {
                'success': True,
                'data': {
                    'url': file_url,
                    'filename': new_filename,
                    'original_name': original_filename,
                    'size': file_size,
                    'md5': md5_hash,
                    'folder': upload_folder,
                    'content_type': 'image' if validation_result['is_image'] else 'document'
                },
                'etag': response.get('ETag', ''),
                'upload_time': datetime.now().isoformat()
            }
            
        except (CosServiceError, CosClientError) as e:
            logger.error(f"COS上传失败: {e}")
            return {
                'success': False,
                'error': f"COS服务错误: {str(e)}",
                'code': 'COS_ERROR'
            }
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return {
                'success': False,
                'error': f"上传失败: {str(e)}",
                'code': 'UPLOAD_ERROR'
            }
    
    def delete_file(self, remote_key: str) -> Dict[str, Any]:
        """删除COS文件"""
        try:
            self.client.delete_object(
                Bucket=self.cos_config['bucket'],
                Key=remote_key
            )
            
            logger.info(f"文件删除成功: {remote_key}")
            return {
                'success': True,
                'message': '文件删除成功'
            }
            
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return {
                'success': False,
                'error': f"删除失败: {str(e)}"
            }
    
    def get_file_info(self, remote_key: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            response = self.client.head_object(
                Bucket=self.cos_config['bucket'],
                Key=remote_key
            )
            
            return {
                'success': True,
                'data': {
                    'key': remote_key,
                    'size': response.get('Content-Length', 0),
                    'etag': response.get('ETag', '').strip('"'),
                    'last_modified': response.get('Last-Modified'),
                    'content_type': response.get('Content-Type', 'application/octet-stream')
                }
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {
                'success': False,
                'error': f"获取文件信息失败: {str(e)}"
            }


# 创建全局COS服务实例
cos_service = COSService()