import json, os
from typing import List, Dict, Any
GLOBAL_CACHE_FILE = ".labeler_cache.json"
def load_cache():
    if os.path.exists(GLOBAL_CACHE_FILE):
        try:
            with open(GLOBAL_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(obj: dict):
    with open(GLOBAL_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records

def dump_jsonl(records: List[Dict[str, Any]], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default
    
def reset_work_from_input(in_path: str, work_path: str):
    """
    用 input.jsonl 覆盖 work_file，相当于“重置标注状态”
    """
    records = load_jsonl(in_path)
    dump_jsonl(records, work_path)
    return records