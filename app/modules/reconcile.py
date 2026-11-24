from collections import Counter

from app.modules.policy import PROVISIONAL, SIGN, summarize


def _row_ledger(intake, cases):
    accounted = (
        intake["accepted"] + intake["rejected"] + intake["blank"] + intake["repeated"]
    )
    observed = sum(len(case["records"]) for case in cases)
    return {
        "source": intake["input"],
        "accepted": intake["accepted"],
        "isolated": intake["rejected"],
        "ignored": intake["blank"] + intake["repeated"],
        "accounted": accounted,
        "observed": observed,
        "balanced": accounted == intake["input"] and observed == intake["accepted"],
        "breaks": [
            item
            for item, ok in (
                ("accepted+isolated+ignored != source", accounted == intake["input"]),
                ("case_records != accepted", observed == intake["accepted"]),
            )
            if not ok
        ],
    }


def _pixel_checks(case):
    measure = case.get("measure") or {}
    prep = (case.get("prep") or {}).get("details") or {}
    formal = measure.get("formal")
    proxy = measure.get("proxy")
    excluded = measure.get("excluded")
    if formal is None or proxy is None or excluded is None:
        return None
    region = formal["region_cells"]
    gain = proxy["covered_cells"] - formal["covered_cells"]
    # 采信行里，除一行业务区外，其余都应是被裁切的瓦片/预览行并已进入覆盖计算。
    used_rows = len(case.get("records", []))
    raw_tiles = prep.get("raw_tiles")
    return {
        "case": case["case"],
        "region_cells": region,
        "accepted_rows": used_rows,
        "tile_rows": raw_tiles,
        "kept_tiles": prep.get("kept_tiles"),
        "dropped_tiles": prep.get("dropped_tiles"),
        "formal_covered": formal["covered_cells"],
        "formal_gap": formal["gap_cells"],
        "proxy_covered": proxy["covered_cells"],
        "proxy_gap": proxy["gap_cells"],
        "proxy_gain": gain,
        "outside_cells": excluded["outside_cells"],
        "checks": {
            "formal_covered+formal_gap==region": formal["covered_cells"]
            + formal["gap_cells"]
            == region,
            "proxy_covered+proxy_gap==region": proxy["covered_cells"]
            + proxy["gap_cells"]
            == region,
            "proxy_covered==formal_covered+proxy_gain": proxy["covered_cells"]
            == formal["covered_cells"] + gain
            and gain >= 0,
            "formal_gross==formal_covered+formal_overlap": formal["gross_cells"]
            == formal["covered_cells"] + formal["overlap_excess_cells"],
            "proxy_gross==proxy_covered+proxy_overlap": proxy["gross_cells"]
            == proxy["covered_cells"] + proxy["overlap_excess_cells"],
            "raw_proxy_gross==clipped_proxy_gross+outside": excluded["raw_proxy_gross"]
            == excluded["clipped_proxy_gross"] + excluded["outside_cells"],
            "clipped_full_gross==formal_gross": excluded["clipped_full_gross"]
            == formal["gross_cells"],
            "clipped_preview_gross+clipped_full_gross==clipped_proxy_gross": excluded[
                "clipped_preview_gross"
            ]
            + excluded["clipped_full_gross"]
            == excluded["clipped_proxy_gross"],
            "outside_not_in_coverage": formal["covered_cells"] <= region
            and proxy["covered_cells"] <= region,
            # 采信行 = 业务区 + 全部瓦片/预览行；瓦片行 = 保留 + 丢出作业区。
            "accepted_rows==region+tile_rows": raw_tiles is not None
            and used_rows == 1 + raw_tiles,
            "tile_rows==kept+dropped": raw_tiles is not None
            and raw_tiles == prep.get("kept_tiles", 0) + prep.get("dropped_tiles", 0),
            "kept_rows==full+preview_tiles": prep.get("kept_tiles")
            == prep.get("full_tiles", 0) + prep.get("preview_tiles", 0),
        },
    }


def _pixel_ledger(cases):
    rows, breaks = [], []
    for case in cases:
        checks = _pixel_checks(case)
        if checks is None:
            continue
        failed = [name for name, ok in checks["checks"].items() if not ok]
        rows.append({**checks, "failed": failed})
        breaks.extend(f"{case['case']}:{name}" for name in failed)
    return {"cases": rows, "balanced": not breaks, "breaks": breaks}


def balance(intake, cases):
    rows = _row_ledger(intake, cases)
    pixels = _pixel_ledger(cases)
    status = Counter(case["status"] for case in cases)
    ready = status.get(SIGN, 0)
    provisional = status.get(PROVISIONAL, 0)
    held = len(cases) - ready - provisional
    issues = {k: v for k, v in sorted(status.items()) if k != SIGN}

    summary = summarize(cases)
    blocks = list(rows["breaks"]) + pixels["breaks"]
    if not cases:
        blocks.append("no business cases")
    if intake["rejected"]:
        blocks.append("isolated rows present")
    if held:
        blocks.append("held cases present")
    # 行账、像元账逐项对平是任何交付的前置；对不上就不签、不代理。
    balanced = rows["balanced"] and pixels["balanced"]
    releasable = (
        balanced
        and bool(cases)
        and ready == len(cases)
        and not intake["rejected"]
        and summary["choice"] == "SIGN_FULL"
    )
    proxy_releasable = (
        balanced
        and bool(cases)
        and not intake["rejected"]
        and summary["choice"] == "DELIVER_PROXY"
    )
    if not releasable and not proxy_releasable and not blocks:
        blocks.append("delivery blocked")
    return dict(
        input=intake["input"],
        accepted=intake["accepted"],
        isolated=intake["rejected"],
        ignored=intake["blank"] + intake["repeated"],
        accounted=rows["accounted"],
        balanced=balanced,
        rows=rows,
        pixels=pixels,
        ready=ready,
        provisional=provisional,
        pending=held,
        issues=issues,
        delivery=summary,
        releasable=releasable,
        proxy_releasable=proxy_releasable,
        blocked=bool(blocks),
        blocks=blocks,
    )
