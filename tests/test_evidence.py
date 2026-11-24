import json
from hashlib import sha256

from app.evidence.render import artifact
from app.review.service import execute, review


def test_origin_checksum_matches_input(store, clean):
    output = json.loads(artifact(execute(store, clean)))
    assert output["manifest"]["sha256"] == sha256(clean).hexdigest()


def test_same_revision_bytes_are_deterministic(store, clean):
    run = execute(store, clean)
    assert artifact(run) == artifact(store.load(run["id"]))


def test_export_preserves_isolated_row_numbers(store, dirty):
    output = json.loads(artifact(execute(store, dirty)))
    isolated = output["intake"]["isolation"]
    assert len(isolated) == 5 and all(row["line"] > 1 for row in isolated)


def test_export_preserves_approved_note(store, clean):
    run = execute(store, clean)
    revised = review(
        store, run["id"], dict(revision=0, status="APPROVED", note="复核结果通过")
    )
    assert json.loads(artifact(revised))["review"]["note"] == "复核结果通过"


def test_evidence_404(client):
    assert client.get("/api/runs/unknown/evidence").status_code == 404


def test_download_attachment(client):
    run = client.post("/api/runs", data={"sample": "clean"}).json
    response = client.get("/api/runs/" + run["id"] + "/evidence")
    assert (
        response.status_code == 200
        and "attachment" in response.headers["Content-Disposition"]
    )
    assert response.json["schema"] == "review-evidence/1"


def test_evidence_has_reconciliation_ledgers(store, dirty):
    output = json.loads(artifact(execute(store, dirty)))
    rows = output["reconciliation"]["rows"]
    pixels = output["reconciliation"]["pixels"]
    assert rows["source"] == output["balance"]["input"]
    assert rows["accepted"] + rows["isolated"] + rows["ignored"] == rows["source"]
    assert pixels["cases"] and all("checks" in item for item in pixels["cases"])
    assert output["delivery"]["choice"] == "HOLD"


def test_evidence_records_proxy_delivery(store, deadline):
    record = execute(store, deadline)
    review(store, record["id"], dict(revision=0, status="PROVISIONAL", note="截止日先交代理"))
    output = json.loads(artifact(store.load(record["id"])))
    assert output["delivery"]["choice"] == "DELIVER_PROXY"
    assert output["review"]["status"] == "PROVISIONAL"
    assert output["balance"]["proxy_releasable"] and not output["balance"]["releasable"]
