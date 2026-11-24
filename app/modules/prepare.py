from app.business import DomainIssue, by_kind, prepared, single

FULL_KIND = "tile"
PREVIEW_KIND = "preview"


def _clip(region, tile):
    a, b, c, d = region
    x0, y0, x1, y1 = tile
    box = (max(a, x0), max(b, y0), min(c, x1), min(d, y1))
    if box[0] < box[2] and box[1] < box[3]:
        return box
    return None


def _area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def _bounds(row, code):
    x0, y0, x1, y1 = (row[key] for key in ("x0", "y0", "x1", "y1"))
    if x0 >= x1 or y0 >= y1:
        raise DomainIssue(code)
    return (x0, y0, x1, y1)


def prepare(rows):
    region = single(rows, "region")
    a, b, c, d = (region[key] for key in ("x0", "y0", "x1", "y1"))
    if a >= c or b >= d or region["min_cells"] > (c - a) * (d - b):
        raise DomainIssue("REGION_BOUNDS")
    region_cells = (c - a) * (d - b)

    kept = []
    stats = dict(
        raw_tiles=0,
        dropped_tiles=0,
        full_tiles=0,
        preview_tiles=0,
        raw_full_gross=0,
        raw_preview_gross=0,
        clipped_full_gross=0,
        clipped_preview_gross=0,
        outside_full_cells=0,
        outside_preview_cells=0,
    )
    for kind, tier in ((FULL_KIND, "full"), (PREVIEW_KIND, "preview")):
        for row in by_kind(rows, kind):
            raw_box = _bounds(row, "TILE_BOUNDS")
            raw_cells = _area(raw_box)
            stats["raw_tiles"] += 1
            stats[f"raw_{tier}_gross"] += raw_cells
            box = _clip((a, b, c, d), raw_box)
            if box is None:
                stats["dropped_tiles"] += 1
                stats[f"outside_{tier}_cells"] += raw_cells
                continue
            kept.append((box, tier))
            stats[f"{tier}_tiles"] += 1
            inside = _area(box)
            stats[f"clipped_{tier}_gross"] += inside
            # 越出作业区、被裁掉的面积只记账为排除量，不进入覆盖账。
            stats[f"outside_{tier}_cells"] += raw_cells - inside

    full_boxes = [box for box, tier in kept if tier == "full"]
    preview_boxes = [box for box, tier in kept if tier == "preview"]
    details = dict(
        region_cells=region_cells,
        target=region["min_cells"],
        raw_tiles=stats["raw_tiles"],
        kept_tiles=len(kept),
        dropped_tiles=stats["dropped_tiles"],
        full_tiles=len(full_boxes),
        preview_tiles=len(preview_boxes),
        raw_full_gross=stats["raw_full_gross"],
        raw_preview_gross=stats["raw_preview_gross"],
        clipped_full_gross=stats["clipped_full_gross"],
        clipped_preview_gross=stats["clipped_preview_gross"],
        clipped_proxy_gross=stats["clipped_full_gross"] + stats["clipped_preview_gross"],
        raw_proxy_gross=stats["raw_full_gross"] + stats["raw_preview_gross"],
        outside_cells=stats["outside_full_cells"] + stats["outside_preview_cells"],
        outside_full_cells=stats["outside_full_cells"],
        outside_preview_cells=stats["outside_preview_cells"],
    )
    payload = dict(
        details,
        full_boxes=full_boxes,
        proxy_boxes=full_boxes + preview_boxes,
    )
    return prepared(len(kept), details, payload)
