from app.business import intervals, measured


def union_area(boxes):
    """每块瓦片裁剪到作业区后取并集；同一像元被多块瓦片覆盖只计一次。"""
    edges = sorted({x for a, _, b, _ in boxes for x in (a, b)})
    covered = 0
    for left, right in zip(edges, edges[1:]):
        spans = intervals(
            (y0, y1) for x0, y0, x1, y1 in boxes if x0 <= left and right <= x1
        )
        covered += (right - left) * sum(y1 - y0 for y0, y1 in spans)
    return covered


def layer(boxes, gross, region_cells):
    covered = union_area(boxes)
    # 并集之外的重叠多计量 = 合计毛面积 - 去重后的覆盖面积。
    overlap_excess = max(0, gross - covered)
    return {
        "covered_cells": covered,
        "region_cells": region_cells,
        "gap_cells": region_cells - covered,
        "overlap_excess_cells": overlap_excess,
        "tiles": len(boxes),
        "gross_cells": gross,
    }


def compute(details):
    region_cells = details["region_cells"]
    formal = layer(details["full_boxes"], details["clipped_full_gross"], region_cells)
    proxy = layer(details["proxy_boxes"], details["clipped_proxy_gross"], region_cells)

    result = measured(
        formal["covered_cells"],
        details["target"],
        "像元",
        {
            "gap_cells": formal["gap_cells"],
            "overlap_excess_cells": formal["overlap_excess_cells"],
        },
    )
    result["formal"] = formal
    result["proxy"] = proxy
    result["tiles"] = {
        "raw": details["raw_tiles"],
        "kept": details["kept_tiles"],
        "dropped": details["dropped_tiles"],
        "full": details["full_tiles"],
        "preview": details["preview_tiles"],
    }
    result["excluded"] = {
        # 越出作业区的面积只在这里记账，不进入覆盖账。
        "outside_cells": details["outside_cells"],
        "outside_full_cells": details["outside_full_cells"],
        "outside_preview_cells": details["outside_preview_cells"],
        "raw_full_gross": details["raw_full_gross"],
        "raw_preview_gross": details["raw_preview_gross"],
        "raw_proxy_gross": details["raw_proxy_gross"],
        "clipped_full_gross": details["clipped_full_gross"],
        "clipped_preview_gross": details["clipped_preview_gross"],
        "clipped_proxy_gross": details["clipped_proxy_gross"],
        "dropped_tiles": details["dropped_tiles"],
    }
    return result
