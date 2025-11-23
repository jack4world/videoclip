"""
文件工具函数
"""
import re
from pathlib import Path
from typing import Optional


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        目录路径
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str, max_length: int = 50) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        max_length: 最大长度
        
    Returns:
        清理后的文件名
    """
    # 移除非法字符，只保留字母、数字、空格、连字符和下划线
    safe = re.sub(r'[^\w\s\-_]', '', filename)
    safe = re.sub(r'\s+', ' ', safe).strip()
    
    # 限制长度
    if len(safe) > max_length:
        safe = safe[:max_length]
    
    return safe


def get_output_path(
    base_dir: Path,
    stem: str,
    extension: str,
    pattern: Optional[str] = None
) -> Path:
    """
    生成输出文件路径
    
    Args:
        base_dir: 基础目录
        stem: 文件名（不含扩展名）
        extension: 文件扩展名（包含点号，如 .json）
        pattern: 文件名模式（可选，如 "{stem}_subtitles{extension}"）
        
    Returns:
        完整文件路径
    """
    if pattern:
        filename = pattern.format(stem=stem, extension=extension)
    else:
        filename = f"{stem}{extension}"
    
    return base_dir / filename

