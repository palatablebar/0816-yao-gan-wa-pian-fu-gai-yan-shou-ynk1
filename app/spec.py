COLUMNS = ("x0", "y0", "x1", "y1", "min_cells")
# region 为作业区；tile 为全分辨率正式瓦片；preview 为低分辨率预览瓦片（仅够临时代理）。
KINDS = ("region", "tile", "preview")
PROJECT = {
    "name": "遥感瓦片覆盖验收",
    "actor": "地理数据交付工程师",
    "stages": [
        ("intake", "样例采信"),
        ("prepare", "范围裁切"),
        ("calculate", "覆盖归并"),
        ("policy", "缺口验收"),
        ("balance", "运行对账"),
    ],
    "chart": "覆盖区域",
}
