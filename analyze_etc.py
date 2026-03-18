#!/usr/bin/env python3
"""分析 ETC 记录中同一起止站点出现不同收费金额的情况。"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


DEFAULT_INPUT = Path("ETC.csv")
DEFAULT_OUTPUT = Path("ETC_起止站点差异收费汇总.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "统计每个起止站点的收费情况，输出起止站点相同但收费金额不同的汇总结果。"
        )
    )
    parser.add_argument("-i", "--input", type=Path, default=DEFAULT_INPUT, help="输入 CSV 文件路径")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT, help="输出 CSV 文件路径")
    return parser.parse_args()


def format_amount(amount: Decimal) -> str:
    return f"{amount:.2f}"


def main() -> None:
    args = parse_args()

    grouped: dict[str, Counter[Decimal]] = defaultdict(Counter)

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required_columns = {"起止站点", "金额"}
        if not required_columns.issubset(reader.fieldnames or []):
            missing = required_columns.difference(reader.fieldnames or [])
            raise ValueError(f"输入文件缺少必要列: {', '.join(sorted(missing))}")

        for row in reader:
            route = (row.get("起止站点") or "").strip()
            amount_raw = (row.get("金额") or "").strip()
            if not route or not amount_raw:
                continue

            try:
                amount = Decimal(amount_raw)
            except InvalidOperation:
                continue

            grouped[route][amount] += 1

    inconsistent_routes = {
        route: counts for route, counts in grouped.items() if len(counts) > 1
    }

    if not inconsistent_routes:
        with args.output.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["起止站点", "最低收费", "总记录数", "不同收费数"])
        print(
            f"分析完成：共读取 {sum(sum(c.values()) for c in grouped.values())} 条记录，"
            "未发现起止站点相同但收费金额不同的记录。"
        )
        print(f"输出文件：{args.output}")
        return

    max_price_levels = max((len(counts) for counts in inconsistent_routes.values()), default=0)

    header = ["起止站点", "最低收费", "总记录数", "不同收费数"]
    for index in range(1, max_price_levels + 1):
        header.extend([f"价格{index}", f"价格{index}条数", f"价格{index}较最低差额"])

    rows: list[list[str]] = []
    for route, counts in sorted(inconsistent_routes.items()):
        sorted_prices = sorted(counts.items(), key=lambda x: x[0])
        min_price = sorted_prices[0][0]
        total_count = sum(counts.values())

        row = [
            route,
            format_amount(min_price),
            str(total_count),
            str(len(sorted_prices)),
        ]

        for price, count in sorted_prices:
            delta = price - min_price
            row.extend([
                format_amount(price),
                str(count),
                format_amount(delta),
            ])

        missing_columns = (max_price_levels - len(sorted_prices)) * 3
        if missing_columns:
            row.extend([""] * missing_columns)

        rows.append(row)

    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(
        f"分析完成：共读取 {sum(sum(c.values()) for c in grouped.values())} 条记录，"
        f"发现 {len(rows)} 个起止站点存在不同收费金额。"
    )
    print(f"输出文件：{args.output}")


if __name__ == "__main__":
    main()
