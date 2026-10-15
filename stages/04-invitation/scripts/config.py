"""Versioned, host-neutral invitation configuration. No external dependencies."""
from __future__ import annotations
import copy
import json
import math
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

STYLES = ('redwhite', 'floral', 'gold')
TEXT = ('name1', 'name2', 'date', 'welcome_time', 'ceremony_time', 'banquet_time',
        'venue', 'address', 'event_type', 'message', 'story', 'slogan', 'ending',
        'music', 'music_credit', 'map_url', 'public_url', 'share_title', 'share_description', 'primary_color')
DEFAULTS = dict(schema_version=2, demo=False, style='redwhite', event_type='婚礼',
                photos=[], cover_index=0, bgm='auto', effects='normal', opening=True,
                particles=True, photo_transition=True, music_volume=.55, music_start=0,
                music_seconds=None, sections=dict(invitation=True, album=True, address=True))

def link(value, field):
    if not value: return
    u = urlparse(value)
    if u.scheme not in ('http', 'https') or not u.netloc or u.username or u.password:
        raise ValueError(f'{field} 需要完整的 http/https 链接，且不能含账号密码')

def normalize(raw: dict) -> dict:
    if not isinstance(raw, dict): raise ValueError('配置必须是 JSON 对象')
    if type(raw.get('schema_version', 1)) is not int or raw.get('schema_version', 1) not in (1, 2): raise ValueError('配置版本不支持，请使用 schema_version=2')
    allowed = set(TEXT) | set(DEFAULTS)
    unknown = set(raw) - allowed
    if unknown: raise ValueError('不支持的字段: ' + ', '.join(sorted(unknown)))
    d = copy.deepcopy(DEFAULTS)
    d.update(copy.deepcopy(raw))
    d['schema_version'] = 2
    for key in TEXT:
        if key in d and not isinstance(d[key], str): raise ValueError(f'{key} 必须是文本')
        d[key] = d.get(key, '').strip()
    for key in ('demo', 'opening', 'particles', 'photo_transition'):
        if not isinstance(d[key], bool): raise ValueError(f'{key} 必须是 true 或 false')
    if d['date']:
        try: date.fromisoformat(d['date'])
        except ValueError as exc: raise ValueError('date 请使用 YYYY-MM-DD') from exc
    for key in ('welcome_time', 'ceremony_time', 'banquet_time'):
        if d[key] and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', d[key]):
            raise ValueError(f'{key} 请使用 24 小时 HH:MM 格式')
    for key in ('map_url', 'public_url'): link(d[key], key)
    if d['primary_color'] and not re.fullmatch(r'#[0-9a-fA-F]{6}', d['primary_color']):
        raise ValueError('primary_color 请使用 #RRGGBB')
    if d['style'] not in STYLES: raise ValueError('style 可选 redwhite / floral / gold')
    if d['effects'] not in ('off', 'subtle', 'normal', 'festive'): raise ValueError('effects 可选 off / subtle / normal / festive')
    if d['bgm'] not in ('auto', 'none', 'custom'): raise ValueError('bgm 可选 auto / none / custom')
    if d['bgm'] == 'custom' and not d['music']: raise ValueError('自定义配乐需要 music 路径')
    for key in ('music_volume', 'music_start', 'music_seconds'):
        v = d[key]
        if v is None and key == 'music_seconds': continue
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError(f'{key} 必须是有限数字')
    if not 0 <= d['music_volume'] <= 1: raise ValueError('music_volume 范围为 0 到 1')
    if d['music_start'] < 0 or (d['music_seconds'] is not None and d['music_seconds'] < 4):
        raise ValueError('音乐起点须非负，截取时长须至少4秒')
    if not isinstance(d['sections'], dict) or set(d['sections']) - set(DEFAULTS['sections']):
        raise ValueError('sections 支持 invitation / album / address')
    d['sections'] = {**DEFAULTS['sections'], **d['sections']}
    if any(not isinstance(v, bool) for v in d['sections'].values()): raise ValueError('栏目开关必须是布尔值')
    if not isinstance(d['photos'], list) or len(d['photos']) > 12: raise ValueError('photos 需要至多12项的列表')
    photos = []
    for entry in d['photos']:
        p = {'path': entry} if isinstance(entry, str) else copy.deepcopy(entry)
        if not isinstance(p, dict) or set(p) - {'path', 'caption', 'fit', 'position'}:
            raise ValueError('照片支持路径字符串，或 path / caption / fit / position 对象')
        if not isinstance(p.get('path'), str) or not p['path'].strip(): raise ValueError('每张照片需要 path')
        p.setdefault('caption', '')
        p.setdefault('fit', 'contain')
        p.setdefault('position', [50, 50])
        if not isinstance(p['caption'], str) or p['fit'] not in ('contain', 'cover'): raise ValueError('照片 caption 须为文本，fit 可选 contain / cover')
        pos = p['position']
        if not isinstance(pos, list) or len(pos) != 2 or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 100 for x in pos):
            raise ValueError('照片 position 需要两个0到100的百分比数字')
        photos.append(p)
    d['photos'] = photos
    if type(d['cover_index']) is not int or not 0 <= d['cover_index'] < max(1, len(photos)):
        raise ValueError('cover_index 从0开始，须指向现有照片')
    if not d['demo'] and missing(d): raise ValueError('缺少必填信息: ' + ', '.join(missing(d)))
    return d

def missing(d):
    fields = [k for k in ('name1', 'name2', 'date', 'venue', 'address') if not d.get(k)]
    if not d.get('ceremony_time') and not d.get('banquet_time'): fields.append('ceremony_time 或 banquet_time')
    if not d.get('photos'): fields.append('photos')
    return fields

def read_config(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(raw, dict) and raw.get('project_format') == 1:
        raw = raw['config']
    return normalize(raw)

def source_path(name: str, config: Path) -> Path:
    p = Path(name).expanduser()
    return (p if p.is_absolute() else config.parent / p).resolve()

def absolute_config(d: dict, origin: Path) -> dict:
    d = copy.deepcopy(d)
    for p in d['photos']: p['path'] = str(source_path(p['path'], origin))
    if d['music']: d['music'] = str(source_path(d['music'], origin))
    return d

def merge_patch(base, patch):
    if not isinstance(patch, dict): return copy.deepcopy(patch)
    result = copy.deepcopy(base) if isinstance(base, dict) else {}
    for k, v in patch.items(): result[k] = merge_patch(result.get(k), v)
    return result
