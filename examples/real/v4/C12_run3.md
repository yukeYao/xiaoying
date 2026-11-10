# Trace：C12

**真实模型运行**：`gpt-4o-mini`

- question：报销期限多久？
- data_dir：data/docs
- max_steps：2

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "报销期限", "top_k": 5} | 查找公司关于报销期限的相关规定。 | 命中 5 条：D02/P2(6.191)，D01/P3(5.499)，D05/P3(4.962)，D05/P2(3.708)，D01/P2(3.097) | read_doc |
| 2 | read_doc | {"doc_id": "D02"} | 读取员工费用报销操作指引以确认报销期限。 | D02《员工费用报销操作指引》版本 2024-06-15，全文 P1,P2,P3,P4 | 结束（incomplete） |

## 结果

- status：`incomplete`
- reason：`max_steps_reached`
- steps_used：2
- answer：
- citations：
  - （无）
- gaps：
  - 达到最大步数 2 仍未完成
