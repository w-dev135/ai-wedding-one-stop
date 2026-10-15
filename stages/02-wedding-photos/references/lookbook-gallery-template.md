# 沉浸式左右滑动选片画廊规范 (Swipeable Photo Gallery Template)

## 设计铁律 (UI/UX Rules)

1. **拒绝文字卡片堆砌**：画廊界面 **90% 以上的视觉面积必须是婚纱照成片本身**。严禁在页面上方放“双人特征锚点”大段文字框，严禁在图片下方放冗长的英文 Prompt 代码框！
2. **禁止裂图（Zero Broken Images）**：所有写入 `<img src="...">` 的路径必须是**已经真实生成并落盘的本地图片相对路径、Data URI (Base64) 或可访问的真实图片 URL**。如果本地图片与 HTML 不在同一目录，优先通过脚本将生成的图片转为 Base64 内嵌进单文件 HTML，保证 100% 零裂图！
3. **丝滑左右滑动体验**：
   - 采用 `scroll-snap-type: x mandatory` 实现原生级丝滑左右滑动。
   - 同时支持：**手指/触控板左右滑动**、**鼠标按住左右拖拽（Drag to Scroll）**、**左右悬浮箭头点击**、**键盘 `←` / `→` 方向键切换**、以及**底部胶片缩略图条点击跳转**。

---

## 标准单页画廊代码模板 (`wedding_lookbook.html`)

Agent 在生成选片画廊时，**必须直接复用以下结构**，仅需将 `PHOTOS_DATA` 数组中的图片数据替换为真实生成的婚纱照数据：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>AI 婚纱照沉浸式选片画廊 · Lookbook</title>
<style>
  :root {
    --bg: #0F0E0D;
    --surface: rgba(28, 26, 24, 0.78);
    --gold: #D4AF37;
    --text: #F5F2EB;
    --muted: #9E988E;
    --border: rgba(255, 255, 255, 0.12);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; -webkit-user-drag: none; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Serif SC", serif;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* 顶部极简导航栏 */
  header {
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
  }
  .brand { display: flex; align-items: center; gap: 12px; }
  .brand h1 { font-size: 17px; font-weight: 500; letter-spacing: 2px; }
  .counter-pill {
    font-size: 12px;
    color: var(--gold);
    border: 1px solid rgba(212, 175, 55, 0.4);
    padding: 3px 10px;
    border-radius: 999px;
  }
  .filter-bar { display: flex; align-items: center; gap: 10px; }
  .btn-chip {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12.5px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-chip.active, .btn-chip:hover {
    color: #111;
    background: var(--gold);
    border-color: var(--gold);
    font-weight: 600;
  }

  /* 主视觉横向滑动舞台 */
  .stage-wrapper {
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
    overflow: hidden;
  }
  .carousel-track {
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
  }
  .carousel-track:active { cursor: grabbing; }
  .carousel-track::-webkit-scrollbar { display: none; }

  /* 单张婚纱照画框卡片 */
  .photo-slide {
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
  }
  .photo-slide.is-center {
    transform: scale(1);
    opacity: 1;
    border-color: rgba(212, 175, 55, 0.55);
  }
  .photo-slide img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  /* 图片底部极简渐变浮层（仅展示风格名与选片按钮） */
  .slide-overlay {
    position: absolute;
    inset: auto 0 0 0;
    padding: 36px 20px 18px;
    background: linear-gradient(to top, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0.35) 60%, transparent 100%);
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 12px;
  }
  .style-meta .badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    background: var(--gold);
    color: #111;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 6px;
  }
  .style-meta h2 { font-size: 18px; font-weight: 600; color: #fff; }
  .style-meta p { font-size: 12px; color: rgba(255,255,255,0.72); margin-top: 2px; }

  /* 右上角与右下角悬浮操作键 */
  .slide-actions { display: flex; gap: 8px; }
  .icon-btn {
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
  }
  .icon-btn:hover { transform: scale(1.08); border-color: #fff; }
  .icon-btn.fav.liked {
    background: #E11D48;
    border-color: #E11D48;
    color: #fff;
  }

  /* 左右切换大箭头 */
  .nav-arrow {
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
  }
  .nav-arrow:hover { background: var(--gold); color: #111; border-color: var(--gold); }
  .nav-arrow.prev { left: 24px; }
  .nav-arrow.next { right: 24px; }

  /* 底部胶片缩略图导览条 (Filmstrip) */
  .filmstrip-bar {
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
  }
  .thumb-item {
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
  }
  .thumb-item.active {
    border-color: var(--gold);
    opacity: 1;
    transform: translateY(-3px);
  }
  .thumb-item img { width: 100%; height: 100%; object-fit: cover; }
  .thumb-fav-dot {
    position: absolute;
    top: 3px;
    right: 3px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #E11D48;
    display: none;
  }
  .thumb-item.liked .thumb-fav-dot { display: block; }

  /* 全屏高清看片灯箱 (Lightbox) */
  .lightbox {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.94);
    z-index: 100;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }
  .lightbox.open { display: flex; }
  .lightbox img {
    max-width: 92vw;
    max-height: 90vh;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.8);
  }
  .lightbox-close {
    position: absolute;
    top: 24px;
    right: 28px;
    font-size: 28px;
    color: #fff;
    background: none;
    border: none;
    cursor: pointer;
  }
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
  <button class="nav-arrow prev" onclick="stepSlide(-1)" title="上一张 (←)">‹</button>
  <div class="carousel-track" id="carouselTrack"></div>
  <button class="nav-arrow next" onclick="stepSlide(1)" title="下一张 (→)">›</button>
</div>

<div class="filmstrip-bar" id="filmstripBar"></div>

<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <button class="lightbox-close">×</button>
  <img id="lightboxImg" src="" alt="Full size wedding photo">
</div>

<script>
  // Agent 在生成 HTML 时，将真实生成的图片路径或 Base64 注入此数组
  const PHOTOS_DATA = [
    // 示例数据结构：
    // { id: "S1", code: "S1", title: "森系纪实松弛感", camera: "35mm f/1.4 · Kodak Portra 400", src: "data:image/jpeg;base64,..." }
  ];

  let currentFilter = 'all';
  let activeIndex = 0;
  const likedSet = new Set();

  const track = document.getElementById('carouselTrack');
  const filmstrip = document.getElementById('filmstripBar');
  const indicator = document.getElementById('slideIndicator');
  const favCountEl = document.getElementById('favCount');

  function getVisiblePhotos() {
    return currentFilter === 'fav'
      ? PHOTOS_DATA.filter(p => likedSet.has(p.id))
      : PHOTOS_DATA;
  }

  function renderGallery() {
    const list = getVisiblePhotos();
    track.innerHTML = '';
    filmstrip.innerHTML = '';

    if (list.length === 0) {
      track.innerHTML = '<div style="margin:auto;color:#888;font-size:15px;">尚未标记心仪成片，点击照片右下角 ♥ 即可选入相册</div>';
      indicator.innerText = '0 / 0';
      return;
    }

    if (activeIndex >= list.length) activeIndex = 0;

    list.forEach((item, idx) => {
      const isLiked = likedSet.has(item.id);
      const slide = document.createElement('div');
      slide.className = 'photo-slide' + (idx === activeIndex ? ' is-center' : '');
      slide.dataset.index = idx;
      slide.innerHTML = `
        <img src="${item.src}" alt="${item.title}" ondblclick="openLightbox('${item.src}')">
        <div class="slide-overlay">
          <div class="style-meta">
            <span class="badge">${item.code}</span>
            <h2>${item.title}</h2>
            <p>${item.camera}</p>
          </div>
          <div class="slide-actions">
            <button class="icon-btn" onclick="openLightbox('${item.src}')" title="全屏放大">⤢</button>
            <button class="icon-btn fav ${isLiked ? 'liked' : ''}" onclick="toggleFav('${item.id}', event)" title="选入相册">♥</button>
          </div>
        </div>
      `;
      slide.addEventListener('click', (e) => {
        if (!e.target.closest('button')) scrollToSlide(idx);
      });
      track.appendChild(slide);

      const thumb = document.createElement('div');
      thumb.className = `thumb-item ${idx === activeIndex ? 'active' : ''} ${isLiked ? 'liked' : ''}`;
      thumb.innerHTML = `<img src="${item.src}" alt="${item.title}"><span class="thumb-fav-dot"></span>`;
      thumb.onclick = () => scrollToSlide(idx);
      filmstrip.appendChild(thumb);
    });

    updateActiveState(activeIndex);
    setTimeout(() => scrollToSlide(activeIndex, false), 30);
  }

  function scrollToSlide(idx, smooth = true) {
    const slides = track.querySelectorAll('.photo-slide');
    if (!slides[idx]) return;
    activeIndex = idx;
    const target = slides[idx];
    const left = target.offsetLeft - (track.clientWidth - target.clientWidth) / 2;
    track.scrollTo({ left, behavior: smooth ? 'smooth' : 'auto' });
    updateActiveState(idx);
  }

  function updateActiveState(idx) {
    const list = getVisiblePhotos();
    const slides = track.querySelectorAll('.photo-slide');
    const thumbs = filmstrip.querySelectorAll('.thumb-item');
    slides.forEach((el, i) => el.classList.toggle('is-center', i === idx));
    thumbs.forEach((el, i) => el.classList.toggle('active', i === idx));
    indicator.innerText = list.length ? `${idx + 1} / ${list.length}` : '0 / 0';
  }

  function stepSlide(delta) {
    const list = getVisiblePhotos();
    if (!list.length) return;
    const next = Math.max(0, Math.min(list.length - 1, activeIndex + delta));
    scrollToSlide(next);
  }

  function toggleFav(id, ev) {
    ev.stopPropagation();
    if (likedSet.has(id)) likedSet.delete(id);
    else likedSet.add(id);
    favCountEl.innerText = likedSet.size;
    renderGallery();
  }

  function setFilter(mode) {
    currentFilter = mode;
    document.getElementById('btnAll').classList.toggle('active', mode === 'all');
    document.getElementById('btnFav').classList.toggle('active', mode === 'fav');
    activeIndex = 0;
    renderGallery();
  }

  function openLightbox(src) {
    document.getElementById('lightboxImg').src = src;
    document.getElementById('lightbox').classList.add('open');
  }
  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('open');
  }

  // 监听滚动自动高亮中心卡片
  let scrollTimer = null;
  track.addEventListener('scroll', () => {
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => {
      const center = track.scrollLeft + track.clientWidth / 2;
      const slides = track.querySelectorAll('.photo-slide');
      let bestIdx = activeIndex;
      let minDist = Infinity;
      slides.forEach((s, i) => {
        const sCenter = s.offsetLeft + s.clientWidth / 2;
        const d = Math.abs(center - sCenter);
        if (d < minDist) { minDist = d; bestIdx = i; }
      });
      if (bestIdx !== activeIndex) {
        activeIndex = bestIdx;
        updateActiveState(activeIndex);
      }
    }, 60);
  });

  // 鼠标拖拽横向滑动支持
  let isDown = false, startX = 0, scrollLeftStart = 0;
  track.addEventListener('mousedown', (e) => {
    isDown = true;
    startX = e.pageX - track.offsetLeft;
    scrollLeftStart = track.scrollLeft;
  });
  window.addEventListener('mouseup', () => { isDown = false; });
  track.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - track.offsetLeft;
    track.scrollLeft = scrollLeftStart - (x - startX) * 1.4;
  });

  // 键盘左右方向键切图
  window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') stepSlide(-1);
    if (e.key === 'ArrowRight') stepSlide(1);
    if (e.key === 'Escape') closeLightbox();
  });

  renderGallery();
</script>
</body>
</html>
```
