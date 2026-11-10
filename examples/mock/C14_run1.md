# Trace：C14

**MOCK 运行**：脚本化 Mock 模型，只验证流程，不代表真实模型的决策效果。

- question：客户在系统里导不出报表数据，提示超时报错，这个该怎么处理或者联系谁解决？
- data_dir：data/docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "报表 导出 超时", "top_k": 5} | 检索报表导出问题 | 命中 4 条：D09/P2(3.617)，D09/P1(3.568)，D09/P4(3.405)，D09/P3(3.105) | search_docs |
| 2 | search_docs | {"query": "系统 导出失败 报错", "top_k": 5} | 结果不相关，换说法再检索 | 命中 5 条：D09/P3(6.393)，D09/P2(3.617)，D09/P1(3.568)，D09/P4(3.405)，D03/P3(1.953) | finish |
| 3 | finish | {"status": "out_of_scope", "answer": "资料库中没有关于报表导出超时的处理说明；D09 是剪影Pro 视频导出，不适用。", "gaps": ["缺少报表系统的故障处理文档或支持联系人"], "citations": []} | 两次检索结果均不相关 | 校验通过，结束 | 结束（out_of_scope） |

## 结果

- status：`out_of_scope`
- reason：`finish_called`
- steps_used：3
- answer：资料库中没有关于报表导出超时的处理说明；D09 是剪影Pro 视频导出，不适用。
- citations：
  - （无）
- gaps：
  - 缺少报表系统的故障处理文档或支持联系人
