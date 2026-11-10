# Trace：C11

**真实模型运行**：`gpt-4o-mini`

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- fail_times：1
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假", "top_k": 5} | 需要查找关于年假的相关规定 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "年假 规定", "top_k": 5} | 需要查找关于年假的相关规定 | 命中 5 条：D03/P4(4.837)，D03/P1(4.788)，D03/P3(4.707)，D03/P2(3.494)，D07/P1(1.807) | read_doc |
| 3 | read_doc | {"doc_id": "D03", "paragraph_ids": ["P1"]} | 需要确认年假天数的具体规定 | D03《年假管理制度》版本 2024-01-01，段落 P1 | finish |
| 4 | finish | {"status": "answered", "answer": "根据《年假管理制度》，员工累计工作已满5年的，年休假为5天。", "citations": [{"doc_id": "D03", "paragraph_id": "P1", "quote": "员工累计工作已满1年不满10年的，年休假5天；"}], "gaps": []} | 根据年假管理制度确认年假天数的具体规定 | 校验通过，结束 | 结束（answered） |

## 结果

- status：`answered`
- reason：`finish_called`
- steps_used：4
- answer：根据《年假管理制度》，员工累计工作已满5年的，年休假为5天。
- citations：
  - D03/P1：「员工累计工作已满1年不满10年的，年休假5天；」
- gaps：
  - （无）
