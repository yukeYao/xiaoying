# Trace：C10

**真实模型运行**：`gpt-4.1`

- question：工作满5年有几天年假？
- data_dir：data/docs
- fail_tool：search_docs
- max_steps：10

## 步骤

| step | 动作 | 参数 | 决策依据 (reason) | 返回摘要 | 下一步 |
|---|---|---|---|---|---|
| 1 | search_docs | {"query": "工作满5年 年假天数", "top_k": 5} | 需要查找公司关于工作年限与年假天数的规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 2 | search_docs | {"query": "司龄5年 年假", "top_k": 5} | 更换关键词尝试检索工作满5年对应的年假天数。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 3 | search_docs | {"query": "年假天数与工龄关系", "top_k": 5} | 尝试用不同表述检索年假天数与工龄的关系。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 4 | search_docs | {"query": "年假规定", "top_k": 5} | 尝试用更宽泛的关键词检索年假相关规定。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | search_docs |
| 5 | search_docs | {"query": "年假", "top_k": 5} | 用最基础关键词检索年假相关制度。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | read_doc |
| 6 | read_doc | {"doc_id": "D01"} | 尝试直接读取编号为D01的文档，查找年假相关规定。 | D01《财务报销管理办法》版本 2023-03-01，全文 P1,P2,P3,P4,P5 | search_docs |
| 7 | search_docs | {"query": "年假", "top_k": 5} | 直接读取D01未找到年假相关内容，需继续检索年假相关制度。 | 错误 tool_unavailable：search_docs 服务暂时不可用（注入故障），请稍后重试或换用其他方式 | read_doc |
| 8 | read_doc | {"doc_id": "D02"} | 尝试直接读取编号为D02的文档，查找年假相关规定。 | D02《员工费用报销操作指引》版本 2024-06-15，全文 P1,P2,P3,P4 | read_doc |
| 9 | read_doc | {"doc_id": "D03"} | 继续尝试读取编号为D03的文档，查找年假相关规定。 | D03《年假管理制度》版本 2024-01-01，全文 P1,P2,P3,P4 | read_doc |
| 10 | read_doc | {"doc_id": "D04"} | 为排查是否有冲突或补充，继续读取D04文档查找年假相关内容。 | D04《请假审批流程》版本 2024-02-01，全文 P1,P2,P3,P4 | 结束（incomplete） |

## 结果

- status：`incomplete`
- reason：`max_steps_reached`
- steps_used：10
- answer：
- citations：
  - （无）
- gaps：
  - 达到最大步数 10 仍未完成
