"""ReAct 循环：模型选择动作 → 执行工具 → 观察结果 → 模型决定下一步或调用 finish 结束。

步数计算：每次工具调用算 1 步；被拒绝的 finish 和没有调用工具的纯文本回复也各算 1 步。
达到 max_steps 仍未结束时返回 status=incomplete, reason=max_steps_reached。

循环防护（只提供信息，不替模型决策）：
- 每次 observation 附上"剩余步数"。
- 与之前完全相同的调用（工具名和参数都相同，不含 reason）照常执行，并在 observation 中注明
  "与第 N 步调用相同"；结果也相同时注明"结果未变"。

两类失败的处理不同：
- 工具失败（检索/读取报错）：错误作为 observation 交给模型，由模型决定重试、换工具或结束。
- 模型调用失败（网络、限流等）：模型无法决策；llm.py 在 API 层对临时错误重试 1 次，
  仍失败时这里返回 status=failed, reason=llm_error。
"""
import json

from .tools import TOOL_SCHEMAS, ToolRunner, error

DEFAULT_MAX_STEPS = 10

SYSTEM_PROMPT = """你是企业知识问答助手，帮助员工查找公司制度和产品问题的可靠答案。你只能依据工具返回的文档内容回答，不得用常识或猜测补充规则。

工作方式：每一步调用一个工具，并在 reason 参数里用一句话说明这样做的依据。可用动作：search_docs（检索）、read_doc（读取文档全文）、ask_user（追问或请用户确认）、finish（结束并输出结果）。每次工具返回都附有"剩余步数"，请在步数用完前调用 finish。

基本流程：
1. 先用 search_docs 检索。结果不相关或不足时，换同义说法、拆分问题或补充关键词再检索；不要重复完全相同的调用。
2. 回答前用 read_doc 读取要引用的文档。citations 中的 quote 必须从 read_doc 返回的原文逐字复制，每条至少 8 个字，并写明 doc_id 和 paragraph_id。
3. 检索命中不等于能回答：先确认原文确实包含回答所需的信息；原文没有写的内容不要推断。
4. 单一文档能直接回答的问题，读完原文即可回答，不要额外查找适用范围，也不要反复读取同一文档。

冲突核对（只有当多份文档对同一问题给出不同结论时才执行）：
a. 逐份查看这些文档原文中的适用范围、优先级、替代或废止说明。
b. 判断属于以下哪一种：
   - 范围分工：各文档原文写明适用于不同情形（例如一份是通用规定，另一份写明只适用于某类费用并优先适用）。按情形回答，并引用写明适用范围或优先关系的那段原文。
   - 已被替代：某文档原文写明替代或废止另一份。以仍有效的文档回答，并引用写明替代或废止的那段原文。
   - 真冲突：适用范围相同或未写明，且原文没有优先、替代或废止说明。以 conflict_need_confirmation 结束：列出各文档的不同说法（含文档 ID、版本日期）和引用，请用户确认适用哪份制度。
c. 版本日期更新不代表优先适用，除非文档原文写明替代或优先关系。
d. 不得只采用其中一份文档而忽略另一份的不同说法；不得把互相矛盾的规定并列作为答案（status=answered）。

资料外与追问：
- 只有问题本身指代不清、无法确定要查什么时，才用 ask_user 追问。
- 问题清楚但文档内容不覆盖（例如文档讲的是其他产品或功能，或没有相关规定），以 out_of_scope 结束，在 gaps 中写明缺少什么资料。能回答一部分时，只回答有依据的部分，并在 gaps 中写明缺口。
- answer 中每个事实性陈述都必须有引用支持；out_of_scope 时不提供文档以外的建议。

工具失败：
- 工具返回错误时，可以换参数重试或换用其他工具。同一工具连续失败 2 次后，改用其他方式，或以 failed 结束并在 gaps 中说明缺口；不要重复相同的调用。

结束：最后必须调用 finish。status 取值：
answered（有依据地回答）、conflict_need_confirmation（真冲突需用户确认，至少引用 2 份不同文档）、need_clarification（问题指代不清，需用户澄清）、out_of_scope（资料库中没有依据）、failed（工具故障等原因无法完成）。
answer 中写清结论，并注明依据的文档 ID 和版本日期。

finish 的 conflict_check（必填，会被程序校验）：
- claims：本次用 read_doc 读过的每一份文档都要列出：doc_id；claim 写该文档对本问题的结论（与本问题无关时写“与问题无关”）；scope_quote 写该文档声明适用范围的原文（逐字复制），没有则写“未说明”。
- relations：claims 中 claim 不是“与问题无关”的文档，两两各写一条关系：docs（两个文档 ID）、type、basis。
  type 取值：consistent（结论一致）、scope_split（范围分工）、superseded（已被替代或废止）、priority（原文写明优先适用）、true_conflict（真冲突）。
  scope_split / superseded / priority 必须给出 basis：说明依据的那段原文（doc_id、paragraph_id、逐字 quote），且来自这两份文档之一；scope_split 时两份文档的 scope_quote 不能都是“未说明”。consistent / true_conflict 的 basis 可为 null。
- 两份文档结论不同、又找不到写明范围、优先或替代关系的原文时，type 只能是 true_conflict；存在 true_conflict 时 status 必须是 conflict_need_confirmation。
- 没有读过任何文档时，claims 和 relations 都为空列表。"""

NO_TOOL_REMINDER = "[系统提示] 你没有调用任何工具。请通过工具行动；要结束本轮必须调用 finish 并给出结构化结果。"


def _result(status: str, reason: str, steps: int, gaps: list[str], answer: str = "") -> dict:
    return {"status": status, "answer": answer, "citations": [], "gaps": gaps, "conflict_check": None,
            "reason": reason, "steps_used": steps}


def run_agent(question: str, llm, runner: ToolRunner, history: list[dict] | None = None,
              max_steps: int = DEFAULT_MAX_STEPS, tracer=None) -> dict:
    """history：此前的对话，[{"role": "user"|"assistant", "content": str}]。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *(history or []), {"role": "user", "content": question}]
    seen: dict[str, tuple[int, dict]] = {}  # 调用签名 -> (首次出现的步数, 当时的结果)
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
                         {"role": "user", "content": f"{NO_TOOL_REMINDER}剩余步数：{max_steps - step}"}]
            if tracer:
                tracer.add(step, None, {}, "", {"notice": "模型未调用工具，已提醒必须调用 finish",
                                                "剩余步数": max_steps - step}, text=reply["content"])
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

            observation = dict(observation)
            signature = call["name"] + json.dumps(args, sort_keys=True, ensure_ascii=False)
            if signature in seen:
                first_step, first_obs = seen[signature]
                same = "，结果未变" if first_obs == observation else ""
                observation["重复调用"] = f"与第 {first_step} 步调用相同{same}"
            else:
                seen[signature] = (step, dict(observation))
            observation["剩余步数"] = max_steps - step

            if tracer:
                tracer.add(step, call["name"], args, reason, observation)
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(observation, ensure_ascii=False)})
            if final:
                return {**final, "reason": "finish_called", "steps_used": step}

    return _result("incomplete", "max_steps_reached", step, [f"达到最大步数 {max_steps} 仍未完成"])
