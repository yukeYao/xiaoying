# Trace：C09

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：这个能报吗？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | ask_user | {"question": "请问您想报销的是哪类费用（如差旅、日常费用）？"} | 问题中的“这个”指代不清 | 非交互模式，提示模型调用 finish | finish |
| 2 | finish | {"status": "need_clarification", "answer": "您的问题“这个能报吗”没有说明具体费用，请补充是哪类费用。", "gaps": [], "citations": []} | 非交互模式，需用户澄清 | 校验通过，结束 | 结束（need_clarification） |

## 结果

- status：`need_clarification`
- reason：`finish_called`
- steps_used：2
- answer：您的问题“这个能报吗”没有说明具体费用，请补充是哪类费用。
- citations：
  - （无）
- gaps：
  - （无）
