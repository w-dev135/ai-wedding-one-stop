#!/usr/bin/env python3
"""Compose a local share poster with exact typography and a real QR matrix."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from config import read_config, absolute_config, source_path

PALETTES = {
    'redwhite': ('#fff9ef', '#a61924', '#4b3330', '#886e67'),
    'floral': ('#fffaf4', '#896957', '#594c45', '#897b70'),
    'gold': ('#400e1a', '#e8c68a', '#fff4e1', '#d5bfa6'),
}

def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def find_font(explicit):
    if explicit:
        path = explicit.expanduser().resolve()
        if not path.is_file(): raise ValueError('指定字体文件不存在')
        return path
    candidates = [
        Path(__file__).resolve().parents[1] / 'assets/fonts/NotoSansSC-Regular.ttf',
        Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
        Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'),
        Path('/System/Library/Fonts/PingFang.ttc'),
        Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyh.ttc',
    ]
    for p in candidates:
        if p.is_file(): return p
    raise ValueError('未找到中文字体，请使用 --font 指定本机有权使用的中文 TTF/OTF/TTC；不自动下载字体')

def check_glyphs(path, content):
    from fontTools.ttLib import TTFont
    with TTFont(str(path), fontNumber=0) as font:
        cmap = font.getBestCmap() or {}
    absent = sorted({c for c in content if not c.isspace() and ord(c) not in cmap})
    if absent: raise ValueError('字体缺少字符，请更换字体: ' + ''.join(absent))

def atomic_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f: f.write(content)
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='发布目录外的 PNG 海报路径')
    parser.add_argument('--report', type=Path, help='默认同目录同名 .sharing.json；保持在发布目录外')
    parser.add_argument('--font', type=Path)
    parser.add_argument('--bold-font', type=Path)
    parser.add_argument('--online-report', type=Path, help='同一配置与地址的 check_publish 成功报告')
    parser.add_argument('--url-evidence', help='用户确认实际地址可访问的原话和日期；仅在无自动报告时使用')
    parser.add_argument('--allow-unverified-url', action='store_true', help='显式制作标有链接待验证的候选海报')
    parser.add_argument('--allow-demo', action='store_true')
    parser.add_argument('--demo-note', help='演示来源短句，例如 AI 照片、姓名、婚期及场地均为示例')
    a = parser.parse_args()
    config = a.config.resolve(); data = read_config(config)
    out = a.out.resolve(); report_path = (a.report or out.with_suffix('.sharing.json')).resolve()
    if out.suffix.lower() != '.png': raise ValueError('海报输出需要 .png 扩展名')
    if not data['public_url']: raise ValueError('请先将真实发布地址写入 public_url，不生成虚构链接或二维码')
    if not data['photos']: raise ValueError('分享海报需要至少一张照片')
    if data['demo'] and not a.allow_demo: raise ValueError('演示海报须显式 --allow-demo，正式分享请补全真实资料')
    if a.demo_note and not data['demo']: raise ValueError('--demo-note 仅用于演示项目')
    if a.online_report and a.url_evidence: raise ValueError('线上报告与用户确认请选择一项作为访问证据')
    normalized = absolute_config(data, config); config_sha = digest(normalized)
    source = source_path(data['photos'][data['cover_index']]['path'], config)
    font = find_font(a.font); bold = find_font(a.bold_font) if a.bold_font else font
    protected = {config, font.resolve(), bold.resolve(), *[source_path(p['path'], config) for p in data['photos']]}
    if data['music']: protected.add(source_path(data['music'], config))
    if a.online_report: protected.add(a.online_report.resolve())
    if out == report_path or out in protected or report_path in protected:
        raise ValueError('海报和报告须使用独立路径，不能覆盖配置、证据、字体或原始素材')
    for dest in (out, report_path):
        if any((parent / 'build-manifest.json').exists() for parent in dest.parents):
            raise ValueError('海报与分享报告请放在网页发布目录外')
    url_state = 'pending'; evidence = ''
    if a.online_report:
        check = json.loads(a.online_report.read_text(encoding='utf-8'))
        if (check.get('online') != 'passed' or check.get('static') != 'passed' or check.get('errors')
                or check.get('url') != data['public_url'] or check.get('config_sha256') != config_sha
                or check.get('styles') != [data['style']]):
            raise ValueError('线上报告未通过或与当前配置、风格、地址不一致，请重新检查')
        url_state = 'passed'; evidence = 'check_publish'
    elif a.url_evidence and a.url_evidence.strip():
        url_state = 'user_confirmed'; evidence = a.url_evidence.strip()
    elif not a.allow_unverified_url:
        raise ValueError('先验证地址并提供 --online-report 或 --url-evidence；候选海报须显式 --allow-unverified-url')
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
        import qrcode
        from fontTools.ttLib import TTFont  # required glyph coverage check
    except ImportError as e:
        raise ValueError('海报需要 Pillow、qrcode、fonttools；按宿主权限准备依赖后重试') from e
    bg, accent, ink, muted = PALETTES[data['style']]
    heading = data['share_title'] or data['event_type'] + '请柬'
    names = (data['name1'] or '新人称呼待确认') + ' & ' + (data['name2'] or '新人称呼待确认')
    day = date.fromisoformat(data['date']).strftime('%Y.%m.%d') if data['date'] else '日期待确认'
    venue = data['venue'] or '场地待确认'
    times = ' · '.join(label + ' ' + data[key] for key, label in
                       [('welcome_time','迎宾'),('ceremony_time','仪式'),('banquet_time','开席')] if data[key]) or '时间待确认'
    slogan = data['slogan'] or '诚邀您见证我们的幸福时刻'
    ending = data['ending'] or '岁月作序，与你成诗'
    footer = ('演示版 · ' + (a.demo_note or '照片与婚宴资料请以实际标注为准')) if data['demo'] else ''
    if url_state == 'pending': footer = (footer + ' · ' if footer else '') + '链接待验证'
    badge = '囍' if data['style'] == 'redwhite' else '良缘' if data['style'] == 'floral' else '佳期'
    qr_caption = '长按识别 · 查看动态请柬'
    content = ''.join([heading, names, day, venue, times, slogan, ending, footer, badge, qr_caption])
    check_glyphs(font, content); check_glyphs(bold, content)
    canvas = Image.new('RGB', (1080,1920), bg); draw = ImageDraw.Draw(canvas)
    def write(txt, x, y, size, color=ink, align='start', strong=False, max_width=880, min_size=22):
        txt = ' '.join(txt.split())
        font_path = bold if strong else font
        for chosen in range(size, min_size-1, -1):
            face = ImageFont.truetype(str(font_path), chosen)
            if draw.textlength(txt, font=face) <= max_width: break
        else: raise ValueError('文案过长，当前海报无法完整排下，请缩短: ' + txt[:24])
        width = draw.textlength(txt, font=face)
        if align == 'middle': x -= width/2
        draw.text((round(x), y), txt, font=face, fill=color, anchor='ls')
    draw.rectangle((18,18,1061,1901), outline=accent, width=3)
    for x,y,sx,sy in [(38,38,1,1),(1042,38,-1,1),(38,1882,1,-1),(1042,1882,-1,-1)]:
        draw.line([(x+sx*56,y),(x,y),(x,y+sy*56)], fill=accent, width=7)
    write(badge,540,115,92,accent,'middle',True)
    draw.line((140,165,305,165), fill=accent,width=1); draw.line((775,165,940,165),fill=accent,width=1)
    write(heading,540,211,62,accent,'middle',True,max_width=780)
    write(names,540,277,40,ink,'middle')
    write(slogan,540,322,26,muted,'middle',max_width=880)
    with Image.open(source) as original:
        oriented = ImageOps.exif_transpose(original); oriented.load()
        fitted = ImageOps.contain(oriented.convert('RGBA'),(880,1173),Image.Resampling.LANCZOS)
        canvas.paste(fitted,(100+(880-fitted.width)//2,356+(1173-fitted.height)//2),fitted.getchannel('A'))
    draw.rectangle((98,354,981,1531), outline=accent,width=2)
    # QR has a white four-module quiet zone; never decorate or generate it with an image model.
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=1,border=4)
    qr.add_data(data['public_url'])
    try: qr.make(fit=True)
    except qrcode.exceptions.DataOverflowError as e:
        raise ValueError('链接过长，二维码无法编码，请使用经确认可用的更短地址') from e
    matrix=qr.get_matrix()
    module=276//len(matrix)
    if module < 4: raise ValueError('链接过长，二维码过密，请使用经确认可用的更短地址')
    side=len(matrix)*module; qx=980-side; qy=1550
    draw.rectangle((qx,qy,qx+side-1,qy+side-1),fill='white')
    for row, values in enumerate(matrix):
        for col, value in enumerate(values):
            if value: draw.rectangle((qx+col*module,qy+row*module,qx+(col+1)*module-1,qy+(row+1)*module-1),fill='#1c1513')
    left_width=qx-136
    write(day,100,1601,47,accent,strong=True,max_width=left_width)
    write(venue,100,1664,36,ink,strong=True,max_width=left_width)
    write(times,100,1716,27,muted,max_width=left_width)
    write(ending,100,1777,29,accent,max_width=left_width)
    write(qr_caption,qx+side/2,qy+side+36,24,ink,'middle',max_width=340)
    draw.line((100,1831,min(570,qx-36),1831),fill=muted,width=1)
    if footer: write(footer,540,1885,22,muted,'middle',max_width=900)
    qr_state='not_run'; sizes=[]; warnings=[]
    try:
        import zxingcpp
        for width in [1080,540,360]:
            sample=canvas.resize((width,round(canvas.height*width/canvas.width)),Image.Resampling.LANCZOS)
            if not any(r.text == data['public_url'] for r in zxingcpp.read_barcodes(sample)):
                raise ValueError(f'海报在{width}px宽度下二维码解码失败，旧版海报保留')
            sizes.append(width)
        qr_state='passed'
    except ImportError: warnings.append('未安装 zxing-cpp，二维码程序解码待验证，请在微信长按原图实测')
    if data['demo']: warnings.append('演示内容请保留标记；AI 照片来源须在交付时说明')
    if url_state=='pending': warnings.append('候选链接未验证，不能宣称亲友可用')
    import io
    png=io.BytesIO(); canvas.save(png,'PNG',optimize=True)
    info=dict(generator='create-wedding-invitation-share-poster',generated_at=datetime.now(timezone.utc).isoformat(),
              config_sha256=config_sha,style=data['style'],demo=data['demo'],url=data['public_url'],
              cover_index=data['cover_index'],photo_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              poster_sha256=hashlib.sha256(png.getvalue()).hexdigest(),size=[1080,1920],
              verification=dict(url=url_state,url_evidence=evidence,qr=qr_state,qr_widths=sizes,visual='pending',wechat='pending'),
              warnings=warnings)
    # All validation occurs before replacing either deliverable.
    atomic_bytes(out,png.getvalue())
    atomic_bytes(report_path,json.dumps(info,ensure_ascii=False,indent=2).encode())
    print(json.dumps(dict(output=str(out),report=str(report_path),**info),ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except (ValueError,OSError) as error: raise SystemExit(str(error))
