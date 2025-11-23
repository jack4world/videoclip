"""
分析器基类
定义所有分析器的通用接口
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional


class BaseAnalyzer(ABC):
    """分析器基类"""
    
    @abstractmethod
    def analyze(self, input_path: str, output_path: Optional[str] = None, **kwargs) -> str:
        """
        执行分析操作
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（可选）
            **kwargs: 其他参数
            
        Returns:
            输出文件路径
        """
        pass
    
    @abstractmethod
    def load_results(self, results_path: str) -> Dict:
        """
        加载分析结果
        
        Args:
            results_path: 结果文件路径
            
        Returns:
            分析结果字典
        """
        pass

