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
        
        try:
            prompt = f"""请对以下英文文本进行处理，要求：
1. 首先检查并修正文本中的明显错别字和拼写错误
2. 然后将修正后的英文文本翻译成中文
3. 保持原意准确，语言自然流畅
4. 返回格式：第一行是"修正后的英文："，第二行是修正后的英文文本，第三行是"中文翻译："，第四行是中文翻译

英文文本：
{text}

请按照上述格式返回结果："""
            
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
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测章节标记
            if any(marker in line for marker in ['修正后的英文', 'Corrected English', '英文：', '英文:']):
                current_section = 'english'
                continue
            elif any(marker in line for marker in ['中文翻译', 'Chinese Translation', '中文：', '中文:']):
                current_section = 'chinese'
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
                if any('\u4e00' <= char <= '\u9fff' for char in line_stripped):
                    chinese_lines.append(line_stripped)
                elif line_stripped and not any(keyword in line_stripped for keyword in ['修正', '中文', '翻译', 'Corrected', 'Translation']):
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
    
    def save_subtitle_srt(self, subtitle_data: Dict, output_path: Path):
        """
        将字幕数据保存为 SRT 格式（中英文双语，每个时间戳段落12-15个字符）
        
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
        
        with open(output_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            total_segments = len(segments)
            
            logger.info(f"正在生成双语字幕（共 {total_segments} 个原始段落）...")
            
            for idx, seg in enumerate(segments, 1):
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                text = seg.get("text", "").strip()
                
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
                
                # 将文本分割成每段12-15个字符的片段
                english_chunks = self.split_text_by_length(english_text)
                chinese_chunks = self.split_text_by_length(chinese_text) if chinese_text else []
                
                # 计算每个片段的时间分配（按文本长度比例）
                total_duration = end - start
                total_english_chars = sum(self.calculate_text_width(chunk) for chunk in english_chunks)
                
                # 为每个片段创建独立的时间戳段落
                current_time = start
                for chunk_idx, english_chunk in enumerate(english_chunks):
                    # 计算这个片段应该占用的时间（按字符数比例）
                    chunk_chars = self.calculate_text_width(english_chunk)
                    if total_english_chars > 0:
                        chunk_duration = total_duration * (chunk_chars / total_english_chars)
                    else:
                        chunk_duration = total_duration / len(english_chunks) if english_chunks else total_duration
                    
                    chunk_start = current_time
                    chunk_end = min(current_time + chunk_duration, end)
                    current_time = chunk_end
                    
                    # 获取对应的中文片段（如果有）
                    chinese_chunk = chinese_chunks[chunk_idx] if chunk_idx < len(chinese_chunks) else ""
                    
                    # 写入 SRT 格式
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{format_timestamp(chunk_start)} --> {format_timestamp(chunk_end)}\n")
                    
                    # 写入英文文本（单个片段，12-15字符）
                    f.write(f"{english_chunk}\n")
                    
                    # 写入中文文本（如果有）
                    if chinese_chunk:
                        f.write(f"{chinese_chunk}\n")
                    
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

