"""Local asset inspection and publishing copies; originals remain untouched."""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from config import source_path

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
AUDIO_EXT = {'.mp3', '.m4a', '.ogg', '.wav'}

def copy_media(data, config, output):
    folder = output / 'media'; folder.mkdir(parents=True)
    photos, warnings, seen = [], [], set()
    try:
        from PIL import Image, ImageOps
    except ImportError:
        Image = None
        warnings.append('未安装 Pillow，图片解码、方向修正、压缩及元数据清理未验证')
    for idx, photo in enumerate(data['photos']):
        source = source_path(photo['path'], config)
        if source.suffix.lower() not in IMAGE_EXT or not source.is_file(): raise ValueError(f'照片无法读取: 第{idx+1}张')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest in seen: warnings.append(f'第{idx+1}张与前面的照片内容重复')
        seen.add(digest)
        p = {k: v for k, v in photo.items() if k != 'path'}
        p.update(width=None, height=None, metadata_removed=False)
        if Image:
            try:
                with Image.open(source) as original:
                    if getattr(original, 'is_animated', False): warnings.append(f'第{idx+1}张为动图，发布副本使用首帧')
                    image = ImageOps.exif_transpose(original)
                    image.load()
                    p['width'], p['height'] = image.size
                    if min(image.size) < 600: warnings.append(f'第{idx+1}张短边小于600像素，可能不够清晰')
                    image.thumbnail((1800, 2400))
                    # Start with a clean image object to omit EXIF/GPS/XMP/comments.
                    rgba = image.convert('RGBA')
                    clean = Image.new('RGB', image.size, '#f7eedf')
                    clean.paste(rgba, mask=rgba.getchannel('A'))
                    target = folder / f'photo_{idx+1:02d}.jpg'
                    clean.save(target, 'JPEG', quality=86, optimize=True)
                    p['metadata_removed'] = True
            except (OSError, ValueError) as e: raise ValueError(f'第{idx+1}张照片解码失败，请换一份图片') from e
        else:
            target = folder / f'photo_{idx+1:02d}{source.suffix.lower()}'
            if source.stat().st_size < 16: raise ValueError(f'第{idx+1}张照片为空或不完整')
            shutil.copyfile(source, target)
        p['src'] = 'media/' + target.name
        p['orientation'] = 'landscape' if p['width'] and p['width'] > p['height'] * 1.15 else 'portrait' if p['width'] and p['height'] > p['width'] * 1.15 else 'square'
        photos.append(p)
    custom = ''
    if data['music'] and data['bgm'] != 'none':
        source = source_path(data['music'], config)
        if source.suffix.lower() not in AUDIO_EXT or not source.is_file(): raise ValueError('音频文件无法读取或格式不支持')
        trim = data['music_start'] > 0 or data['music_seconds'] is not None
        target = folder / ('music.mp3' if trim else 'music' + source.suffix.lower())
        if trim:
            try:
                subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_audio.py')), '--input', str(source), '--output', str(target), '--start', str(data['music_start']), '--seconds', str(data['music_seconds'] or 72)], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as error:
                raise ValueError('音乐截取失败，请检查 ffmpeg/ffprobe、音频格式与起点后的剩余时长；旧版已保留') from error
        else: shutil.copyfile(source, target)
        custom = 'media/' + target.name
        if not data['music_credit']: warnings.append('自定义音乐未填写来源，请核对使用范围')
    return photos, custom, warnings

def choose_music(data, custom, output, style):
    if data['bgm'] == 'none': return ''
    if custom: return custom
    source = ASSETS / 'music' / f'{style}.mp3'
    if not source.is_file(): raise ValueError('内置配乐缺失，请关闭 BGM 或提供本地音乐')
    target = output / 'media' / source.name
    shutil.copyfile(source, target)
    return 'media/' + target.name

def share_image(photos, data, output):
    try:
        from PIL import Image, ImageOps
    except ImportError: return ''
    colors = {'redwhite': ('#f7edd9', '#86131b'), 'floral': ('#f7eedf', '#921e32'), 'gold': ('#4b0c1a', '#d7aa63')}
    bg, ink = colors[data['style']]
    canvas = Image.new('RGB', (1200, 630), bg)
    if photos:
        source = output / photos[data['cover_index']]['src']
        with Image.open(source) as image:
            fitted = ImageOps.contain(image.convert('RGB'), (1160, 590))
            canvas.paste(fitted, ((1200-fitted.width)//2, (630-fitted.height)//2))
    else:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((30, 30, 1170, 600), outline=ink, width=3)
        draw.ellipse((440, 155, 760, 475), outline=ink, width=5)
        draw.ellipse((465, 180, 735, 450), outline=ink, width=2)
    canvas.save(output / 'media' / 'share-cover.jpg', quality=88, optimize=True)
    return 'media/share-cover.jpg'
