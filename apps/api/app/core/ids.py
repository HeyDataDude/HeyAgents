"""Prefixed, sortable identifiers for domain objects.

We use short prefixed ULationish IDs (timestamp-prefixed + random) so IDs are human-recognizable in
logs and URLs (e.g. `thg_01H...`, `agt_...`). They remain opaque strings in the DB.
"""

from __future__ import annotations

import secrets
import time

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _b36(n: int) -> str:
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(_ALPHABET[r])
    return "".join(reversed(out))


def new_id(prefix: str) -> str:
    ts = _b36(int(time.time() * 1000))
    rand = _b36(secrets.randbits(48))
    return f"{prefix}_{ts}{rand}"


# Convenience factories keep prefixes consistent across the codebase.
def thought_id() -> str: return new_id("thg")
def dispatch_id() -> str: return new_id("dsp")
def agent_dispatch_id() -> str: return new_id("adp")
def agent_id() -> str: return new_id("agt")
def memory_id() -> str: return new_id("mem")
def task_id() -> str: return new_id("tsk")
def project_id() -> str: return new_id("prj")
def research_id() -> str: return new_id("rsh")
def report_id() -> str: return new_id("rpt")
def question_id() -> str: return new_id("qst")
def connection_id() -> str: return new_id("cxn")
def job_id() -> str: return new_id("job")
def message_id() -> str: return new_id("msg")
def activity_id() -> str: return new_id("act")
def user_id() -> str: return new_id("usr")
def conversation_id() -> str: return new_id("cnv")
def artifact_id() -> str: return new_id("art")
