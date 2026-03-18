"""
ETC通行记录详情展开脚本
直接从 ETC.csv 全量数据中识别起止站点相同但收费金额不同的路线，
并只输出金额高于该路线最低收费的记录，生成清晰易懂、可供下载的 ETC_details.csv。

输出列说明：
  序号            - 行序号
  起止站点        - 收费路线（起始站-终点站）
  编号            - 原始通行记录编号
  通行时间        - 通行日期时间
  车牌号          - 车辆牌照
  金额（元）      - 实际收费金额（已高于该路线最低收费）
  该路线最低收费  - 该路线在全量数据中出现的最低金额
  与最低收费差额  - 实际金额 - 最低收费（均为正数）
"""

import csv
import os
from collections import defaultdict

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "ETC.csv")
output_file = os.path.join(script_dir, "ETC_details.csv")

# 第一遍：从 ETC.csv 全量数据中统计每条路线的所有价格及最低价
route_prices: dict[str, set[float]] = defaultdict(set)
route_min: dict[str, float] = {}

with open(input_file, "r", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        route_prices[row["起止站点"]].add(float(row["金额"]))

# 只保留有多种价格的路线，并记录其最低收费
varied_routes: set[str] = set()
for route, prices in route_prices.items():
    if len(prices) > 1:
        varied_routes.add(route)
        route_min[route] = min(prices)

# 第二遍：收集全量记录中属于差价路线、且金额高于最低收费的记录
output_header = ["序号", "起止站点", "编号", "通行时间", "车牌号", "金额（元）", "该路线最低收费", "与最低收费差额"]
route_records: dict[str, list[dict]] = defaultdict(list)

with open(input_file, "r", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        route = row["起止站点"]
        if route not in varied_routes:
            continue
        amount = float(row["金额"])
        min_price = route_min[route]
        diff = round(amount - min_price, 2)
        if diff > 0:  # 只保留高于最低收费的记录
            route_records[route].append({
                "起止站点": route,
                "编号": row["编号"],
                "通行时间": row["通行时间"],
                "车牌号": row["车牌号"],
                "金额（元）": amount,
                "该路线最低收费": min_price,
                "与最低收费差额": diff,
            })

# 按路线排序，同一路线内按差额降序、再按通行时间排序
detail_rows = []
seq = 1
for route in sorted(route_records.keys()):
    records_sorted = sorted(
        route_records[route],
        key=lambda r: (-r["与最低收费差额"], r["通行时间"]),
    )
    for r in records_sorted:
        r["序号"] = seq
        detail_rows.append(r)
        seq += 1

with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=output_header)
    writer.writeheader()
    writer.writerows(detail_rows)

print(f"分析完成：全量数据共 {len(route_prices)} 条路线，其中 {len(varied_routes)} 条存在价格差异")
print(f"输出：仅保留高于最低收费的 {len(detail_rows)} 条记录")
print(f"输出文件：{output_file}")
print(f"\n前15条详情预览：")
print(",".join(output_header))
for row in detail_rows[:15]:
    print(",".join(str(row[h]) for h in output_header))
