"""
ETC收费记录分析脚本

分析ETC.csv中的车辆通行记录，找出起止站点相同但收费金额不同的记录，
并将相同起止站点的记录汇总到一条记录中，显示每个不同价格、对应记录数、
以及与最低收费标准的差额。
"""

import csv
from collections import defaultdict, Counter


def analyze_etc(input_file="ETC.csv", output_file="ETC_分析结果.csv"):
    """
    分析ETC收费记录，找出起止站点相同但收费金额不同的路线并生成汇总报告。

    参数:
        input_file: 输入CSV文件路径，需包含"起止站点"和"金额"列
        output_file: 输出CSV文件路径
    """
    # 读取所有记录，按起止站点分组
    routes = defaultdict(list)
    with open(input_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required_cols = {"起止站点", "金额"}
        if not required_cols.issubset(reader.fieldnames or []):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"CSV文件缺少必需的列: {missing}")
        for line_num, row in enumerate(reader, start=2):
            route = row["起止站点"]
            try:
                amount = float(row["金额"])
            except ValueError:
                raise ValueError(
                    f"第{line_num}行金额数据无效: '{row['金额']}'"
                )
            routes[route].append(amount)

    # 筛选出有不同金额的起止站点
    diff_routes = {}
    for route, amounts in routes.items():
        unique_amounts = sorted(set(amounts))
        if len(unique_amounts) > 1:
            diff_routes[route] = amounts

    if not diff_routes:
        print("未发现起止站点相同但金额不同的路线。")
        return

    # 找出最大不同价格数量，用于确定列数
    max_prices = max(len(set(amounts)) for amounts in diff_routes.values())

    # 构建表头
    header = ["起止站点", "总记录数"]
    for i in range(1, max_prices + 1):
        header.append(f"价格{i}")
        header.append(f"价格{i}记录数")
        header.append(f"价格{i}与最低价差额")

    # 生成汇总数据
    rows = []
    for route in sorted(diff_routes.keys()):
        amounts = diff_routes[route]
        counter = Counter(amounts)
        unique_amounts = sorted(counter.keys())
        min_amount = unique_amounts[0]
        total_records = len(amounts)

        row = [route, total_records]
        for i in range(max_prices):
            if i < len(unique_amounts):
                price = unique_amounts[i]
                count = counter[price]
                diff = round(price - min_amount, 2)
                row.append(price)
                row.append(count)
                row.append(diff)
            else:
                row.append("")
                row.append("")
                row.append("")
        rows.append(row)

    # 写入输出CSV
    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"分析完成！共发现 {len(diff_routes)} 条起止站点相同但金额不同的路线。")
    print(f"结果已保存到: {output_file}")


if __name__ == "__main__":
    analyze_etc()
