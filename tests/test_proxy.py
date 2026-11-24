"""低分辨率代理与全分辨率正式覆盖的区分规则。"""

from app.modules.calculate import compute, union_area
from app.modules.pipeline import run
from conftest import csv_data


def case_of(data, code, stage=5):
    return next(c for c in run(data, stage)["cases"] if c["case"] == code)


def build(region, tiles, minimum=0):
    rows = [["R", "01", "region", *map(str, region), str(minimum), "作业区"]]
    for index, (kind, *box) in enumerate(tiles, 1):
        rows.append([f"T{index:02d}", "01", kind, *map(str, box), "0", "瓦片"])
    return csv_data(rows)


def test_same_pixel_covered_by_many_tiles_counts_once():
    assert union_area([(0, 0, 6, 10), (4, 0, 12, 10)]) == 120


def test_overlapping_proxy_and_formal_do_not_double_count():
    data = build((0, 0, 10, 10), [("tile", 0, 0, 10, 5), ("preview", 0, 4, 10, 10)])
    item = case_of(data, "01")
    assert item["formal"]["covered_cells"] == 50
    # 预览与全分辨率重叠一行只计一次，代理覆盖是 100 而不是 110。
    assert item["proxy"]["covered_cells"] == 100
    assert item["proxy_gain_cells"] == 50


def test_low_resolution_preview_is_not_formal_coverage():
    data = build((0, 0, 10, 10), [("tile", 0, 0, 10, 5), ("preview", 0, 4, 10, 10)], 100)
    item = case_of(data, "01")
    assert item["status"] == "PROVISIONAL"
    assert item["recommendation"] == "DELIVER_PROXY"
    assert item["basis"] == "PROXY"
    assert not item["formal_ready"] and item["proxy_ready"]


def test_full_resolution_alone_signs():
    data = build((0, 0, 10, 10), [("tile", 0, 0, 6, 10), ("tile", 4, 0, 12, 10)], 100)
    item = case_of(data, "01")
    assert item["status"] == "READY" and item["recommendation"] == "SIGN_FULL"
    assert item["measure"]["excluded"]["outside_cells"] == 20


def test_proxy_still_missing_region_is_held():
    data = build((0, 0, 10, 10), [("tile", 0, 0, 10, 2), ("preview", 0, 2, 10, 4)], 100)
    item = case_of(data, "01")
    assert item["status"] == "COVERAGE_GAP" and item["recommendation"] == "HOLD"
    assert not item["proxy_ready"]


def test_outside_region_area_never_enters_coverage():
    data = build((0, 0, 10, 10), [("tile", 0, 0, 20, 10)], 100)
    measure = case_of(data, "01", 3)["measure"]
    assert measure["formal"]["covered_cells"] == 100
    assert measure["excluded"]["outside_cells"] == 100
    assert measure["excluded"]["raw_full_gross"] == 200


def test_deadline_sample_recommends_proxy(deadline):
    report = run(deadline)
    assert [c["status"] for c in report["cases"]] == ["PROVISIONAL", "READY"]
    assert report["balance"]["delivery"]["choice"] == "DELIVER_PROXY"
    assert report["balance"]["proxy_releasable"] and not report["balance"]["releasable"]


def test_clean_sample_still_signs(clean):
    report = run(clean)
    assert report["balance"]["releasable"] and report["balance"]["delivery"]["choice"] == "SIGN_FULL"
