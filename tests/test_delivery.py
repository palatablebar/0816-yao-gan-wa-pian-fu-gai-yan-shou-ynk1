"""代理交付与正式签发的复核状态机、以及逐项对账。"""

import pytest

from app.business import DomainIssue
from app.review.service import execute, review
from app.modules.pipeline import run


def test_proxy_only_batch_cannot_be_formally_signed(store, deadline):
    run_record = execute(store, deadline)
    with pytest.raises(DomainIssue, match="UNRESOLVED_ISSUES"):
        review(store, run_record["id"], dict(revision=0, status="APPROVED", note="直接签发"))
    assert store.load(run_record["id"])["revision"] == 0


def test_proxy_only_batch_can_be_delivered_as_proxy(store, deadline):
    run_record = execute(store, deadline)
    output = review(
        store, run_record["id"], dict(revision=0, status="PROVISIONAL", note="截止日先交代理")
    )
    assert (output["status"], output["revision"]) == ("PROVISIONAL", 1)


def test_proxy_delivery_is_terminal_for_same_source(store, deadline):
    run_record = execute(store, deadline)
    review(store, run_record["id"], dict(revision=0, status="PROVISIONAL", note="截止日先交代理"))
    again = execute(store, deadline)
    assert again["id"] == run_record["id"]
    assert (again["status"], again["revision"]) == ("PROVISIONAL", 1)
    with pytest.raises(DomainIssue, match="RUN_FINALIZED"):
        review(store, run_record["id"], dict(revision=1, status="APPROVED", note="升级为正式"))


def test_formal_batch_cannot_mark_provisional(store, clean):
    run_record = execute(store, clean)
    with pytest.raises(DomainIssue, match="UNRESOLVED_ISSUES"):
        review(store, run_record["id"], dict(revision=0, status="PROVISIONAL", note="无需代理"))


def test_failed_sign_keeps_old_version_and_evidence(store, deadline):
    run_record = execute(store, deadline)
    before = store.load(run_record["id"])
    with pytest.raises(DomainIssue):
        review(store, run_record["id"], dict(revision=0, status="APPROVED", note="尝试正式"))
    after = store.load(run_record["id"])
    assert after == before


def test_row_and_pixel_ledgers_balance(clean):
    checks = run(clean)["balance"]
    assert checks["rows"]["balanced"] and checks["pixels"]["balanced"]
    assert checks["rows"]["source"] == (
        checks["rows"]["accepted"] + checks["rows"]["isolated"] + checks["rows"]["ignored"]
    )


def test_isolated_rows_block_proxy_delivery(store, dirty):
    checks = run(dirty)["balance"]
    assert checks["isolated"] == 5 and not checks["proxy_releasable"]
    assert any("isolated" in block for block in checks["blocks"])
    run_record = execute(store, dirty)
    with pytest.raises(DomainIssue, match="UNRESOLVED_ISSUES"):
        review(store, run_record["id"], dict(revision=0, status="PROVISIONAL", note="强行代理"))


def _measured(formal, proxy, excluded, prep=None):
    return {
        "case": "01",
        "records": ["region", "tile"],
        "status": "READY",
        "prep": {
            "count": 1,
            "details": dict(
                prep
                or dict(
                    raw_tiles=1,
                    kept_tiles=1,
                    dropped_tiles=0,
                    full_tiles=1,
                    preview_tiles=0,
                )
            ),
        },
        "measure": {
            "formal": dict(formal),
            "proxy": dict(proxy),
            "excluded": dict(excluded),
        },
    }


def _intake(**overrides):
    return dict(dict(input=1, accepted=1, rejected=0, blank=0, repeated=0), **overrides)


def test_pixel_ledger_break_blocks_release():
    from app.modules.reconcile import balance

    formal = dict(
        covered_cells=80, gap_cells=10, region_cells=100, gross_cells=80,
        overlap_excess_cells=0,
    )
    proxy = dict(
        covered_cells=90, gap_cells=10, region_cells=100, gross_cells=90,
        overlap_excess_cells=0,
    )
    excluded = dict(
        outside_cells=0, raw_proxy_gross=90, clipped_proxy_gross=90,
        clipped_preview_gross=10, clipped_full_gross=80,
    )
    checks = balance(_intake(input=2, accepted=2), [_measured(formal, proxy, excluded)])
    assert not checks["pixels"]["balanced"]
    assert any("formal_covered+formal_gap" in b for b in checks["pixels"]["breaks"])
    assert checks["blocked"] and not checks["releasable"]


def test_balanced_case_dict_passes_pixel_ledger():
    from app.modules.reconcile import balance

    formal = dict(
        covered_cells=100, gap_cells=0, region_cells=100, gross_cells=120,
        overlap_excess_cells=20,
    )
    proxy = dict(
        covered_cells=100, gap_cells=0, region_cells=100, gross_cells=120,
        overlap_excess_cells=20,
    )
    excluded = dict(
        outside_cells=0, raw_proxy_gross=120, clipped_proxy_gross=120,
        clipped_preview_gross=0, clipped_full_gross=120,
    )
    checks = balance(_intake(input=2, accepted=2), [_measured(formal, proxy, excluded)])
    assert checks["pixels"]["balanced"] and checks["releasable"]


def test_row_to_pixel_linkage_balances(clean):
    item = run(clean)["balance"]["pixels"]["cases"][0]
    assert not item["failed"]
    assert item["accepted_rows"] == 1 + item["tile_rows"]
    assert item["tile_rows"] == item["kept_tiles"] + item["dropped_tiles"]


def test_dropped_tile_is_still_accounted_not_covered():
    from app.modules.pipeline import run as run_pipeline
    from conftest import csv_data

    payload = csv_data(
        [
            ["R", "01", "region", "0", "0", "10", "10", "100", "作业区"],
            ["A", "01", "tile", "0", "0", "10", "10", "0", "区内"],
            ["B", "01", "tile", "20", "20", "30", "30", "0", "完全在区外"],
        ]
    )
    report = run_pipeline(payload)
    item = report["balance"]["pixels"]["cases"][0]
    assert item["dropped_tiles"] == 1 and not item["failed"]
    assert report["balance"]["releasable"]
    assert item["formal_covered"] == 100 and item["outside_cells"] == 100


def test_evidence_carries_delivery_and_reconciliation(client):
    run_record = client.post("/api/runs", data={"sample": "deadline"}).json
    packet = client.get(f"/api/runs/{run_record['id']}/evidence").json
    assert packet["delivery"]["choice"] == "DELIVER_PROXY"
    assert packet["reconciliation"]["rows"]["balanced"]
    assert [item["case"] for item in packet["reconciliation"]["pixels"]["cases"]] == [
        "0101",
        "0102",
    ]


def test_full_resolution_arrival_starts_new_signable_batch(store, deadline):
    """先交代理的批次保持不动；全分辨率补齐后是新来源，可另签一批。"""
    proxied = execute(store, deadline)
    review(store, proxied["id"], dict(revision=0, status="PROVISIONAL", note="截止日先交代理"))

    from conftest import csv_data

    complete = csv_data(
        [
            ["010101", "0101", "region", "0", "0", "10", "10", "100", "全分辨率补齐"],
            ["010102", "0101", "tile", "0", "0", "10", "5", "0", "上半"],
            ["010103", "0101", "tile", "0", "5", "10", "10", "0", "下半"],
        ]
    )
    fresh = execute(store, complete)
    assert fresh["id"] != proxied["id"]
    assert fresh["report"]["balance"]["releasable"]
    signed = review(
        store, fresh["id"], dict(revision=0, status="APPROVED", note="全分辨率齐备后签发")
    )
    assert signed["status"] == "APPROVED"
    untouched = store.load(proxied["id"])
    assert (untouched["status"], untouched["report"]["balance"]["delivery"]["choice"]) == (
        "PROVISIONAL",
        "DELIVER_PROXY",
    )


def test_release_modes_are_mutually_exclusive(store, clean, deadline):
    for data in (clean, deadline):
        checks = run(data)["balance"]
        assert not (checks["releasable"] and checks["proxy_releasable"])
        assert checks["delivery"]["can_sign_now"] != checks["delivery"]["can_proxy_now"]


def test_delivery_summary_lists_case_buckets(deadline):
    checks = run(deadline)["balance"]["delivery"]
    assert checks["signable"] == ["0102"]
    assert checks["proxied"] == ["0101"]
    assert checks["held"] == []
    assert checks["can_proxy_now"] and not checks["can_sign_now"]
