---
id: "{{ card_id }}"
course: "{{ course_name }}"
topic: "{{ topic }}"
category: "{{ category }}"
tags: {{ tags_json }}
confidence: "{{ confidence }}"
source_chunk: "{{ source_chunk }}"
---

# {{ topic }} · 知识卡片

## 概念
{{ concept }}

## 为什么重要
{{ importance }}

## 如何应用
{{ application }}

## 常见误区
{{ pitfalls }}

## 关联标签
{{ tags_text }}

## 溯源
- **课程**: {{ course_name }}
- **来源文件**: {{ source_file }}
- **时间戳**: {{ timestamp }}
- **Chunk ID**: {{ card_id }}
