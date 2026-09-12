import json
from pathlib import Path
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metriccue.models import Finding, ValidationIssue


def render_markdown(
    findings: list[Finding],
    issues: list[ValidationIssue],
    metadata: dict[str, Any],
    recommendations: list[dict[str, Any]] | None = None,
) -> str:
    lines = ["# MetricCue 诊断报告", "", "## 执行摘要", ""]
    if not findings:
        lines.append("当前数据不足以形成可靠诊断。请先查看数据健康部分并补充数据。")
    else:
        for finding in findings[:3]:
            lines.append(
                f"- `{finding.finding_id}`：{finding.metric} 从 {finding.baseline_value:g} 变化到 {finding.current_value:g}（{finding.relative_change:+.1%}，置信度：{finding.confidence.value}）。"
            )
    lines.extend(["", "## 数据健康", ""])
    lines.extend(
        [f"- [{issue.severity.value}] `{issue.code}`：{issue.message}" for issue in issues]
        or ["- 未发现已记录的数据质量问题。"]
    )
    lines.extend(["", "## 核心指标", ""])
    for finding in findings:
        lines.append(f"### {finding.metric} · `{finding.finding_id}`")
        lines.append("")
        lines.append(
            f"当前值：{finding.current_value:g}；基准值：{finding.baseline_value:g}；相对变化：{finding.relative_change:+.1%}。"
        )
        for evidence in finding.evidence:
            lines.append(f"- 证据：{evidence}")
        for limitation in finding.limitations:
            lines.append(f"- 局限：{limitation}")
        lines.append("")
    lines.extend(["## 异常贡献", ""])
    contributions = metadata.get("contribution_summaries", [])
    if contributions:
        for item in contributions:
            lines.append(
                f"- {item['dimension']} / {item['metric']}：within={item['within_effect']:.4g}，mix={item['mix_effect']:.4g}。"
            )
    else:
        lines.append("本次运行暂无可报告的合格分群贡献。")
    lines.extend(["", "## 内容洞察", ""])
    lifecycle = metadata.get("lifecycle_summary", [])
    if lifecycle:
        for item in lifecycle[:12]:
            lines.append(
                f"- Day {item['content_age_days']} / {item['metric']}：中位数 {item['median']:.4g}，样本 {item['count']}。"
            )
    else:
        lines.append("本次运行没有足够的内容生命周期数据。")
    lines.extend(["", "## 生产效率", ""])
    production = [
        item
        for item in findings
        if item.metric.endswith(("_hours", "_cost")) or item.metric == "revision_count"
    ]
    if production:
        for item in production:
            lines.append(
                f"- `{item.finding_id}`：{item.metric} 相对变化 {item.relative_change:+.1%}。"
            )
    else:
        lines.append("本次运行暂无生产效率信号。")
    lines.append("")
    lines.extend(["## 实验建议", ""])
    if recommendations:
        for item in recommendations:
            finding_ids = ", ".join(f"`{value}`" for value in item["finding_ids"])
            lines.append(f"- {item['hypothesis']} 证据：{finding_ids}")
    else:
        lines.append("本次运行暂无更多可报告内容。")
    lines.extend(["", "## 局限性", "", "所有信号仅表示观察性关联，不构成因果结论。", ""])
    return "\n".join(lines).rstrip() + "\n"


def _write_change_chart(findings: list[Finding], charts: Path) -> Path | None:
    usable = [item for item in findings if item.relative_change is not None]
    if not usable:
        return None
    charts.mkdir(parents=True, exist_ok=True)
    path = charts / "finding_changes.svg"
    figure, axis = plt.subplots(figsize=(8, max(3, len(usable) * 0.5)))
    axis.barh(
        [item.finding_id for item in usable],
        [cast(float, item.relative_change) * 100 for item in usable],
    )
    axis.axvline(0, color="black", linewidth=0.8)
    axis.set_xlabel("Relative change (%)")
    figure.tight_layout()
    figure.savefig(path, format="svg")
    plt.close(figure)
    return path


def write_report(run_dir: Path) -> Path:
    findings = [
        Finding.model_validate(item)
        for item in json.loads((run_dir / "evidence.json").read_text(encoding="utf-8"))
    ]
    issues = [
        ValidationIssue.model_validate(item)
        for item in json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
    ]
    recommendation_path = run_dir / "recommendations.json"
    recommendations: list[dict[str, Any]] = (
        json.loads(recommendation_path.read_text(encoding="utf-8"))
        if recommendation_path.exists()
        else []
    )
    manifest_path = run_dir / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    )
    report = run_dir / "report.md"
    report.write_text(
        render_markdown(findings, issues, manifest.get("metadata", {}), recommendations),
        encoding="utf-8",
    )
    _write_change_chart(findings, run_dir / "charts")
    return report
