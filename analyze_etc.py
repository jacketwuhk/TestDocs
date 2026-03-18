"""
ETC通行记录分析脚本
分析起止站点相同但收费金额不同的记录，汇总到一条记录中，
每个不同价格显示为独立列，包含数量及与最低收费标准的差额。
"""

import csv
import os
from collections import defaultdict

# 读取ETC.csv数据
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "ETC.csv")
output_file = os.path.join(script_dir, "ETC_analysis.csv")

data = []
with open(input_file, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["金额"] = float(row["金额"])
        data.append(row)

# 按起止站点分组，统计每个价格的出现次数
route_price_counts: dict[str, dict[float, int]] = defaultdict(lambda: defaultdict(int))
for record in data:
    route_price_counts[record["起止站点"]][record["金额"]] += 1

# 筛选出起止站点相同但收费金额不同的记录
varied_routes = {
    route: price_counts
    for route, price_counts in route_price_counts.items()
    if len(price_counts) > 1
}

# 求所有路线中最多有多少种不同价格
max_price_count = max((len(pc) for pc in varied_routes.values()), default=0)

# 构造输出列名
# 起止站点 | 记录总数 | 价格1 | 价格1数量 | 价格1与最低收费差额 | 价格2 | 价格2数量 | 价格2与最低收费差额 | ...
header = ["起止站点", "记录总数"]
for i in range(1, max_price_count + 1):
    header.append(f"价格{i}")
    header.append(f"价格{i}数量")
    header.append(f"价格{i}与最低收费差额")

# 按起止站点排序，写出结果
rows = []
for route in sorted(varied_routes.keys()):
    price_counts = varied_routes[route]
    prices = sorted(price_counts.keys())
    min_price = prices[0]
    total = sum(price_counts.values())

    row = {"起止站点": route, "记录总数": total}
    for i, price in enumerate(prices, start=1):
        count = price_counts[price]
        diff = round(price - min_price, 2)
        row[f"价格{i}"] = price
        row[f"价格{i}数量"] = count
        row[f"价格{i}与最低收费差额"] = diff

    rows.append(row)

with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

print(f"分析完成：共找到 {len(varied_routes)} 条起止站点相同但收费金额不同的汇总记录")
print(f"输出文件：{output_file}")
print(f"\n前10条汇总记录预览：")
for row in rows[:10]:
    print(f"  {row['起止站点']}: 总计{row['记录总数']}条", end="")
    i = 1
    while f"价格{i}" in row:
        print(
            f"  价格{i}={row[f'价格{i}']}({row[f'价格{i}数量']}条,+{row[f'价格{i}与最低收费差额']})",
            end="",
        )
        i += 1
    print()
