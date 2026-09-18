# -*- coding: utf-8 -*-
import io

OLD = r'E:\龙虾AI主控中心\Obsidian\wiki\我的AI分身'
NEW = r'G:\龙虾AI主控中心\Obsidian\wiki\我的AI分身'

files = [
    r'E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\我的AI分身\AI分身实体\auto_learn_tangxiaolong.py',
    r'E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\我的AI分身\AI分身实体\evolve_tangxiaolong.py',
]

for p in files:
    s = io.open(p, 'r', encoding='utf-8').read()
    n = s.count(OLD)
    if n:
        io.open(p, 'w', encoding='utf-8').write(s.replace(OLD, NEW))
        print('已改 %d 处 -> %s' % (n, p.split('\\')[-1]))
    else:
        print('无匹配 -> %s' % p.split('\\')[-1])
print('done')
