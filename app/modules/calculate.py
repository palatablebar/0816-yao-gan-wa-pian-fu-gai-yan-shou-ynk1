from app.business import measured, intervals


def compute(data):
    boxes, area, target = data
    edges = sorted({x for a, _, b, _ in boxes for x in (a, b)})
    covered = 0
    for left, right in zip(edges, edges[1:]):
        spans = intervals(
            (y0, y1) for x0, y0, x1, y1 in boxes if x0 <= left and right <= x1
        )
        covered += (right - left) * sum(y1 - y0 for y0, y1 in spans)
    gross = sum((b - a) * (d - c) for a, c, b, d in boxes)
    return measured(
        covered,
        target,
        "像元",
        {"gap_cells": area - covered, "overlap_excess_cells": gross - covered},
    )
