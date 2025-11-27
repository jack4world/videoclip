"""
视频裁剪模块
根据时间戳裁剪视频片段，并为每个片段生成对应的字幕文件
"""
import ffmpeg
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import dashscope
from dashscope import Generation

from videoclip.config import get_settings
from videoclip.utils.logger import get_logger
from videoclip.utils.file_utils import safe_filename
from videoclip.config.constants import PATTERN_CLIP_SUBTITLE_JSON, PATTERN_CLIP_SUBTITLE_SRT

logger = get_logger(__name__)

# 常见的语音识别错误修正字典
# 键为错误识别的文本，值为正确的文本
SPEECH_RECOGNITION_FIXES = {
    # 技术术语
    'call chips': 'cool chips',
    'cool chips': 'cool chips',  # 保持正确的不变
    'tarot wait': 'terawatt',
    'tarot watt': 'terawatt',
    'terra watt': 'terawatt',
    'car to ship': 'Kardashev',
    'card a shove': 'Kardashev',
    'car to shove': 'Kardashev',
    # 人名和书名
    'in banks, culture books': "Iain Banks' Culture books",
    'in banks culture books': "Iain Banks' Culture books",
    'ian banks': 'Iain Banks',
    'in banks': 'Iain Banks',
    # 其他常见错误
    'giga watt': 'gigawatt',
    'mega watt': 'megawatt',
    'kilo watt': 'kilowatt',
}


def fix_speech_recognition_errors(text: str) -> str:
    """
    修正常见的语音识别错误
    
    Args:
        text: 原始文本
        
    Returns:
        修正后的文本
    """
    result = text
    for wrong, correct in SPEECH_RECOGNITION_FIXES.items():
        # 不区分大小写的替换
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        result = pattern.sub(correct, result)
    return result


class VideoClipper:
    """视频裁剪器"""
    
    def __init__(self, output_dir: str = "clips", api_key: Optional[str] = None):
        """
        初始化视频裁剪器
        
        Args:
            output_dir: 裁剪后的视频保存目录
            api_key: DashScope API 密钥（用于翻译功能），如果为None则从配置中读取
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.settings = get_settings()
        # 设置翻译 API Key
        self.api_key = api_key or self.settings.qwen_api_key
        if self.api_key:
            dashscope.api_key = self.api_key
    
    def clip(self, video_path: str, start_time: float, end_time: float, 
             output_filename: Optional[str] = None) -> str:
        """
        裁剪视频片段
        
        Args:
            video_path: 原始视频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_filename: 输出文件名（不含扩展名），如果为None则自动生成
            
        Returns:
            裁剪后的视频文件路径
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if output_filename is None:
            output_filename = f"{video_path.stem}_clip_{start_time:.1f}_{end_time:.1f}"
        
        output_path = self.output_dir / f"{output_filename}.mp4"
        
        try:
            duration = end_time - start_time
            logger.info(f"裁剪视频片段: {start_time:.2f}s - {end_time:.2f}s (时长: {duration:.2f}s)")
            
            # 使用 ffmpeg 裁剪视频并重新编码以确保音视频同步
            stream = ffmpeg.input(str(video_path), ss=start_time, t=duration)
            stream = ffmpeg.output(
                stream,
                str(output_path),
                vcodec=self.settings.video_codec,
                acodec=self.settings.audio_codec,
                preset=self.settings.video_preset,
                crf=self.settings.video_crf,
                movflags='faststart'
            )
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"视频裁剪完成: {output_path}")
            return str(output_path)
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"裁剪视频时出错: {error_msg}")
            raise
        except Exception as e:
            logger.error(f"裁剪视频时出错: {str(e)}")
            raise
    
    def extract_subtitle_for_clip(self, subtitle_data: Dict, start_time: float, end_time: float) -> Dict:
        """
        从完整字幕数据中提取对应时间段的内容
        
        Args:
            subtitle_data: 完整的字幕数据（包含 segments 和 words）
            start_time: 片段开始时间（秒）
            end_time: 片段结束时间（秒）
            
        Returns:
            提取的字幕数据，时间戳已调整为相对于片段开始时间
        """
        segments = subtitle_data.get("segments", [])
        words = subtitle_data.get("words", [])
        
        # 提取对应时间段的 segments
        clip_segments = []
        for seg in segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            
            # 如果 segment 与片段时间有重叠
            if seg_end >= start_time and seg_start <= end_time:
                # 调整时间戳为相对于片段开始时间
                adjusted_seg = seg.copy()
                adjusted_seg["start"] = max(0, seg_start - start_time)
                adjusted_seg["end"] = min(end_time - start_time, seg_end - start_time)
                clip_segments.append(adjusted_seg)
        
        # 提取对应时间段的 words
        clip_words = []
        for word in words:
            word_start = word.get("start", 0)
            word_end = word.get("end", 0)
            
            # 如果 word 与片段时间有重叠
            if word_end >= start_time and word_start <= end_time:
                adjusted_word = word.copy()
                adjusted_word["start"] = max(0, word_start - start_time)
                adjusted_word["end"] = min(end_time - start_time, word_end - start_time)
                clip_words.append(adjusted_word)
        
        # 构建片段字幕文本
        clip_text = " ".join([seg.get("text", "") for seg in clip_segments])
        
        return {
            "text": clip_text.strip(),
            "segments": clip_segments,
            "words": clip_words,
            "clip_start_time": start_time,
            "clip_end_time": end_time,
            "clip_duration": end_time - start_time
        }
    
    def translate_to_chinese(self, text: str) -> Tuple[str, str]:
        """
        使用 Qwen API 将英文翻译成中文，同时进行文字校验和错别字修正
        
        Args:
            text: 要翻译的英文文本
            
        Returns:
            (修正后的英文文本, 翻译后的中文文本) 元组
        """
        if not self.api_key or not text.strip():
            if not self.api_key:
                logger.warning("未配置 API Key，跳过翻译")
            return (text, "")
        
        # 先用规则修正常见的语音识别错误
        text = fix_speech_recognition_errors(text)
        
        try:
            prompt = f"""请严格按照以下要求处理英文文本（这是视频字幕，可能不完整）：

【重要】只做两件事：
1. 修正明显的语音识别错误（如 "call chips"→"cool chips", "tarot watt"→"terawatt"）
2. 将文本翻译成中文

【禁止】
- 不要添加任何原文中没有的内容
- 不要扩展、解释或补充不完整的句子
- 如果原文只有几个词或不完整，翻译也必须同样简短

返回格式（严格遵守）：
修正后的英文：[只包含修正后的原文，不多不少]
中文翻译：[简洁的翻译，长度与原文相当]

英文文本：{text}"""
            
            result = Generation.call(
                model=self.settings.qwen_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 检查 API 调用结果
            if result.status_code != 200:
                error_msg = result.message if hasattr(result, 'message') else f"API 返回状态码: {result.status_code}"
                logger.warning(f"翻译 API 调用失败: {error_msg}")
                return (text, "")
            
            # 提取返回内容
            content = self._extract_content_from_response(result)
            
            if not content:
                logger.warning("API 返回内容为空")
                return (text, "")
            
            # 解析返回结果
            corrected_english, chinese_translation = self._parse_translation_response(content, text)
            
            if chinese_translation == "":
                logger.warning(f"无法从 API 响应中提取中文翻译，响应内容预览: {content[:200]}...")
            
            return (corrected_english.strip(), chinese_translation.strip())
            
        except Exception as e:
            logger.error(f"翻译和校验失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return (text, "")
    
    def _extract_content_from_response(self, result) -> str:
        """从API响应中提取内容"""
        if hasattr(result, 'output') and result.output:
            if hasattr(result.output, 'choices') and result.output.choices:
                return result.output.choices[0].message.content.strip()
            elif isinstance(result.output, dict):
                choices = result.output.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content', '').strip()
                else:
                    return result.output.get('text', '').strip()
        return ""
    
    def _parse_translation_response(self, content: str, original_text: str) -> Tuple[str, str]:
        """解析翻译响应"""
        corrected_english = original_text
        chinese_translation = ""
        
        # 首先尝试处理单行格式：修正后的英文：xxx 中文翻译：xxx
        if '修正后的英文：' in content and '中文翻译：' in content:
            # 提取英文部分
            english_start = content.find('修正后的英文：') + len('修正后的英文：')
            chinese_marker_pos = content.find('中文翻译：')
            if english_start < chinese_marker_pos:
                corrected_english = content[english_start:chinese_marker_pos].strip()
            
            # 提取中文部分
            chinese_start = chinese_marker_pos + len('中文翻译：')
            chinese_translation = content[chinese_start:].strip()
            
            # 清理可能的多余内容
            if corrected_english and chinese_translation:
                return (corrected_english, chinese_translation)
        
        # 多行格式处理
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测章节标记
            if any(marker in line for marker in ['修正后的英文', 'Corrected English']):
                current_section = 'english'
                # 如果标记后面直接跟着内容（如 "修正后的英文：xxx"）
                for marker in ['修正后的英文：', '修正后的英文:']:
                    if marker in line:
                        rest = line.split(marker, 1)[1].strip()
                        if rest and '中文翻译' not in rest:
                            corrected_english = rest
                continue
            elif any(marker in line for marker in ['中文翻译', 'Chinese Translation']):
                current_section = 'chinese'
                # 如果标记后面直接跟着内容
                for marker in ['中文翻译：', '中文翻译:']:
                    if marker in line:
                        rest = line.split(marker, 1)[1].strip()
                        if rest:
                            chinese_translation = rest
                continue
            
            # 根据章节提取内容
            if current_section == 'english':
                if corrected_english == original_text:
                    corrected_english = line
                else:
                    corrected_english += " " + line
            elif current_section == 'chinese':
                if chinese_translation:
                    chinese_translation += " " + line
                else:
                    chinese_translation = line
        
        # 如果没有找到明确的章节标记，尝试智能提取
        if corrected_english == original_text and chinese_translation == "":
            chinese_lines = []
            english_lines = []
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                # 跳过包含标记的行
                if any(keyword in line_stripped for keyword in ['修正后的英文', '中文翻译', 'Corrected', 'Translation']):
                    continue
                if any('\u4e00' <= char <= '\u9fff' for char in line_stripped):
                    chinese_lines.append(line_stripped)
                else:
                    english_lines.append(line_stripped)
            
            if chinese_lines:
                chinese_translation = " ".join(chinese_lines)
            if english_lines:
                corrected_english = " ".join(english_lines)
        
        # 如果还是没有找到中文，尝试直接查找所有包含中文的行
        if chinese_translation == "":
            all_chinese_lines = []
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and any('\u4e00' <= char <= '\u9fff' for char in line_stripped):
                    all_chinese_lines.append(line_stripped)
            if all_chinese_lines:
                chinese_translation = " ".join(all_chinese_lines)
        
        return corrected_english, chinese_translation
    
    def calculate_text_width(self, text: str) -> int:
        """
        计算文本显示宽度（中文字符算2个字符宽度）
        
        Args:
            text: 文本内容
            
        Returns:
            文本宽度
        """
        width = 0
        for char in text:
            # 中文字符、日文、韩文等宽字符算2个宽度
            if ord(char) > 127:
                width += 2
            else:
                width += 1
        return width
    
    def split_text_by_length(self, text: str, max_chars: Optional[int] = None) -> List[str]:
        """
        将文本智能分割成指定长度的片段
        
        Args:
            text: 要分割的文本
            max_chars: 每段最大字符数，如果为None则使用配置中的默认值
            
        Returns:
            分割后的文本片段列表
        """
        if not text.strip():
            return []
        
        max_chars = max_chars or self.settings.subtitle_max_chars
        
        lines = []
        words = re.split(r'(\s+)', text)  # 保留空格
        current_line = ""
        
        for word in words:
            if not word.strip():
                # 空格或标点，直接添加到当前行
                if current_line:
                    current_line += word
                continue
            
            # 检查添加这个词后是否超过长度
            test_line = current_line + word if current_line else word
            if self.calculate_text_width(test_line) <= max_chars:
                current_line = test_line
            else:
                # 当前行已满，保存并开始新行
                if current_line:
                    lines.append(current_line.strip())
                # 如果单个词就超过长度，需要强制分割
                if self.calculate_text_width(word) > max_chars:
                    # 强制分割长词（按字符分割）
                    for char in word:
                        if not current_line:
                            current_line = char
                        elif self.calculate_text_width(current_line + char) <= max_chars:
                            current_line += char
                        else:
                            lines.append(current_line.strip())
                            current_line = char
                else:
                    current_line = word
        
        # 添加最后一行
        if current_line:
            lines.append(current_line.strip())
        
        return lines if lines else [text]
    
    def wrap_text(self, text: str, max_width: int = 45) -> str:
        """
        对长文本进行换行处理
        
        Args:
            text: 原始文本
            max_width: 每行最大字符宽度（中文字符算2个宽度）
            
        Returns:
            换行后的文本
        """
        if self.calculate_text_width(text) <= max_width:
            return text
        
        lines = []
        words = text.split(' ')
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            if self.calculate_text_width(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines) if lines else text
    
    def wrap_chinese_text(self, text: str, max_chars: int = 22) -> str:
        """
        对中文长文本进行换行处理
        
        Args:
            text: 原始中文文本
            max_chars: 每行最大字符数
            
        Returns:
            换行后的文本
        """
        if len(text) <= max_chars:
            return text
        
        lines = []
        current_line = ""
        
        for char in text:
            if len(current_line) >= max_chars:
                # 尝试在标点符号处断行
                break_pos = -1
                for i, c in enumerate(reversed(current_line)):
                    if c in '，。、；：！？':
                        break_pos = len(current_line) - i
                        break
                
                if break_pos > len(current_line) // 2:
                    lines.append(current_line[:break_pos])
                    current_line = current_line[break_pos:]
                else:
                    lines.append(current_line)
                    current_line = ""
            
            current_line += char
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines) if lines else text
    
    def _split_long_segment(self, english_text: str, chinese_text: str, 
                             start: float, end: float, max_lines: int = 2) -> List[Dict]:
        """
        将长文本段落分割成多个子段落，每个子段落最多显示指定行数
        
        Args:
            english_text: 英文文本
            chinese_text: 中文文本
            start: 开始时间
            end: 结束时间
            max_lines: 每个子段落最大行数
            
        Returns:
            分割后的子段落列表
        """
        duration = end - start
        
        # 将英文按句子分割（在句号、问号、感叹号处）
        import re
        sentences = re.split(r'(?<=[.!?])\s+', english_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            # 无法按句子分割，按词分割
            words = english_text.split()
            mid = len(words) // 2
            sentences = [' '.join(words[:mid]), ' '.join(words[mid:])]
        
        # 计算每个句子的字符权重
        total_chars = sum(len(s) for s in sentences)
        
        # 创建子段落
        sub_segments = []
        current_time = start
        
        for i, sentence in enumerate(sentences):
            # 按字符比例分配时间
            char_ratio = len(sentence) / total_chars if total_chars > 0 else 1 / len(sentences)
            segment_duration = duration * char_ratio
            segment_end = min(current_time + segment_duration, end)
            
            # 对应的中文部分（简单按比例分割）
            if chinese_text:
                chinese_start_idx = int(len(chinese_text) * (current_time - start) / duration)
                chinese_end_idx = int(len(chinese_text) * (segment_end - start) / duration)
                chinese_part = chinese_text[chinese_start_idx:chinese_end_idx]
                # 尝试在标点处断开
                for punct in '。！？，、；：':
                    last_punct = chinese_part.rfind(punct)
                    if last_punct > len(chinese_part) // 2:
                        chinese_part = chinese_part[:last_punct + 1]
                        break
            else:
                chinese_part = ""
            
            sub_segments.append({
                'english': sentence,
                'chinese': chinese_part,
                'start': current_time,
                'end': segment_end
            })
            
            current_time = segment_end
        
        return sub_segments
    
    def save_subtitle_srt(self, subtitle_data: Dict, output_path: Path):
        """
        将字幕数据保存为 SRT 格式（中英文双语，保留原始时间戳）
        智能分割长段落，每个字幕最多显示2行英文+2行中文
        
        Args:
            subtitle_data: 字幕数据
            output_path: 输出文件路径
        """
        segments = subtitle_data.get("segments", [])
        
        # 格式化时间戳为 SRT 格式 (HH:MM:SS,mmm)
        def format_timestamp(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        # 判断文本是否需要分割（超过2行）
        def needs_split(text: str, max_width: int = 65) -> bool:
            if not text:
                return False
            wrapped = self.wrap_text(text, max_width)
            return wrapped.count('\n') >= 2  # 超过2行需要分割
        
        with open(output_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            total_segments = len(segments)
            
            logger.info(f"正在生成双语字幕（共 {total_segments} 个原始段落）...")
            
            for idx, seg in enumerate(segments, 1):
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                text = seg.get("text", "").strip()
                duration = end - start
                
                if not text:
                    continue
                
                # 翻译成中文并修正错别字
                if self.api_key:
                    if idx == 1 or idx % 10 == 0:
                        logger.info(f"  翻译和校验进度: {idx}/{total_segments}")
                    corrected_english, chinese_text = self.translate_to_chinese(text)
                    
                    # 使用修正后的英文文本
                    english_text = corrected_english if corrected_english != text else text
                else:
                    english_text = text
                    chinese_text = ""
                    if idx == 1:
                        logger.warning("未配置 API Key，仅生成英文字幕（不进行错别字修正）")
                
                # 判断是否需要分割：时间跨度>=5秒且文本超过2行
                if duration >= 5.0 and needs_split(english_text):
                    # 分割长段落
                    sub_segments = self._split_long_segment(english_text, chinese_text, start, end)
                    
                    for sub_seg in sub_segments:
                        english_wrapped = self.wrap_text(sub_seg['english'], max_width=65)
                        chinese_wrapped = self.wrap_chinese_text(sub_seg['chinese'], max_chars=35) if sub_seg['chinese'] else ""
                        
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{format_timestamp(sub_seg['start'])} --> {format_timestamp(sub_seg['end'])}\n")
                        f.write(f"{english_wrapped}\n")
                        if chinese_wrapped:
                            f.write(f"{chinese_wrapped}\n")
                        f.write("\n")
                        subtitle_index += 1
                else:
                    # 短段落直接换行显示
                    english_wrapped = self.wrap_text(english_text, max_width=65)
                    chinese_wrapped = self.wrap_chinese_text(chinese_text, max_chars=35) if chinese_text else ""
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
                    f.write(f"{english_wrapped}\n")
                    if chinese_wrapped:
                        f.write(f"{chinese_wrapped}\n")
                    f.write("\n")
                    subtitle_index += 1
            
            logger.info(f"✓ 双语字幕生成完成（共生成 {subtitle_index - 1} 个时间戳段落）")
    
    def clip_multiple(self, video_path: str, highlights: List[Dict], 
                     prefix: str = "highlight", subtitle_data: Optional[Dict] = None) -> List[Dict]:
        """
        根据多个时间戳裁剪多个视频片段，并为每个片段生成对应的字幕文件
        
        Args:
            video_path: 原始视频文件路径
            highlights: 精彩片段列表，每个元素包含 start_time 和 end_time
            prefix: 输出文件名前缀
            subtitle_data: 完整的字幕数据（可选），如果提供则生成对应的字幕文件
            
        Returns:
            裁剪结果列表，每个元素包含视频路径和字幕路径等信息
        """
        clipped_results = []
        
        for i, highlight in enumerate(highlights, 1):
            start_time = highlight.get("start_time", 0)
            end_time = highlight.get("end_time", 0)
            text = highlight.get("text", "")[:30]
            
            # 清理文件名
            safe_text = safe_filename(text, max_length=30)
            output_filename = f"{prefix}_{i:02d}_{safe_text}" if safe_text else f"{prefix}_{i:02d}"
            
            try:
                # 裁剪视频
                clipped_file = self.clip(video_path, start_time, end_time, output_filename)
                
                result = {
                    "index": i,
                    "video_path": clipped_file,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                    "text": highlight.get("text", ""),
                    "reason": highlight.get("reason", ""),
                    "subtitle_path": None,
                    "subtitle_srt_path": None
                }
                
                # 如果提供了字幕数据，生成对应的字幕文件
                if subtitle_data:
                    # 提取片段对应的字幕
                    clip_subtitle = self.extract_subtitle_for_clip(subtitle_data, start_time, end_time)
                    
                    # 保存 JSON 格式字幕
                    subtitle_json_path = self.output_dir / PATTERN_CLIP_SUBTITLE_JSON.format(filename=output_filename)
                    with open(subtitle_json_path, 'w', encoding='utf-8') as f:
                        json.dump(clip_subtitle, f, ensure_ascii=False, indent=2)
                    result["subtitle_path"] = str(subtitle_json_path)
                    
                    # 保存 SRT 格式字幕
                    subtitle_srt_path = self.output_dir / PATTERN_CLIP_SUBTITLE_SRT.format(filename=output_filename)
                    self.save_subtitle_srt(clip_subtitle, subtitle_srt_path)
                    result["subtitle_srt_path"] = str(subtitle_srt_path)
                    
                    logger.info(f"  ✓ 字幕文件已生成: {subtitle_srt_path.name}")
                
                clipped_results.append(result)
            except Exception as e:
                logger.error(f"裁剪片段 {i} 时出错: {str(e)}")
                continue
        
        logger.info(f"共成功裁剪 {len(clipped_results)} 个视频片段")
        return clipped_results
    
    def _get_chinese_font(self) -> str:
        """
        获取支持中文的字体名称（用于 fontconfig）
        
        Returns:
            字体名称（fontconfig 可识别的名称）
        """
        import platform
        import subprocess
        
        system = platform.system()
        
        # 优先使用的中文字体名称列表（按优先级排序）
        if system == "Darwin":  # macOS
            # macOS 上的中文字体名称（fontconfig 识别的名称）
            font_candidates = [
                "Heiti SC",              # 黑体-简（macOS 内置）
                "Hiragino Sans GB",      # 冬青黑体简体中文
                "STHeiti",               # 华文黑体
                "PingFang SC",           # 苹方-简
                "Arial Unicode MS",      # Arial Unicode
            ]
        elif system == "Windows":
            # Windows 上的中文字体名称
            font_candidates = [
                "Microsoft YaHei",       # 微软雅黑
                "SimHei",                # 黑体
                "SimSun",                # 宋体
                "KaiTi",                 # 楷体
            ]
        else:  # Linux
            # Linux 上的中文字体名称
            font_candidates = [
                "WenQuanYi Micro Hei",   # 文泉驿微米黑
                "WenQuanYi Zen Hei",     # 文泉驿正黑
                "Noto Sans CJK SC",      # Noto Sans CJK 简体中文
                "Droid Sans Fallback",   # Droid Sans Fallback
            ]
        
        # 尝试使用 fc-list 检查字体是否可用
        try:
            result = subprocess.run(
                ["fc-list", ":lang=zh", "family"],
                capture_output=True,
                text=True,
                timeout=5
            )
            available_fonts = result.stdout.lower()
            
            for font_name in font_candidates:
                if font_name.lower() in available_fonts:
                    logger.debug(f"使用中文字体: {font_name}")
                    return font_name
        except Exception as e:
            logger.debug(f"检查字体时出错: {e}")
        
        # 如果没有找到，返回第一个候选字体（希望系统能找到）
        default_font = font_candidates[0] if font_candidates else "Sans"
        logger.warning(f"未能确认中文字体可用性，将使用: {default_font}")
        return default_font
    
    def burn_subtitle(self, video_path: str, subtitle_path: str, 
                     output_path: Optional[str] = None,
                     font_size: int = 18,
                     font_color: str = "white",
                     outline_color: str = "black",
                     position: str = "bottom") -> str:
        """
        将SRT字幕烧录到视频中（硬编码字幕）
        
        Args:
            video_path: 视频文件路径
            subtitle_path: SRT字幕文件路径
            output_path: 输出视频文件路径，如果为None则自动生成
            font_size: 字体大小（默认: 24）
            font_color: 字体颜色（默认: white）
            outline_color: 描边颜色（默认: black）
            position: 字幕位置（top, center, bottom，默认: bottom）
            
        Returns:
            输出视频文件路径
        """
        video_path = Path(video_path)
        subtitle_path = Path(subtitle_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
        
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_with_subtitle.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            logger.info(f"开始将字幕烧录到视频: {video_path.name}")
            logger.info(f"字幕文件: {subtitle_path.name}")
            
            # 获取支持中文的字体
            font_path = self._get_chinese_font()
            
            # ASS/SSA 字幕对齐方式 (numpad 布局)
            # 1=左下, 2=中下, 3=右下
            # 4=左中, 5=正中, 6=右中  
            # 7=左上, 8=中上, 9=右上
            alignment_map = {
                "top": "8",      # 中上
                "center": "5",   # 正中
                "bottom": "2"    # 中下（底部居中）
            }
            alignment = alignment_map.get(position, "2")
            
            # 设置垂直边距（MarginV）- 底部时设置很小以贴近底边
            margin_v = 10 if position == "bottom" else 20
            
            # 使用 ffmpeg 烧录字幕
            video_input = ffmpeg.input(str(video_path))
            
            # 构建字幕样式字符串
            # ASS 颜色格式: &HAABBGGRR (AA=透明度, BB=蓝, GG=绿, RR=红)
            # 白色: &H00FFFFFF (不透明白色)
            # 黑色: &H00000000 (不透明黑色)
            # 半透明黑色背景: &H80000000 (50%透明度黑色)
            #
            # BorderStyle: 
            #   1 = 描边 + 阴影
            #   3 = 不透明背景框
            #   4 = 不透明背景框（带阴影）
            #
            # 使用 BorderStyle=4 可以获得黑色高光背景效果
            force_style = (
                f"FontName={font_path},"        # 中文字体
                f"FontSize={font_size},"        # 字体大小
                f"PrimaryColour=&H00FFFFFF,"    # 白色字体（不透明）
                f"SecondaryColour=&H00FFFFFF,"  # 次要颜色（白色）
                f"OutlineColour=&H00000000,"    # 黑色描边
                f"BackColour=&H80000000,"       # 半透明黑色背景
                f"Bold=1,"                      # 加粗
                f"BorderStyle=4,"               # 不透明背景框带阴影
                f"Outline=2,"                   # 描边宽度
                f"Shadow=1,"                    # 阴影深度
                f"Alignment={alignment},"       # 底部居中
                f"MarginL=20,"                  # 左边距
                f"MarginR=20,"                  # 右边距
                f"MarginV={margin_v}"           # 垂直边距（贴近底部）
            )
            
            logger.info(f"字幕样式: 白色字体 + 黑色高光背景, 位置: {position}")
            
            # 应用字幕滤镜
            video_stream = video_input['v']
            video_stream = video_stream.filter(
                'subtitles',
                str(subtitle_path),
                force_style=force_style
            )
            
            # 输出视频
            output = ffmpeg.output(
                video_stream,
                video_input['a'],
                str(output_path),
                vcodec=self.settings.video_codec,
                acodec='copy',  # 音频流复制，不重新编码
                preset=self.settings.video_preset,
                crf=self.settings.video_crf,
                movflags='faststart'
            )
            
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
            logger.info(f"✓ 字幕烧录完成: {output_path}")
            return str(output_path)
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"烧录字幕时出错: {error_msg}")
            raise
        except Exception as e:
            logger.error(f"烧录字幕时出错: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            raise
    
    def burn_subtitle_simple(self, video_path: str, subtitle_path: str,
                            output_path: Optional[str] = None) -> str:
        """
        将SRT字幕烧录到视频中（简化版本，使用默认样式）
        
        Args:
            video_path: 视频文件路径
            subtitle_path: SRT字幕文件路径
            output_path: 输出视频文件路径，如果为None则自动生成
            
        Returns:
            输出视频文件路径
        """
        return self.burn_subtitle(video_path, subtitle_path, output_path)

