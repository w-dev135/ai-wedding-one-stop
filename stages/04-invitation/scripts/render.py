"""Photo-first layouts with independently configurable event information."""
import json
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urljoin
from config import missing

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
STYLES = {'redwhite': ('红白双喜', '喜帖轻启，良缘成章'),
          'floral': ('花鸟雅韵', '花开有时，佳期有约'),
          'gold': ('酒红鎏金', '以爱为名，共赴良辰')}
PLACEHOLDER = '<div class="placeholder" role="img" aria-label="待上传照片"><svg viewBox="0 0 210 200" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M22 174c16-37 52-48 85-48s72 15 85 48M64 125c-8-29-1-67 29-71 18-3 27 13 29 34 2 18-6 32-23 41M118 128c-8-30-2-65 27-67 18-1 27 16 27 35 0 20-9 33-29 39"/></svg><span>待上传您的婚纱照</span></div>'

def esc(value): return escape(str(value), quote=True)

def photo_html(photo, eager=False):
    if not photo: return PLACEHOLDER
    x, y = photo['position']
    dims = f' width="{photo["width"]}" height="{photo["height"]}"' if photo['width'] else ''
    priority = 'fetchpriority="high"' if eager else ''
    return f'<img src="{esc(photo["src"])}" alt="{esc(photo["caption"] or "新人婚纱照")}" loading="{"eager" if eager else "lazy"}" decoding="async"{dims} style="object-fit:{photo["fit"]};object-position:{x}% {y}%" {priority}>'

def contrast(color):
    values = [int(color[i:i+2], 16)/255 for i in (1,3,5)]
    linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values]
    luminance = sum(x*y for x,y in zip(linear, (.2126,.7152,.0722)))
    return '#181818' if (luminance+.05)/.059 > 1.05/(luminance+.05) else '#ffffff'

def render(data, photos, music, style, share_cover=''):
    label, default_slogan = STYLES[style]
    slogan = data['slogan'] or default_slogan
    n1, n2 = esc(data['name1'] or '称呼待确认'), esc(data['name2'] or '称呼待确认')
    day = date.fromisoformat(data['date']) if data['date'] else None
    date_text = day.strftime('%Y.%m.%d') if day else '日期待确认'
    event_type = data['event_type'] or '婚礼'
    safe_title = data['share_title'] or f"{data['name1'] or '新人'}与{data['name2'] or '新人'}的{event_type}请柬"
    title = esc(safe_title)
    description = data['share_description'] or f'{slogan}。{date_text}，诚邀您相聚。'
    cover = photos[data['cover_index']] if photos else None
    gallery = [p for i, p in enumerate(photos) if i != data['cover_index']]
    cards = ''.join(f'<figure class="photo-card reveal {p["orientation"]}">{photo_html(p)}{("<figcaption>"+esc(p["caption"])+"</figcaption>") if p["caption"] else ""}</figure>' for p in gallery)
    album = f'<section class="album"><span class="section-label reveal">OUR MOMENTS</span><h2 class="reveal">岁月成诗</h2><div class="photo-grid count-{len(gallery)}">{cards}</div></section>' if gallery and data['sections']['album'] else ''
    headings = {'订婚宴': '良缘初定', '答谢宴': '相聚致谢', '归宁宴': '归宁之喜'}
    heading = headings.get(event_type, '吾家有喜')
    message = esc(data['message'] or f'诚邀您参加我们的{event_type}，共同见证这份喜悦。')
    story = f'<p class="body-copy story-copy reveal">{esc(data["story"])}</p>' if data['story'] else ''
    invitation = f'<section class="invitation" id="story"><span class="section-label reveal">OUR INVITATION</span><h2 class="reveal">{heading}</h2><p class="body-copy reveal">{message}</p>{story}<div class="flourish reveal" aria-hidden="true">✦ · ✦</div></section>' if data['sections']['invitation'] else ''
    times = ''.join(f'<div class="info-line"><span>{name}</span><strong>{esc(data[key])}</strong></div>' for key, name in [('welcome_time', '迎宾'), ('ceremony_time', '仪式'), ('banquet_time', '开席')] if data[key])
    if not times: times = '<div class="info-line pending"><span>时间</span><strong>待确认</strong></div>'
    venue, address = esc(data['venue'] or '场地待确认'), esc(data['address'] or '详细地址待确认')
    map_link = f'<a href="{esc(data["map_url"])}" target="_blank" rel="noopener noreferrer">查看地图</a>' if data['map_url'] else ''
    address_section = f'<section class="address"><span class="section-label reveal">FIND US</span><h2 class="reveal">相聚于此</h2><strong class="reveal">{venue}</strong><p class="body-copy reveal" id="addressText">{address}</p><div class="actions reveal"><button id="copyBtn">复制地址</button>{map_link}<button id="shareBtn">分享请柬</button></div></section>' if data['sections']['address'] else '<div class="actions"><button id="shareBtn">分享请柬</button></div>'
    music_button = '<button class="music" id="musicBtn" aria-label="播放音乐" aria-pressed="false" title="播放音乐">♫</button>' if music else ''
    audio = f'<audio id="musicAudio" src="{esc(music)}" loop preload="none"></audio>' if music else ''
    volume = f'<label class="volume-control">音乐音量<input id="musicVolume" type="range" min="0" max="1" step="0.05" value="{data["music_volume"]}" aria-label="音乐音量"></label>' if music else ''
    demo = f'<div class="demo">{"资料待补充 · 仅供预览" if missing(data) else "演示请柬 · 仅供预览"}</div>' if data['demo'] else ''
    footer = '<div class="footer">演示模板 · 请核对并补全真实资料</div>' if data['demo'] else ''
    settings = dict(title=safe_title, shareText=description, style=style, effects=data['effects'], opening=data['opening'], particles=data['particles'], photo_transition=data['photo_transition'], music_volume=data['music_volume'])
    runtime_config = json.dumps(settings, ensure_ascii=False).replace('<', '\\u003c')
    css = '\n'.join((ASSETS/name).read_text(encoding='utf-8') for name in ('base.css', 'effects.css', 'layout.css'))
    if data['primary_color']:
        css += f'body.{style}' + '{--accent:' + data['primary_color'] + ';--line:' + data['primary_color'] + ';--on-accent:' + contrast(data['primary_color']) + ';}'
    runtime = (ASSETS/'runtime.js').read_text(encoding='utf-8')
    branch = '<svg class="flower-branch" viewBox="0 0 150 280" aria-hidden="true"><path d="M8 270 Q42 190 52 115 Q61 64 107 20 M34 192 Q72 163 116 176 M50 128 Q12 97 12 47 M60 76 Q102 72 128 43"/><circle cx="107" cy="20" r="9"/><circle cx="116" cy="176" r="8"/><circle cx="12" cy="47" r="8"/><circle cx="128" cy="43" r="7"/></svg>'
    arch = '<svg class="arch-line" viewBox="0 0 300 600" preserveAspectRatio="none" aria-hidden="true"><path d="M20 580V170C20 10 280 10 280 170V580Z"/></svg>' if style == 'gold' else ''
    intro = f'<div class="intro" id="intro" role="dialog" aria-modal="true" aria-label="开启请柬" hidden><div class="door left"></div><div class="door right"></div><div class="window-ring"></div>{branch}{arch}<div class="intro-inner"><p class="overline">A LETTER OF LOVE</p><div class="symbol">囍</div><p class="eyebrow">{esc(event_type)}请柬</p><h2 class="names">{n1}<span class="amp">&amp;</span>{n2}</h2><p class="date">{date_text}</p><p class="hero-note">{esc(slogan)}</p><button class="open" id="soundOpen" {"" if music else "hidden"}>有声开启 · ♫</button><button class="silent" id="silentOpen">{"静音浏览" if music else "轻启喜帖"}</button></div><button class="skip" id="skipIntro">跳过开场</button></div>'
    meta = ''
    if data['public_url']:
        meta += f'<link rel="canonical" href="{esc(data["public_url"])}"><meta property="og:url" content="{esc(data["public_url"])}">'
        if share_cover: meta += f'<meta property="og:image" content="{esc(urljoin(data["public_url"], share_cover))}">'
    ending = esc(data['ending'] or '敬备喜筵，恭候光临')
    cls = style + (' no-photo-motion' if not data['photo_transition'] else '')
    hero_class = cover['orientation'] if cover else 'portrait'
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="{data['primary_color'] or '#6e1219'}"><title>{title}</title><meta name="description" content="{esc(description)}"><meta property="og:title" content="{title}"><meta property="og:description" content="{esc(description)}">{meta}<style>{css}</style></head>
<body class="{cls}">{demo}{music_button}{audio}{intro}<div class="audio-status" id="audioStatus" role="status" aria-live="polite"></div><main class="site">
<section class="hero {hero_class}" id="top">{branch}{arch}<div class="cover-photo">{photo_html(cover, True)}</div><div class="hero-core"><p class="overline">{esc(event_type)} · INVITATION</p><h1 class="names" id="mainTitle" tabindex="-1">{n1}<span class="amp">&amp;</span>{n2}</h1><p class="date">{date_text}</p><p class="hero-note">{esc(slogan)}</p><button class="open" id="openBtn">查看宴会安排</button></div><span class="scroll-cue">向下浏览 ↓</span></section>
{invitation}{album}<section class="event" id="event"><span class="section-label reveal">SAVE THE DATE</span><h2 class="reveal">良辰已定</h2><div class="date-big reveal">{date_text}</div>{times}<div class="info-line"><span>宴会地点</span><strong>{venue}</strong></div></section>{address_section}
<div class="ending"><div class="small-symbol" aria-hidden="true">囍</div><p>{ending}<br>{n1} · {n2}</p>{volume}<button class="replay" id="replayBtn" {"" if data['opening'] else "hidden"}>重播开场</button></div>{footer}</main><script id="invitationConfig" type="application/json">{runtime_config}</script><script>{runtime}</script></body></html>'''
