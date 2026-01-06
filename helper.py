import html
from typing import List
from base import CheckItem
from util import safe_int
def merge_spans(
    items: List[CheckItem],
    text: str,
    *,
    merge_if_adjacent: bool = True,  # 相邻也合并（end==start）
    require_same_type: bool = True,  # 只合并同 type
    require_same_decision: bool = True,  # 只合并同 decision
) -> List[CheckItem]:
    """
    合并重叠/相邻 spans。合并后会：
    - start/end 取并集
    - before_check 重新取 text[start:end]（更靠谱）
    - after_check / errormsg / note：优先保留“非空”的（简单策略）
    """
    if not items:
        return items

    # 先 normalize + 排序
    norm = normalize_items(items, len(text))
    norm.sort(key=lambda x: (x.start_position, x.end_position))

    def can_merge(a: CheckItem, b: CheckItem) -> bool:
        if require_same_type and (a.type or "") != (b.type or ""):
            return False
        if require_same_decision and (a.decision or "") != (b.decision or ""):
            return False

        # overlap or adjacent
        if merge_if_adjacent:
            return b.start_position <= a.end_position
        else:
            return b.start_position < a.end_position  # 只重叠才合并

    def pick_nonempty(x: str, y: str) -> str:
        x = x or ""
        y = y or ""
        return x if x.strip() else y

    merged: List[CheckItem] = []
    cur = norm[0]

    for nxt in norm[1:]:
        if can_merge(cur, nxt):
            # 合并区间
            new_s = min(cur.start_position, nxt.start_position)
            new_e = max(cur.end_position, nxt.end_position)

            cur.start_position = new_s
            cur.end_position = new_e

            # 合并字段：保留非空优先（你也可以改成拼接）
            cur.after_check = pick_nonempty(cur.after_check, nxt.after_check)
            cur.errormsg = pick_nonempty(cur.errormsg, nxt.errormsg)
            cur.note = pick_nonempty(cur.note, nxt.note)

            # before_check 统一用原文切片更可靠
            cur.before_check = text[new_s:new_e]
        else:
            merged.append(cur)
            cur = nxt

    merged.append(cur)
    return merged

# =========================
# Rendering highlights
# =========================
TYPE_STYLE = {
    "可疑错字": ("#fff3cd", "#7a4a00"),   # bg, text
    "语义优化": ("#d1ecf1", "#0c5460"),
    "其他": ("#e2e3e5", "#383d41"),
}

def normalize_items(items: List[CheckItem], text_len: int) -> List[CheckItem]:
    # clip & sort
    out = []
    for it in items:
        s = max(0, min(text_len, safe_int(it.start_position)))
        e = max(0, min(text_len, safe_int(it.end_position)))
        if e < s:
            s, e = e, s
        it.start_position, it.end_position = s, e
        out.append(it)
    out.sort(key=lambda x: (x.start_position, x.end_position))
    return out

def render_highlight_html(text: str, items: List[CheckItem]) -> str:
    n = len(text)
    items = normalize_items(items, n)

    segments = []
    cur = 0
    covered_until = 0

    for k, it in enumerate(items):   # ⭐这里拿到 k
        s, e = it.start_position, it.end_position
        if e <= s:
            continue
        if s < covered_until:
            s = max(s, covered_until)
            if e <= s:
                continue

        if cur < s:
            segments.append(("plain", text[cur:s], None))

        t = it.type if it.type in TYPE_STYLE else "其他"
        bg, fg = TYPE_STYLE[t]
        tip = (
            f"type: {it.type}\n"
            f"before: {it.before_check}\n"
            f"after:  {it.after_check}\n"
            f"range:  [{it.start_position}, {it.end_position})\n"
            f"decision: {it.decision}\n"
            f"msg: {it.errormsg}"
        )
        span_text = text[s:e]

        # meta 里把 k 带进去
        segments.append(("mark", span_text, (bg, fg, tip, it.decision, k)))

        cur = e
        covered_until = max(covered_until, e)

    if cur < n:
        segments.append(("plain", text[cur:], None))

    out = []
    out.append("<div style='line-height:1.9; font-size:16px; white-space:pre-wrap; word-break:break-word;'>")

    for kind, seg, meta in segments:
        esc = html.escape(seg)
        if kind == "plain":
            out.append(esc)
        else:
            bg, fg, tip, decision, k = meta
            border = "2px solid #28a745" if decision == "accept" else ("2px solid #dc3545" if decision == "reject" else "1px dashed #666")

            out.append(
                f"<span class='hl-span' data-k='{k}' title='{html.escape(tip)}' "
                f"style='cursor:pointer; background:{bg}; color:{fg}; border:{border}; padding:1px 2px; border-radius:6px;'>"
                f"{esc}</span>"
            )

    out.append("</div>")
    return "".join(out)


def apply_one_edit(text: str, it: CheckItem) -> str:
    """
    Apply accepted suggestion to text:
    - replace [s:e) with after_check (can be empty => deletion)
    Note: this changes subsequent indices; for MVP we apply in reverse order later.
    """
    s, e = it.start_position, it.end_position
    return text[:s] + (it.after_check or "") + text[e:]

