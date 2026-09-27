import json
from datetime import datetime

class JSONAutomation:
    """JSON 文件自動化處理類"""
    def __init__(self):
        self.data = None

    def read_json(self, filepath):
        """讀取 JSON 文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        return self.data

    def write_json(self, filepath, data=None, indent=2):
        """寫入 JSON 文件（美化格式）"""
        write_data = data if data is not None else self.data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(write_data, f, ensure_ascii=False, indent=indent)
        print(f"JSON 已保存: {filepath}")

    def update_json(self, filepath, update_func):
        """讀取、修改並保存 JSON"""
        data = self.read_json(filepath)
        updated_data = update_func(data)
        self.write_json(filepath, updated_data)
        return updated_data

    def json_to_csv(self, json_file, csv_file):
        """將 JSON 轉換為 CSV，展開嵌套字典（list不會自動拆行）"""
        data = self.read_json(json_file)
        if not isinstance(data, list):
            print("警告：JSON root 不是 list，跳過CSV輸出")
            return
        if len(data) == 0:
            print("警告：JSON array 是空的")
            return

        import csv
        flat_data = []
        for item in data:
            flat_data.append(self._flatten_dict(item))

        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
            writer.writeheader()
            writer.writerows(flat_data)
        print(f"已轉換為 CSV: {csv_file}")

    def _flatten_dict(self, d, parent_key='', sep='_'):
        """扁平化嵌套字典，list保持原值不展開"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def merge_json_files(self, file_list, output_file):
        """合併多個 JSON 文件"""
        merged = []
        temp_data = None
        for file_path in file_list:
            temp_data = self.read_json(file_path)
            if isinstance(temp_data, list):
                merged.extend(temp_data)
            else:
                merged.append(temp_data)
        self.write_json(output_file, merged)
        print(f"已合併 {len(file_list)} 個文件")

    def validate_json_schema(self, filepath, schema):
        """驗證 JSON 是否符合 Schema"""
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            print("請安裝 jsonschema: pip install jsonschema")
            return None
        try:
            data = self.read_json(filepath)
            validate(instance=data, schema=schema)
            print(f"JSON 驗證通過: {filepath}")
            return True
        except ValidationError as e:
            print(f"JSON 驗證失敗: {e.message}")
            return False
        except json.JSONDecodeError:
            print(f"文件 {filepath} JSON格式錯誤，無法解析")
            return False

    def search_json(self, data, key, value=None):
        """在 JSON 數據中搜索特定鍵或鍵值對"""
        results = []
        def _search(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if k == key:
                        if value is None or v == value:
                            results.append({
                                'path': current_path,
                                'value': v,
                                'parent': obj
                            })
                    if isinstance(v, (dict, list)):
                        _search(v, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    _search(item, current_path)
        _search(data)
        return results

# 使用示例
if __name__ == "__main__":
    json_auto = JSONAutomation()
    # 讀取配置
    config = json_auto.read_json("config.json")
    print(f"數據庫主機: {config['database']['host']}")
    # 更新配置
    def update_config(cfg):
        cfg['database']['port'] = 3307
        cfg['version'] = '2.0'
        cfg['last_updated'] = datetime.now().isoformat()
        return cfg
    json_auto.update_json("config.json", update_config)
    # 嵌套 JSON 轉 CSV
    nested_data = [
        {
            "user": {
                "name": "張三",
                "contact": {
                    "email": "zhang@example.com",
                    "phone": "91234567"
                }
            },
            "orders": [
                {"id": "001", "amount": 100},
                {"id": "002", "amount": 200}
            ]
        }
    ]
    json_auto.write_json("nested_data.json", nested_data)
    json_auto.json_to_csv("nested_data.json", "flattened_data.csv")
    # 搜索 JSON
    results = json_auto.search_json(config, "host")
    print(f"找到 {len(results)} 個 'host' 鍵")
