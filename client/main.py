"""
FastAPI主应用 - Client层
支持多个构图服务
"""

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import time
from typing import Dict, Any
from services.service_factory import ServiceFactory
from services.cos_service import cos_service
from config import Config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="WaveClothes 多服务图像生成系统",
    description="基于RabbitMQ的分布式多构图服务系统",
    version="2.0.0"
)

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/ai-camera-demo.html", response_class=HTMLResponse)
async def ai_camera_demo(request: Request):
    """AI 拍摄页面"""
    return templates.TemplateResponse("ai-camera-demo.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "waveclothes-client-multi",
        "timestamp": time.time(),
        "supported_services": list(Config.QUEUE_CONFIG.keys()),
        "queue_info": ServiceFactory.get_all_queue_info()
    }


@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片到腾讯云COS

    参数：
    - file: 图片文件

    Returns:
        - success: 是否成功
        - url: 图片访问URL
    """
    try:
        # 记录文件信息
        logger.info(f"接收到的文件 - 文件名: {file.filename}, Content-Type: {file.content_type}")

        # 验证文件类型
        if file.content_type and not file.content_type.startswith('image/'):
            logger.warning(f"文件类型验证失败: {file.content_type}")
            raise HTTPException(status_code=400, detail="只支持图片文件上传")

        # 上传文件到COS
        logger.info("开始上传到COS...")
        upload_result = cos_service.upload_file(file, folder='temp')

        logger.info(f"COS上传结果: {upload_result}")

        if not upload_result.get('success'):
            error_msg = upload_result.get('error', '上传失败')
            logger.error(f"COS上传失败: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        # 返回上传结果
        logger.info(f"上传成功，URL: {upload_result['data']['url']}")
        return {
            "success": True,
            "url": upload_result['data']['url']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.post("/api/basic/compose")
async def submit_basic_compose(task_data: Dict[str, Any]):
    """
    提交基础构图任务

    参数：
    - image_url: 基础图像URL (必填)
    - style_type: 特效风格类型 (style1, style2, style3, style4, style5, style6) (可选)
    - user_id: 用户ID (可选)
    """
    try:
        # 验证必填参数
        if not task_data.get("image_url"):
            raise HTTPException(status_code=400, detail="image_url参数不能为空")

        # 获取风格类型
        style_type = task_data.get("style_type")
        image_url = task_data.get("image_url")
        user_id = task_data.get("user_id", "anonymous")

        # 根据风格类型设置不同参数
        prompt = ""
        example_image_url = None

        #新年烟花
        if style_type == "new_year_style":
            # 风格1参数配置
            prompt = "请勿以任何方式修改原始照片。保持原始图像完全不变，包括主体、背景、光线、色彩、视角和整体构图。原始主体必须保持逼真且未被改动。仅使用上传的图像作为身份和环境的唯一来源。精确保留主体、相机角度构图、天际线、建筑物、灯光、地平线和构图。不要修改或风格化背景或天际线。仅在现有天空中添加烟花。添加超逼真、专业的新年前夜烟花，其规模和效果与纽约真实的烟花相匹配。使用物理上精确的烟火（菊花、垂柳、棕榈、噼啪作响的金色爆发），具有层次感、逼真的烟雾、薄雾、渐逝的余烬和微妙的天空照明。通过协调的空中烟花编排形成“2026”，而非火花棒或霓虹文字。这些数字应醒目、清晰、远距离可辨，采用明亮的白色和香槟金，自然地融入天空，带有逼真的烟雾和消散效果。匹配原始的寒冷冬夜光线。颜色限制为白色、金色以及微妙的红色或蓝色点缀。不要过度饱和，也不要给建筑物或主体添加光晕。让烟花位于主体后方和上方，避免重叠。不要改变天际线轮廓或视角。风格：超逼真、电影感但自然、高动态范围。禁用：天际线变化、地标改动、火花棒书写、霓虹文字、卡通效果、奇幻色彩、夸张的光晕或人工智能塑料质感。"
            example_image_url = None

        elif style_type == "winter_four_frame_grid":
            # 风格2参数配置
            prompt = ("创建一个逼真的 2×2 单人照片网格拼贴画，四幅画面中均为同一位年轻亚裔女性。所有画面中的面部特征、脸型、皮肤质感、发型和身份必须 100% "
                      "一致，不能有任何变化。主题：圣诞冬季人像，沉浸式降雪氛围，高端工作室时尚摄影。主体：年轻亚裔女性（20-23 "
                      "岁），面容精致优雅，拥有大而有神的双眼皮眼睛、高颧骨，肌肤白皙如瓷，质感真实，毛孔清晰可见。妆容（重要 —— "
                      "精致冬日妆容）：冬日轻薄透亮的妆容风格。底妆通透干净，带有自然光泽。脸颊上淡淡晕染着柔和细腻的粉色腮红。淡雅的裸粉色眼影，妆面干净。极细的内眼线修饰眼型，毫无厚重感。睫毛自然卷曲，根根分明，精致动人。"
                      "水润有光泽的玫瑰豆沙色 / 柔和淡紫色唇釉，质地柔软水润。整体妆容显得清新、优雅且高端。发型（重要 —— 自然动感）：齐肩深棕色头发，带有柔和的蓬松度和自然的垂坠感。几缕纤细的发丝被冬日微风轻轻吹起。"
                      "一些散落的发丝轻柔地拂过脸颊和下颌线附近。头发的动感显得微妙、可控且自然 —— 绝不凌乱，也不过分夸张。服装（所有画面保持一致）：鲜红色粗针织无边便帽，鲜红色粗羊毛围巾（质感优良，尽显高级），黑色羊毛大衣。"
                      "帽子的针织纹路、围巾的褶皱、发丝、肩膀和大衣表面都明显积有雪花。背景与氛围（重要）：高调明亮的白色工作室背景，干净且富有光泽。纯白色调，带有柔和的光晕，无灰色调、无渐变、无纹理。在明亮的背景下，雪花依然清晰可见。"
                      "雪景与氛围：大量多层次的雪花布满整个场景。前景是大片柔软的雪花，主体周围是中等大小的雪花，背景则是细小的飘雪。雪花缓缓飘落，有些略带动态模糊，柔和地反射着光线。"
                      "光线与氛围：专业工作室柔光照明，以清冷的冬日自然光为基调，脸部带有微妙的温暖高光。光线均匀，对比度柔和，皮肤过渡自然，无刺眼阴影。营造出干净、明亮、通透且优雅的冬日氛围。相机与画质：85 毫米人像镜头效果，浅景深（f/1.8–2.8）。高分辨率，超逼真的皮肤细节，高端时尚人像质感，色彩平衡精致自然。2×2 画面构图：左上：近距离工作室人像。女性轻轻将红色围巾拢在唇边附近，直视镜头。几缕纤细的发丝轻柔地划过脸颊。雪花从镜头前飘过，增添了层次感。表情温暖而优雅。右上：侧颜人像。女性微微抬头望向飘落的雪花。微风拂起脸部附近的几缕发丝，更添柔美与动感。左下：正面人像，头上举着一把红色雨伞。伞沿堆积着雪花。头发保持整齐，仅脸颊附近有微妙的动感。目光平静而沉稳。右下：四分之三侧面人像。女性身体微微转动，轻轻触碰着围巾。一抹温柔的微笑，几缕散落的发丝拂过脸庞，营造出自然而亲切的冬日感觉。")
            example_image_url = None

        #宽幅拍立得
        elif style_type == "wide_format_instant_camera":
            # 风格3参数配置
            prompt = """
                        一张横向宽幅的宝丽来照片，采用风景 orientation。一个单独的宽幅宝丽来相框内，
                        有两张人像照片水平并排放置在同一个相框中。这张宝丽来照片的宽度明显大于高度，
                        类似于复古的宽幅即时胶片格式。

                        宝丽来照片放置在白色的桌面表面上，桌面带有细微、逼真的纹理（细腻的纸张或哑光桌面纹理），
                        与光滑纯白的宝丽来边框形成明显区分。桌面不反光。
                        宝丽来下方有柔和、细腻的接触阴影，使其自然地置于表面上，
                        边缘附近的阴影稍深，并向外逐渐变淡。

                        重要背景规则：
                        在宝丽来相框内，两张照片都必须有干净、朴素的白色墙壁背景。
                        背景是真实的白色工作室墙壁，光线均匀，没有图案、没有物体、没有风景。
                        完全替换并覆盖原始照片的背景。
                        不要保留、参考或重建原始图像中的任何背景元素。
                        只保留主体；背景必须重新生成为白色墙壁。

                        宝丽来相框内：
                        两张图像都以同一位年轻女性为特征，
                        保持她的脸部、面部特征、发型、服装和妆容与参考图像完全一致。
                        妆容是柔和的自然妆，皮肤光洁。

                        左侧照片：
                        - 直视镜头
                        - 表情平和、温柔
                        - 姿势放松、自然

                        右侧照片：
                        - 正对镜头
                        - 在脸部附近做出一个小巧、自然的 V 字手势（和平手势），
                        捕捉的是手势进行中的状态，而非固定姿势
                        - 手部和肩部有轻微动作，营造出一种 candid、介于两个动作之间的瞬间
                        - 手指放松，不僵硬，也不是完美对齐的
                        - 表情柔和、生动，带有细微的动态感，自然而不费力

                        光线采用柔和的工作室灯光，闪光灯经过柔和扩散，明亮但不过曝。
                        纯净的白色色调带有细微的暖色调底色。
                        阴影柔和，没有强烈的对比度。

                        整体氛围：
                        干净、简约、具有编辑感、胶片感。
                        柔焦，略带模糊，细微的胶片颗粒，柔和的薄雾感，低对比度，
                        梦幻而怀旧的即时胶片感觉。
                        高光部分有轻微过曝和柔和的扩散效果。
                        具有复古宝丽来摄影特有的自然柔和感。
                        没有文字、没有标识、没有水印。
                        不锐利、不清晰，呈现出真实的即时照片质感。
                    """
            example_image_url = None

        #2026雪地图
        elif style_type == "style4":
            # 风格4参数配置
            prompt = """
            生成一张俯视视角的雪地照片。

            从线描的角度先提取图中的主体角色线条轮廓，
            再以 1:1 的比例将轮廓印刻在雪地上。
            线条干净、清晰，并向下凹陷，
            模仿用手指在雪地上画出来的效果。

            整体风格极简、干净，照片般真实。

            画面的上方或下方，
            有一行同样模仿手指在雪地上画出来的文字：
            “2026你好”。

            柔和的冬日阳光照射在凹陷的线条内部，
            形成微妙而自然的阴影，
            清晰地展示线条的深度。

            低角度的阳光强调雪的真实质感和凹槽的立体深度，
            投下柔和、精致且真实的阴影。

            整体氛围：
            宁静、极简、高细节，
            具有冬日的浪漫氛围。
            高清，近景拍摄，
            真实细腻的雪地质感。
"""
            example_image_url = None

        # 卡通涂鸦
        elif style_type == "doodle_subject":
            # 风格5参数配置
            prompt = """
            基于原始图像，将整个场景制作成带有手绘卡通风格叠加层的混合媒体插画。

            根据原始图像中的现有元素，
            将环境转换为带有明亮但均衡色彩填充的轮廓卡通草图。
            只对场景中存在的物体进行风格化处理，
            如建筑、城市元素、自然细节或室内结构，
            使其自然地与图像内容相融合。

            添加适量有趣的涂鸦来丰富构图，
            将它们自然地放置在图像的开阔区域或次要区域。
            这些涂鸦可以包括漂浮的图形形状、心形、星星、箭头、面板、素描线条或柔和的装饰元素，
            应与场景布局相呼应，而非遵循固定模式。
            在适用时，有选择地在合适的表面或结构上使用攀爬线条、藤蔓或装饰性草图。

            避免图像过于拥挤——保持视觉密度简洁、生动且均衡。

            保持主体完全真实、清晰且不受任何改动。
            不要改变主体的面部特征、皮肤纹理、光线或比例。

            整体风格应给人以有趣、年轻和轻快的感觉，
            类似于叠加在真实照片上的手绘涂鸦。
            """
            example_image_url = None

        # 换装体验
        elif style_type == "selfie_living":
            # 风格6参数配置
            prompt = """
            附图人物的全身自拍照，身处明亮的现代客厅。

            人物一手持白色智能手机（对着自己自拍，但不要挡住脸），
            背景包括：
            - 浅灰色沙发
            - 白色格纹抱枕
            - 木质小边凳
            - 绿植盆栽
            - 挂有装饰画的墙面

            光线为暖调自然光，人物姿势随性松弛，
            整体呈现超写实质感。

            注意：
            - 不要改变人物的面部特征
            - 不要改变人物的服装
            """
            example_image_url = None

        # 使用服务工厂提交任务
        result = ServiceFactory.submit_basic_task(
            prompt=prompt,
            image_url=image_url,
            example_image_url=example_image_url,
            user_id=user_id
        )

        if result is None:
            raise HTTPException(status_code=504, detail="任务处理超时")

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交基础构图任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@app.post("/api/advanced/compose")
async def submit_advanced_compose(task_data: Dict[str, Any]):
    """
    提交高级构图任务

    参数：
    - images: 图像列表，每个元素包含 url 和 weight (可选)
    - image_url: 单张图像URL (可选，与images二选一)
    - style_type: 特效风格类型 (style1, style2, style3, style4, style5, style6) (可选)
    - user_id: 用户ID (可选)
    """
    try:
        # 支持两种模式：images数组 或 单张image_url
        images = task_data.get("images")
        image_url = task_data.get("image_url")

        if not images and not image_url:
            raise HTTPException(status_code=400, detail="images或image_url参数必须提供一个")

        # 获取风格类型
        style_type = task_data.get("style_type")
        user_id = task_data.get("user_id", "anonymous")

        # 根据风格类型设置不同参数
        prompt = ""
        example_image_url = None
        composition_type = "grid"
        layout = {}

        if style_type == "style1":
            # 风格1参数配置
            prompt = ""
            example_image_url = None
            composition_type = "grid"
            layout = {}

        elif style_type == "style2":
            # 风格2参数配置
            prompt = ""
            example_image_url = None
            composition_type = "grid"
            layout = {}

        elif style_type == "style3":
            # 风格3参数配置
            prompt = ""
            example_image_url = None
            composition_type = "grid"
            layout = {}

        elif style_type == "style4":
            # 风格4参数配置
            prompt = ""
            example_image_url = None
            composition_type = "grid"
            layout = {}

        elif style_type == "style5":
            # 风格5参数配置
            prompt = ""
            example_image_url = None
            composition_type = "grid"
            layout = {}

        elif style_type == "style6":
            # 风格6参数配置
            prompt = ""
            example_image_url = None
            composition_type = "grid"
            layout = {}

        # 使用服务工厂提交任务
        result = ServiceFactory.submit_advanced_task(
            prompt=prompt,
            images=images,
            image_url=image_url,
            example_image_url=example_image_url,
            composition_type=composition_type,
            layout=layout,
            user_id=user_id
        )

        if result is None:
            raise HTTPException(status_code=504, detail="任务处理超时")

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交高级构图任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@app.get("/api/services")
async def get_services():
    """获取所有可用服务信息"""
    return {
        "services": ServiceFactory.get_all_queue_info(),
        "supported_types": list(Config.QUEUE_CONFIG.keys())
    }


@app.get("/api/tasks/{task_id}")
async def get_task_result(task_id: str):
    """
    获取任务结果（预留接口，用于异步模式）
    """
    return {
        "task_id": task_id,
        "status": "not_implemented"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.APP_HOST,
        port=Config.APP_PORT,
        reload=True
    )
