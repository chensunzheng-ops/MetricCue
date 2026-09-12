# 合成公众号内容运营案例

这是一个完全虚构的微信公众号风格案例，不包含真实账号、用户或业务数据，也不复现任何个人账号的实际指标。

案例模拟一个游戏内容账号最近七天的阅读量与互动率下降。数据中刻意加入了三类可核验信号：动画资讯内容自身表现走弱、近期内容结构更偏向动画资讯，以及审核等待时间变长。它们都是观察性关联，不代表已经证明因果关系。

## 运行

```bash
python examples/synthetic_wechat/generate.py
metriccue analyze examples/synthetic_wechat/performance.csv --content examples/synthetic_wechat/content.csv --production examples/synthetic_wechat/production.csv --config examples/synthetic_wechat/metriccue.yaml --as-of 2026-09-12 --output runs
```

运行后打开时间戳目录中的 `report.md`，并用 `evidence.json` 核验报告里的 `finding_id`。

## 适合演示的问题

> 最近一周互动率为什么下降？请区分事实、信号和假设，并提出一个下周可以执行的实验。

合理结论应同时提到总体指标变化、内容主题信号和审核周期信号，但不得直接声称审核变慢或选题结构变化导致了互动率下降。
