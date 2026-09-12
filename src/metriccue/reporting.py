import json
from pathlib import Path
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metriccue.models import Finding, ValidationIssue


def render_markdown(
    findings: list[Finding], issues: list[ValidationIssue], metadata: dict[str, Any]
) -> str:
    del metadata
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
    for heading in ("异常贡献", "内容洞察", "生产效率", "实验建议", "局限性"):
        lines.extend([f"## {heading}", "", "本次运行暂无更多可报告内容。", ""])
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
    report = run_dir / "report.md"
    report.write_text(render_markdown(findings, issues, {}), encoding="utf-8")
    _write_change_chart(findings, run_dir / "charts")
    return report
