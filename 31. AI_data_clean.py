import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer, KNNImputer, IterativeImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.feature_selection import mutual_info_classif, SelectKBest
from typing import Optional, List


class AIDataCleaner:
    """AI 輔助數據清洗類"""
    def __init__(self, df, target_col: Optional[str] = None):
        self.df = df.copy()
        self.transformers = {}
        self.target_col = target_col       # ✅ 統一存 target，避免各處硬編碼 'target'

    # ============================================
    # 缺失值處理
    # ============================================
    def smart_impute(self, strategy='knn', n_neighbors=5):
        """
        智能缺失值填充
        Args:
            strategy: 'knn', 'iterative', 'simple', 'advanced'
        """
        numeric_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        # 排除 target 與異常標記
        numeric_cols = [c for c in numeric_cols if c not in (self.target_col, 'is_anomaly')]
        if len(numeric_cols) == 0:
            print("警告：沒有可填充的數值型欄位")
            return self

        if strategy == 'knn':
            imputer = KNNImputer(n_neighbors=n_neighbors)
            self.df[numeric_cols] = imputer.fit_transform(self.df[numeric_cols])
            self.transformers['imputer'] = imputer
            print(f"KNN (k={n_neighbors}) 填充 {len(numeric_cols)} 個數值欄位")
        elif strategy == 'iterative':
            imputer = IterativeImputer(random_state=42, max_iter=10)
            self.df[numeric_cols] = imputer.fit_transform(self.df[numeric_cols])
            self.transformers['imputer'] = imputer
            print("迭代算法填充完成")
        elif strategy == 'simple':
            # ✅ 實作 missing 的 'simple'
            for col in numeric_cols:
                if self.df[col].isnull().any():
                    self.df[col] = self.df[col].fillna(self.df[col].median())
            print("使用中位數填充（simple 策略）")
        elif strategy == 'advanced':
            for col in numeric_cols:
                missing_pct = self.df[col].isnull().sum() / len(self.df)
                if missing_pct < 0.05:
                    self.df[col] = self.df[col].fillna(self.df[col].mean())
                elif missing_pct < 0.3:
                    imputer = KNNImputer(n_neighbors=3)
                    self.df[[col]] = imputer.fit_transform(self.df[[col]])
                else:
                    imputer = IterativeImputer(random_state=42)
                    self.df[[col]] = imputer.fit_transform(self.df[[col]])
            print("進階策略填充完成")
        else:
            raise ValueError(f"不支援的策略: {strategy}")
        return self

    # ============================================
    # 類別編碼
    # ============================================
    def auto_encode_categorical(self, max_categories=10,
                                high_cardinality_strategy='target_encoding',
                                encode_target: bool = False):
        """
        自動編碼類別變量
        Args:
            encode_target: 是否也編碼 target 欄位（預設 False 避免誤編）
        """
        categorical_cols = list(self.df.select_dtypes(include=['object', 'category']).columns)
        # ✅ 預設排除 target 欄位
        if not encode_target and self.target_col in categorical_cols:
            categorical_cols.remove(self.target_col)

        for col in categorical_cols:
            unique_count = self.df[col].nunique()
            missing_count = self.df[col].isnull().sum()
            if missing_count > 0:
                self.df[col] = self.df[col].fillna('Missing')

            if unique_count <= max_categories:
                # 低基數：One-Hot
                dummies = pd.get_dummies(self.df[col], prefix=col, drop_first=True)
                self.df = pd.concat([self.df.drop(col, axis=1), dummies], axis=1)
                print(f"{col}: One-Hot 編碼 ({unique_count})")

            elif high_cardinality_strategy == 'target_encoding':
                if self.target_col and self.target_col in self.df.columns:
                    target_mean = self.df.groupby(col)[self.target_col].mean()
                    enc = self.df[col].map(target_mean).fillna(self.df[self.target_col].mean())
                    self.df[f'{col}_target_enc'] = enc      # ✅ NaN→全體均值
                    self.df = self.df.drop(col, axis=1)
                    print(f"{col}: 目標編碼 ({unique_count})")
                else:
                    freq = self.df[col].value_counts(normalize=True)
                    self.df[f'{col}_freq_enc'] = self.df[col].map(freq)
                    self.df = self.df.drop(col, axis=1)
                    print(f"{col}: 頻率編碼（無目標欄位）")

            elif high_cardinality_strategy == 'frequency':
                freq = self.df[col].value_counts(normalize=True)
                self.df[f'{col}_freq_enc'] = self.df[col].map(freq)
                self.df = self.df.drop(col, axis=1)
                print(f"{col}: 頻率編碼 ({unique_count})")

            elif high_cardinality_strategy == 'label':
                le = LabelEncoder()
                self.df[col] = le.fit_transform(self.df[col].astype(str))
                self.transformers[f'label_{col}'] = le
                print(f"{col}: Label 編碼 ({unique_count})")

            else:
                raise ValueError(f"不支援的高基數策略: {high_cardinality_strategy}")
        return self

    # ============================================
    # 數值縮放
    # ============================================
    def auto_scale(self, method='standard', target_range=(0, 1)):
        """自動標準化數值特徵"""
        numeric_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        exclude = {self.target_col, 'is_anomaly'}
        # 排除已是 0-1 的欄位
        already_01 = [c for c in numeric_cols
                      if self.df[c].min() >= 0 and self.df[c].max() <= 1]
        scale_cols = [c for c in numeric_cols
                      if c not in exclude and c not in already_01]

        if len(scale_cols) == 0:                    # ✅ 空列表防護
            print("沒有需要縮放的數值欄位，跳過")
            return self

        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler(feature_range=target_range)
        elif method == 'robust':
            scaler = RobustScaler()
        else:
            raise ValueError(f"不支援的縮放方法: {method}")

        self.df[scale_cols] = scaler.fit_transform(self.df[scale_cols])
        self.transformers['scaler'] = scaler
        print(f"{method} 縮放 {len(scale_cols)} 個欄位")
        return self

    def transform_new_data(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """用已fit的 transformers 轉換新資料（測試集），避免資料洩漏"""
        df = new_df.copy()
        # 縮放
        if 'scaler' in self.transformers and 'scaler' in self.df.columns:
            scale_cols = list(self.transformers['scaler'].feature_names_in_)
            df[scale_cols] = self.transformers['scaler'].transform(df[scale_cols])
        # imputer
        if 'imputer' in self.transformers and 'imputer' in self.df.columns:
            num_cols = list(self.transformers['imputer'].feature_names_in_)
            df[num_cols] = self.transformers['imputer'].transform(df[num_cols])
        return df

    # ============================================
    # 異常值檢測
    # ============================================
    def detect_anomalies(self, contamination=0.1, method='isolation_forest'):
        """自動檢測異常值，返回 -1 異常 / 1 正常"""
        numeric_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        numeric_cols = [c for c in numeric_cols
                        if c not in (self.target_col, 'is_anomaly')]
        if len(numeric_cols) == 0:
            print("無數值型欄位可供檢測")
            return None
        data = self.df[numeric_cols].dropna()
        if len(data) < 2:
            print("有效樣本不足")
            return None

        if method == 'isolation_forest':
            detector = IsolationForest(contamination=contamination,
                                       random_state=42, n_estimators=100)
            predictions = detector.fit_predict(data)
        elif method == 'local_outlier_factor':
            detector = LocalOutlierFactor(contamination=contamination)
            predictions = detector.fit_predict(data)
        else:
            raise ValueError(f"不支援的異常值方法: {method}")   # ✅ 防 NameError

        anomalies = predictions == -1
        self.df['is_anomaly'] = False
        self.df.loc[data.index, 'is_anomaly'] = anomalies
        print(f"檢測到 {anomalies.sum()} 個異常值")
        return anomalies

    # ============================================
    # 特徵選擇
    # ============================================
    def auto_feature_selection(self, method='correlation', threshold=0.05):
        """
        自動特徵選擇
        Args:
            method: 'correlation', 'mutual_info', 'model_based'
        """
        if not self.target_col:
            print("請在建構時提供 target_col")
            return []
        feature_cols = [c for c in self.df.columns
                        if c != self.target_col and c != 'is_anomaly']
        X = self.df[feature_cols].select_dtypes(include=[np.number]).dropna()
        y = self.df.loc[X.index, self.target_col]

        if len(X) == 0:
            print("沒有數值特徵可供選擇")
            return []

        selected: List[str] = []          # ✅ 預先定義，避免 UnboundLocalError

        if method == 'correlation':
            correlations = X.corrwith(y).abs().sort_values(ascending=False)
            selected = [c for c, v in correlations.items() if v > threshold]
            print(f"相關性選擇 {len(selected)} 個特徵")
        elif method == 'mutual_info':
            selector = SelectKBest(mutual_info_classif, k='all')
            selector.fit(X, y)
            scores = pd.Series(selector.scores_, index=X.columns)
            selected = [c for c, s in scores.items() if s > threshold]
            print(f"互信息選擇 {len(selected)} 個特徵")
        elif method == 'model_based':
            # ✅ 實作 model_based：用隨機森林特徵重要度
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            importances = pd.Series(model.feature_importances_, index=X.columns)
            selected = [c for c, v in importances.items() if v > threshold]
            print(f"模型特徵重要度選擇 {len(selected)} 個特徵")
        else:
            raise ValueError(f"不支援的特徵選擇方法: {method}")

        self.selected_features = selected
        return selected


# 使用示例
if __name__ == "__main__":
    np.random.seed(42)
    n_samples = 1000
    df = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.choice(['A', 'B', 'C', 'D'], n_samples),
        'feature_4': np.random.choice(['X', 'Y'], n_samples),
        'target': np.random.choice([0, 1], n_samples)
    })
    df.loc[np.random.choice(n_samples, 50, replace=False), 'feature_1'] = np.nan
    df.loc[np.random.choice(n_samples, 30, replace=False), 'feature_3'] = np.nan
    df.loc[np.random.choice(n_samples, 20, replace=False), 'feature_1'] = 10

    print("原始形狀:", df.shape)
    print("缺失值:\n", df.isnull().sum())

    ai_cleaner = AIDataCleaner(df, target_col='target')
    (ai_cleaner
        .smart_impute(strategy='advanced')
        .auto_encode_categorical(max_categories=3)
        .auto_scale(method='standard')
        .detect_anomalies(contamination=0.05))

    print("\n清洗後形狀:", ai_cleaner.df.shape)
    print("異常值:", ai_cleaner.df['is_anomaly'].sum())
