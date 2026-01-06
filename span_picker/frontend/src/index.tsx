import React, { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib";

// ✅ Value 改成 union：pick / click
type Value =
  | null
  | { kind: "pick"; start: number; end: number; text: string }
  | { kind: "click"; index: number };

function App(props: ComponentProps) {
  const { args } = props;
  const text: string = args["text"] ?? "";
  const preview_html: string = args["preview_html"] ?? "";
  const height: number = args["height"] ?? 240;

  const taRef = useRef<HTMLTextAreaElement | null>(null);
  const [lastSig, setLastSig] = useState<string>("");

  useEffect(() => {
    Streamlit.setComponentReady();
  }, []);

  useEffect(() => {
    const raf1 = requestAnimationFrame(() => {
      Streamlit.setFrameHeight();
      const raf2 = requestAnimationFrame(() => Streamlit.setFrameHeight());
      (window as any).__raf2 = raf2;
    });

    return () => {
      cancelAnimationFrame(raf1);
      const raf2 = (window as any).__raf2;
      if (raf2) cancelAnimationFrame(raf2);
    };
  }, [text, preview_html, height]);

  // ✅ 点击高亮：事件委托抓 .hl-span[data-k]
  const onPreviewClick = (ev: React.MouseEvent<HTMLDivElement>) => {
    const target = ev.target as HTMLElement | null;
    if (!target) return;

    const el = target.closest(".hl-span") as HTMLElement | null;
    if (!el) return;

    const kStr = el.getAttribute("data-k");
    if (!kStr) return;

    const k = parseInt(kStr, 10);
    if (!Number.isFinite(k)) return;

    Streamlit.setComponentValue({ kind: "click", index: k } as Value);

    // 点击也顺手量一下高度
    requestAnimationFrame(() => Streamlit.setFrameHeight());
  };

  const onMouseUp = () => {
    const ta = taRef.current;
    if (!ta) return;

    const s = ta.selectionStart ?? 0;
    const e = ta.selectionEnd ?? 0;
    if (e <= s) return;

    const pickedText = text.slice(s, e);
    const sig = `${s}-${e}-${pickedText}`;

    if (sig === lastSig) return;
    setLastSig(sig);

    Streamlit.setComponentValue({
      kind: "pick",
      start: s,
      end: e,
      text: pickedText,
    } as Value);

    requestAnimationFrame(() => Streamlit.setFrameHeight());
  };

  const onKeyUp = (ev: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (ev.key.startsWith("Arrow") || ev.key === "Shift") onMouseUp();
  };

  return (
    <div
      style={{
        fontFamily:
          "system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
        paddingBottom: 8,
      }}
    >
      {preview_html ? (
        <div
          onClick={onPreviewClick} // ✅ 关键：加上点击监听
          style={{
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            padding: 12,
            marginBottom: 10,
            lineHeight: 1.9,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontSize: 16,
          }}
          dangerouslySetInnerHTML={{ __html: preview_html }}
        />
      ) : null}

      <textarea
        ref={taRef}
        readOnly
        value={text}
        onMouseUp={onMouseUp}
        onKeyUp={onKeyUp}
        style={{
          display: "block",
          width: "100%",
          boxSizing: "border-box",
          height,
          padding: 12,
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          outline: "none",
          fontSize: 14,
          lineHeight: 1.6,
          whiteSpace: "pre-wrap",
        }}
      />

      <div style={{ marginTop: 6, fontSize: 12, color: "#6b7280", lineHeight: 1.4 }}>
        拖拽选中文字后松开鼠标即可拾取选区（返回 start/end/text）。
      </div>
    </div>
  );
}

const ConnectedApp = withStreamlitConnection(App);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConnectedApp />
  </React.StrictMode>
);
