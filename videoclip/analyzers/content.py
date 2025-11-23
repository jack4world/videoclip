"""
内容分析模块
使用 DashScope Qwen 模型分析字幕文件，找出精彩观点和时间戳
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import dashscope
from dashscope import Generation

from videoclip.analyzers.base import BaseAnalyzer
from videoclip.config import get_settings
from videoclip.utils.logger import get_logger
from videoclip.config.constants import PATTERN_HIGHLIGHTS

logger = get_logger(__name__)


class ContentAnalyzer(BaseAnalyzer):
    """内容分析器（使用 Qwen）"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化内容分析器
        
        Args:
            api_key: DashScope API 密钥（如果为None则从配置中读取）
            base_url: DashScope API 基础 URL（通常不需要修改）
        """
        self.settings = get_settings()
        self.api_key = api_key or self.settings.qwen_api_key
        self.base_url = base_url or self.settings.qwen_base_url
        
        if not self.api_key:
            raise ValueError("请设置 QWEN_API_KEY 环境变量或传入 api_key 参数")
        
        # 设置 DashScope API Key
        dashscope.api_key = self.api_key
    
    def analyze(self, subtitle_path: str, output_path: Optional[str] = None, custom_prompt: Optional[str] = None) -> str:
        """
        分析字幕文件，找出精彩观点和时间戳
        
        Args:
            subtitle_path: 字幕文件路径
            output_path: 输出分析结果文件路径（JSON格式），如果为None则自动生成
            custom_prompt: 自定义提示词（可选），如果不提供则使用默认提示词
            
        Returns:
            分析结果文件路径
        """
        subtitle_path = Path(subtitle_path)
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
        
        if output_path is None:
            output_path = subtitle_path.parent / PATTERN_HIGHLIGHTS.format(stem=subtitle_path.stem)
        else:
            output_path = Path(output_path)
        
        try:
            logger.info(f"开始分析字幕内容: {subtitle_path.name}")
            
            # 加载字幕数据
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                subtitle_data = json.load(f)
            
            # 构建提示词
            transcription = subtitle_data.get("transcription", "")
            segments = subtitle_data.get("segments", [])
            
            # 将字幕分段整理成文本
            subtitle_text = self._format_subtitles(segments, transcription)
            
            # 使用自定义提示词或默认提示词
            if custom_prompt:
                # 如果提供了自定义提示词，将字幕内容插入其中
                if "{subtitle_text}" in custom_prompt:
                    prompt = custom_prompt.format(subtitle_text=subtitle_text)
                else:
                    prompt = f"{custom_prompt}\n\n字幕内容：\n{subtitle_text}"
            else:
                # 默认提示词
                prompt = self._get_default_prompt(subtitle_text)
            
            # 使用 DashScope SDK 调用 API
            logger.info("正在调用 DashScope API 进行内容分析...")
            
            result = Generation.call(
                model=self.settings.qwen_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.settings.qwen_temperature,
                max_tokens=self.settings.qwen_max_tokens,
                result_format='message'
            )
            
            # 检查 API 调用结果
            if result.status_code != 200:
                error_msg = result.message if hasattr(result, 'message') else f"API 返回状态码: {result.status_code}"
                raise Exception(f"API 调用失败: {error_msg}")
            
            # 获取返回内容
            content = self._extract_content_from_response(result)
            
            # 尝试从返回内容中提取 JSON
            highlights_data = self._extract_json_from_response(content)
            
            # 保存分析结果
            analysis_result = {
                "subtitle_file": str(subtitle_path),
                "highlights": highlights_data.get("highlights", [])
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"内容分析完成: {output_path}")
            logger.info(f"找到 {len(analysis_result['highlights'])} 个精彩片段")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"分析内容时出错: {str(e)}")
            raise
    
    def _get_default_prompt(self, subtitle_text: str) -> str:
        """
        获取默认提示词
        
        Args:
            subtitle_text: 字幕文本
            
        Returns:
            提示词字符串
        """
        return f"""请分析以下视频字幕内容，找出其中的精彩观点和关键片段。

要求：
1. 识别出3-5个最精彩的观点或内容片段
2. 每个片段需要包含：
   - 开始时间（秒）
   - 结束时间（秒）
   - 精彩内容的文字描述
   - 为什么这段内容精彩（简要说明）
3. 返回 JSON 格式，包含 highlights 数组

字幕内容：
{subtitle_text}

请返回 JSON 格式的分析结果，格式如下：
{{
  "highlights": [
    {{
      "start_time": 10.5,
      "end_time": 25.3,
      "text": "精彩内容的文字",
      "reason": "为什么精彩"
    }}
  ]
}}
"""
    
    def _format_subtitles(self, segments: List[Dict], transcription: str) -> str:
        """
        格式化字幕为文本
        
        Args:
            segments: 字幕分段列表
            transcription: 完整转录文本
            
        Returns:
            格式化后的字幕文本
        """
        if segments:
            formatted = []
            for seg in segments:
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                text = seg.get("text", "")
                formatted.append(f"[{start:.2f}s - {end:.2f}s] {text}")
            return "\n".join(formatted)
        else:
            return transcription
    
    def _extract_content_from_response(self, result) -> str:
        """
        从API响应中提取内容
        
        Args:
            result: API响应对象
            
        Returns:
            内容字符串
        """
        if hasattr(result, 'output') and result.output:
            if hasattr(result.output, 'choices') and result.output.choices:
                return result.output.choices[0].message.content
            elif isinstance(result.output, dict):
                choices = result.output.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content', '')
                else:
                    return result.output.get('text', '')
            else:
                return str(result.output)
        return ""
    
    def _extract_json_from_response(self, content: str) -> Dict:
        """
        从 API 响应中提取 JSON
        
        Args:
            content: API 返回的内容
            
        Returns:
            解析后的 JSON 字典
        """
        # 尝试找到 JSON 代码块
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # 如果找不到，返回默认结构
        return {"highlights": []}
    
    def load_results(self, results_path: str) -> Dict:
        """
        加载分析结果（实现基类接口）
        
        Args:
            results_path: 结果文件路径
            
        Returns:
            分析结果字典
        """
        return self.load_highlights(results_path)
    
    def load_highlights(self, highlights_path: str) -> Dict:
        """
        加载精彩片段数据
        
        Args:
            highlights_path: 精彩片段文件路径
            
        Returns:
            精彩片段数据字典
        """
        with open(highlights_path, 'r', encoding='utf-8') as f:
            return json.load(f)

