import os

root = 'G:/龙虾AI主控中心/Obsidian/wiki'
all_md = []
for dp, dn, fn in os.walk(root):
    for f in fn:
        if f.endswith('.md'):
            rel = os.path.relpath(os.path.join(dp, f), root).replace('\\', '/')
            # 跳过 .obsidian 内部
            if rel.startswith('.obsidian/'):
                continue
            all_md.append(rel)
all_md.sort()

loose = [r for r in all_md if '/' not in r]
proj = '企业微信群定制接单项目'
has_proj = any(r.startswith(proj + '/') for r in all_md)
tops = sorted({r.split('/')[0] for r in all_md if '/' in r})

print('=== wiki 全量 md 文件数:', len(all_md))
print('=== 根目录松散 md 文件(', len(loose), '):')
for r in loose:
    print('   ', r)
print('=== 是否存在', proj, '子目录:', has_proj)
print('=== 一级目录:', tops)

# 生成路径索引 markdown
out = ['# Obsidian wiki 路径索引（自动生成）', '',
       f'> 根目录：`G:/龙虾AI主控中心/Obsidian/wiki`',
       f'> 共 {len(all_md)} 个 md 文件', '',
       '## 一级目录', '']
for t in tops:
    out.append(f'- `{t}/`')
out.append('')
out.append('## 全部文件（相对路径）')
out.append('')
for r in all_md:
    out.append(f'- `{r}`')

idx_path = os.path.join(root, '00_导航_路径索引.md')
with open(idx_path, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(out) + '\n')
print('=== 已写入路径索引:', idx_path)
