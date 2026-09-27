import pandas as pd
import numpy as np
from pathlib import Path

class PandasAutomation:
    """Pandas 自動化數據處理類"""
    def __init__(self):
        self.df = None

    def load_data(self, filepath, **kwargs):
        """智能載入各類數據，含 .sql 與格式錯誤處理"""
        path = Path(filepath)
        ext = path.suffix.lower()
        try:
            if ext == '.csv':
                self.df = pd.read_csv(filepath, **kwargs)
            elif ext in ['.xlsx', '.xls']:
                self.df = pd.read_excel(filepath, **kwargs)
            elif ext == '.json':
                self.df = pd.read_json(filepath, **kwargs)
            elif ext == '.parquet':
                self.df = pd.read_parquet(filepath, **kwargs)
            elif ext == '.sql':
                import sqlite3
                db_path = kwargs.pop('db_path', 'database.db')
                conn = sqlite3.connect(db_path)
                try:
                    with open(filepath, 'r', encoding=kwargs.get('encoding', 'utf-8')) as f:
                        query = f.read()      # ✅ 讀檔案內容當SQL
                    self.df = pd.read_sql(query, conn)
                finally:
                    conn.close()
            else:
                raise ValueError(f"不支援的文件格式: {ext}")
        except FileNotFoundError:
            print(f"錯誤：找不到檔案 {filepath}")
            return None
        except PermissionError:
            print(f"錯誤：沒有權限讀取 {filepath}")
            return None
        except (pd.errors.ParserError, ValueError) as e:
            print(f"錯誤：資料解析失敗 {str(e)}")
            return None
        except ImportError as e:
            print(f"錯誤：缺少套件 {str(e)}，請先 pip install")
            return None
        except Exception as e:
            print(f"載入失敗：{str(e)}")
            return None
        print(f"已載入數據: {len(self.df)} 行, {len(self.df.columns)} 列")
        return self.df

    def save_data(self, filepath, **kwargs):
        """保存數據到文件，含 .sql 分支"""
        if self.df is None:
            raise ValueError("沒有數據可保存")
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        ext = path.suffix.lower()
        try:
            if ext == '.csv':
                self.df.to_csv(filepath, index=False, encoding='utf-8-sig', **kwargs)
            elif ext == '.xlsx':
                self.df.to_excel(filepath, index=False, engine='openpyxl', **kwargs)
            elif ext == '.json':
                self.df.to_json(filepath, orient='records', force_ascii=False, **kwargs)
            elif ext == '.parquet':
                self.df.to_parquet(filepath, **kwargs)
            elif ext == '.sql':
                import sqlite3
                db_path = kwargs.pop('db_path', 'database.db')
                table = kwargs.pop('table', 'data')
                conn = sqlite3.connect(db_path)
                try:
                    self.df.to_sql(table, conn, if_exists='replace', index=False)
                finally:
                    conn.close()
            else:
                raise ValueError(f"不支援的文件格式: {ext}")
        except Exception as e:
            print(f"保存失敗：{str(e)}")
            return False
        print(f"數據已保存: {filepath}")
        return True

    def quick_profile(self):
        """快速數據概覽"""
        if self.df is None:
            return None
        profile = {
            'shape': self.df.shape,
            'columns': list(self.df.columns),
            'dtypes': self.df.dtypes.astype(str).to_dict(),
            'missing': self.df.isnull().sum().to_dict(),
            'missing_pct': (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
            'memory_usage': self.df.memory_usage(deep=True).sum(),
            'numeric_summary': {},
            'categorical_summary': {}
        }
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            s = self.df[col]
            profile['numeric_summary'][col] = {
                'mean': s.mean(), 'median': s.median(), 'std': s.std(),
                'min': s.min(), 'max': s.max(),
                'q25': s.quantile(0.25), 'q75': s.quantile(0.75)
            }
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            try:
                top = self.df[col].value_counts().head(5).to_dict()
            except TypeError:   # unhashable value
                top = {}
            profile['categorical_summary'][col] = {
                'unique': self.df[col].nunique(),
                'top_values': top
            }
        return profile

    @staticmethod
    def _fmt(value):
        """安全格式化數值，處理 NaN / None"""
        if value is None:
            return "N/A"
        try:
            if pd.isna(value):
                return "N/A"
            return f"{value:.2f}"
        except (TypeError, ValueError):
            return str(value)

    def generate_report(self, output_file="data_profile.txt"):
        """生成數據分析報告"""
        profile = self.quick_profile()
        if profile is None:
            print("沒有資料可分析")
            return None
        report = []
        report.append("=" * 60)
        report.append("數據分析報告")
        report.append("=" * 60)
        report.append(f"數據形狀: {profile['shape'][0]} 行 × {profile['shape'][1]} 列")
        report.append(f"內存佔用: {profile['memory_usage'] / 1024**2:.2f} MB")
        report.append(f"\n欄位列表:")
        for col, dtype in profile['dtypes'].items():
            missing = profile['missing'][col]
            missing_pct = profile['missing_pct'][col]
            report.append(f"  - {col}: {dtype} (缺失: {missing}, {missing_pct:.1f}%)")
        report.append(f"\n數值型欄位統計:")
        for col, stats in profile['numeric_summary'].items():
            report.append(f"  {col}:")
            for stat, value in stats.items():
                report.append(f"    {stat}: {self._fmt(value)}")
        report.append(f"\n類別型欄位統計:")
        for col, stats in profile['categorical_summary'].items():
            report.append(f"  {col}:")
            report.append(f"    唯一值: {stats['unique']}")
            report.append(f"    最常見:")
            for val, count in stats['top_values'].items():
                report.append(f"      {val}: {count}")
        report_text = "\n".join(report)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(report_text)
        return report_text

# 使用示例
if __name__ == "__main__":
    pa = PandasAutomation()
    # 載入數據
    pa.load_data("sales_data.csv")
    # 生成分析報告
    pa.generate_report("sales_profile.txt")
