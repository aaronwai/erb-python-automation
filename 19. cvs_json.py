import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import numpy as np

class DataTransformPipeline:
    """數據轉換管道類"""
    def __init__(self):
        self.transform_log = []

    def csv_to_json_pipeline(self, csv_file, json_file, transformations=None):
        self.transform_log.clear()
        # 讀取 CSV
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        self.transform_log.append(f"讀取 CSV: {len(df)} 行")
        # 應用轉換
        if transformations:
            for transform in transformations:
                df = transform(df)
                self.transform_log.append(f"應用轉換: {transform.__name__}")

        # Convert datetime64 / Timestamp to ISO string for JSON serialization
        for col in df.select_dtypes(include=["datetime64"]).columns:
            df[col] = df[col].dt.isoformat()

        records = df.to_dict(orient='records')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        self.transform_log.append(f"保存 JSON: {json_file}")
        return records

    def json_to_excel_pipeline(self, json_file, excel_file, sheet_name='Data'):
        try:
            import openpyxl
        except ImportError:
            raise ImportError("請安裝 openpyxl: pip install openpyxl")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)

        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            # Optimized column width calculation
            for col_idx, col_name in enumerate(df.columns):
                col_data = df[col_name].astype(str).fillna("")
                max_len = col_data.str.len().max()
                adjusted_width = min(max_len + 2, 50)
                col_letter = worksheet.cell(row=1, column=col_idx+1).column_letter
                worksheet.column_dimensions[col_letter].width = adjusted_width

        self.transform_log.append(f"保存 Excel: {excel_file}")
        return df

    def create_data_report(self, source_file, output_dir="reports"):
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if source_file.endswith('.csv'):
            df = pd.read_csv(source_file, encoding='utf-8-sig')
        elif source_file.endswith('.json'):
            with open(source_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        else:
            raise ValueError("不支援的文件格式")

        report_file = output_path / f"data_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("數據分析報告\n")
            f.write("=" * 60 + "\n")
            f.write(f"數據源: {source_file}\n")
            f.write(f"生成時間: {datetime.now().isoformat()}\n")
            f.write(f"總記錄數: {len(df)}\n")
            f.write(f"總欄位數: {len(df.columns)}\n\n")
            f.write("欄位信息:\n")
            for col in df.columns:
                f.write(f"  - {col}: {df[col].dtype}\n")
            f.write("\n數值統計:\n")
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                f.write(df[numeric_cols].describe().to_string())

            f.write("\n\n類別統計:\n")
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                f.write(f"\n{col} - 唯一值: {df[col].nunique()}\n")
                vc = df[col].value_counts().head(5)
                if not vc.empty:
                    f.write(vc.to_string())
                f.write("\n")
        print(f"報告已生成: {report_file}")
        return report_file

# 使用示例
if __name__ == "__main__":
    pipeline = DataTransformPipeline()

    def clean_data(df):
        """清洗數據"""
        df = df.dropna(subset=['name', 'email'])
        # Keep NaN instead of "nan" string
        df['phone'] = df['phone'].apply(lambda x: "" if pd.isna(x) else str(x))
        df['phone'] = df['phone'].str.replace(r'\D', '', regex=True)
        return df

    def enrich_data(df):
        """豐富數據"""
        if "created_date" not in df.columns:
            print("警告：缺少 created_date 欄位，跳過日期轉換")
            return df
        df['created_date'] = pd.to_datetime(df['created_date'], errors="coerce")
        df['year'] = df['created_date'].dt.year
        df['month'] = df['created_date'].dt.month
        # Handle email without @
        df['domain'] = df['email'].str.split('@').str[1]
        return df

    try:
        pipeline.csv_to_json_pipeline(
            "customers.csv",
            "customers_transformed.json",
            transformations=[clean_data, enrich_data]
        )
        pipeline.create_data_report("customers_transformed.json")
    except FileNotFoundError:
        print("錯誤：找不到 customers.csv")
    except Exception as e:
        print(f"管道執行異常: {e}")
