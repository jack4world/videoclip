#!/usr/bin/env python3
"""
将视频和SRT字幕合成为带字幕的视频 - 命令行工具
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from videoclip.clippers import VideoClipper
from videoclip.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="将视频和SRT字幕合成为带字幕的视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 为片段1烧录字幕
  python scripts/burn_subtitle_cli.py --clip 1
  
  # 为所有片段烧录字幕
  python scripts/burn_subtitle_cli.py --all
  
  # 指定视频和字幕文件
  python scripts/burn_subtitle_cli.py --video video.mp4 --subtitle subtitle.srt
  
  # 自定义输出路径和样式
  python scripts/burn_subtitle_cli.py --video video.mp4 --subtitle subtitle.srt \\
    --output output.mp4 --font-size 28 --position top
        """
    )
    
    # 输入方式：片段索引、所有片段、或直接指定文件
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--clip",
        type=int,
        help="片段索引（1开始），例如：--clip 1"
    )
    input_group.add_argument(
        "--all",
        action="store_true",
        help="处理所有片段"
    )
    input_group.add_argument(
        "--video",
        type=str,
        help="视频文件路径（需要配合 --subtitle 使用）"
    )
    
    parser.add_argument(
        "--subtitle",
        type=str,
        help="SRT字幕文件路径（与 --video 配合使用）"
    )
    
    parser.add_argument(
        "--clips-dir",
        type=str,
        default="work/clips",
        help="片段目录（默认: work/clips）"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出视频文件路径（可选，默认自动生成）"
    )
    
    parser.add_argument(
        "--font-size",
        type=int,
        default=24,
        help="字体大小（默认: 24）"
    )
    
    parser.add_argument(
        "--position",
        type=str,
        choices=["top", "center", "bottom"],
        default="bottom",
        help="字幕位置（默认: bottom）"
    )
    
    args = parser.parse_args()
    
    clipper = VideoClipper(output_dir=args.clips_dir)
    
    try:
        if args.clip:
            # 处理指定片段
            clips_dir = Path(args.clips_dir)
            video_pattern = f"highlight_{args.clip:02d}_*.mp4"
            srt_pattern = f"highlight_{args.clip:02d}_*_subtitle.srt"
            
            video_files = list(clips_dir.glob(video_pattern))
            srt_files = list(clips_dir.glob(srt_pattern))
            
            if not video_files:
                logger.error(f"❌ 未找到片段 {args.clip} 的视频文件")
                sys.exit(1)
            
            if not srt_files:
                logger.error(f"❌ 未找到片段 {args.clip} 的字幕文件")
                sys.exit(1)
            
            video_path = video_files[0]
            srt_path = srt_files[0]
            output_path = args.output or (clips_dir / f"{video_path.stem}_with_subtitle.mp4")
            
            logger.info(f"处理片段 {args.clip}")
            logger.info(f"视频: {video_path.name}")
            logger.info(f"字幕: {srt_path.name}")
            
            result = clipper.burn_subtitle(
                video_path=str(video_path),
                subtitle_path=str(srt_path),
                output_path=str(output_path),
                font_size=args.font_size,
                position=args.position
            )
            
            logger.info(f"✓ 完成: {Path(result).name}")
            
        elif args.all:
            # 处理所有片段
            clips_dir = Path(args.clips_dir)
            video_files = sorted(clips_dir.glob("highlight_*.mp4"))
            
            if not video_files:
                logger.error(f"❌ 未找到任何视频文件")
                sys.exit(1)
            
            logger.info(f"找到 {len(video_files)} 个视频文件")
            success_count = 0
            
            for video_file in video_files:
                stem = video_file.stem
                parts = stem.split('_')
                if len(parts) < 2 or not parts[1].isdigit():
                    continue
                
                clip_index = int(parts[1])
                srt_pattern = f"highlight_{clip_index:02d}_*_subtitle.srt"
                srt_files = list(clips_dir.glob(srt_pattern))
                
                if not srt_files:
                    logger.warning(f"⚠ 片段 {clip_index} 没有字幕文件，跳过")
                    continue
                
                srt_path = srt_files[0]
                output_path = clips_dir / f"{video_file.stem}_with_subtitle.mp4"
                
                try:
                    logger.info(f"\n处理片段 {clip_index}: {video_file.name}")
                    result = clipper.burn_subtitle(
                        video_path=str(video_file),
                        subtitle_path=str(srt_path),
                        output_path=str(output_path),
                        font_size=args.font_size,
                        position=args.position
                    )
                    logger.info(f"✓ 完成: {Path(result).name}")
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ 失败: {str(e)}")
                    continue
            
            logger.info(f"\n{'='*60}")
            logger.info(f"处理完成！成功: {success_count}/{len(video_files)}")
            logger.info(f"{'='*60}")
            
        else:
            # 直接指定文件
            if not args.subtitle:
                logger.error("❌ 使用 --video 时必须同时指定 --subtitle")
                sys.exit(1)
            
            video_path = Path(args.video)
            subtitle_path = Path(args.subtitle)
            
            if not video_path.exists():
                logger.error(f"❌ 视频文件不存在: {video_path}")
                sys.exit(1)
            
            if not subtitle_path.exists():
                logger.error(f"❌ 字幕文件不存在: {subtitle_path}")
                sys.exit(1)
            
            output_path = args.output or (video_path.parent / f"{video_path.stem}_with_subtitle.mp4")
            
            result = clipper.burn_subtitle(
                video_path=str(video_path),
                subtitle_path=str(subtitle_path),
                output_path=str(output_path),
                font_size=args.font_size,
                position=args.position
            )
            
            logger.info(f"✓ 完成: {Path(result).name}")
            
    except Exception as e:
        logger.error(f"❌ 处理失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()








