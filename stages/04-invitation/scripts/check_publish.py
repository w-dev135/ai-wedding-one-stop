#!/usr/bin/env python3
"""Check local resources and, only when requested, exact deployed bytes."""
import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from config import link

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.resources=set(); self.ids=set(); self.meta={}
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if 'id' in d: self.ids.add(d['id'])
        if tag in ('img','audio','script') and d.get('src'): self.resources.add(d['src'])
        if tag=='meta' and d.get('property'): self.meta[d['property']]=d.get('content','')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--url',help='仅在已发布且用户选择的地址上执行网络检查')
    parser.add_argument('--report',type=Path)
    parser.add_argument('--allow-demo',action='store_true')
    a=parser.parse_args(); root=a.out.resolve(); errors=[]; warnings=[]; online=[]
    manifest=json.loads((root/'build-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('mode')!='final': errors.append('正式分享需要 --mode final 输出')
    if (manifest.get('demo') or manifest.get('pending')) and not a.allow_demo: errors.append('演示或待补充资料不能作为正式请柬发布')
    main_page=root/'index.html'; raw=main_page.read_bytes(); page=Page(); page.feed(raw.decode('utf-8'))
    if not {'mainTitle','event','shareBtn'}.issubset(page.ids): errors.append('关键内容或分享入口缺失')
    for p in root.rglob('*'):
        if p.is_symlink(): errors.append('发布目录包含符号链接')
        if p.is_file() and (p.name in ('project.json','config.json','patch.json') or p.suffix in ('.py','.zip') or '.git' in p.parts):
            errors.append(f'发布目录含项目资料或源文件: {p.name}')
    resources=[]
    for key in ('share_cover',):
        if manifest.get(key): page.resources.add(manifest[key])
    if manifest.get('qr'): page.resources.add('media/link-qr.png')
    for value in page.resources:
        if urlparse(value).scheme: errors.append('页面依赖外部资源，须逐项核对'); continue
        p=(root/value).resolve()
        if root not in p.parents or not p.is_file(): errors.append(f'资源缺失或越界: {value}')
        else: resources.append((value,p))
    for key in ('og:title','og:description'):
        if not page.meta.get(key): errors.append(f'缺少分享信息: {key}')
    warnings.extend(manifest.get('warnings',[]))
    if not page.meta.get('og:image'): warnings.append('未配置绝对分享封面 URL；微信卡片效果待实机验证')
    if a.url:
        link(a.url,'url')
        for name,path in [('index.html',main_page),*resources]:
            url=a.url if name=='index.html' else urljoin(a.url,name)
            try:
                with urlopen(Request(url,headers={'User-Agent':'WeddingInvitationCheck/2'}),timeout=15) as response:
                    content=response.read(path.stat().st_size+1)
                    match=hashlib.sha256(content).digest()==hashlib.sha256(path.read_bytes()).digest()
                    if not match: errors.append(f'线上资源与当前版本不一致，可能被登录页或旧缓存替代: {name}')
                    online.append(dict(resource=name,status=response.status,bytes_match=match))
            except Exception as e:
                errors.append(f'线上资源检查失败: {name} ({type(e).__name__})')
    report=dict(url=a.url, config_sha256=manifest.get('config_sha256'), styles=manifest.get('styles'), index_sha256=hashlib.sha256(raw).hexdigest(), static='passed' if not errors else 'failed',
                online=('passed' if not errors else 'failed') if a.url else 'not_run',
                browser='pending',wechat='pending',resources=len(resources),online_resources=online,
                errors=errors,warnings=warnings)
    if a.report:
        if root in a.report.resolve().parents: raise ValueError('检查报告请放在发布目录外')
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError) as e: raise SystemExit(str(e))
