#!/usr/bin/env python3
"""Optional local audio trimming, normalization and fades; requires ffmpeg."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--seconds', type=float, default=72)
    args = parser.parse_args()
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        parser.error('未安装 ffmpeg/ffprobe；可以直接使用原始音频或内置配乐')
    if not args.input.is_file() or args.start < 0 or args.seconds < 4:
        parser.error('请检查输入文件，并使用非负起点与至少4秒时长')
    if args.input.resolve() == args.output.resolve():
        parser.error('输出路径必须与输入不同，以保留原文件')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(args.input)], capture_output=True, text=True, check=True)
    remaining = float(json.loads(probe.stdout)['format']['duration']) - args.start
    length = min(args.seconds, remaining)
    if length < 4:
        parser.error('起点之后不足4秒，请调整剪辑起点')
    filters = f'loudnorm=I=-20:TP=-1.5:LRA=8,afade=t=in:d=1,afade=t=out:st={length-2}:d=2'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(args.start), '-i', str(args.input), '-t', str(length), '-af', filters, '-ar', '44100', '-codec:a', 'libmp3lame', '-b:a', '128k', str(args.output)], check=True)
    print(args.output.resolve())


if __name__ == '__main__':
    main()
