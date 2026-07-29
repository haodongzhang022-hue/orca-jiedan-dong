---
name: 5WorkBody舰队编排
description: 企业接单群多智能体舰队编排标准流程。5台WorkBody自检+双流水线(A分布式/B直驱)贯通+图生视频本地免费渲染+Claude四项硬校验+群监听兜底+自动打包交付。触发词：舰队编排、WorkBody调度、双流水线、图生视频接单。
version: 1.0
agent_created: true
---

# 5WorkBody舰队编排技能

## 一键执行序列（龙虾五步法V2.7）

```bash
cd "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
PY="C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe"

# Step1 舰队自检（PASS才继续）
PYTHONDONTWRITEBYTECODE=1 $PY scripts/workbody_fleet_check.py

# Step2 双流水线贯通+视频渲染（本地免费，零积分）
PYTHONDONTWRITEBYTECODE=1 $PY scripts/pipeline_ab_video_test.py

# Step4 群监听（--once单轮 / 无参常驻）+ 自动打包
PYTHONDONTWRITEBYTECODE=1 $PY scripts/wework_group_listener.py --once
PYTHONDONTWRITEBYTECODE=1 $PY scripts/delivery_packager.py <order_id> --quote <金额>
```

## 图生视频关键帧法（无FAL_KEY免费路径）

1. ImageGen生成3张同场景关键帧（KF1合照首尾帧/KF2跑出/KF3停留），**每张prompt开头必须差异化**，否则同秒生成会重名互相覆盖（已踩坑）
2. imageio+libx264时序合成：hold+smoothstep交叉渐变，首尾用同一帧保证「首尾帧统一」校验0误差
3. Claude审核阈值：首尾帧均值差≤2.0 / 时长≤12s / 背景漂移≤60 / 宽≥1280

## 已踩坑

- ImageGen同批次同前缀prompt→文件名冲突覆盖，务必差异化开头
- Windows write_text换行转义→MD5校验必须以落盘字节(read_bytes)为准
- E盘受管仓库：bash mkdir/.git写被沙箱拒，Write工具可写；Python必须PYTHONDONTWRITEBYTECODE=1
- 产出一律落 G:/WorkBuddy-Cache/企业微信群定制接单项目

## 关联

- 配置基线：config/图生视频业务配置快照_v1.0.json
- 全域模板条目：docs/全域模板_企业接单群舰队编排流程.md（#291待本机粘贴）
- 上游技能：FAL-free图像生成适配器（skills/）
