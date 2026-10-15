#!/usr/bin/env python3
"""Build review or final invitations from versioned JSON or a saved project."""
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from config import read_config, missing, source_path, absolute_config
from media import copy_media, choose_music, share_image
from render import render, STYLES
from preview import render_preview_app
from html import escape as esc

def render_previews(data, photos):
    links = ''.join(f'<a href="{style}.html"><strong>{esc(label)}</strong><span>{esc(slogan)}</span><small>查看完整请柬 →</small></a>' for style, (label,slogan) in STYLES.items())
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>请柬方案对比</title><style>body{{margin:0;background:#f7eedf;color:#681d29;font:16px/1.8 "Songti SC",serif}}main{{max-width:800px;margin:auto;padding:60px 20px;text-align:center}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px}}a{{display:grid;gap:25px;padding:60px 20px;border:1px solid #b48178;background:#fff9f0;color:inherit;text-decoration:none}}strong{{font-size:28px}}small{{margin-top:30px}}</style></head><body><main><p>WEDDING INVITATION</p><h1>选择一封属于你们的请帖</h1><p>{esc(data['name1'])} · {esc(data['name2'])}</p><div class="grid">{links}</div></main></body></html>'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='专用输出目录，勿与项目文件同目录')
    parser.add_argument('--style', choices=['all', *STYLES])
    parser.add_argument('--mode', choices=['review', 'final'], default='review')
    parser.add_argument('--allow-demo', action='store_true', help='明确生成带演示标记的发布样本')
    parser.add_argument('--preview-file', type=Path)
    args = parser.parse_args()
    config, out = args.config.resolve(), args.out.resolve()
    data = read_config(config)
    config_digest = hashlib.sha256(json.dumps(absolute_config(data, config), ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if args.mode == 'final' and data['demo'] and not args.allow_demo:
        raise ValueError('演示资料仅供预览，正式发布须补全真实资料；发布样本可显式使用 --allow-demo')
    if config == out or out in config.parents: raise ValueError('项目或配置文件必须放在发布目录外')
    if args.preview_file and (out == args.preview_file.resolve() or out in args.preview_file.resolve().parents):
        raise ValueError('评审预览请放在发布目录外')
    if out.exists() and any(out.iterdir()):
        marker = out / 'build-manifest.json'
        if not marker.is_file() or json.loads(marker.read_text()).get('generator') != 'create-wedding-invitation':
            raise ValueError('输出目录非空且不属于此生成器，请使用新的专用目录')
    for name in [p['path'] for p in data['photos']] + ([data['music']] if data['music'] else []):
        if out in source_path(name, config).parents: raise ValueError('源照片或音频不能放在生成目录内')
    selected = args.style or data['style']
    styles = list(STYLES) if selected == 'all' and args.mode == 'review' else [data['style'] if selected == 'all' else selected]
    data['style'] = styles[0]
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wedding-build-', dir=out.parent) as temp:
        staging = Path(temp)/'site'; staging.mkdir()
        photos, custom, warnings = copy_media(data, config, staging)
        share = share_image(photos, data, staging)
        if not share: warnings.append('分享封面未生成，需要 Pillow')
        pages = {}
        for style in styles:
            music = choose_music(data, custom, staging, style)
            pages[style] = render(data, photos, music, style, share)
            if args.mode == 'review':
                (staging/f'{style}.html').write_text(pages[style], encoding='utf-8')
        published_photos = photos
        if args.mode == 'final':
            published_photos = [p for p in photos if f'src="{p["src"]}"' in pages[styles[0]]]
            for p in photos:
                if p not in published_photos: (staging/p['src']).unlink()
        (staging/'index.html').write_text(pages[styles[0]], encoding='utf-8')
        if len(styles) > 1: (staging/'previews.html').write_text(render_previews(data, photos), encoding='utf-8')
        preview = render_preview_app(pages, staging, data) if args.preview_file else None
        qr = False
        if data['public_url'] and args.mode == 'final':
            try:
                import qrcode
                qrcode.make(data['public_url']).save(staging/'media'/'link-qr.png'); qr = True
            except ImportError: warnings.append('二维码未生成，需要可选 qrcode 库')
        report = dict(generator='create-wedding-invitation', schema_version=2, config_sha256=config_digest, mode=args.mode, styles=styles, demo=data['demo'],
                      pending=missing(data), photos=[{k:p[k] for k in ('src','width','height','orientation','metadata_removed')} for p in published_photos],
                      warnings=warnings, public_url=data['public_url'], share_cover=share, qr=qr,
                      built_at=datetime.now(timezone.utc).isoformat(),
                      verification=dict(static='generated', browser='pending', wechat='pending', hosts='pending'))
        (staging/'build-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8')
        backup = Path(temp)/'previous'
        if out.exists(): out.rename(backup)
        try: staging.rename(out)
        except BaseException:
            if backup.exists(): backup.rename(out)
            raise
        if args.preview_file:
            args.preview_file.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(dir=args.preview_file.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as f: f.write(preview)
                os.replace(name,args.preview_file)
            finally:
                if os.path.exists(name): os.unlink(name)
    print(json.dumps(dict(output=str(out), styles=styles, mode=args.mode, warnings=warnings, pending=missing(data)),ensure_ascii=False))

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError) as error: raise SystemExit(str(error))
