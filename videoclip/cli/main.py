"""
命令行接口
"""
import argparse
import sys
from pathlib import Path

from videoclip.core.processor import VideoClipProcessor
from videoclip.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能视频剪辑工具 - 从 YouTube 视频中提取精彩片段",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从 YouTube 下载并处理
  python -m videoclip.cli --url "https://www.youtube.com/watch?v=example"
  python -m videoclip.cli --url "https://www.youtube.com/watch?v=example" --keep-intermediate
  
  # 处理已下载的视频文件
  python -m videoclip.cli --video "path/to/video.mp4"
  python -m videoclip.cli --video "path/to/video.mp4" --prompt "你的自定义提示词"
  python -m videoclip.cli --video "path/to/video.mp4" --prompt-file prompt.txt
        """
    )
    
    # URL 和 video 参数互斥，但至少要提供一个
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--url",
        type=str,
        help="YouTube 视频 URL"
    )
    input_group.add_argument(
        "--video",
        type=str,
        help="已下载的视频文件路径（本地文件）"
    )
    
    parser.add_argument(
        "--work-dir",
        type=str,
        default=None,
        help="工作目录（默认: work）"
    )
    
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="保留中间文件（音频、字幕等）"
    )
    
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="自定义分析提示词（可选），如果不提供则使用默认提示词。可以在提示词中使用 {subtitle_text} 占位符来插入字幕内容"
    )
    
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="从文件读取自定义提示词（可选），文件路径"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认: INFO）"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="日志文件路径（可选）"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    import logging
    log_level = getattr(logging, args.log_level.upper())
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(level=log_level, log_file=log_file)
    
    # 处理提示词：优先使用文件，其次使用命令行参数
    custom_prompt = None
    if args.prompt_file:
        try:
            with open(args.prompt_file, 'r', encoding='utf-8') as f:
                custom_prompt = f.read()
            logger.info(f"从文件读取提示词: {args.prompt_file}")
        except Exception as e:
            logger.error(f"⚠ 读取提示词文件失败: {str(e)}")
            sys.exit(1)
    elif args.prompt:
        custom_prompt = args.prompt
    
    # 创建处理器并执行
    processor = VideoClipProcessor(work_dir=args.work_dir)
    processor.process(
        youtube_url=args.url,
        video_path=args.video,
        keep_intermediate=args.keep_intermediate,
        custom_prompt=custom_prompt
    )


if __name__ == "__main__":
    main()

