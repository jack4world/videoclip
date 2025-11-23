"""
日志工具模块
提供统一的日志记录功能
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> None:
    """
    设置日志配置
    
    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
        format_string: 日志格式字符串（可选）
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
        
    Returns:
        Logger实例
    """
    return logging.getLogger(name)

