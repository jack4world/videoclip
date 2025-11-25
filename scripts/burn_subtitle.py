"""
将视频和SRT字幕合成为带字幕的视频
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from videoclip.clippers import VideoClipper
from videoclip.config import get_settings
from videoclip.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def burn_subtitle_for_clip(clip_index: int = 1, clips_dir: str = "work/clips"):
    """
    为指定片段烧录字幕
    
    Args:
        clip_index: 片段索引（1开始）
        clips_dir: 片段目录
    """
    clips_dir = Path(clips_dir)
    
    if not clips_dir.exists():
        logger.error(f"❌ 错误: 片段目录不存在: {clips_dir}")
        sys.exit(1)
    
    # 查找对应的视频和字幕文件
    video_pattern = f"highlight_{clip_index:02d}_*.mp4"
    srt_pattern = f"highlight_{clip_index:02d}_*_subtitle.srt"
    
    video_files = list(clips_dir.glob(video_pattern))
    srt_files = list(clips_dir.glob(srt_pattern))
    
    if not video_files:
        logger.error(f"❌ 错误: 未找到片段 {clip_index} 的视频文件")
        logger.error(f"   查找模式: {video_pattern}")
        sys.exit(1)
    
    if not srt_files:
        logger.error(f"❌ 错误: 未找到片段 {clip_index} 的字幕文件")
        logger.error(f"   查找模式: {srt_pattern}")
        sys.exit(1)
    
    video_path = video_files[0]
    srt_path = srt_files[0]
    
    logger.info(f"找到视频文件: {video_path.name}")
    logger.info(f"找到字幕文件: {srt_path.name}")
    
    # 生成输出文件名
    output_filename = f"{video_path.stem}_with_subtitle.mp4"
    output_path = clips_dir / output_filename
    
    # 创建视频裁剪器并烧录字幕
    clipper = VideoClipper(output_dir=str(clips_dir))
    
    try:
        result_path = clipper.burn_subtitle(
            video_path=str(video_path),
            subtitle_path=str(srt_path),
            output_path=str(output_path)
        )
        
        logger.info(f"\n✓ 完成！")
        logger.info(f"  输入视频: {video_path.name}")
        logger.info(f"  字幕文件: {srt_path.name}")
        logger.info(f"  输出视频: {Path(result_path).name}")
        logger.info(f"  完整路径: {result_path}")
        
    except Exception as e:
        logger.error(f"❌ 处理失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


def burn_all_subtitles(clips_dir: str = "work/clips"):
    """
    为所有片段烧录字幕
    
    Args:
        clips_dir: 片段目录
    """
    clips_dir = Path(clips_dir)
    
    if not clips_dir.exists():
        logger.error(f"❌ 错误: 片段目录不存在: {clips_dir}")
        sys.exit(1)
    
    # 查找所有视频文件
    video_files = sorted(clips_dir.glob("highlight_*.mp4"))
    
    if not video_files:
        logger.error(f"❌ 错误: 未找到任何视频文件")
        sys.exit(1)
    
    logger.info(f"找到 {len(video_files)} 个视频文件")
    
    clipper = VideoClipper(output_dir=str(clips_dir))
    success_count = 0
    
    for video_file in video_files:
        # 提取片段编号
        stem = video_file.stem
        parts = stem.split('_')
        if len(parts) < 2 or not parts[1].isdigit():
            logger.warning(f"⚠ 跳过无法识别的文件: {video_file.name}")
            continue
        
        clip_index = int(parts[1])
        
        # 查找对应的字幕文件
        srt_pattern = f"highlight_{clip_index:02d}_*_subtitle.srt"
        srt_files = list(clips_dir.glob(srt_pattern))
        
        if not srt_files:
            logger.warning(f"⚠ 片段 {clip_index} 没有找到字幕文件，跳过")
            continue
        
        srt_path = srt_files[0]
        output_filename = f"{video_file.stem}_with_subtitle.mp4"
        output_path = clips_dir / output_filename
        
        try:
            logger.info(f"\n处理片段 {clip_index}: {video_file.name}")
            result_path = clipper.burn_subtitle(
                video_path=str(video_file),
                subtitle_path=str(srt_path),
                output_path=str(output_path)
            )
            logger.info(f"✓ 完成: {Path(result_path).name}")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ 片段 {clip_index} 处理失败: {str(e)}")
            continue
    
    logger.info(f"\n{'='*60}")
    logger.info(f"处理完成！成功: {success_count}/{len(video_files)}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            # 处理所有片段
            clips_dir = sys.argv[2] if len(sys.argv) > 2 else "work/clips"
            burn_all_subtitles(clips_dir)
        else:
            # 处理指定片段
            try:
                clip_index = int(sys.argv[1])
                clips_dir = sys.argv[2] if len(sys.argv) > 2 else "work/clips"
                burn_subtitle_for_clip(clip_index, clips_dir)
            except ValueError:
                logger.error("❌ 错误: 片段索引必须是数字，或使用 'all' 处理所有片段")
                logger.error("   用法: python scripts/burn_subtitle.py <片段索引>")
                logger.error("   示例: python scripts/burn_subtitle.py 1")
                logger.error("   示例: python scripts/burn_subtitle.py all")
                sys.exit(1)
    else:
        # 默认处理片段1
        burn_subtitle_for_clip(1)

