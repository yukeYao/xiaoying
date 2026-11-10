# Trace：C12

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：报销期限多久？
- data_dir：data/docs
- max_steps：2

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "报销期限", "top_k": 5} | 先检索报销期限 | 命中 5 条：D02/P2(6.191)，D01/P3(5.499)，D05/P3(4.962)，D05/P2(3.708)，D01/P2(3.097) | read_doc |
| 2 | read_doc | {"doc_id": "D01"} | D01 与 D02 期限不同，读取 D01 全文查找适用范围或优先级 | D01《财务报销管理办法》版本 2023-03-01，全文 P1,P2,P3,P4,P5 | 结束（incomplete） |

## 结果

- status：`incomplete`
- reason：`max_steps_reached`
- steps_used：2
- answer：
- citations：
  - （无）
- gaps：
  - 达到最大步数 2 仍未完成
