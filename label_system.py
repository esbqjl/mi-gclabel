
import html
from dataclasses import asdict
from typing import List, Dict, Any, Tuple
import streamlit as st
from span_picker import span_picker
import os
from base import CheckItem
import util  as u
import helper as h

def persist_items_to_record(records, idx, rec, items):
                    rec["check_result"] = [asdict(it) for it in items]
                    records[idx] = rec
                    st.session_state.records = records  # 确保写回 session_state
                    save_work(st.session_state.records)

# =========================
# Streamlit App
# =========================
st.set_page_config(page_title="错别字可视化标注器", layout="wide")

st.title("错别字/语义优化 可视化标注器（基于 check_result span）")

# =========================
# Session state init (必须最靠前)
# =========================
st.session_state.setdefault("records", [])
st.session_state.setdefault("idx", 0)
st.session_state.setdefault("pending_span", None)
st.session_state.setdefault("last_picked_sig", "")
st.session_state.setdefault("auto_loaded", False)
st.session_state.setdefault("last_click_k", None)

# ===== 恢复上一次数据集选择 =====
cache = u.load_cache()

st.session_state["in_path"] = (
    st.session_state.get("in_path")
    or cache.get("in_path")
    or "input.jsonl"
)

st.session_state["out_path"] = (
    st.session_state.get("out_path")
    or cache.get("out_path")
    or "output/output.jsonl"
)


WORK_FILE_POSTFIX = ".labeler_work.jsonl"
WORK_FILE_PREFIX  = "./work/"
WORK_FILE = WORK_FILE_PREFIX + st.session_state["in_path"]+WORK_FILE_POSTFIX


def save_work(records: List[Dict[str, Any]], path: str = WORK_FILE):
    u.dump_jsonl(records, path)

def load_work_if_exists(work_path: str = WORK_FILE):
    if os.path.exists(work_path):
        return u.load_jsonl(work_path)
    return None
 
if "auto_loaded" not in st.session_state:
    st.session_state.auto_loaded = False

reset_col1, reset_col2 = st.columns([1, 5])

with reset_col1:
    if st.button("♻️ 重置当前数据集", type="secondary"):
        try:
            st.session_state.records = u.reset_work_from_input(
                st.session_state.in_path,
                WORK_FILE
            )
            st.session_state.idx = 0
            st.session_state.auto_loaded = True  # 防止后面 auto load 再覆盖
            st.success("已将工作副本重置为 input.jsonl 初始状态")
            st.rerun()
        except Exception as e:
            st.error(f"重置失败：{e}")
            
with st.sidebar:
    st.header("数据文件")

    st.session_state.in_path = st.text_input(
        "输入 JSONL 路径",
        value=st.session_state.in_path,
        key="in_path_input"
    )

    st.session_state.out_path = st.text_input(
        "输出 JSONL 路径",
        value=st.session_state.out_path,
        key="out_path_input"
    )

    # ✅ 立刻记住最近一次选择
    u.save_cache({
        "in_path": st.session_state.in_path,
        "out_path": st.session_state.out_path
    })
    st.divider()
    load_btn = st.button("加载数据", type="primary")

in_path = st.session_state.in_path
out_path = st.session_state.out_path

if "idx" not in st.session_state:
    st.session_state.idx = 0

if load_btn:
    try:
        work = load_work_if_exists(WORK_FILE)
        if work:
            st.session_state.records = work
            st.success(f"已恢复工作副本：{len(work)} 条")
        else:
            st.session_state.records = u.load_jsonl(in_path)
            st.success(f"已加载原始数据：{len(st.session_state.records)} 条")

        st.session_state.idx = 0
        st.session_state.auto_loaded = True   # 🔥 很关键：防止后面再 auto load
        st.rerun()

    except Exception as e:
        st.error(f"加载失败：{e}")

records = st.session_state.records

# ✅ 确保 session_state 里这些键都存在（放在这段之前或紧挨着也行）
if "records" not in st.session_state:
    st.session_state.records = []
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "auto_loaded" not in st.session_state:
    st.session_state.auto_loaded = False

records = st.session_state.records  # 先拿一次

# ✅ 自动加载：优先 work，其次原始 input（必须在 st.stop() 之前）
if (not records) and (not st.session_state.auto_loaded):
    st.session_state.auto_loaded = True
    try:
        work = load_work_if_exists(WORK_FILE)
        if work:
            st.session_state.records = work
            st.sidebar.success(f"已从工作副本恢复：{len(work)} 条")
        else:
            if os.path.exists(st.session_state.in_path):
                st.session_state.records = u.load_jsonl(st.session_state.in_path)
                st.sidebar.success(f"已加载原始数据：{len(st.session_state.records)} 条")
            else:
                st.sidebar.info(
                    f"未找到文件：{st.session_state.in_path}，请在左侧选择数据集"
                )
                st.session_state.records = []

        # 更新 records 引用（关键）
        records = st.session_state.records

        # idx 合法化（比如 work 条数变少时不越界）
        st.session_state.idx = min(st.session_state.idx, max(0, len(records) - 1))

    except Exception as e:
        st.sidebar.warning(f"自动加载失败：{e}（可手动点击加载）")

# ✅ 没数据就 stop（放在自动加载之后）
if not st.session_state.records:
    st.info("左侧设置 input.jsonl 路径后，点击“加载数据”。")
    st.stop()

# Current record
idx = st.session_state.idx
idx = max(0, min(len(records) - 1, idx))
st.session_state.idx = idx

rec = records[idx]
text = rec.get("corrected_sent", "")
raw_items = rec.get("check_result", [])

# Convert items to CheckItem with persisted decisions if exist
items: List[CheckItem] = []
for it in raw_items:
    # allow old annotated fields if they exist
    items.append(
        CheckItem(
            before_check=it.get("before_check", ""),
            after_check=it.get("after_check", ""),
            start_position=u.safe_int(it.get("start_position", 0)),
            end_position=u.safe_int(it.get("end_position", 0)),
            errormsg=it.get("errormsg", ""),
            type=it.get("type", ""),
            decision=it.get("decision", "pending"),
            note=it.get("note", ""),
        )
    )

# Top nav
colA, colB, colC, colD = st.columns([2, 2, 3, 3])
with colA:
    if st.button("⬅️ 上一条", disabled=(idx == 0)):
        st.session_state.idx -= 1
        st.rerun()
with colB:
    if st.button("➡️ 下一条", disabled=(idx >= len(records) - 1)):
        st.session_state.idx += 1
        st.rerun()
with colC:
    go = st.number_input("跳转到序号（0-based）", min_value=0, max_value=len(records)-1, value=idx)
    if st.button("跳转"):
        st.session_state.idx = int(go)
        st.rerun()
with colD:
    st.write(f"当前：{idx+1} / {len(records)}")

st.divider()

left, right = st.columns([1.25, 1])

with left:
    st.subheader("可视化文本（固定高亮） + 拖选取 span（稳定 offset）")

    # 你原来的 labels/valid/norm_label/annotations 可以保留（annotations 仍用于 existing_ranges）
    labels = [
        ("可疑错字", "#fff3cd"),
        ("语义优化", "#d1ecf1"),
        ("其他", "#e2e3e5"),
    ]
    valid = {x[0] for x in labels}

    def norm_label(t: str) -> str:
        t = (t or "").strip()
        return t if t in valid else "其他"

    annotations = [
        {
            "start": int(it.start_position),
            "end": int(it.end_position),
            "tag": norm_label(it.type),
            "label": norm_label(it.type),
        }
        for it in items
        if int(it.end_position) > int(it.start_position)
    ]

    st.caption(f"已加载标注: {len(annotations)} 个")

    # ✅ 固定高亮预览 HTML（不会被点掉）
    preview_html = h.render_highlight_html(text, items)

    # ✅ 用自定义组件拿选区（start/end/text），不再依赖 text_highlighter 的 result
    picked = span_picker(
        text=text,
        preview_html=preview_html,
        key=f"spanpicker_{idx}",     # idx 变化才重建
        height=220
    )

    # ✅ focus 状态（给右侧 expander 用）
    st.session_state.setdefault("focus_k", None)

    if isinstance(picked, dict) and picked.get("kind") == "click":
        k = int(picked.get("index", -1))

        # ✅ 防抖：同一个 k 不重复处理
        if st.session_state.get("last_click_k") != k:
            st.session_state.last_click_k = k
            st.session_state.focus_k = k
            st.rerun()
            
    pick_payload = None
    if isinstance(picked, dict):
        if picked.get("kind") == "pick":
            pick_payload = picked
        elif "start" in picked and "end" in picked:
            pick_payload = {"kind": "pick", **picked}

    picked_sig = ""
    if pick_payload:
        try:
            ps = int(pick_payload.get("start", -1))
            pe = int(pick_payload.get("end", -1))
            picked_sig = f"{ps}-{pe}"
        except Exception:
            picked_sig = ""

    existing_ranges = [(a["start"], a["end"]) for a in annotations]

    if "last_picked_sig" not in st.session_state:
        st.session_state.last_picked_sig = ""

    if "pending_span" not in st.session_state:
        st.session_state.pending_span = None

    # ✅ 只有 pick 才进入 pending_span 逻辑
    if (
        st.session_state.pending_span is None
        and pick_payload
        and picked_sig
        and picked_sig != st.session_state.last_picked_sig
    ):
        s = int(pick_payload.get("start", -1))
        e = int(pick_payload.get("end", -1))
        ttxt = pick_payload.get("text") or text[s:e]

        def same_range(s, e, ranges):
            return any(s == a and e == b for a, b in ranges)

        if e > s and not same_range(s, e, existing_ranges):
            st.session_state.pending_span = {
                "start": s,
                "end": e,
                "text": ttxt,
                "suggest_type": "可疑错字",
            }
            st.session_state.last_picked_sig = picked_sig

    st.caption("边框含义：绿色=已接受，红色=已拒绝，灰色虚线=未决。")

    # 下面 pending span UI 你原封不动保留即可
    pending_box = st.empty()
    pending = st.session_state.get("pending_span")
    if pending:
        default_type = pending.get("suggest_type", "可疑错字")
        pend_type = st.selectbox(
            "type",
            ["可疑错字", "语义优化", "其他"],
            index=["可疑错字","语义优化","其他"].index(default_type) if default_type in ["可疑错字","语义优化","其他"] else 0,
            key=f"pend_type_{idx}"
        )
        pend_after = st.text_input("after_check（可选；空=删除）", value="", key=f"pend_after_{idx}")
        pend_msg = st.text_input("errormsg（可选）", value="", key=f"pend_msg_{idx}")
        pend_before = st.text_input("before_check（可选）", value=pending["text"], key=f"pend_before_{idx}")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("✅ 添加为标注", key=f"pend_add_{idx}", use_container_width=True):
                items.append(CheckItem(
                    before_check=pend_before,
                    after_check=pend_after,
                    start_position=int(pending["start"]),
                    end_position=int(pending["end"]),
                    errormsg=pend_msg,
                    type=pend_type,
                    decision="pending",
                    note=""
                ))

                items = h.merge_spans(items, text, require_same_type=True, require_same_decision=True)

                # ✅ 写回 record & 落盘（必须在 rerun 前）
                rec["check_result"] = [asdict(x) for x in items]
                records[idx] = rec
                st.session_state.records = records
                save_work(st.session_state.records, WORK_FILE)

                # ✅ 清 pending + 需要的话重建（这里可以重建一次，因为 annotations 变了）
                st.session_state.pending_span = None

                if picked_sig:
                    st.session_state.last_picked_sig = picked_sig
                st.rerun()

        with b2:
            if st.button("❎ 取消选区", key=f"pend_cancel_{idx}", use_container_width=True):
                # 用 pending 自己的范围做 sig，确保一定能挡住“同一个 picked 再弹”
                s = int(st.session_state.pending_span["start"])
                e = int(st.session_state.pending_span["end"])
                st.session_state.last_picked_sig = f"{s}-{e}"

                st.session_state.pending_span = None
                pending_box.empty()   # 如果你用了 st.empty() 容器
                st.rerun() 
with right:
    st.subheader("Span 列表与标注")

    del_k = st.session_state.pop("delete_k", None)
    if del_k is not None:
        if 0 <= del_k < len(items):
            items.pop(del_k)
            rec["check_result"] = [asdict(x) for x in items]
            records[idx] = rec
            st.session_state.records = records
            save_work(st.session_state.records, WORK_FILE)

            st.toast("已删除该标注")
            st.rerun()

    # show overlaps warning
    norm = h.normalize_items(items, len(text))
    overlaps = []
    last_end = -1
    for it0 in norm:
        if it0.start_position < last_end:
            overlaps.append((it0.start_position, it0.end_position))
        last_end = max(last_end, it0.end_position)
    if overlaps:
        st.warning(f"检测到 {len(overlaps)} 处重叠 span（建议人工调整 start/end 或合并）。")

    focus_k = st.session_state.get("focus_k", None)
    # Edit each item
    for k, it in enumerate(items):
        expanded = (k == focus_k) if focus_k is not None else (k == 0)
        with st.expander(
            f"[{k}] {it.type}  range=[{it.start_position},{it.end_position})  decision={it.decision}",
            expanded=expanded
        ):
            c1, c2, c3 = st.columns([2, 2, 3])

            with c1:
                it.type = st.text_input("type", value=it.type, key=f"type_{idx}_{k}")
                it.before_check = st.text_area("before_check", value=it.before_check, height=60, key=f"before_{idx}_{k}")

            with c2:
                it.after_check = st.text_area("after_check（为空=删除）", value=it.after_check, height=60, key=f"after_{idx}_{k}")
                it.errormsg = st.text_area("errormsg", value=it.errormsg, height=60, key=f"msg_{idx}_{k}")

            with c3:
                s = st.number_input(
                    "start_position",
                    min_value=0,
                    max_value=max(0, len(text)),
                    value=int(it.start_position),
                    key=f"s_{idx}_{k}"
                )
                e = st.number_input(
                    "end_position",
                    min_value=0,
                    max_value=max(0, len(text)),
                    value=int(it.end_position),
                    key=f"e_{idx}_{k}"
                )
                it.start_position, it.end_position = int(s), int(e)

                it.note = st.text_input("note（可选）", value=it.note, key=f"note_{idx}_{k}")

                st.markdown("**决策（按钮）**")
                st.caption(f"当前决策：{it.decision}")  # 让你“看到有变化”

                # ✅ 按钮：点了就写回 + 落盘 + rerun
                if st.button("✅ Accept", key=f"acc_{idx}_{k}", use_container_width=True):
                    it.decision = "accept"
                    persist_items_to_record(records, idx, rec, items)
                    st.rerun()

                if st.button("❌ Reject", key=f"rej_{idx}_{k}", use_container_width=True):
                    it.decision = "reject"
                    persist_items_to_record(records, idx, rec, items)
                    st.rerun()

                if st.button("↩️ Reset", key=f"rst_{idx}_{k}", use_container_width=True):
                    it.decision = "pending"
                    persist_items_to_record(records, idx, rec, items)
                    st.rerun()
                # 🗑 删除当前 span
                if st.button("🗑 删除此标注", key=f"del_{idx}_{k}", use_container_width=True):
                    st.session_state.delete_k = k
                    st.rerun()

    with st.expander("➕ 新增一个错误/建议", expanded=False):
        new_type = st.selectbox("type", ["可疑错字", "语义优化", "其他"], key=f"new_type_{idx}")
        new_start = st.number_input("start_position", min_value=0, max_value=len(text), value=0, key=f"new_start_{idx}")
        new_end = st.number_input("end_position", min_value=0, max_value=len(text), value=0, key=f"new_end_{idx}")

        st.caption("提示：end_position 是开区间 [start, end)，例如替换一个字就 end = start+1")
        new_before = st.text_input("before_check（可选，建议填）", value="", key=f"new_before_{idx}")
        new_after = st.text_input("after_check（可选；空=删除）", value="", key=f"new_after_{idx}")
        new_msg = st.text_input("errormsg（可选）", value="", key=f"new_msg_{idx}")

        if st.button("添加到当前条目", key=f"add_new_item_{idx}"):
            s = int(new_start); e = int(new_end)
            if e < s:
                s, e = e, s
            # 自动补 before_check：如果你没填，就从原文切片拿
            if not new_before:
                new_before = text[s:e]

            items.append(CheckItem(
                before_check=new_before,
                after_check=new_after,
                start_position=s,
                end_position=e,
                errormsg=new_msg,
                type=new_type,
                decision="pending",
                note=""
            ))
            # 写回并刷新
            items = h.merge_spans(items, text, require_same_type=True, require_same_decision=True)
            rec["check_result"] = [asdict(x) for x in items]
            records[idx] = rec
            st.session_state.records = records
            save_work(st.session_state.records, WORK_FILE)

            st.rerun()
    
    st.divider()

    # ✅ 清空当前条：放在 for 循环外面（否则每个 span 里都有一个清空按钮）
    if st.button("🧹 清空当前条标注", key=f"clear_item_{idx}"):
        rec2 = st.session_state.records[idx]
        rec2["check_result"] = []
        st.session_state.records[idx] = rec2
        save_work(st.session_state.records, WORK_FILE)
        st.toast("已清空当前条标注")
        st.rerun()


    st.divider()

    # Apply accepted edits
    if st.button("应用所有已 Accept 的修改到 corrected_sent（会改变文本）", type="primary"):
        # apply from back to front to keep indices stable as much as possible
        accepted = [it for it in items if it.decision == "accept"]
        accepted = h.normalize_items(accepted, len(text))
        accepted.sort(key=lambda x: (x.start_position, x.end_position), reverse=True)

        new_text = text
        for it in accepted:
            new_text = h.apply_one_edit(new_text, it)

        rec["corrected_sent"] = new_text
        # store back items (with decisions/notes)
        rec["check_result"] = [asdict(it) for it in items]
        records[idx] = rec
        save_work(st.session_state.records)
        st.success("已应用修改到 corrected_sent（注意：span 下标可能需要重新校准）。")
        st.rerun()

    if st.button("保存当前条目（仅保存 decision/note，不改文本）"):
        rec["check_result"] = [asdict(it) for it in items]
        records[idx] = rec
        save_work(st.session_state.records)
        st.success("已保存当前条目标注。")

    st.divider()

    if st.button("导出 数据集", type="secondary"):
        try:
            # ensure current item persisted
            rec["check_result"] = [asdict(it) for it in items]
            records[idx] = rec
            u.dump_jsonl(records, out_path)
            st.success(f"已导出到：{out_path}")
        except Exception as e:
            st.error(f"导出失败：{e}")

