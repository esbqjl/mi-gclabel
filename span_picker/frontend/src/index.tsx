import React, { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib";

type Value = null | { start: number; end: number; text: string };

function App(props: ComponentProps) {
  const { args } = props;
  const text: string = args["text"] ?? "";
  const preview_html: string = args["preview_html"] ?? "";
  const height: number = args["height"] ?? 240;

  const taRef = useRef<HTMLTextAreaElement | null>(null);
  const [lastSig, setLastSig] = useState<string>("");

  // 1) 首次：告诉 Streamlit “我准备好了”
  useEffect(() => {
    Streamlit.setComponentReady();
  }, []);

  // 2) 任何内容变化后：重新计算 iframe 高度，避免底部被裁
  useEffect(() => {
    const raf1 = requestAnimationFrame(() => {
      Streamlit.setFrameHeight();
      const raf2 = requestAnimationFrame(() => Streamlit.setFrameHeight());
      // @ts-ignore
      (window as any).__raf2 = raf2;
    });

    return () => {
      cancelAnimationFrame(raf1);
      // @ts-ignore
      const raf2 = (window as any).__raf2;
      if (raf2) cancelAnimationFrame(raf2);
    };
  }, [text, preview_html, height]);

  const onMouseUp = () => {
    const ta = taRef.current;
    if (!ta) return;

    const s = ta.selectionStart ?? 0;
    const e = ta.selectionEnd ?? 0;
    if (e <= s) return;

    const pickedText = text.slice(s, e);
    const sig = `${s}-${e}-${pickedText}`; // ✅ 注意这里必须是反引号

    if (sig === lastSig) return;
    setLastSig(sig);

    const value: Value = { start: s, end: e, text: pickedText };
    Streamlit.setComponentValue(value);

    // 选区变化也可能影响布局（比如出现/隐藏某些 UI），顺手再量一次
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
        paddingBottom: 8, // ✅ 给底部一点空间，防止半行被裁
      }}
    >
      {preview_html ? (
        <div
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
