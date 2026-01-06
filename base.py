from dataclasses import dataclass
# =========================
# Data structures
# =========================
@dataclass
class CheckItem:
    before_check: str
    after_check: str
    start_position: int
    end_position: int
    errormsg: str = ""
    type: str = ""
    # human annotation
    decision: str = "pending"  # pending | accept | reject
    note: str = ""