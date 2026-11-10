"""ReAct 循环：模型选择动作 → 执行工具 → 观察结果 → 模型决定下一步或调用 finish 结束。

步数计算：每次工具调用算 1 步；被拒绝的 finish 和没有调用工具的纯文本回复也各算 1 步。
达到 max_steps 仍未结束时返回 status=incomplete, reason=max_steps_reached。

两类失败的处理不同：
- 工具失败（检索/读取报错）：错误作为 observation 交给模型，由模型决定重试、换工具或结束。
- 模型调用失败（网络、限流等）：模型无法决策；llm.py 在 API 层对临时错误重试 1 次，
  仍失败时这里返回 status=failed, reason=llm_error。
"""
import json

from .tools import TOOL_SCHEMAS, ToolRunner, error

DEFAULT_MAX_STEPS = 10

SYSTEM_PROMPT = """你是企业知识问答助手，帮助员工查找公司制度和产品问题的可靠答案。你只能依据工具返回的文档内容回答，不得用常识或猜测补充规则。

工作方式：每一步调用一个工具，并在 reason 参数里用一句话说明这样做的依据。可用动作：search_docs（检索）、read_doc（读取原文）、ask_user（追问或请用户确认）、finish（结束并输出结果）。

规则：
1. 先用 search_docs 检索。结果不相关或不足时，换同义说法、拆分问题或补充关键词再检索。
2. 回答前必须用 read_doc 读取要引用的段落。citations 中的 quote 必须从 read_doc 返回的原文逐字复制，每条至少 8 个字，并写明 doc_id 和 paragraph_id。
3. 检索命中不等于能回答：先确认原文确实包含回答所需的信息；原文没有写的内容不要推断。
4. 冲突处理：如果多份文档对同一问题说法不同，必须读取这些文档全文，查找适用范围、优先级或替代/废止说明。
   - 文档明确写了适用范围、优先级或替代关系：据此回答，并引用那条说明。
   - 没有写：不得自行选择其一，也不得仅因版本日期较新就认定优先适用。列出各文档的说法（含版本日期）和引用，请用户确认适用哪份制度。
5. 资料库中找不到依据时，以 out_of_scope 结束，在 gaps 中说明缺少什么资料。只能回答一部分时，回答有依据的部分，并在 gaps 中写明缺口。
6. 问题指代不清、无法确定要查什么时，用 ask_user 追问。
7. 工具返回错误时，可以换参数重试或换用其他工具；仍无法获取资料时以 failed 结束，并在 gaps 中说明原因。
8. 最后必须调用 finish。status 取值：
   answered（有依据地回答）、conflict_need_confirmation（资料冲突需用户确认，至少引用 2 份不同文档）、
   need_clarification（需要用户澄清问题）、out_of_scope（资料库中没有依据）、failed（工具故障等原因无法完成）。
   answer 中写清结论，并注明依据的文档 ID 和版本日期。"""

NO_TOOL_REMINDER = "[系统提示] 你没有调用任何工具。请通过工具行动；要结束本轮必须调用 finish 并给出结构化结果。"


def _result(status: str, reason: str, steps: int, gaps: list[str], answer: str = "") -> dict:
    return {"status": status, "answer": answer, "citations": [], "gaps": gaps, "reason": reason, "steps_used": steps}


def run_agent(question: str, llm, runner: ToolRunner, history: list[dict] | None = None,
              max_steps: int = DEFAULT_MAX_STEPS, tracer=None) -> dict:
    """history：此前的对话，[{"role": "user"|"assistant", "content": str}]。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *(history or []), {"role": "user", "content": question}]
    step = 0
    while step < max_steps:
        try:
            reply = llm.chat(messages, TOOL_SCHEMAS)
        except Exception as e:  # 模型不可用：明确返回失败，不伪造答案
            return _result("failed", "llm_error", step, [f"模型调用失败：{type(e).__name__}: {e}"])

        calls = reply["tool_calls"]
        if not calls:
            step += 1
            messages += [{"role": "assistant", "content": reply["content"] or ""},
                         {"role": "user", "content": NO_TOOL_REMINDER}]
            if tracer:
                tracer.add(step, None, {}, "", {"notice": "模型未调用工具，已提醒必须调用 finish"}, text=reply["content"])
            continue

        messages.append({"role": "assistant", "content": reply["content"],
                         "tool_calls": [{"id": c["id"], "type": "function",
                                         "function": {"name": c["name"], "arguments": c["arguments"]}} for c in calls]})
        for call in calls:
            if step >= max_steps:
                break
            step += 1
            try:
                args = json.loads(call["arguments"] or "{}")
                if not isinstance(args, dict):
                    raise ValueError
            except ValueError:
                args, reason = {}, ""
                observation, final = error("invalid_arguments", "工具参数不是合法的 JSON 对象"), None
            else:
                reason = str(args.pop("reason", ""))
                observation, final = runner.call(call["name"], args)
            if tracer:
                tracer.add(step, call["name"], args, reason, observation)
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(observation, ensure_ascii=False)})
            if final:
                return {**final, "reason": "finish_called", "steps_used": step}

    return _result("incomplete", "max_steps_reached", step, [f"达到最大步数 {max_steps} 仍未完成"])
