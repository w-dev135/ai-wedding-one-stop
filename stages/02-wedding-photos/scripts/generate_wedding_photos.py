#!/usr/bin/env python3
"""
AI Wedding Photo Batch Generator & Swipeable Gallery Builder (v2.0)
支持：
1. 组装双人防串脸多风格婚纱照生图指令
2. 将已生成的婚纱照图片目录（自动转 Base64 防裂图）打包成全屏左右滑动选片画廊 (wedding_lookbook.html)
"""

import argparse
import base64
import json
import mimetypes
import os
from datetime import datetime

STYLE_PRESETS = {
    "S1": {
        "name": "森系纪实松弛感",
        "en_name": "Forest Candid & Effortless",
        "camera": "35mm f/1.4 · Kodak Portra 400",
        "prompt_template": (
            "Candid editorial wedding photography in a sunlit misty cedar forest. "
            "On the left stands the groom ({groom}), wearing a breathable beige linen suit with an unbuttoned white shirt. "
            "On the right stands the bride ({bride}), wearing a flowy lightweight French tulle slip wedding dress, holding a wild chamomile bouquet. "
            "They are running hand-in-hand along a forest path, laughing joyfully. Golden hour backlight creating volumetric Tyndall light beams. "
            "Shot on 35mm f/1.4 lens, Kodak Portra 400 film stock, authentic skin texture, distinct individual facial features, no face swapping."
        )
    },
    "S2": {
        "name": "王家卫复古港风",
        "en_name": "90s Hong Kong Cinema Vintage",
        "camera": "50mm f/1.2 · CineStill 800T",
        "prompt_template": (
            "1990s Wong Kar-wai style cinematic wedding portrait set in a vintage Hong Kong street corner at dusk. "
            "On the left stands the groom ({groom}) in a classic tailored double-breasted black tuxedo. "
            "On the right stands the bride ({bride}) in a vintage off-shoulder ivory satin gown and pearl drop earrings with retro wavy hair. "
            "Warm tungsten streetlamps and emerald-green neon reflections, subtle motion blur, shallow depth of field. "
            "Shot on 50mm f/1.2 lens, CineStill 800T film look, rich film grain, distinct individual facial features."
        )
    },
    "S3": {
        "name": "新中式东方雅韵",
        "en_name": "Neo-Chinese Oriental Elegance",
        "camera": "85mm f/1.8 · Medium Format",
        "prompt_template": (
            "High-fashion Neo-Chinese wedding photography in a classical Suzhou courtyard with white walls and dappled bamboo shadows. "
            "On the left stands the groom ({groom}) wearing a refined black mandarin-collar tailored suit. "
            "On the right stands the bride ({bride}) wearing an exquisite champagne-gold and crimson Song brocade bridal gown, holding a silk round fan. "
            "Soft diffused natural lighting, poetic negative space, serene affectionate eye contact. "
            "Shot on 85mm f/1.8 lens, muted oriental color palette, distinct individual facial features."
        )
    },
    "S4": {
        "name": "极简韩式光影主纱",
        "en_name": "Minimalist Korean Fine-Art Studio",
        "camera": "80mm Hasselblad · Fine-Art Studio",
        "prompt_template": (
            "Minimalist Korean fine-art studio wedding portrait. Architectural concrete grey background with a sharp diagonal beam of natural window light. "
            "On the left stands the groom ({groom}) in a bespoke black peak-lapel tuxedo and bow tie. "
            "On the right stands the bride ({bride}) in a sculptural heavy silk mikado satin ballgown with a long sheer veil floating in the air. "
            "Clean editorial lighting, exquisite silk sheen, shot on Hasselblad medium format camera, 80mm lens, distinct individual facial features."
        )
    },
    "S5": {
        "name": "冰岛旷野公路旅拍",
        "en_name": "Icelandic Wilderness & Blue Hour",
        "camera": "24mm f/1.4 · Fujifilm Pro 400H",
        "prompt_template": (
            "Epic destination wedding photography on a black sand beach in Iceland during blue hour with snow-capped mountains behind. "
            "On the left stands the groom ({groom}) in a charcoal wool overcoat over a suit, holding the bride close. "
            "On the right stands the bride ({bride}) in a romantic lace long-sleeve wedding gown with a 3-meter sheer veil billowing in the wind. "
            "Warm lantern glow on their faces against the cool teal twilight sky. Shot on 24mm f/1.4 wide-angle lens, Fujifilm Pro 400H."
        )
    },
    "S6": {
        "name": "赫本黑金复古画报",
        "en_name": "Audrey Hepburn Black & Gold Glamour",
        "camera": "50mm Leica · Studio Butterfly Light",
        "prompt_template": (
            "Classic 1950s Hollywood glamour wedding portrait inside a vintage opera house with dark velvet curtains and warm chandelier bokeh. "
            "On the left stands the groom ({groom}) in a velvet shawl-collar tuxedo. "
            "On the right stands the bride ({bride}) in a fitted black velvet couture gown, layered pearl necklace, black opera gloves, and birdcage veil. "
            "Dramatic butterfly lighting, black and champagne-gold color grading, shot on 50mm Leica lens."
        )
    },
    "S7": {
        "name": "南法庄园莫奈油画",
        "en_name": "South of France Manor & Monet Pastel",
        "camera": "50mm Soft-Focus · Kodak Portra 160",
        "prompt_template": (
            "Romantic French countryside chateau wedding photography in a blooming garden of pastel hydrangeas. "
            "On the left stands the groom ({groom}) in a cream-white tailored three-piece suit. "
            "On the right stands the bride ({bride}) in a vintage Chantilly lace mermaid wedding dress. "
            "Dreamy afternoon golden sunlight, subtle soft-focus lens filter creating a Monet impressionist glow, Kodak Portra 160 aesthetic."
        )
    },
    "S8": {
        "name": "街头夜景机顶直闪",
        "en_name": "Urban Night & Direct Flash Editorial",
        "camera": "28mm Direct Flash · Fujifilm Superia 400",
        "prompt_template": (
            "Cool urban night street wedding photography shot with direct on-camera paparazzi flash on a city rooftop. "
            "On the left stands the groom ({groom}) in an oversized black blazer and loosened tie, holding a champagne glass. "
            "On the right stands the bride ({bride}) in a chic mini tulle puff wedding dress and short sheer veil. "
            "Playful candid laughing expressions, hard direct flash lighting, Fujifilm Superia 400 film grain."
        )
    }
}


def image_to_data_uri(filepath: str) -> str:
    mime, _ = mimetypes.guess_type(filepath)
    if not mime:
        mime = "image/jpeg"
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def build_swipe_gallery_html(photos_data: list, output_path: str):
    photos_json = json.dumps(photos_data, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>AI 婚纱照沉浸式选片画廊 · Lookbook</title>
<style>
  :root {{
    --bg: #0F0E0D;
    --surface: rgba(28, 26, 24, 0.78);
    --gold: #D4AF37;
    --text: #F5F2EB;
    --muted: #9E988E;
    --border: rgba(255, 255, 255, 0.12);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; -webkit-user-drag: none; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Serif SC", serif;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  header {{
    height: 60px;
    padding: 0 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    background: rgba(15, 14, 13, 0.85);
    backdrop-filter: blur(12px);
    z-index: 20;
    flex-shrink: 0;
  }}
  .brand {{ display: flex; align-items: center; gap: 12px; }}
  .brand h1 {{ font-size: 17px; font-weight: 500; letter-spacing: 2px; }}
  .counter-pill {{
    font-size: 12px;
    color: var(--gold);
    border: 1px solid rgba(212, 175, 55, 0.4);
    padding: 3px 10px;
    border-radius: 999px;
  }}
  .filter-bar {{ display: flex; align-items: center; gap: 10px; }}
  .btn-chip {{
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12.5px;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .btn-chip.active, .btn-chip:hover {{
    color: #111;
    background: var(--gold);
    border-color: var(--gold);
    font-weight: 600;
  }}
  .stage-wrapper {{
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
    overflow: hidden;
  }}
  .carousel-track {{
    display: flex;
    align-items: center;
    gap: 32px;
    padding: 0 calc(50vw - 230px);
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    width: 100%;
    height: 100%;
    scrollbar-width: none;
    cursor: grab;
  }}
  .carousel-track:active {{ cursor: grabbing; }}
  .carousel-track::-webkit-scrollbar {{ display: none; }}
  .photo-slide {{
    scroll-snap-align: center;
    flex: 0 0 auto;
    width: min(76vw, 460px);
    height: min(72vh, 640px);
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    background: #1A1817;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65);
    border: 1px solid var(--border);
    transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.35s, border-color 0.35s;
    transform: scale(0.9);
    opacity: 0.45;
  }}
  .photo-slide.is-center {{
    transform: scale(1);
    opacity: 1;
    border-color: rgba(212, 175, 55, 0.55);
  }}
  .photo-slide img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}
  .slide-overlay {{
    position: absolute;
    inset: auto 0 0 0;
    padding: 36px 20px 18px;
    background: linear-gradient(to top, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0.35) 60%, transparent 100%);
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 12px;
  }}
  .style-meta .badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    background: var(--gold);
    color: #111;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 6px;
  }}
  .style-meta h2 {{ font-size: 18px; font-weight: 600; color: #fff; }}
  .style-meta p {{ font-size: 12px; color: rgba(255,255,255,0.72); margin-top: 2px; }}
  .slide-actions {{ display: flex; gap: 8px; }}
  .icon-btn {{
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.25);
    background: rgba(20, 20, 20, 0.65);
    backdrop-filter: blur(8px);
    color: #fff;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .icon-btn:hover {{ transform: scale(1.08); border-color: #fff; }}
  .icon-btn.fav.liked {{
    background: #E11D48;
    border-color: #E11D48;
    color: #fff;
  }}
  .nav-arrow {{
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: 1px solid var(--border);
    background: var(--surface);
    backdrop-filter: blur(10px);
    color: var(--text);
    font-size: 20px;
    cursor: pointer;
    z-index: 15;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }}
  .nav-arrow:hover {{ background: var(--gold); color: #111; border-color: var(--gold); }}
  .nav-arrow.prev {{ left: 24px; }}
  .nav-arrow.next {{ right: 24px; }}
  .filmstrip-bar {{
    height: 92px;
    padding: 10px 24px;
    background: rgba(15, 14, 13, 0.92);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    overflow-x: auto;
    flex-shrink: 0;
  }}
  .thumb-item {{
    width: 52px;
    height: 68px;
    border-radius: 6px;
    overflow: hidden;
    border: 2px solid transparent;
    opacity: 0.45;
    cursor: pointer;
    position: relative;
    transition: all 0.2s;
    flex-shrink: 0;
  }}
  .thumb-item.active {{
    border-color: var(--gold);
    opacity: 1;
    transform: translateY(-3px);
  }}
  .thumb-item img {{ width: 100%; height: 100%; object-fit: cover; }}
  .thumb-fav-dot {{
    position: absolute;
    top: 3px;
    right: 3px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #E11D48;
    display: none;
  }}
  .thumb-item.liked .thumb-fav-dot {{ display: block; }}
  .lightbox {{
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.94);
    z-index: 100;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }}
  .lightbox.open {{ display: flex; }}
  .lightbox img {{
    max-width: 92vw;
    max-height: 90vh;
    object-fit: contain;
    border-radius: 8px;
  }}
  .lightbox-close {{
    position: absolute;
    top: 24px;
    right: 28px;
    font-size: 28px;
    color: #fff;
    background: none;
    border: none;
    cursor: pointer;
  }}
</style>
</head>
<body>
<header>
  <div class="brand">
    <h1>AI WEDDING GALLERY · 选片台</h1>
    <span class="counter-pill" id="slideIndicator">1 / 1</span>
  </div>
  <div class="filter-bar">
    <button class="btn-chip active" id="btnAll" onclick="setFilter('all')">全部成片</button>
    <button class="btn-chip" id="btnFav" onclick="setFilter('fav')">♥ 已选入册 (<span id="favCount">0</span>)</button>
  </div>
</header>
<div class="stage-wrapper">
  <button class="nav-arrow prev" onclick="stepSlide(-1)">‹</button>
  <div class="carousel-track" id="carouselTrack"></div>
  <button class="nav-arrow next" onclick="stepSlide(1)">›</button>
</div>
<div class="filmstrip-bar" id="filmstripBar"></div>
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <button class="lightbox-close">×</button>
  <img id="lightboxImg" src="" alt="Full size wedding photo">
</div>
<script>
  const PHOTOS_DATA = {photos_json};
  let currentFilter = 'all';
  let activeIndex = 0;
  const likedSet = new Set();
  const track = document.getElementById('carouselTrack');
  const filmstrip = document.getElementById('filmstripBar');
  const indicator = document.getElementById('slideIndicator');
  const favCountEl = document.getElementById('favCount');

  function getVisiblePhotos() {{
    return currentFilter === 'fav' ? PHOTOS_DATA.filter(p => likedSet.has(p.id)) : PHOTOS_DATA;
  }}
  function renderGallery() {{
    const list = getVisiblePhotos();
    track.innerHTML = '';
    filmstrip.innerHTML = '';
    if (!list.length) {{
      track.innerHTML = '<div style="margin:auto;color:#888;font-size:15px;">尚未标记心仪成片，点击照片右下角 ♥ 即可选入相册</div>';
      indicator.innerText = '0 / 0';
      return;
    }}
    if (activeIndex >= list.length) activeIndex = 0;
    list.forEach((item, idx) => {{
      const isLiked = likedSet.has(item.id);
      const slide = document.createElement('div');
      slide.className = 'photo-slide' + (idx === activeIndex ? ' is-center' : '');
      slide.innerHTML = `
        <img src="${{item.src}}" alt="${{item.title}}" ondblclick="openLightbox('${{item.src}}')">
        <div class="slide-overlay">
          <div class="style-meta">
            <span class="badge">${{item.code}}</span>
            <h2>${{item.title}}</h2>
            <p>${{item.camera}}</p>
          </div>
          <div class="slide-actions">
            <button class="icon-btn" onclick="openLightbox('${{item.src}}')" title="全屏放大">⤢</button>
            <button class="icon-btn fav ${{isLiked ? 'liked' : ''}}" onclick="toggleFav('${{item.id}}', event)" title="选入相册">♥</button>
          </div>
        </div>
      `;
      slide.addEventListener('click', (e) => {{ if (!e.target.closest('button')) scrollToSlide(idx); }});
      track.appendChild(slide);

      const thumb = document.createElement('div');
      thumb.className = `thumb-item ${{idx === activeIndex ? 'active' : ''}} ${{isLiked ? 'liked' : ''}}`;
      thumb.innerHTML = `<img src="${{item.src}}" alt="${{item.title}}"><span class="thumb-fav-dot"></span>`;
      thumb.onclick = () => scrollToSlide(idx);
      filmstrip.appendChild(thumb);
    }});
    updateActiveState(activeIndex);
    setTimeout(() => scrollToSlide(activeIndex, false), 30);
  }}
  function scrollToSlide(idx, smooth = true) {{
    const slides = track.querySelectorAll('.photo-slide');
    if (!slides[idx]) return;
    activeIndex = idx;
    const target = slides[idx];
    const left = target.offsetLeft - (track.clientWidth - target.clientWidth) / 2;
    track.scrollTo({{ left, behavior: smooth ? 'smooth' : 'auto' }});
    updateActiveState(idx);
  }}
  function updateActiveState(idx) {{
    const list = getVisiblePhotos();
    track.querySelectorAll('.photo-slide').forEach((el, i) => el.classList.toggle('is-center', i === idx));
    filmstrip.querySelectorAll('.thumb-item').forEach((el, i) => el.classList.toggle('active', i === idx));
    indicator.innerText = list.length ? `${{idx + 1}} / ${{list.length}}` : '0 / 0';
  }}
  function stepSlide(delta) {{
    const list = getVisiblePhotos();
    if (!list.length) return;
    scrollToSlide(Math.max(0, Math.min(list.length - 1, activeIndex + delta)));
  }}
  function toggleFav(id, ev) {{
    ev.stopPropagation();
    if (likedSet.has(id)) likedSet.delete(id); else likedSet.add(id);
    favCountEl.innerText = likedSet.size;
    renderGallery();
  }}
  function setFilter(mode) {{
    currentFilter = mode;
    document.getElementById('btnAll').classList.toggle('active', mode === 'all');
    document.getElementById('btnFav').classList.toggle('active', mode === 'fav');
    activeIndex = 0;
    renderGallery();
  }}
  function openLightbox(src) {{
    document.getElementById('lightboxImg').src = src;
    document.getElementById('lightbox').classList.add('open');
  }}
  function closeLightbox() {{ document.getElementById('lightbox').classList.remove('open'); }}

  let scrollTimer = null;
  track.addEventListener('scroll', () => {{
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => {{
      const center = track.scrollLeft + track.clientWidth / 2;
      let bestIdx = activeIndex, minDist = Infinity;
      track.querySelectorAll('.photo-slide').forEach((s, i) => {{
        const d = Math.abs(center - (s.offsetLeft + s.clientWidth / 2));
        if (d < minDist) {{ minDist = d; bestIdx = i; }}
      }});
      if (bestIdx !== activeIndex) {{ activeIndex = bestIdx; updateActiveState(activeIndex); }}
    }}, 60);
  }});

  let isDown = false, startX = 0, scrollLeftStart = 0;
  track.addEventListener('mousedown', (e) => {{ isDown = true; startX = e.pageX - track.offsetLeft; scrollLeftStart = track.scrollLeft; }});
  window.addEventListener('mouseup', () => {{ isDown = false; }});
  track.addEventListener('mousemove', (e) => {{
    if (!isDown) return;
    e.preventDefault();
    track.scrollLeft = scrollLeftStart - (e.pageX - track.offsetLeft - startX) * 1.4;
  }});
  window.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowLeft') stepSlide(-1);
    if (e.key === 'ArrowRight') stepSlide(1);
    if (e.key === 'Escape') closeLightbox();
  }});
  renderGallery();
</script>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(description="Build Swipeable AI Wedding Photo Gallery from generated images.")
    parser.add_argument("--images-dir", required=True, help="Directory containing generated wedding photos (e.g. S1.jpg, S2.png)")
    parser.add_argument("--out-html", default="./wedding_lookbook.html", help="Output path for swipeable HTML gallery")
    args = parser.parse_args()

    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    photos_data = []
    if os.path.isdir(args.images_dir):
        for fname in sorted(os.listdir(args.images_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in valid_exts:
                continue
            fpath = os.path.join(args.images_dir, fname)
            prefix = os.path.splitext(fname)[0].split("_")[0].upper()
            preset = STYLE_PRESETS.get(prefix, {
                "name": os.path.splitext(fname)[0],
                "camera": "AI Wedding Portrait · Editorial Look"
            })
            photos_data.append({
                "id": fname,
                "code": prefix if prefix in STYLE_PRESETS else "PHOTO",
                "title": preset["name"],
                "camera": preset["camera"],
                "src": image_to_data_uri(fpath)
            })

    build_swipe_gallery_html(photos_data, args.out_html)
    print(f"[OK] Built swipeable gallery with {len(photos_data)} embedded photos -> {args.out_html}")


if __name__ == "__main__":
    main()
