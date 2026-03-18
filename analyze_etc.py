from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path


def format_amount(amount: Decimal) -> str:
    return format(amount.quantize(Decimal("0.00")), "f")


def build_summary_rows(source_path: Path) -> tuple[list[dict[str, str]], int]:
    route_amounts: dict[str, Counter[Decimal]] = defaultdict(Counter)

    with source_path.open("r", encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        for row in reader:
            route_amounts[row["起止站点"]][Decimal(row["金额"])] += 1

    varying_routes = {
        route: amounts
        for route, amounts in route_amounts.items()
        if len(amounts) > 1
    }
    max_amount_count = max((len(amounts) for amounts in varying_routes.values()), default=0)

    rows: list[dict[str, str]] = []
    for route in sorted(varying_routes):
        amounts = varying_routes[route]
        sorted_amounts = sorted(amounts)
        minimum_amount = sorted_amounts[0]
        row = {
            "起止站点": route,
            "总记录数": str(sum(amounts.values())),
            "不同收费金额数": str(len(sorted_amounts)),
            "最低收费标准": format_amount(minimum_amount),
        }
        for index, amount in enumerate(sorted_amounts, start=1):
            row[f"收费金额{index}"] = format_amount(amount)
            row[f"该金额记录数{index}"] = str(amounts[amount])
            row[f"与最低收费差额{index}"] = format_amount(amount - minimum_amount)
        rows.append(row)

    return rows, max_amount_count


def write_summary(rows: list[dict[str, str]], max_amount_count: int, output_path: Path) -> None:
    fieldnames = ["起止站点", "总记录数", "不同收费金额数", "最低收费标准"]
    for index in range(1, max_amount_count + 1):
        fieldnames.extend(
            [f"收费金额{index}", f"该金额记录数{index}", f"与最低收费差额{index}"]
        )

    with output_path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="汇总 ETC 记录中起止站点相同但收费金额不同的记录。"
    )
    parser.add_argument(
        "--input",
        default="ETC.csv",
        help="原始 ETC CSV 文件路径，默认值为 ETC.csv。",
    )
    parser.add_argument(
        "--output",
        default="ETC_起止站点差异收费汇总.csv",
        help="分析结果 CSV 文件路径。",
    )
    args = parser.parse_args()

    rows, max_amount_count = build_summary_rows(Path(args.input))
    write_summary(rows, max_amount_count, Path(args.output))
    print(f"已输出 {len(rows)} 条起止站点相同但收费金额不同的汇总记录到 {args.output}")


if __name__ == "__main__":
    main()
