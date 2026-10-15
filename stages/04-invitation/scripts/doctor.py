#!/usr/bin/env python3
"""Read-only local capability check; never installs tools or probes logins."""
import importlib.util
import json
import shutil
import sys

def main():
    result = dict(python=sys.version.split()[0], supported=sys.version_info >= (3,10),
                  pillow=importlib.util.find_spec('PIL') is not None,
                  qrcode=importlib.util.find_spec('qrcode') is not None,
                  fonttools=importlib.util.find_spec('fontTools') is not None,
                  qr_decoder=importlib.util.find_spec('zxingcpp') is not None,
                  poster_font='share_poster.py 自动查找常见系统中文字体，或以 --font 指定；逐字检查缺字',
                  ffmpeg=bool(shutil.which('ffmpeg')), ffprobe=bool(shutil.which('ffprobe')),
                  hosts={name: bool(shutil.which(name)) for name in ('claude','codex','gemini')},
                  browser='由当前 Agent 检查可用浏览器工具；脚本不自动安装',
                  publishing='由当前 Agent 检查用户所选托管能力；脚本不读取密钥')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['supported'] else 1

if __name__ == '__main__': raise SystemExit(main())
