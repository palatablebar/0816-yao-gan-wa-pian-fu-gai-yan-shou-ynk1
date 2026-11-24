from datetime import datetime, timezone
from hashlib import sha256
from time import monotonic

from app.business import DomainIssue
from app.config import RULE_VERSION
from app.modules.pipeline import run


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def execute(store, data):
    start = monotonic()
    fingerprint = sha256(data).hexdigest()
    run_id = sha256(f"{RULE_VERSION}:{fingerprint}".encode()).hexdigest()
    try:
        return store.load(run_id)
    except DomainIssue as error:
        if error.code != "RUN_NOT_FOUND":
            raise
    report = run(data)
    report["manifest"] = dict(
        sha256=fingerprint,
        version=RULE_VERSION,
        created=now(),
        duration_ms=round((monotonic() - start) * 1000, 3),
        bytes=len(data),
        run_id=run_id,
    )
    return store.register(run_id, report)


REVIEW_STATUSES = ("APPROVED", "PROVISIONAL", "HELD")
# 正式签发与临时代理交付都是终态，重跑不得覆盖。
FINAL_STATUSES = ("APPROVED", "PROVISIONAL")


def review(store, run_id, values):
    if not isinstance(values, dict):
        raise DomainIssue("REVIEW_FIELDS")
    revision, status, note = (values.get(key) for key in ("revision", "status", "note"))
    if (
        type(revision) is not int
        or revision < 0
        or status not in REVIEW_STATUSES
        or not isinstance(note, str)
        or not (3 <= len(note.strip()) <= 200)
    ):
        raise DomainIssue("REVIEW_FIELDS")
    current = store.load(run_id)
    if revision != current["revision"]:
        raise DomainIssue("STALE_REVIEW")
    if current["status"] in FINAL_STATUSES:
        raise DomainIssue("RUN_FINALIZED")
    checks = current["report"]["balance"]
    # 正式签发只认全分辨率覆盖；代理交付可先把低分辨率预览交出去。
    if status == "APPROVED" and not checks["releasable"]:
        raise DomainIssue("UNRESOLVED_ISSUES")
    if status == "PROVISIONAL" and not checks["proxy_releasable"]:
        raise DomainIssue("UNRESOLVED_ISSUES")
    return store.revise(run_id, revision, status, note.strip(), now())
