# 扩展开发指南

学习如何扩展 VideoClip 的功能。

## 架构概述

VideoClip 采用模块化设计，通过基类定义统一接口，便于扩展：

- `BaseExtractor` - 提取器基类
- `BaseAnalyzer` - 分析器基类

## 创建自定义提取器

### 1. 继承基类

```python
from videoclip.extractors.base import BaseExtractor
from pathlib import Path

class MyExtractor(BaseExtractor):
    def extract(self, input_path: str, output_path: str = None) -> str:
        """
        实现提取逻辑
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            输出文件路径
        """
        input_file = Path(input_path)
        
        if output_path is None:
            output_path = self.output_dir / f"{input_file.stem}_extracted.txt"
        else:
            output_path = Path(output_path)
        
        # 您的提取逻辑
        with open(output_path, 'w') as f:
            f.write("提取结果")
        
        return str(output_path)
```

### 2. 使用自定义提取器

```python
from my_extractor import MyExtractor

extractor = MyExtractor(output_dir="output")
result = extractor.extract("input.txt")
```

## 创建自定义分析器

### 1. 继承基类

```python
from videoclip.analyzers.base import BaseAnalyzer
import json
from pathlib import Path

class MyAnalyzer(BaseAnalyzer):
    def analyze(self, input_path: str, output_path: str = None, **kwargs) -> str:
        """
        实现分析逻辑
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（可选）
            **kwargs: 其他参数
            
        Returns:
            输出文件路径
        """
        input_file = Path(input_path)
        
        if output_path is None:
            output_path = input_file.parent / f"{input_file.stem}_analyzed.json"
        else:
            output_path = Path(output_path)
        
        # 您的分析逻辑
        result = {
            "highlights": [
                {
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "text": "分析结果",
                    "reason": "原因"
                }
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def load_results(self, results_path: str) -> dict:
        """
        加载分析结果
        
        Args:
            results_path: 结果文件路径
            
        Returns:
            分析结果字典
        """
        with open(results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
```

### 2. 使用自定义分析器

```python
from my_analyzer import MyAnalyzer

analyzer = MyAnalyzer()
result_path = analyzer.analyze("input.json")
results = analyzer.load_results(result_path)
```

## 集成到主流程

### 方式1：修改 Processor

```python
from videoclip.core.processor import VideoClipProcessor
from my_extractor import MyExtractor

class CustomProcessor(VideoClipProcessor):
    def __init__(self, work_dir=None):
        super().__init__(work_dir)
        # 替换或添加自定义模块
        self.my_extractor = MyExtractor(output_dir=str(self.work_dir / "custom"))
```

### 方式2：独立使用

```python
from videoclip.extractors import AudioExtractor
from my_extractor import MyExtractor

# 使用标准模块
audio_extractor = AudioExtractor()
audio_path = audio_extractor.extract("video.mp4")

# 使用自定义模块
my_extractor = MyExtractor()
result = my_extractor.extract(audio_path)
```

## 配置管理

### 添加新配置项

在 `videoclip/config/settings.py` 中添加：

```python
class Settings:
    def __init__(self):
        # ... 现有配置 ...
        
        # 新配置项
        self.my_custom_setting = os.getenv("MY_CUSTOM_SETTING", "default_value")
```

### 使用配置

```python
from videoclip.config import get_settings

settings = get_settings()
value = settings.my_custom_setting
```

## 日志集成

```python
from videoclip.utils.logger import get_logger

logger = get_logger(__name__)

class MyExtractor(BaseExtractor):
    def extract(self, input_path: str, output_path: str = None) -> str:
        logger.info(f"开始提取: {input_path}")
        try:
            # 处理逻辑
            logger.info("提取完成")
        except Exception as e:
            logger.error(f"提取失败: {e}")
            raise
```

## 最佳实践

### 1. 遵循接口规范

确保实现所有必需的方法，并遵循基类的接口定义。

### 2. 错误处理

```python
def extract(self, input_path: str, output_path: str = None) -> str:
    try:
        # 处理逻辑
        pass
    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在: {input_path}")
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise
```

### 3. 类型提示

```python
from typing import Optional
from pathlib import Path

def extract(self, input_path: str, output_path: Optional[str] = None) -> str:
    # ...
```

### 4. 文档字符串

```python
def extract(self, input_path: str, output_path: str = None) -> str:
    """
    提取功能说明
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径（可选）
        
    Returns:
        输出文件路径
        
    Raises:
        FileNotFoundError: 文件不存在时抛出
    """
    # ...
```

## 测试扩展

```python
import unittest
from my_extractor import MyExtractor

class TestMyExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = MyExtractor(output_dir="test_output")
    
    def test_extract(self):
        result = self.extractor.extract("test_input.txt")
        self.assertTrue(Path(result).exists())
```

## 贡献扩展

如果您创建了有用的扩展，欢迎：

1. 编写文档说明
2. 添加测试用例
3. 提交 Pull Request

## 相关文档

- [架构设计](../architecture.md)
- [API参考](../api/README.md)
- [代码示例](../examples/README.md)

