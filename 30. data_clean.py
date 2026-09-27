import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
import re


class DataCleaner:
    """數據清洗自動化類"""
    def __init__(self, df):
        self.df = df.copy()
        self.original_shape = df.shape          # ✅ 記錄原始形狀
        self.cleaning_log = []
        self.transformers = {}

    # ============================================
    # 缺失值處理
    # ============================================
    def remove_duplicates(self, subset=None, keep='first'):
        """移除重複行"""
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        removed = before - len(self.df)
        self.cleaning_log.append(f"移除重複行: {removed} 行")
        print(f"移除 {removed} 個重複行")
        return self

    def handle_missing_values(self, strategy='auto', fill_values=None):
        """
        處理缺失值
        Args:
            strategy: 'drop', 'mean', 'median', 'mode', 'fill', 'auto', 'knn'
        """
        missing_before = int(self.df.isnull().sum().sum())

        if strategy == 'drop':
            self.df = self.df.dropna()
            self.cleaning_log.append("刪除包含缺失值的行")

        elif strategy in ('mean', 'median', 'mode'):
            # ✅ 實作這三個宣告但未實作的策略
            for col in self.df.columns:
                if self.df[col].isnull().any():
                    if strategy == 'mean' and pd.api.types.is_numeric_dtype(self.df[col]):
                        fill_val = self.df[col].mean()
                    elif strategy == 'median' and pd.api.types.is_numeric_dtype(self.df[col]):
                        fill_val = self.df[col].median()
                    else:
                        mode = self.df[col].mode()
                        fill_val = mode[0] if not mode.empty else None
                    if fill_val is not None:
                        self.df[col] = self.df[col].fillna(fill_val)
                        self.cleaning_log.append(f"{col}: 使用 {strategy}({fill_val:.2f}) 填充")
                    else:
                        self.df[col] = self.df[col].fillna("Unknown")
                        self.cleaning_log.append(f"{col}: 無有效眾數，填充 Unknown")

        elif strategy == 'auto':
            for col in self.df.columns:
                if self.df[col].isnull().any():
                    missing_count = self.df[col].isnull().sum()
                    missing_pct = missing_count / len(self.df) * 100
                    if missing_pct > 50:
                        self.df = self.df.drop(col, axis=1)
                        self.cleaning_log.append(f"{col}: 缺失 {missing_pct:.1f}%，已刪除欄位")
                    elif pd.api.types.is_numeric_dtype(self.df[col]):
                        median = self.df[col].median()
                        self.df[col] = self.df[col].fillna(median)
                        self.cleaning_log.append(f"{col}: 中位數 {median:.2f} 填充 ({missing_count})")
                    else:
                        mode = self.df[col].mode()
                        if not mode.empty:
                            self.df[col] = self.df[col].fillna(mode[0])
                            self.cleaning_log.append(f"{col}: 眾數 {mode[0]} 填充 ({missing_count})")
                        else:
                            self.df[col] = self.df[col].fillna("Unknown")
                            self.cleaning_log.append(f"{col}: 填充 Unknown")

        elif strategy == 'knn':
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                imputer = KNNImputer(n_neighbors=5)
                self.df[numeric_cols] = imputer.fit_transform(self.df[numeric_cols])
                self.cleaning_log.append("使用 KNN 算法填充數值型缺失值")
            else:
                print("警告：無數值型欄位，KNN 填充跳過")

        elif strategy == 'fill':
            if fill_values is None:
                raise ValueError("strategy='fill' 時必須提供 fill_values")
            self.df = self.df.fillna(fill_values)
            self.cleaning_log.append(f"使用指定值填充: {fill_values}")

        else:
            raise ValueError(f"不支援的缺失值策略: {strategy}")

        missing_after = int(self.df.isnull().sum().sum())
        print(f"缺失值處理完成: {missing_before} -> {missing_after}")
        return self

    # ============================================
    # 文本清洗
    # ============================================
    def standardize_text(self, columns=None, operations=None):
        """標準化文本數據"""
        if operations is None:
            operations = ['strip', 'remove_extra_spaces']
        text_cols = list(columns) if columns else list(self.df.select_dtypes(include=['object']).columns)
        # ✅ 先記下原本的 NaN 位置，避免 astype(str) 後難還原
        nan_mask_cache = {}
        for col in text_cols:
            if col not in self.df.columns:
                continue
            nan_mask_cache[col] = self.df[col].isna()
            self.df[col] = self.df[col].astype(str)
            for op in operations:
                if op == 'strip':
                    self.df[col] = self.df[col].str.strip()
                elif op == 'lower':
                    self.df[col] = self.df[col].str.lower()
                elif op == 'upper':
                    self.df[col] = self.df[col].str.upper()
                elif op == 'remove_extra_spaces':
                    self.df[col] = self.df[col].str.replace(r'\s+', ' ', regex=True)
                elif op == 'remove_special_chars':
                    self.df[col] = self.df[col].str.replace(r'[^\w\s]', '', regex=True)
                else:
                    print(f"警告：未知操作 {op}")
            # ✅ 用原本的 NaN mask 還原，比 replace('nan'/'None') 可靠
            self.df.loc[nan_mask_cache[col], col] = np.nan
            self.cleaning_log.append(f"{col}: 文本標準化 ({', '.join(operations)})")
        print(f"已標準化 {len(text_cols)} 個文本欄位")
        return self

    def extract_from_text(self, column, pattern, new_column_name, extract_type='first'):
        """從文本中提取信息"""
        if extract_type == 'first':
            self.df[new_column_name] = self.df[column].str.extract(pattern)[0]
        elif extract_type == 'all':
            self.df[new_column_name] = self.df[column].str.findall(pattern)
        elif extract_type == 'groups':
            # ✅ 實作 groups 分支
            self.df[new_column_name] = self.df[column].str.extract(pattern)
        else:
            raise ValueError(f"不支援的 extract_type: {extract_type}")
        self.cleaning_log.append(f"{new_column_name}: 從 {column} 提取 '{pattern}'")
        return self

    # ============================================
    # 數據類型轉換
    # ============================================
    def convert_types(self, type_mapping=None, auto_detect=True):
        """轉換數據類型"""
        if type_mapping:
            for col, dtype in type_mapping.items():
                if col not in self.df.columns:
                    continue
                try:
                    if dtype == 'datetime':
                        self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    elif dtype == 'category':
                        self.df[col] = self.df[col].astype('category')
                    elif dtype == 'numeric':
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    elif dtype == 'boolean':
                        mapping = {'Y': True, 'N': False, 'Yes': True, 'No': False,
                                   '1': True, '0': False, 'True': True, 'False': False}
                        self.df[col] = self.df[col].map(mapping)
                        # ✅ boolean 未命中值補 NaN，或保留原值
                        self.df[col] = self.df[col].astype('boolean')
                    else:
                        self.df[col] = self.df[col].astype(dtype)
                    self.cleaning_log.append(f"{col}: 轉換為 {dtype}")
                except Exception as e:
                    print(f"轉換失敗 {col}: {str(e)}")

        if auto_detect:
            for col in self.df.select_dtypes(include=['object']).columns:
                # 先試日期（避免 20200101 被誤判為數值）
                conv_date = pd.to_datetime(self.df[col], errors='coerce')
                date_ratio = conv_date.notna().sum() / len(self.df)
                # ✅ 日期格式需含分隔符或長度符合，避免純數字誤判
                is_date_like = self.df[col].astype(str).str.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', na=False).any()
                if date_ratio > 0.5 and is_date_like:
                    self.df[col] = conv_date
                    self.cleaning_log.append(f"{col}: 自動檢測為日期型")
                    continue
                # 再試數值
                conv_num = pd.to_numeric(self.df[col], errors='coerce')
                if conv_num.notna().sum() / len(self.df) > 0.8:
                    self.df[col] = conv_num
                    self.cleaning_log.append(f"{col}: 自動檢測為數值型")
        return self

    # ============================================
    # 異常值處理
    # ============================================
    def remove_outliers(self, columns=None, method='iqr', threshold=1.5):
        """移除異常值"""
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns
        for col in columns:
            if col not in self.df.columns:
                continue
            before = len(self.df)
            if method == 'iqr':
                Q1, Q3 = self.df[col].quantile(0.25), self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower, upper = Q1 - threshold * IQR, Q3 + threshold * IQR
                # ✅ 保留 NaN 行
                self.df = self.df[(self.df[col].isna()) | ((self.df[col] >= lower) & (self.df[col] <= upper))]
            elif method == 'zscore':
                from scipy import stats
                non_null = self.df[col].notna()
                if non_null.sum() < 2:
                    print(f"{col}: 有效樣本不足，跳過 zscore")
                    continue
                z = np.abs(stats.zscore(self.df.loc[non_null, col]))
                # ✅ 只移除 zscore 超標的，保留 NaN
                outlier_mask = np.full(len(self.df), False)
                outlier_mask[non_null] = z >= threshold
                self.df = self.df[~outlier_mask]
            elif method == 'mad':
                non_null = self.df[col].notna()
                vals = self.df.loc[non_null, col]
                if len(vals) < 2:
                    continue
                median = vals.median()
                mad = np.median(np.abs(vals - median))
                if mad == 0:
                    # ✅ mad=0 表示過半相同值，無法用 MAD 判定，跳過並警告
                    print(f"{col}: MAD=0（超過半數相同值），跳過 MAD 異常值移除")
                    continue
                modified_z = 0.6745 * (vals - median) / mad
                outlier_mask = np.full(len(self.df), False)
                outlier_mask[non_null] = np.abs(modified_z) >= threshold
                self.df = self.df[~outlier_mask]
            else:
                raise ValueError(f"不支援的方法: {method}")
            removed = before - len(self.df)
            self.cleaning_log.append(f"{col}: {method} 移除 {removed} 個異常值")
        return self

    def cap_outliers(self, columns, lower_percentile=0.01, upper_percentile=0.99):
        """縮尾處理異常值"""
        for col in columns:
            if col not in self.df.columns:
                continue
            lower = self.df[col].quantile(lower_percentile)
            upper = self.df[col].quantile(upper_percentile)
            self.df[col] = self.df[col].clip(lower, upper)
            self.cleaning_log.append(f"{col}: 縮尾處理 ({lower_percentile}, {upper_percentile})")
        return self

    # ============================================
    # 特徵工程
    # ============================================
    def create_features(self, aggregate_numeric=None):
        """自動創建特徵"""
        # 日期特徵
        date_cols = self.df.select_dtypes(include=['datetime64']).columns
        for col in date_cols:
            self.df[f'{col}_year'] = self.df[col].dt.year
            self.df[f'{col}_month'] = self.df[col].dt.month
            self.df[f'{col}_day'] = self.df[col].dt.day
            self.df[f'{col}_weekday'] = self.df[col].dt.weekday
            self.df[f'{col}_quarter'] = self.df[col].dt.quarter
            self.df[f'{col}_is_weekend'] = self.df[col].dt.weekday >= 5
            self.cleaning_log.append(f"從 {col} 提取日期特徵")

        # 數值特徵（✅ 開放指定聚合欄位，避免把所有數值相加）
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        agg_cols = aggregate_numeric if aggregate_numeric else numeric_cols
        if len(agg_cols) >= 2:
            self.df['numeric_sum'] = self.df[agg_cols].sum(axis=1)
            self.df['numeric_mean'] = self.df[agg_cols].mean(axis=1)
            self.df['numeric_max'] = self.df[agg_cols].max(axis=1)
            self.df['numeric_min'] = self.df[agg_cols].min(axis=1)
            self.cleaning_log.append(f"創建數值聚合特徵（{list(agg_cols)}）")

        # 類別特徵編碼
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if self.df[col].nunique() <= 10:
                dummies = pd.get_dummies(self.df[col], prefix=col, drop_first=True)
                self.df = pd.concat([self.df.drop(col, axis=1), dummies], axis=1)
                self.cleaning_log.append(f"{col}: One-Hot 編碼")
        print("特徵工程完成")
        return self

    # ============================================
    # 報告與輸出
    # ============================================
    def get_cleaning_report(self):
        """獲取清洗報告"""
        return {
            'original_shape': self.original_shape,
            'final_shape': self.df.shape,
            'final_dtypes': self.df.dtypes.astype(str).to_dict(),
            'operations': self.cleaning_log,
            'missing_remaining': self.df.isnull().sum().to_dict(),
            'sample': self.df.head().to_dict('records')
        }

    def save_cleaning_log(self, filepath="cleaning_log.txt"):
        """保存清洗日誌"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("數據清洗日誌\n")
            f.write("=" * 50 + "\n")
            f.write(f"原始數據形狀: {self.original_shape}\n")   # ✅ 正確的原始形狀
            f.write(f"最終數據形狀: {self.df.shape}\n\n")
            f.write("執行操作:\n")
            for i, log in enumerate(self.cleaning_log, 1):
                f.write(f"  {i}. {log}\n")
        print(f"清洗日誌已保存: {filepath}")


# 使用示例
if __name__ == "__main__":
    np.random.seed(42)
    data = {
        'name': [' 張三 ', '李四', '王五', '張三', None, '趙六  '],
        'age': [25, 30, 150, 25, 28, 35],
        'salary': ['5000', '6000', None, '5000', '5500', '7000'],
        'join_date': ['2020-01-15', '2019-06-20', '2021-03-10',
                      '2020-01-15', '2022-01-01', 'invalid_date'],
        'department': ['IT', 'HR', 'it', 'IT', 'Finance', 'HR'],
        'gender': ['M', 'F', 'M', 'M', 'F', 'Unknown']
    }
    df = pd.DataFrame(data)
    print("原始數據:")
    print(df)

    cleaner = DataCleaner(df)
    (cleaner
        .remove_duplicates()
        .handle_missing_values(strategy='auto')
        .standardize_text(columns=['name', 'department'],
                         operations=['strip', 'lower', 'remove_extra_spaces'])
        .convert_types(type_mapping={'join_date': 'datetime',
                                    'salary': 'numeric',
                                    'age': 'numeric'})
        .remove_outliers(columns=['age', 'salary'], method='iqr')
        .create_features())

    print("\n清洗後數據:")
    print(cleaner.df)
    print("\n清洗日誌:")
    for log in cleaner.cleaning_log:
        print(f"  - {log}")
