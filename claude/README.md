# Claude 核查层 - 质量校验与合规审核

> 所属分支：`claude/reviewer`  
> 角色定位：核查层 / 质量把关

## 核心职责
- 代码审查与静态检查
- 输出结果校验与边界测试
- 合规性检查（版权、隐私、安全、商单交付标准）
- 生成审查报告与修复建议
- 最终批准合并到 `master`

## 目录说明
- `review_checks/`：代码审查清单、审查报告模板
- `validation/`：边界测试用例、准确率验证、回归测试
- `compliance/`：合规检查规则、版权/隐私/安全清单

## 协作规则
1. 从 `codex/executor` 接收待审查提交；
2. 在 `review_checks/` 输出审查报告；
3. 在 `validation/` 补充测试用例；
4. 在 `compliance/` 确认合规；
5. 通过后批准合并到 `master`。
