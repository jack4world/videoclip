"""
测试 DashScope API 调用
"""
import os
from pathlib import Path

from videoclip.extractors import SubtitleExtractor
from videoclip.analyzers import ContentAnalyzer
from videoclip.config import get_settings
from videoclip.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

def test_subtitle_api():
    """测试字幕提取 API"""
    print("=" * 60)
    print("测试字幕提取 API")
    print("=" * 60)
    
    audio_file = Path("work/audio/WATCH Elon Musk Delivers Remarks at the US - Saudi.wav")
    
    if not audio_file.exists():
        logger.error(f"❌ 音频文件不存在: {audio_file}")
        return False
    
    try:
        extractor = SubtitleExtractor()
        logger.info("✓ API Key 已配置")
        logger.info(f"✓ 开始测试字幕提取...")
        
        result = extractor.extract(str(audio_file))
        logger.info(f"✓ 字幕提取成功: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ 字幕提取失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_content_analyzer_api():
    """测试内容分析 API"""
    print("\n" + "=" * 60)
    print("测试内容分析 API")
    print("=" * 60)
    
    subtitle_file = Path("work/audio/WATCH Elon Musk Delivers Remarks at the US - Saudi_subtitles.json")
    
    if not subtitle_file.exists():
        logger.warning("⚠ 字幕文件不存在，跳过内容分析测试")
        logger.info("   请先运行字幕提取")
        return False
    
    try:
        analyzer = ContentAnalyzer()
        logger.info("✓ API Key 已配置")
        logger.info(f"✓ Base URL: {analyzer.base_url}")
        logger.info(f"✓ 开始测试内容分析...")
        
        result = analyzer.analyze(str(subtitle_file))
        logger.info(f"✓ 内容分析成功: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ 内容分析失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("DashScope API 测试工具\n")
    
    # 测试字幕提取
    subtitle_ok = test_subtitle_api()
    
    # 如果字幕提取成功，测试内容分析
    if subtitle_ok:
        test_content_analyzer_api()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
