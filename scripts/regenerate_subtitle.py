"""
重新生成字幕文件的脚本
用于修复缺少中文翻译的字幕文件
"""
import sys
from pathlib import Path

from videoclip.extractors import SubtitleExtractor
from videoclip.clippers import VideoClipper
from videoclip.config import get_settings
from videoclip.utils.logger import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger(__name__)


def regenerate_subtitle(highlight_index: int = 5, work_dir: str = "work"):
    """重新生成指定片段的字幕文件"""
    
    settings = get_settings()
    
    if not settings.qwen_api_key:
        logger.error("❌ 错误: 未找到 QWEN_API_KEY 环境变量")
        logger.error("   请在 .env 文件中设置 QWEN_API_KEY")
        sys.exit(1)
    
    # 初始化模块
    subtitle_extractor = SubtitleExtractor()
    video_clipper = VideoClipper(output_dir=str(Path(work_dir) / "clips"))
    
    # 加载完整字幕数据
    subtitle_path = Path(work_dir) / "audio" / "WATCH Elon Musk Delivers Remarks at the US - Saudi_subtitles.json"
    if not subtitle_path.exists():
        logger.error(f"❌ 错误: 字幕文件不存在: {subtitle_path}")
        sys.exit(1)
    
    subtitle_data = subtitle_extractor.load_subtitles(str(subtitle_path))
    
    # 加载精彩片段数据
    highlights_path = Path(work_dir) / "audio" / "WATCH Elon Musk Delivers Remarks at the US - Saudi_subtitles_highlights.json"
    if not highlights_path.exists():
        logger.error(f"❌ 错误: 精彩片段文件不存在: {highlights_path}")
        sys.exit(1)
    
    import json
    with open(highlights_path, 'r', encoding='utf-8') as f:
        highlights_data = json.load(f)
    
    highlights = highlights_data.get("highlights", [])
    
    if highlight_index < 1 or highlight_index > len(highlights):
        logger.error(f"❌ 错误: 片段索引 {highlight_index} 超出范围 (1-{len(highlights)})")
        sys.exit(1)
    
    # 获取指定片段
    highlight = highlights[highlight_index - 1]
    start_time = highlight.get("start_time", 0)
    end_time = highlight.get("end_time", 0)
    text = highlight.get("text", "")[:30]
    
    # 清理文件名
    from videoclip.utils.file_utils import safe_filename
    safe_text = safe_filename(text, max_length=30)
    output_filename = f"highlight_{highlight_index:02d}_{safe_text}" if safe_text else f"highlight_{highlight_index:02d}"
    
    logger.info(f"正在重新生成片段 {highlight_index} 的字幕文件...")
    logger.info(f"时间范围: {start_time:.2f}s - {end_time:.2f}s")
    logger.info(f"输出文件名: {output_filename}\n")
    
    # 提取片段对应的字幕
    clip_subtitle = video_clipper.extract_subtitle_for_clip(subtitle_data, start_time, end_time)
    
    # 保存 JSON 格式字幕
    subtitle_json_path = Path(work_dir) / "clips" / f"{output_filename}_subtitle.json"
    with open(subtitle_json_path, 'w', encoding='utf-8') as f:
        json.dump(clip_subtitle, f, ensure_ascii=False, indent=2)
    logger.info(f"✓ JSON 字幕文件已更新: {subtitle_json_path.name}")
    
    # 保存 SRT 格式字幕（重新生成，包含中文翻译）
    subtitle_srt_path = Path(work_dir) / "clips" / f"{output_filename}_subtitle.srt"
    video_clipper.save_subtitle_srt(clip_subtitle, subtitle_srt_path)
    logger.info(f"✓ SRT 字幕文件已重新生成: {subtitle_srt_path.name}")
    
    logger.info("\n完成！")


if __name__ == "__main__":
    # 默认重新生成第5个片段，也可以通过命令行参数指定
    highlight_index = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    work_dir = sys.argv[2] if len(sys.argv) > 2 else "work"
    regenerate_subtitle(highlight_index, work_dir)
