# OCR 服务
# 用 RapidOCR（onnxruntime 版）把扫描件 / 图片识别成文字。
# 模型已内置在 rapidocr_onnxruntime 包中，无需联网下载。
# 采用懒加载 + 优雅降级：OCR 未安装或识别失败时返回空字符串，不影响文本型文档的解析。

import logging

logger = logging.getLogger("contract-review.ocr")

_engine = None
_engine_failed = False


def _get_engine():
    """懒加载 RapidOCR 引擎；失败只记日志，返回 None。"""
    global _engine, _engine_failed
    if _engine is not None:
        return _engine
    if _engine_failed:
        return None
    try:
        from rapidocr_onnxruntime import RapidOCR
        # 关闭方向分类器：合同扫描件基本都是正向的，方向分类会对每一行文字
        # 多做一次模型推理，关闭后可提速。旧版 rapidocr 用 use_angle_cls，
        # 新版（1.4.x）改名为 use_cls，两个都传以兼容不同版本。
        _engine = RapidOCR(use_angle_cls=False, use_cls=False)
    except Exception as e:
        _engine_failed = True
        logger.warning(
            "OCR 引擎初始化失败（rapidocr_onnxruntime 未安装或环境异常）: %s",
            str(e)[:120],
        )
        return None
    return _engine


def ocr_image_path(image_path: str) -> str:
    """
    对一张图片做 OCR，返回识别出的文字（多行用换行连接）。
    引擎不可用或识别失败时返回空字符串，不抛异常。
    """
    engine = _get_engine()
    if engine is None:
        return ""
    try:
        result, _ = engine(str(image_path))
    except Exception as e:
        logger.warning("OCR 识别失败: %s", str(e)[:120])
        return ""
    if not result:
        return ""
    lines = [item[1] for item in result if item and len(item) > 1 and item[1]]
    return "\n".join(lines)
