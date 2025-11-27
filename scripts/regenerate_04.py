#!/usr/bin/env python3
"""重新生成 04 片段的字幕"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from videoclip.clippers import VideoClipper

def main():
    # 初始化
    clipper = VideoClipper(output_dir='work/clips')

    # 读取现有的字幕 JSON
    json_path = Path('work/clips/highlight_04_Sure Well if you say like in_subtitle.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        subtitle_data = json.load(f)

    segments = subtitle_data.get('segments', [])
    print(f'读取字幕数据: {len(segments)} 个段落')

    # 修正 Iain Banks 的识别错误
    for seg in segments:
        text = seg.get('text', '')
        if 'in banks, culture books' in text.lower() or 'read in banks' in text.lower():
            print(f'修正: in banks -> Iain Banks')
            seg['text'] = text.replace('in banks, culture books', "Iain Banks' Culture books").replace('read in banks', "read Iain Banks'")

    # 使用新方法生成字幕
    srt_path = Path('work/clips/highlight_04_subtitle_v4.srt')
    clipper.save_subtitle_srt(subtitle_data, srt_path)

    print(f'✓ 字幕生成完成: {srt_path}')

    # 烧制字幕
    video_path = 'work/clips/highlight_04_Sure Well if you say like in.mp4'
    output_path = 'work/clips/highlight_04_with_subtitle_v4.mp4'
    
    print('开始烧制字幕...')
    result = clipper.burn_subtitle(
        video_path=video_path,
        subtitle_path=str(srt_path),
        output_path=output_path
    )
    print(f'✓ 烧制完成: {result}')

if __name__ == "__main__":
    main()

