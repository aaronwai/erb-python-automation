import pandas as pd
import numpy as np

class DataFrameOperations:
    """DataFrame 核心操作類
    所有操作預設不修改原始 self.df，返回副本
    """
    def __init__(self, df=None):
        self.df = df.copy() if df is not None else None

    def _check_df_exists(self):
        if self.df is None:
            raise ValueError("尚未載入 DataFrame，請在建構時傳入 df")

    # ============================================
    # 數據選擇與過濾（通用工具方法）
    # ============================================
    def select_columns(self, columns):
        """
        選擇特定欄位
        :param columns: list[str] 欄位名稱清單
        :return: DataFrame 副本
        """
        self._check_df_exists()
        return self.df[columns].copy()

    def filter_rows(self, condition):
        """
        條件過濾
        :param condition: boolean Series 布林條件
        :return: DataFrame 副本
        """
        self._check_df_exists()
        return self.df[condition].copy()

    def query_data(self, query_string):
        """
        使用 query 查詢語法過濾
        :param query_string: str pandas query 字串
        :return: DataFrame 副本
        """
        self._check_df_exists()
        return self.df.query(query_string).copy()

    def filter_examples(self):
        """
        【示範用途】多種過濾寫法範例
        ⚠️ 依賴欄位：salary, age, department, name, email, date
        """
        self._check_df_exists()
        df = self.df.copy()

        # 單一條件
        high_salary = df[df['salary'] > 50000]
        # 多條件組合
        filtered = df[(df['salary'] > 50000) & (df['age'] < 35)]
        # isin 過濾
        specific_depts = df[df['department'].isin(['IT', 'HR', 'Finance'])]
        # 字符串過濾
        name_starts_with = df[df['name'].str.startswith('張', na=False)]
        # 正則表達式過濾
        email_pattern = df[df['email'].str.match(r'.*@example\.com$', na=False)]
        # 日期範圍過濾
        date_range = df[(df['date'] >= '2024-01-01') & (df['date'] <= '2024-06-30')]

        return {
            'high_salary': high_salary.copy(),
            'filtered': filtered.copy(),
            'specific_depts': specific_depts.copy(),
            'name_starts_with': name_starts_with.copy(),
            'email_pattern': email_pattern.copy(),
            'date_range': date_range.copy()
        }

    # ============================================
    # 數據排序與排名
    # ============================================
    def sort_examples(self):
        """
        【示範用途】排序、排名範例
        ⚠️ 依賴欄位：salary, department, age
        """
        self._check_df_exists()
        df = self.df.copy()

        # 單欄位排序
        sorted_by_salary = df.sort_values('salary', ascending=False)
        # 多欄位排序
        sorted_multi = df.sort_values(['department', 'salary'], ascending=[True, False])
        # 按索引排序
        sorted_index = df.sort_index()

        # 排名（新增欄位，只在副本上操作）
        df['salary_rank'] = df['salary'].rank(method='dense', ascending=False)
        df['department_rank'] = df.groupby('department')['salary'].rank(ascending=False)

        return df.copy()

    # ============================================
    # 數據聚合與分組
    # ============================================
    def groupby_examples(self):
        """
        【示範用途】groupby 分組聚合範例
        ⚠️ 依賴欄位：department, salary, age, employee_id
        """
        self._check_df_exists()
        df = self.df.copy()

        # 基礎分組統計
        dept_stats = df.groupby('department').agg({
            'salary': ['mean', 'median', 'min', 'max', 'count'],
            'age': 'mean',
            'employee_id': 'count'
        })
        # 命名聚合
        named_agg = df.groupby('department').agg(
            avg_salary=('salary', 'mean'),
            total_employees=('employee_id', 'count'),
            max_age=('age', 'max')
        )
        # 轉換操作（保持原數據形狀）
        df['dept_avg_salary'] = df.groupby('department')['salary'].transform('mean')
        df['salary_vs_dept_avg'] = df['salary'] / df['dept_avg_salary']
        # 過濾分組
        large_depts = df.groupby('department').filter(lambda x: len(x) >= 5)

        # 分組應用自定義函數
        def top_n_per_group(group, n=2):
            return group.nlargest(n, 'salary')
        top_earners = df.groupby('department', group_keys=False).apply(top_n_per_group)

        return {
            'dept_stats': dept_stats.copy(),
            'named_agg': named_agg.copy(),
            'large_depts': large_depts.copy(),
            'top_earners': top_earners.copy(),
            'df_with_group_col': df.copy()
        }

    # ============================================
    # 數據合併與連接
    # ============================================
    def merge_examples(self, other_df):
        """
        【示範用途】merge / concat 連接範例
        ⚠️ 依賴欄位：employee_id, id, fname, lname, emp_id
        :param other_df: DataFrame 要合併的第二張表
        """
        self._check_df_exists()
        if not isinstance(other_df, pd.DataFrame):
            raise TypeError("other_df 必須是 pandas DataFrame")

        df = self.df.copy()
        other = other_df.copy()

        # 內連接（只保留匹配的記錄）
        inner = pd.merge(df, other, on='employee_id', how='inner')
        # 左連接（保留左表所有記錄）
        left = pd.merge(df, other, on='employee_id', how='left')
        # 外連接（保留所有記錄）
        outer = pd.merge(df, other, on='employee_id', how='outer')
        # 多欄位連接
        multi = pd.merge(df, other,
                        left_on=['first_name', 'last_name'],
                        right_on=['fname', 'lname'],
                        how='left')
        # 按索引連接
        index_merge = pd.merge(df.set_index('id'),
                              other.set_index('emp_id'),
                              left_index=True,
                              right_index=True,
                              how='inner')
        # 縱向合併
        combined = pd.concat([df, other], ignore_index=True)

        return {
            'inner': inner.copy(),
            'left': left.copy(),
            'outer': outer.copy(),
            'multi': multi.copy(),
            'index_merge': index_merge.copy(),
            'combined': combined.copy()
        }

    # ============================================
    # 數據透視
    # ============================================
    def pivot_examples(self):
        """
        【示範用途】pivot_table / crosstab 透視範例
        ⚠️ 依賴欄位：department, gender, salary, bonus, position, year
        """
        self._check_df_exists()
        df = self.df.copy()

        # 基礎透視表
        pivot = df.pivot_table(
            values='salary',
            index='department',
            columns='gender',
            aggfunc='mean',
            fill_value=0
        )
        # 多層次透視
        multi_pivot = df.pivot_table(
            values=['salary', 'bonus'],
            index=['department', 'position'],
            columns='year',
            aggfunc={'salary': 'mean', 'bonus': 'sum'},
            margins=True,
            margins_name='總計'
        )
        # 交叉表
        crosstab = pd.crosstab(
            df['department'],
            df['gender'],
            values=df['salary'],
            aggfunc='mean'
        )
        # 堆疊與取消堆疊
        stacked = pivot.stack()
        unstacked = stacked.unstack()

        return {
            'pivot': pivot.copy(),
            'multi_pivot': multi_pivot.copy(),
            'crosstab': crosstab.copy(),
            'stacked': stacked.copy(),
            'unstacked': unstacked.copy()
        }


# 使用示例
if __name__ == "__main__":
    # 創建示例數據
    np.random.seed(42)
    data = {
        'employee_id': range(1, 101),
        'name': [f'員工_{i}' for i in range(1, 101)],
        'department': np.random.choice(['IT', 'HR', 'Finance', 'Sales', 'Marketing'], 100),
        'position': np.random.choice(['Junior', 'Senior', 'Manager', 'Director'], 100),
        'salary': np.random.randint(30000, 150000, 100),
        'age': np.random.randint(22, 60, 100),
        'gender': np.random.choice(['M', 'F'], 100),
        'join_date': pd.date_range('2020-01-01', periods=100, freq='D'),
        'bonus': np.random.randint(0, 30000, 100),
        'year': np.random.choice([2023,2024,2025],100)
    }
    df = pd.DataFrame(data)
    ops = DataFrameOperations(df)

    # 執行分組聚合示例
    results = ops.groupby_examples()
    print("部門統計:")
    print(results['dept_stats'])
