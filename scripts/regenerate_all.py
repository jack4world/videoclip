#!/usr/bin/env python3
"""
批量重新生成所有片段的字幕和合成视频
使用优化后的参数：字体18px，智能分割长段落
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from videoclip.clippers import VideoClipper

def main():
    clips_dir = Path('work/clips')
    clipper = VideoClipper(output_dir=str(clips_dir))
    
    # 查找所有需要处理的片段（排除已经处理过的 v4, v5 等）
    video_files = sorted(clips_dir.glob("highlight_*.mp4"))
    
    # 过滤出原始视频文件（不包含 _with_subtitle）
    original_videos = [f for f in video_files if '_with_subtitle' not in f.name and '_v' not in f.name]
    
    print(f"找到 {len(original_videos)} 个原始视频文件")
    
    for video_path in original_videos:
        # 构建对应的字幕 JSON 文件路径
        json_path = video_path.with_name(video_path.stem + '_subtitle.json')
        
        if not json_path.exists():
            print(f"⚠ 跳过 {video_path.name}：未找到对应的字幕 JSON 文件")
            continue
        
        print(f"\n{'='*60}")
        print(f"处理: {video_path.name}")
        print(f"{'='*60}")
        
        # 读取字幕数据
        with open(json_path, 'r', encoding='utf-8') as f:
            subtitle_data = json.load(f)
        
        segments = subtitle_data.get('segments', [])
        print(f"读取字幕数据: {len(segments)} 个段落")
        
        # 修正已知的识别错误
        for seg in segments:
            text = seg.get('text', '')
            # 修正 Iain Banks
            if 'in banks, culture books' in text.lower() or 'read in banks' in text.lower():
                print(f"  修正: in banks -> Iain Banks")
                seg['text'] = text.replace('in banks, culture books', "Iain Banks' Culture books").replace('read in banks', "read Iain Banks'")
        
        # 生成新的 SRT 字幕
        srt_path = video_path.with_name(video_path.stem + '_subtitle_new.srt')
        print(f"生成新字幕: {srt_path.name}")
        clipper.save_subtitle_srt(subtitle_data, srt_path)
        
        # 烧制字幕到视频
        output_path = video_path.with_name(video_path.stem + '_with_subtitle_new.mp4')
        print(f"烧制视频: {output_path.name}")
        
        try:
            result = clipper.burn_subtitle(
                video_path=str(video_path),
                subtitle_path=str(srt_path),
                output_path=str(output_path)
            )
            print(f"✓ 完成: {Path(result).name}")
        except Exception as e:
            print(f"✗ 失败: {e}")
            continue
    
    print(f"\n{'='*60}")
    print("全部处理完成！")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

