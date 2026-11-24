from app.business import decision


def policy(result):
    return decision(
        result,
        "COVERAGE_GAP" if result["value"] < result["expected"] else None,
        lower_bound=True,
    )
