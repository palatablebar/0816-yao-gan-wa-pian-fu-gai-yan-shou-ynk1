# 遥感瓦片覆盖验收

地理数据交付工程师可在工作台上传来源 CSV，对照规则判断差异，签发合格批次或记录暂缓意见。

按栅格坐标计算矩形瓦片并集和交叠，排除边界外面积。正式验收只采信全分辨率瓦片；低分辨率预览只够做临时代理交付，工作台据此给出先交代理还是等全精度后再签的建议，并逐项对平来源行、采信行、隔离行与已覆盖像元。

## 启动

```sh
docker compose up --build -d --wait
```

打开 <http://localhost:18310>。页面预览带异常样例。选中阶段查看计算证据，选择可签发样例并执行批次，然后提交复核意见。

## 核验

```sh
docker compose exec -T app pytest -q
```

[输入字段](docs/DATA-DICTIONARY.md) · [阶段接口](docs/HTTP.md) · [操作步骤](docs/OPERATIONS.md) · [规则与测试](docs/DEPTH.md)
