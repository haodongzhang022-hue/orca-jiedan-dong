# -*- coding: utf-8 -*-
import io

OLD = 'E:\\龙虾AI主控中心\\Obsidian'
NEW = 'G:\\龙虾AI主控中心\\Obsidian'

files = [
    r'E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\龙虾五步法V3.6·PR#21闭环版（成本优先置顶）SKILL.md',
    r'E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\龙虾全域官方模板-最终版.md',
    r'E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\赛博书屋（Cyber Book House）v1.5SKILL.md',
    r'E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\我的AI分身\AI分身实体\AGENTS.md',
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
