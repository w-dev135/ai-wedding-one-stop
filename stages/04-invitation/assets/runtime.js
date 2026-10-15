(() => {
  'use strict';
  const settings = JSON.parse(document.getElementById('invitationConfig').textContent);
  const body = document.body;
  const intro = document.getElementById('intro');
  const music = document.getElementById('musicAudio');
  const musicBtn = document.getElementById('musicBtn');
  const status = document.getElementById('audioStatus');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const main = document.querySelector('main.site');
  const volume = document.getElementById('musicVolume');
  let state = 'closed', timer, toastTimer, soundWanted = false;
  const activeEffects = () => !reduced.matches && settings.effects !== 'off';
  function syncMotion() {
    body.classList.toggle('no-effects', !activeEffects());
    body.classList.toggle('no-photo-motion', !settings.photo_transition);
    body.classList.toggle('js-motion', activeEffects() && settings.photo_transition);
  }
  syncMotion();
  const notice = text => {
    status.textContent = text;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { status.textContent = ''; }, 3200);
  };
  function syncMusic() {
    if (!musicBtn || !music) return;
    const playing = !music.paused && !music.ended;
    musicBtn.classList.toggle('playing', playing);
    musicBtn.textContent = playing ? 'Ⅱ' : '♫';
    musicBtn.setAttribute('aria-label', playing ? '暂停音乐' : '播放音乐');
    musicBtn.setAttribute('aria-pressed', String(playing));
    musicBtn.title = playing ? '暂停音乐' : '播放音乐';
  }
  function playMusic() {
    if (!music) return;
    soundWanted = true;
    // Call play directly inside the user's click; never wait for opening animation.
    try {
      const promise = music.play();
      if (promise && promise.catch) promise.catch(() => {
        soundWanted = false;
        syncMusic();
        notice('音乐暂未播放，可点击右上角重试');
      });
    } catch (_) {
      soundWanted = false;
      notice('音乐暂未播放，可点击右上角重试');
    }
  }
  if (music) {
    music.volume = settings.music_volume;
    if (volume) volume.addEventListener('input', () => {
      music.volume = Math.max(0, Math.min(1, Number(volume.value)));
    });
    music.addEventListener('play', syncMusic);
    music.addEventListener('pause', syncMusic);
    music.addEventListener('ended', syncMusic);
    music.addEventListener('error', () => {
      soundWanted = false;
      syncMusic();
      notice('音乐加载失败，请稍后重试');
    });
    musicBtn.addEventListener('click', () => {
      if (music.paused) playMusic();
      else { soundWanted = false; music.pause(); }
    });
  }
  function burst() {
    if (!activeEffects() || !settings.particles || settings.style !== 'redwhite') return;
    const count = settings.effects === 'subtle' ? 12 : settings.effects === 'festive' ? 32 : 22;
    for (let i = 0; i < count; i++) {
      const piece = document.createElement('i');
      piece.className = 'confetti';
      piece.setAttribute('aria-hidden', 'true');
      piece.style.left = `${5 + (i * 37 % 90)}%`;
      piece.style.setProperty('--drift', `${(i % 2 ? 1 : -1) * (15 + i % 6 * 10)}px`);
      piece.style.setProperty('--duration', `${2 + i % 5 * .16}s`);
      document.body.append(piece);
      setTimeout(() => piece.remove(), 3100);
    }
  }
  function ambient() {
    document.querySelectorAll('.petal,.spark').forEach(item => item.remove());
    body.classList.toggle('no-effects', !activeEffects());
    if (!activeEffects() || !settings.particles || settings.style === 'redwhite') return;
    const count = settings.effects === 'subtle' ? 5 : settings.effects === 'festive' ? 16 : 9;
    for (let i = 0; i < count; i++) {
      const item = document.createElement('i');
      item.className = settings.style === 'floral' ? 'petal' : 'spark';
      item.setAttribute('aria-hidden', 'true');
      // Keep the main reading column free of particle decoration.
      item.style.left = `${i % 2 ? 88 + i % 8 : 2 + i % 8}%`;
      if (settings.style === 'gold') item.style.top = `${8 + i * 79 % 84}%`;
      item.style.setProperty('--duration', `${9 + i % 5}s`);
      item.style.setProperty('--delay', `${-i * 1.4}s`);
      item.style.setProperty('--drift', `${i % 2 ? -14 : 14}px`);
      body.append(item);
    }
  }
  function finishOpening() {
    clearTimeout(timer);
    intro.hidden = true;
    if (main) main.inert = false;
    body.classList.remove('has-intro');
    body.classList.add('opened');
    state = 'opened';
    document.getElementById('mainTitle').focus({ preventScroll: true });
    ambient();
  }
  function open(withSound, skip = false) {
    if (state !== 'closed') return;
    state = 'opening';
    if (withSound) playMusic();
    else if (music) { soundWanted = false; music.pause(); }
    intro.querySelectorAll('button').forEach(button => { button.disabled = button.id !== 'skipIntro'; });
    intro.classList.add('opening');
    burst();
    timer = setTimeout(finishOpening, skip || !activeEffects() ? 0 : 1500);
  }
  document.getElementById('soundOpen').addEventListener('click', () => open(true));
  document.getElementById('silentOpen').addEventListener('click', () => open(false));
  document.getElementById('skipIntro').addEventListener('click', () => {
    if (state === 'opening') finishOpening();
    else open(false, true);
  });
  document.getElementById('replayBtn').addEventListener('click', () => {
    clearTimeout(timer);
    state = 'closed';
    if (music) { soundWanted = false; music.pause(); }
    document.querySelectorAll('.petal,.spark,.confetti').forEach(item => item.remove());
    if (main) main.inert = true;
    intro.classList.remove('opening');
    intro.hidden = false;
    intro.querySelectorAll('button').forEach(button => { button.disabled = false; });
    body.classList.add('has-intro');
    body.classList.remove('opened');
    window.scrollTo({ top: 0, behavior: 'instant' });
    document.getElementById(music ? 'soundOpen' : 'silentOpen').focus();
  });
  document.getElementById('openBtn').addEventListener('click', () => {
    document.getElementById('event').scrollIntoView({ behavior: reduced.matches ? 'instant' : 'smooth' });
  });
  if (settings.opening) {
    if (main) main.inert = true;
    intro.hidden = false;
    body.classList.add('has-intro');
    document.getElementById(music ? 'soundOpen' : 'silentOpen').focus({ preventScroll: true });
  } else { state = 'opened'; intro.hidden = true; body.classList.add('opened'); ambient(); }

  const items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
    }), { threshold: .08 });
    items.forEach(item => observer.observe(item));
  } else items.forEach(item => item.classList.add('visible'));

  async function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(value);
    else {
      const field = document.createElement('textarea');
      field.value = value; body.append(field); field.select();
      const copied = document.execCommand('copy'); field.remove();
      if (!copied) throw new Error('copy unavailable');
    }
  }
  document.getElementById('copyBtn')?.addEventListener('click', async event => {
    try { await copyText(document.getElementById('addressText').textContent); event.target.textContent = '地址已复制'; }
    catch (_) { event.target.textContent = '请长按地址复制'; }
  });
  document.getElementById('shareBtn').addEventListener('click', async event => {
    if (!/^https?:$/.test(location.protocol)) { notice('发布后即可分享链接'); return; }
    try {
      if (navigator.share) await navigator.share({ title: settings.title, text: settings.shareText, url: location.href });
      else { await copyText(location.href); event.target.textContent = '链接已复制'; }
    } catch (error) { if (error.name !== 'AbortError') notice('请从浏览器菜单分享'); }
  });
  document.addEventListener('visibilitychange', () => {
    body.classList.toggle('paused-effects', document.hidden);
    if (document.hidden && music && !music.paused) {
      music.pause();
      notice('音乐已暂停，可点击右上角继续播放');
    }
    // Returning to the foreground never restarts sound without a fresh click.
  });
  window.addEventListener('pagehide', () => { if (music) music.pause(); });
  window.addEventListener('keydown', event => {
    if (event.key === 'Escape' && state === 'opening') finishOpening();
    else if (event.key === 'Escape' && state === 'closed') open(false, true);
    if (event.key === 'Tab' && state !== 'opened') {
      const buttons = [...intro.querySelectorAll('button')].filter(button => !button.hidden && !button.disabled);
      if (!buttons.length) { event.preventDefault(); return; }
      const first = buttons[0], last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  if (reduced.addEventListener) reduced.addEventListener('change', () => {
    syncMotion();
    if (reduced.matches && state === 'opening') finishOpening();
    if (state === 'opened') ambient();
  });
  // Review-only messages adjust a bounded set of visual preferences.
  // A standalone invitation never receives or trusts messages from other tabs.
  window.addEventListener('message', event => {
    if (window.parent === window || event.source !== window.parent || event.data?.type !== 'invitation-preview') return;
    const update = event.data;
    if (['off', 'subtle', 'normal', 'festive'].includes(update.effects)) settings.effects = update.effects;
    if (typeof update.particles === 'boolean') settings.particles = update.particles;
    if (typeof update.photo_transition === 'boolean') settings.photo_transition = update.photo_transition;
    syncMotion();
    document.querySelectorAll('.confetti').forEach(item => item.remove());
    if (state === 'opened') ambient();
    if (!activeEffects() && state === 'opening') finishOpening();
  });
})();
