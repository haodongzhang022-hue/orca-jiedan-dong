---
course: "{{ course_name }}"
category: "{{ category }}"
extract_status: "extracted"
source_type: "{{ source_type }}"
updated: "{{ date }}"
tags: {{ tags_json }}
---

# {{ course_name }} · 课程大纲

## 一、课程概述
- **来源**: {{ source_path }}
- **类型**: {{ source_type }}
- **总时长**: {{ duration }} / **文件数**: {{ file_count }}
- **萃取日期**: {{ date }}

## 二、目录结构
{{ tree }}

## 三、章节大纲
{{ outline }}

## 四、核心知识点
{{ key_points }}

## 五、行动清单
{{ action_items }}

> 本大纲由 `knowledge_extraction_from_cloud_drive` 技能自动生成，请结合实际课程校准。
