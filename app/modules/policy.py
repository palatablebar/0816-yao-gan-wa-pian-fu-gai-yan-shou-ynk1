from app.business import decision

# 正式验收采用全分辨率瓦片；低分辨率预览只够做临时代理交付。
SIGN = "READY"
PROVISIONAL = "PROVISIONAL"
HOLD = "COVERAGE_GAP"

RECOMMEND = {
    SIGN: "SIGN_FULL",
    PROVISIONAL: "DELIVER_PROXY",
    HOLD: "HOLD",
}


def policy(result):
    formal = result["formal"]
    proxy = result["proxy"]
    target = result["expected"]
    formal_ok = formal["covered_cells"] >= target
    proxy_ok = proxy["covered_cells"] >= target

    if formal_ok:
        status = SIGN
    elif proxy_ok:
        status = PROVISIONAL
    else:
        status = HOLD
    # 结论沿用全分辨率测量值，代理测量值单列，避免把预览当作正式覆盖。
    verdict = decision(result, None if formal_ok else status, lower_bound=True)
    verdict["status"] = status
    verdict["recommendation"] = RECOMMEND[status]
    verdict["formal_ready"] = formal_ok
    verdict["proxy_ready"] = proxy_ok
    verdict["basis"] = "FORMAL" if formal_ok else ("PROXY" if proxy_ok else "NONE")
    verdict["formal"] = dict(formal, target=target)
    verdict["proxy"] = dict(proxy, target=target)
    verdict["proxy_gain_cells"] = proxy["covered_cells"] - formal["covered_cells"]
    return verdict


def summarize(cases):
    """从整批结论推导交付口径：先交代理，还是等全精度，还是一次签。"""
    statuses = [case.get("status") for case in cases]
    signable = [case.get("case") for case in cases if case.get("status") == SIGN]
    proxied = [case.get("case") for case in cases if case.get("status") == PROVISIONAL]
    held = [case.get("case") for case in cases if case.get("status") == HOLD]

    settled = bool(cases) and all(s in (SIGN, PROVISIONAL, HOLD) for s in statuses)
    if not settled or held:
        choice = "HOLD"
    elif not proxied:
        choice = "SIGN_FULL"
    else:
        choice = "DELIVER_PROXY"

    note = {
        "SIGN_FULL": "全分辨率瓦片齐备，可一次正式签发",
        "DELIVER_PROXY": "全分辨率覆盖未齐备，可先交临时代理；正式签发待全分辨率瓦片齐备后另跑一批",
        "HOLD": "存在未达最低覆盖或待处理差异，暂不能交付",
    }[choice]
    return {
        "choice": choice,
        "can_sign_now": choice == "SIGN_FULL",
        "can_proxy_now": choice == "DELIVER_PROXY",
        "signable_cases": len(signable),
        "proxied_cases": len(proxied),
        "held_cases": len(held),
        "signable": signable,
        "proxied": proxied,
        "held": held,
        "note": note,
    }
