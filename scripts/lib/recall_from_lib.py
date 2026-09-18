"""前端 fetch 的入口：按 lib_id 返回该子库最近历史案例（list）"""
import sys, json
from pathlib import Path
from datetime import datetime
from urllib.parse import parse_qs

CONFIG = Path(__file__).parent / 'lib_config.json'
ROOT = Path(__file__).parent.parent.parent

def list_recent_cases(lib_id, limit=5):
    with open(CONFIG, encoding='utf-8') as f:
        cfg = json.load(f)
    lib = next((l for l in cfg['libraries'] if l['id'] == lib_id), None)
    if not lib:
        return {'error': f'lib_id={lib_id} not found'}
    root = Path(lib['local_path'])
    if not root.exists():
        return {'lib_id': lib_id, 'lib_name': lib['name'], 'cases': []}
    # 列出最近子目录（按 mtime 倒序）
    dirs = [d for d in root.iterdir() if d.is_dir()]
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    cases = []
    for d in dirs[:limit]:
        files = list(d.rglob('*'))
        fs = [f for f in files if f.is_file()]
        if not fs:
            continue
        sz = sum(f.stat().st_size for f in fs)
        cases.append({
            'name': d.name,
            'date': datetime.fromtimestamp(d.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
            'size': sz,
            'files': len(fs),
            'snippet': (fs[0].read_text(encoding='utf-8', errors='ignore')[:120] if fs else '')
        })
    return {'lib_id': lib_id, 'lib_name': lib['name'], 'cases': cases}

def main():
    qs = parse_qs(__import__('os').environ.get('QUERY_STRING',''))
    lib_id = (qs.get('lib') or ['wecom_jd'])[0]
    j = list_recent_cases(lib_id)
    print('Content-Type: application/json; charset=utf-8')
    print('Access-Control-Allow-Origin: *')
    print()
    print(json.dumps(j, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
