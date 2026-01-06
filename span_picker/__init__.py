import os
import streamlit.components.v1 as components

# 开发模式：前端 dev server
_DEV_URL = "http://localhost:5173"

_RELEASE_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# 你可以用环境变量切换
if os.environ.get("SPAN_PICKER_DEV", "0") == "1":
    _component = components.declare_component("span_picker", url=_DEV_URL)
else:
    _component = components.declare_component("span_picker", path=_RELEASE_DIR)

def span_picker(text: str, preview_html: str = "", key: str = None, height: int = 240):
    """
    返回：
      None 或 {"start": int, "end": int, "text": str}
    """
    return _component(
        text=text,
        preview_html=preview_html,
        height=height,
        default=None,
        key=key,
    )
