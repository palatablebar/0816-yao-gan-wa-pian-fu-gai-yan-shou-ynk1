from app.business import DomainIssue, by_kind, prepared, single


def prepare(rows):
    region = single(rows, "region")
    a, b, c, d = (region[k] for k in ("x0", "y0", "x1", "y1"))
    if a >= c or b >= d or region["min_cells"] > (c - a) * (d - b):
        raise DomainIssue("REGION_BOUNDS")
    clipped = []
    for r in by_kind(rows, "tile"):
        x0, y0, x1, y1 = (r[k] for k in ("x0", "y0", "x1", "y1"))
        if x0 >= x1 or y0 >= y1:
            raise DomainIssue("TILE_BOUNDS")
        box = (max(a, x0), max(b, y0), min(c, x1), min(d, y1))
        if box[0] < box[2] and box[1] < box[3]:
            clipped.append(box)
    return prepared(
        len(clipped),
        {"region_cells": (c - a) * (d - b)},
        (clipped, (c - a) * (d - b), region["min_cells"]),
    )
