import json, shutil, datetime
from pathlib import Path

local = Path(r'C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Bookmarks')
backup = Path(r'C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Bookmarks.bak_20260906')
proxy = Path(r'C:\Users\Administrator\AppData\Local\Google\Chrome\ProxyProfile\Default\Bookmarks')
def load(p):
    return json.loads(p.read_text(encoding='utf-8'))
local_data = load(backup)
proxy_data = load(proxy)
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(local, local.with_name('Bookmarks.bak_before_merge_' + stamp))
seen = set()
def walk(n):
    yield n
    for c in n.get('children', []): yield from walk(c)
for n in walk(local_data['roots']['bookmark_bar']):
    if n.get('url'): seen.add(n['url'])
for n in proxy_data['roots']['bookmark_bar'].get('children', []):
    urls = [x.get('url') for x in walk(n) if x.get('url')]
    if any(u not in seen for u in urls):
        local_data['roots']['bookmark_bar']['children'].append(n)
        seen.update(urls)
local.write_text(json.dumps(local_data, ensure_ascii=False, indent=2), encoding='utf-8')
print('MERGED', local, 'bookmark_bar_nodes', sum(1 for _ in walk(local_data['roots']['bookmark_bar'])))
