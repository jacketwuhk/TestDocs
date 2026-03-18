"""
ETC通行记录详情展开脚本
基于ETC_analysis.csv中已识别的差价路线，从ETC.csv中提取每一条价格差异记录，
生成清晰易懂、可供下载的ETC_details.csv。

输出列说明：
  序号            - 行序号
  起止站点        - 收费路线（起始站-终点站）
  编号            - 原始通行记录编号
  通行时间        - 通行日期时间
  车牌号          - 车辆牌照
  金额（元）      - 实际收费金额
  该路线最低收费  - 该路线在数据集中出现的最低金额
  与最低收费差额  - 实际金额 - 最低收费（0 表示最低价）
"""

import csv
import os
from collections import defaultdict

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "ETC.csv")
analysis_file = os.path.join(script_dir, "ETC_analysis.csv")
output_file = os.path.join(script_dir, "ETC_details.csv")

# 从 ETC_analysis.csv 读取有价格差异的起止站点集合
varied_routes: set[str] = set()
with open(analysis_file, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        varied_routes.add(row["起止站点"])

# 从 ETC.csv 读取原始记录，按起止站点分组
route_records: dict[str, list[dict]] = defaultdict(list)
with open(input_file, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["起止站点"] in varied_routes:
            route_records[row["起止站点"]].append(row)

# 构造展开后的详情行
output_header = ["序号", "起止站点", "编号", "通行时间", "车牌号", "金额（元）", "该路线最低收费", "与最低收费差额"]
detail_rows = []
seq = 1

for route in sorted(route_records.keys()):
    records = route_records[route]
    min_price = min(float(r["金额"]) for r in records)
    # 按金额升序、再按通行时间排序，让差价情况一目了然
    records_sorted = sorted(records, key=lambda r: (float(r["金额"]), r["通行时间"]))
    for r in records_sorted:
        amount = float(r["金额"])
        diff = round(amount - min_price, 2)
        detail_rows.append({
            "序号": seq,
            "起止站点": route,
            "编号": r["编号"],
            "通行时间": r["通行时间"],
            "车牌号": r["车牌号"],
            "金额（元）": amount,
            "该路线最低收费": min_price,
            "与最低收费差额": diff,
        })
        seq += 1

with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=output_header)
    writer.writeheader()
    writer.writerows(detail_rows)

print(f"展开完成：共 {len(varied_routes)} 条差价路线，{len(detail_rows)} 条详情记录")
print(f"输出文件：{output_file}")
print(f"\n前15条详情预览：")
print(",".join(output_header))
for row in detail_rows[:15]:
    print(",".join(str(row[h]) for h in output_header))
