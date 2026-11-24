import json


def artifact(run):
    balances = run["report"]["balance"]
    packet = {
        "schema": "review-evidence/1",
        "manifest": run["report"]["manifest"],
        "balance": balances,
        "delivery": balances.get("delivery"),
        "reconciliation": {
            "rows": balances.get("rows"),
            "pixels": balances.get("pixels"),
            "blocks": balances.get("blocks"),
        },
        "cases": run["report"]["cases"],
        "intake": run["report"]["intake"],
        "review": {key: run[key] for key in ("status", "revision", "note", "reviewed")},
    }
    return (
        json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode()
