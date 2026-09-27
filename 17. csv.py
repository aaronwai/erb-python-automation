import csv
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class Employee:
    """員工數據類"""
    id: int
    name: str
    department: str
    salary: float
    email: str

class CSVAutomation:
    """CSV 文件自動化處理類"""

    def __init__(self):
        self.data: List[Dict] = []

    def read_csv(self, filepath, encoding="utf-8-sig"):
        """讀取 CSV 文件"""
        with open(filepath, 'r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f)
            self.data = list(reader)
        print(f"已讀取 {len(self.data)} 筆記錄")
        return self.data

    def write_csv(self, filepath, data=None, fieldnames=None):
        """寫入 CSV 文件"""
        write_data = data or self.data

        if not write_data:
            print("無數據可寫入")
            return

        # 自動獲取欄位名
        if fieldnames is None:
            fieldnames = list(write_data[0].keys())

        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(write_data)

        print(f"數據已寫入: {filepath}")

    def append_to_csv(self, filepath, row_data, fieldnames):
        """追加數據到 CSV"""
        file_exists = Path(filepath).exists()

        with open(filepath, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row_data)

    def filter_csv(self, condition_func):
        """根據條件過濾數據"""
        return [row for row in self.data if condition_func(row)]

    def sort_csv(self, key_func, reverse=False):
        """排序 CSV 數據"""
        return sorted(self.data, key=key_func, reverse=reverse)

# 使用示例
if __name__ == "__main__":
    csv_auto = CSVAutomation()

    # 讀取員工數據
    csv_auto.read_csv("employees.csv")

    # 過濾高薪水員工
    high_earners = csv_auto.filter_csv(
        lambda x: float(x['salary']) > 50000
    )
    print(f"高薪員工: {len(high_earners)} 人")

    # 按部門排序
    sorted_data = csv_auto.sort_csv(
        key_func=lambda x: x['department']
    )

    # 保存過濾結果
    csv_auto.write_csv("high_earners.csv", high_earners)