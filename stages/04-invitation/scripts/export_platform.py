#!/usr/bin/env python3
"""Create a clean platform-specific folder without installing or packing it."""
import argparse
import json
import shutil
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',choices=['portable','claude','codex','gemini','workbuddy'],required=True)
    parser.add_argument('--out',type=Path,required=True,help='新目录，末级名称必须为 create-wedding-invitation')
    parser.add_argument('--author',help='WorkBuddy 开放平台要求的实际发布方名称')
    a=parser.parse_args(); root=Path(__file__).resolve().parents[1]; destination=a.out.resolve()
    if destination.name!='create-wedding-invitation': parser.error('末级目录请使用 create-wedding-invitation')
    if destination.exists(): parser.error('目标已存在，请选择新目录，避免覆盖已安装的技能')
    if root in destination.parents: parser.error('导出目录须位于技能目录外')
    if a.target=='workbuddy' and not a.author: parser.error('请提供实际发布方 --author')
    shutil.copytree(root,destination,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))
    if a.target=='workbuddy':
        skill=destination/'SKILL.md'; text=skill.read_text(encoding='utf-8'); end=text.index('\n---',3)
        fields=dict(display_name='动态婚礼电子请柬',description_zh='上传婚纱照生成多款动态请柬，支持特效、BGM、修改续做、公开发布与微信二维码分享海报。',
                    description_en='Create animated wedding invitations with effects, music, revision history, publishing checks and QR share posters.',
                    version='2.1.0',author=a.author)
        extra='\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fields.items())
        skill.write_text(text[:end]+'\n'+extra+text[end:],encoding='utf-8')
    print(json.dumps(dict(directory=str(destination),target=a.target,installed=False,host_verified=False),ensure_ascii=False))

if __name__=='__main__': main()
