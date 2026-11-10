# Trace：C13

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：年假没休完能折现吗？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "年假 折现", "top_k": 5} | 检索年假折现规则 | 命中 4 条：D03/P4(4.837)，D03/P1(4.788)，D03/P3(4.707)，D03/P2(3.494) | read_doc |
| 2 | read_doc | {"doc_id": "D03"} | 读取 D03 全文，确认是否有折现规定 | D03《年假管理制度》版本 2024-01-01，段落 P1,P2,P3,P4 | finish |
| 3 | finish | {"status": "out_of_scope", "answer": "D03《年假管理制度》（2024-01-01）没有关于年假折现的规定，只写明未休完的年假可延至次年3月31日前休完，逾期作废。", "gaps": ["资料中没有年假折现规则"], "citations": [{"doc_id": "D03", "paragraph_id": "P2", "quote": "可延至次年3月31日前休完，逾期作废"}]} | 原文没有折现规定，不推断 | 校验通过，结束 | 结束（out_of_scope） |

## 结果

- status：`out_of_scope`
- reason：`finish_called`
- steps_used：3
- answer：D03《年假管理制度》（2024-01-01）没有关于年假折现的规定，只写明未休完的年假可延至次年3月31日前休完，逾期作废。
- citations：
  - D03/P2：「可延至次年3月31日前休完，逾期作废」
- gaps：
  - 资料中没有年假折现规则
