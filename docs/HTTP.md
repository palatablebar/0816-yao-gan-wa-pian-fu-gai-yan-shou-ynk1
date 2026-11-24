# 阶段接口

`POST /api/stages/<stage>` 接收 `multipart/form-data`。字段 `sample=dirty`、`sample=clean`、`sample=deadline` 或 `file=<CSV>` 四选一。阶段为 `intake`、`prepare`、`calculate`、`policy`、`balance`。预览不入库。

`POST /api/runs` 接收同样的输入，执行全批并返回运行报告。同一来源重跑返回同一批次，不覆盖已存结论。`GET /api/runs` 返回最近 50 批。`GET /api/runs/<id>` 查询一批和当前复核状态。

`PATCH /api/runs/<id>` 接收 `revision`、`status` 和 `note`。状态使用：

- `APPROVED`：正式签发，仅在 `balance.releasable` 为真时允许（全分辨率覆盖达标）。
- `PROVISIONAL`：临时代理交付，仅在 `balance.proxy_releasable` 为真时允许（低分辨率预览补齐）。
- `HELD`：暂缓。

`APPROVED` 与 `PROVISIONAL` 都是终态；同一来源重跑不覆盖已签结论，再次复核返回 409
`RUN_FINALIZED`。冲突返回 409，客户端读取新版本后重试。签发失败保留旧版本与证据，批次不变。

运行报告中的交付口径见 `balance.delivery.choice`：

- `SIGN_FULL`：全分辨率齐备，可一次正式签发。
- `DELIVER_PROXY`：部分分组只有低分辨率预览，可先交临时代理，正式签发待全分辨率瓦片齐备。
- `HOLD`：存在未达最低覆盖或待处理差异，暂不能交付。

`balance.blocks` 列出挡住签发的具体项（行账、像元账、隔离行、待处理分组）。

`GET /api/runs/<id>/evidence` 下载内含运行清单、行号隔离、行账与像元账对账、交付口径、
业务证据和复核信息的 JSON。
