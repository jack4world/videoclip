"""
提取器基类
定义所有提取器的通用接口
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseExtractor(ABC):
    """提取器基类"""
    
    def __init__(self, output_dir: str):
        """
        初始化提取器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def extract(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        执行提取操作
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            输出文件路径
        """
        pass

