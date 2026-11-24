# 遥感瓦片覆盖验收规则登记

- 规模：中型

## 功能模块

| 模块 | 动作 | 接口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 样例采信 | 预览并定位坏行 | `POST /api/stages/intake` | `app/intake/service.py` | `tests/test_intake.py` |
| M2 范围裁切 | 检查领域约束 | `POST /api/stages/prepare` | `app/modules/prepare.py` | `tests/test_prepare.py` |
| M3 覆盖归并 | 查看业务计算结果 | `POST /api/stages/calculate` | `app/modules/calculate.py` | `tests/test_calculate.py` |
| M4 缺口验收 | 查看签收判定 | `POST /api/stages/policy` | `app/modules/policy.py` | `tests/test_policy.py` |
| M5 运行对账 | 对照输入、采信和隔离行 | `POST /api/stages/balance` | `app/modules/reconcile.py` | `tests/test_reconcile.py` |
| M6 批次复核 | 执行批次并签发、代理交付或暂缓 | `POST /api/runs、PATCH /api/runs/<id>` | `app/review/service.py` | `tests/test_review.py` |
| M7 证据交付 | 下载复核清单 | `GET /api/runs/<id>/evidence` | `app/evidence/render.py` | `tests/test_evidence.py` |
| M8 分辨率分层 | 区分低分辨率代理与全分辨率正式覆盖 | `calculate`、`policy`、`balance` | `app/modules/prepare.py`、`app/modules/calculate.py`、`app/modules/policy.py` | `tests/test_proxy.py` |
| M9 交付口径 | 先交代理或等全精度 | `balance.delivery`、`PATCH` 状态 | `app/modules/reconcile.py`、`app/review/service.py` | `tests/test_delivery.py` |

## 输入陷阱

| 编号 | 规则 | 处理 | 测试 |
|---|---|---|---|
| TRAP-02 | 去除 BOM | `app/intake/reader.py` | `tests/test_intake.py::test_bom_preserves_identifier` |
| TRAP-03 | 按逻辑记录读取引号内换行 | `app/intake/reader.py` | `tests/test_intake.py::test_quoted_newline_is_one_logical_record` |
| TRAP-04 | 重复表头计入忽略行 | `app/intake/service.py` | `tests/test_intake.py::test_repeated_header_is_counted` |
| TRAP-05 | 异常列数隔离 | `app/intake/schema.py` | `tests/test_intake.py::test_extra_column_is_isolated` |
| TRAP-06 | 归一化全角数字和千分位 | `app/intake/numeric.py` | `tests/test_intake.py::test_full_width_and_grouping_are_canonical` |
| TRAP-07 | 空值行隔离 | `app/intake/numeric.py` | `tests/test_intake.py::test_sentinel_keeps_row_out_of_total` |
| TRAP-08 | 记录键保留前导零 | `app/intake/schema.py` | `tests/test_intake.py::test_bom_preserves_identifier` |
| TRAP-14 | 冲突版本都进入隔离 | `app/intake/resolve.py` | `tests/test_intake.py::test_duplicate_conflict_removes_both_copies` |
| TRAP-16 | 引号未闭合时拒收文件 | `app/intake/reader.py` | `tests/test_intake.py::test_unclosed_quote_invalidates_source` |
| TRAP-18 | 区分空文件、全空白和仅表头 | `app/intake/reader.py` | `tests/test_intake.py::test_empty_states_have_distinct_causes` |
| TRAP-26 | 拒绝旧版本复核 | `app/review/store.py` | `tests/test_review.py::test_review_optimistic_lock` |
| TRAP-27 | 低分辨率预览不计入正式覆盖 | `app/modules/calculate.py`、`app/modules/policy.py` | `tests/test_proxy.py::test_low_resolution_preview_is_not_formal_coverage` |
| TRAP-28 | 重叠瓦片同一像元只计一次 | `app/modules/calculate.py` | `tests/test_proxy.py::test_overlapping_proxy_and_formal_do_not_double_count` |
| TRAP-29 | 越出作业区面积不进入覆盖账 | `app/modules/prepare.py` | `tests/test_proxy.py::test_outside_region_area_never_enters_coverage` |
| TRAP-30 | 行账或像元账不对平挡住签发 | `app/modules/reconcile.py` | `tests/test_delivery.py::test_pixel_ledger_break_blocks_release` |
| TRAP-31 | 同来源重跑不得覆盖已签结论 | `app/review/service.py` | `tests/test_delivery.py::test_proxy_delivery_is_terminal_for_same_source` |

## 领域反例

瓦片为整数网格上的左闭右开矩形。扫过相邻 X 边界，按 Y 区间并集求有效像元。输入重叠多计量与真实缺口独立提供。

同一像元被多块瓦片覆盖只计一次，越出作业区的面积不进入覆盖账；正式验收只认 `tile`，
`preview` 仅够临时代理。行账（来源、采信、隔离、已覆盖）与像元账任一不对平都挡住签发。

逐组预期结论见 `tests/test_policy.py`，计算过程证据见 `tests/test_calculate.py`，分辨率分层见 `tests/test_proxy.py`，交付口径与对账见 `tests/test_delivery.py`。
