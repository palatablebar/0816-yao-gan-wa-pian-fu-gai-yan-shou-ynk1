EXPECTED = {
    "0001": (2, 100, "READY"),
    "0002": (1, 15, "READY"),
    "0003": (0, None, "REGION_BOUNDS"),
    "0004": (2, 24, "COVERAGE_GAP"),
}
EVIDENCE = {
    "0001": {"gap_cells": 0, "overlap_excess_cells": 20},
    "0002": {"gap_cells": 5, "overlap_excess_cells": 0},
}
