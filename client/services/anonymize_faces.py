import shutil
import aiofiles
import cv2
import os
import aiohttp
import uuid
from urllib.parse import urlparse, unquote
from threading import Lock
from typing import Tuple
import numpy as np

# MediaPipe 依赖
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 导入 COS 上传服务
from .cos_service import cos_service
# import cos_service
# 模型路径
MODEL_PATH = 'model/selfie_multiclass_256x256.tflite'


class FaceHairSegmenter:
    """人脸和头发分割器"""

    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件缺失: {model_path}，请先下载放置于根目录。")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.ImageSegmenterOptions(
            base_options=base_options,
            output_category_mask=True,
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(options)
        self.lock = Lock()  # 确保线程安全

    def run(self, image_rgb: np.ndarray) -> np.ndarray:
        """执行推理，返回类别掩码"""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        with self.lock:
            # MediaPipe ImageSegmenter 非严格线程安全，建议加锁
            result = self.segmenter.segment(mp_image)
        return result.category_mask.numpy_view()


# 全局初始化，避免每次请求重新加载模型
try:
    global_segmenter = FaceHairSegmenter(MODEL_PATH)
    print(f"✅ 模型 {MODEL_PATH} 加载成功")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    global_segmenter = None


def get_filename_from_url(file_url: str, default_name: str = "temp_image.jpg") -> str:
    """从URL或本地路径提取文件名"""
    if file_url.startswith("http://") or file_url.startswith("https://"):
        # 解析 URL
        path = urlparse(file_url).path  # 获取 URL 路径部分
        filename = os.path.basename(path)
        filename = unquote(filename)  # 处理 URL 编码
        if not filename or "." not in filename:
            filename = default_name
        return filename
    else:
        # 本地文件直接取 basename
        return os.path.basename(file_url) or default_name


async def anonymize_faces_with_hair(
    file_url: str,
    gray_color: Tuple[int, int, int] = (128, 128, 128),
    alpha: float = 1.0
) -> str:
    """
    检测图片中的人脸和头发，并用灰色遮罩覆盖。

    参数：
        file_url (str): 输入图片的本地路径或URL
        gray_color (tuple): 遮罩颜色，默认灰色 (128, 128, 128)
        alpha (float): 遮罩浓度 (0.0 - 1.0)，默认 1.0 (完全不透明)

    返回：
        str: 处理后上传到COS的图片URL

    异常：
        RuntimeError: 模型未能正确加载
        ValueError: 图片加载失败
        Exception: 图片下载失败或上传失败
    """
    if global_segmenter is None:
        raise RuntimeError("服务启动失败：模型未能正确加载")

    # 在 temp 文件夹下创建随机临时目录
    temp_base_dir = os.path.join(os.path.dirname(__file__), "temp")
    temp_dir = os.path.join(temp_base_dir, f"temp_{uuid.uuid4().hex[:12]}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 获取文件名
        filename = get_filename_from_url(file_url)
        local_input_path = os.path.join(temp_dir, f"download_{filename}")
        output_path = os.path.join(temp_dir, f"processed_{filename}")

        # ====== 1. 下载或复制输入图片 ======
        if file_url.startswith("http://") or file_url.startswith("https://"):
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status != 200:
                        raise Exception(f"图片下载失败: {file_url} ({resp.status})")
                    async with aiofiles.open(local_input_path, "wb") as f:
                        await f.write(await resp.read())
        else:
            if not os.path.exists(file_url):
                raise FileNotFoundError(f"本地文件不存在: {file_url}")
            # 使用 shutil 替代 os.system 更加安全
            shutil.copy(file_url, local_input_path)

        # ====== 2. 读取与处理图片 ======

        # 读取图片
        img = cv2.imread(local_input_path)
        if img is None:
            raise ValueError(f"图片加载失败：{local_input_path}")

        # 转为 RGB 供 MediaPipe 使用
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 执行分割
        mask_np = global_segmenter.run(img_rgb)

        # MediaPipe Multiclass 索引: 1=头发, 3=脸部皮肤
        target_indices = [1, 3]

        # 生成二值掩码 (属于人脸或头发的区域为 1)
        face_hair_mask = np.isin(mask_np, target_indices).astype(np.uint8)

        # 对掩码进行膨胀操作，使mask向外扩展
        kernel = np.ones((20, 20), np.uint8)  # 20x20的核，可根据效果调整大小
        face_hair_mask = cv2.dilate(face_hair_mask, kernel, iterations=3)

        # --- 绘制灰色遮罩 ---
        gray_layer = np.zeros_like(img)
        gray_layer[:] = gray_color

        # 仅提取掩码区域
        roi_indices = (face_hair_mask == 1)

        if np.any(roi_indices):  # 如果检测到了人脸或头发
            img_part = img[roi_indices]
            gray_part = gray_layer[roi_indices]

            # 混合运算: 原图*(1-a) + 灰色*a
            blended_part = cv2.addWeighted(img_part, 1 - alpha, gray_part, alpha, 0)

            # 填回原图
            img[roi_indices] = blended_part

        # ====== 3. 保存结果 ======
        cv2.imwrite(output_path, img)
        print(f"处理完成: {output_path}")

        # ====== 4. 上传到COS ======

        # 构造上传到 COS 的 key
        cos_key = f"temp"

        # 调用上传函数
        # 注意：upload_file 需要文件对象，而不是文件路径列表
        # 我们需要打开文件并传递给 upload_file
        with open(output_path, 'rb') as file_obj:
            upload_result = cos_service.upload_file(file_obj, cos_key)

        if not upload_result.get('success'):
            raise Exception(f"图像上传失败: {upload_result.get('error')}")

        return upload_result['data']['url']

    finally:
        # ====== 5. 清理临时文件夹 ======
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"已清理临时文件夹: {temp_dir}")
        except Exception as e:
            print(f"[WARN] 删除临时文件夹失败: {temp_dir}, 错误: {e}")


# 测试 main 函数
if __name__ == "__main__":
    import asyncio

    async def test_anonymize():
        example_image_url = "https://img-hzcc.huozuyun.com/effect_resource/2026/01/12/18/715911a50f6fd96626b122789fad57cd.png"
        try:
            result = await anonymize_faces_with_hair(example_image_url)
            print(f"✅ 处理成功，输出URL: {result}")
        except Exception as e:
            print(f"❌ 处理失败: {e}")

    asyncio.run(test_anonymize())


