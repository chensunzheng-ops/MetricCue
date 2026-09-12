# MetricCue

[English](README.en.md)

MetricCue 是一个本地优先、证据优先的内容运营诊断工具。它把平台导出的 CSV 转成可追溯的问题信号、数据质量提示和 Markdown/SVG 报告，让“指标为什么变了”先回到可核验的证据，再进入假设与实验。

```text
performance.csv + content.csv + production.csv + metriccue.yaml
                              │
                     validate → analyze
                              │
       manifest + validation + evidence + report + SVG charts
```

当前版本为 `v0.1.0-rc1`。仓库示例使用完全合成的数据，包含指标下滑、累计计数器重置、缺失分群字段、异常值和审核等待变长等刻意植入的情况。

## 三步开始

需要 Python 3.11–3.13。Windows PowerShell 与 Ubuntu 均作为 CI 目标。

```bash
python -m pip install -e ".[dev]"
metriccue validate examples/synthetic_xhs/performance.csv --config examples/synthetic_xhs/metriccue.yaml --json
metriccue analyze examples/synthetic_xhs/performance.csv --content examples/synthetic_xhs/content.csv --production examples/synthetic_xhs/production.csv --config examples/synthetic_xhs/metriccue.yaml --output runs
```

命令会打印本次运行目录。打开其中的 `report.md` 查看摘要；`evidence.json` 是结构化证据源，每条数值信号都有稳定的 `finding_id`。也可以运行 `metriccue init`、`metriccue findings` 和 `metriccue report` 创建模板或检查已有运行。

`validate` 遇到阻断问题返回退出码 3；`analyze` 遇到阻断问题返回 3，没有达到阈值的发现时返回 4；报告生成失败返回 5。已有模板不会被 `init` 覆盖。

## 输出与边界

每次分析写入不可变的时间戳目录：

- `manifest.json`：版本、输入哈希、配置哈希、数据日期和启用模块。
- `validation.json`：错误、警告、受影响行号和修复建议。
- `evidence.json`：事实或信号、窗口值、变化、样本量、置信度和限制。
- `recommendations.json`：当前 RC 保留的结构化推荐接口。
- `report.md` 与 `charts/*.svg`：便于阅读和分享的聚合报告。

MetricCue 不支持登录或抓取平台、不替代数据仓库、不自动发布/投放/删除内容、不把观察性关联写成因果结论，也不提供虚构的行业基准。分群比较和构成分解目前提供 Python 分析原语，尚未接入 CLI 报告主流程。它不会承诺节省多少时间；该结论要等真实用户测试后再衡量。

所有计算默认在本机完成。请不要提交真实客户数据、密钥、手机号、邮箱或可识别个人的信息。发现疑似敏感列时，本地校验会警告，任何模型交接都应停止，直到字段被删除或匿名化。详见[隐私说明](docs/privacy.md)。

## 方法和扩展

- [数据契约](docs/data-contract.md)
- [诊断方法与限制](docs/methodology.md)
- [贡献指南](docs/contributing.md)
- [用户测试协议](docs/user-test-protocol.md)
- [Codex Skill](skills/metriccue/SKILL.md)
- [合成示例](examples/synthetic_xhs/README.md)

代码以 MIT 许可证发布。RC 阶段欢迎提交匿名化的缺陷、平台字段映射和诊断规则建议。
