#!/usr/bin/env python3
"""Read result.csv from CloudflareSpeedTest and write report.md + top5.json.

result.csv columns (XIU2/CloudflareSpeedTest):
IP 地址,已发送,已接收,丢包率,平均延迟,下载速度(MB/s),地区码
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HEADER_MAP = {
    "IP 地址": "ip",
    "IP": "ip",
    "已发送": "sent",
    "已接收": "received",
    "丢包率": "loss",
    "平均延迟": "latency_ms",
    "下载速度(MB/s)": "download_mbps",
    "下载速度": "download_mbps",
    "地区码": "region",
}


def to_float(value, default=0.0):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def main():
    csv_path = ROOT / "result.csv"
    rows = []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {}
            for key, value in raw.items():
                if key is None:
                    continue
                name = HEADER_MAP.get(key.strip(), key.strip())
                row[name] = value.strip() if isinstance(value, str) else value
            if not row.get("ip"):
                continue
            rows.append(
                {
                    "ip": row["ip"],
                    "latency_ms": to_float(row.get("latency_ms")),
                    "loss": to_float(row.get("loss")),
                    "download_mbps": to_float(row.get("download_mbps")),
                    "region": row.get("region") or "N/A",
                }
            )

    top5 = rows[:5]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    data = {
        "generated_at": generated_at,
        "location": "GitHub Actions",
        "regions": ["HKG", "SIN", "NRT", "KIX"],
        "mode": "HTTPing",
        "count": len(top5),
        "top5": [
            {"rank": i + 1, **item} for i, item in enumerate(top5)
        ],
    }
    (ROOT / "top5.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Cloudflare 优选 IP 测速报告",
        "",
        f"- 测速时间：{generated_at}",
        "- 测速位置：GitHub Actions",
        "- 测速模式：HTTPing，地区 HKG、SIN、NRT、KIX",
        "- 说明：这是 GitHub Runner 到 Cloudflare 的延迟，不是家里宽带的延迟；家里真实结果以路由器每天 05:00 的测速为准。",
        "",
        "| 排名 | IP | 平均延迟 (ms) | 丢包率 | 下载速度 (MB/s) | 地区 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in data["top5"]:
        lines.append(
            f"| {item['rank']} | {item['ip']} | {item['latency_ms']} | {item['loss']} | {item['download_mbps']} | {item['region']} |"
        )
    if not top5:
        lines.append("")
        lines.append("本次没有符合条件的 IP（result.csv 为空或全部被过滤）。")
    lines.append("")
    lines.append("完整结果见 result.csv。")
    (ROOT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote report.md and top5.json with {len(top5)} IPs.")


if __name__ == "__main__":
    main()
