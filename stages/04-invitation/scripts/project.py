#!/usr/bin/env python3
"""Keep invitation revisions outside the public output directory."""
import argparse
import copy
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from config import read_config, normalize, absolute_config, source_path, merge_patch, missing

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.invitation-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

def load(path):
    p = json.loads(path.read_text(encoding='utf-8'))
    if p.get('project_format') != 1: raise ValueError('请先用 init 创建项目文件')
    normalize(p['config'])
    return p

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--config', type=Path, required=True); init.add_argument('--project', type=Path, required=True)
    edit = sub.add_parser('update'); edit.add_argument('--project', type=Path, required=True); edit.add_argument('--patch', type=Path, required=True); edit.add_argument('--note', default='更新资料'); edit.add_argument('--expected-revision', type=int, required=True)
    restore = sub.add_parser('restore'); restore.add_argument('--project', type=Path, required=True); restore.add_argument('--revision', type=int, required=True); restore.add_argument('--expected-revision', type=int, required=True)
    status = sub.add_parser('status'); status.add_argument('--project', type=Path, required=True)
    publication = sub.add_parser('record-publication'); publication.add_argument('--project',type=Path,required=True); publication.add_argument('--report',type=Path,required=True); publication.add_argument('--out',type=Path,required=True); publication.add_argument('--expected-revision',type=int,required=True)
    a = parser.parse_args()
    if a.command == 'init':
        if a.project.exists(): raise ValueError('项目已存在，请使用 update 或选择新路径')
        p = dict(project_format=1, project_id=str(uuid.uuid4()), revision=1,
                 config=absolute_config(read_config(a.config), a.config.resolve()), history=[], publication={})
    else:
        p = load(a.project)
        if a.command == 'status':
            print(json.dumps(dict(project_id=p['project_id'], revision=p['revision'], missing=missing(p['config']), style=p['config']['style'], photos=len(p['config']['photos']), publication=p.get('publication', {})), ensure_ascii=False)); return
        if p['revision'] != a.expected_revision: raise ValueError('项目已变化，请重新读取当前版本后再修改')
        if a.command == 'record-publication':
            import hashlib
            report=json.loads(a.report.read_text(encoding='utf-8'))
            digest=hashlib.sha256((a.out/'index.html').read_bytes()).hexdigest()
            if report.get('online')!='passed' or not report.get('url') or report.get('index_sha256')!=digest:
                raise ValueError('请先检查当前线上版本，报告必须与当前发布目录一致')
            config_digest=hashlib.sha256(json.dumps(p['config'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            if report.get('config_sha256') != config_digest or report.get('styles') != [p['config']['style']]:
                raise ValueError('发布版本与当前项目配置不一致，请重建并更新线上版本')
            p['publication']=dict(url=report['url'],revision=p['revision'],index_sha256=digest,checked_at=datetime.now(timezone.utc).isoformat(),needs_update=False,browser=report['browser'],wechat=report['wechat'])
            write(a.project,p); print(json.dumps(p['publication'],ensure_ascii=False)); return
        if a.command == 'restore':
            entry = next((x for x in p['history'] if x['revision'] == a.revision), None)
            if entry is None: raise ValueError('未找到指定历史版本')
            updated = copy.deepcopy(entry['config']); note = f'恢复到版本{a.revision}'
        else:
            patch = json.loads(a.patch.read_text(encoding='utf-8'))
            if not isinstance(patch, dict): raise ValueError('patch 必须是 JSON 对象')
            if 'photos' in patch:
                for i, item in enumerate(patch['photos']):
                    if isinstance(item, str): patch['photos'][i] = str(source_path(item, a.patch.resolve()))
                    elif isinstance(item, dict) and item.get('path'): item['path'] = str(source_path(item['path'], a.patch.resolve()))
            if patch.get('music'): patch['music'] = str(source_path(patch['music'], a.patch.resolve()))
            updated = normalize(merge_patch(p['config'], patch)); note = a.note
        p['history'].append(dict(revision=p['revision'], config=copy.deepcopy(p['config']), note=note, changed_at=datetime.now(timezone.utc).isoformat()))
        p['config'] = updated; p['revision'] += 1
        if p.get('publication'): p['publication']['needs_update'] = True
    write(a.project, p)
    print(json.dumps(dict(project=str(a.project.resolve()), revision=p['revision'], missing=missing(p['config'])), ensure_ascii=False))

if __name__ == '__main__':
    try: main()
    except (ValueError, KeyError, OSError, TypeError) as e: raise SystemExit(str(e))
