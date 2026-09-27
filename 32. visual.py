import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class DataVisualization:
    """自動化數據可視化類"""
    def __init__(self, df):
        self.df = df.copy()
        self.figures = []
        # 不修改全域 rcParams，改為繪圖時使用 rc_context

    def _set_font_context(self):
        """回傳中文字體設定context，局部生效，不污染全域"""
        return plt.rc_context({
            'font.sans-serif': ['SimHei', 'PingFang SC', 'Arial Unicode MS', 'DejaVu Sans'],
            'axes.unicode_minus': False
        })

    def auto_visualize(self, output_dir="charts", target_col=None):
        """
        自動分析並生成可視化圖表
        根據數據類型自動選擇合適的圖表
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 驗證 target_col
        if target_col is not None and target_col not in self.df.columns:
            print(f"警告：目標欄位 {target_col} 不存在，忽略目標變量分析")
            target_col = None

        numeric_cols = self.df.select_dtypes(include=['number']).columns
        numeric_cols = [c for c in numeric_cols if c != target_col]
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
        date_cols = self.df.select_dtypes(include=['datetime64']).columns

        # 數值型欄位分佈
        for col in numeric_cols:
            try:
                self._plot_distribution(col, output_path)
                self._plot_boxplot(col, output_path)
            except Exception as e:
                print(f"跳過 {col} 分佈/箱線圖: {str(e)}")

        # 類別型欄位分佈
        for col in categorical_cols:
            try:
                if self.df[col].nunique() <= 20:
                    self._plot_categorical(col, output_path)
            except Exception as e:
                print(f"跳過類別圖 {col}: {str(e)}")

        # 數值關係分析
        try:
            if len(numeric_cols) >= 2:
                self._plot_correlation(numeric_cols, output_path)
                if len(numeric_cols) <= 5:
                    self._plot_pairplot(numeric_cols, target_col, output_path)
        except Exception as e:
            print(f"跳過相關性/散點矩陣: {str(e)}")

        # 時間序列
        for col in date_cols:
            try:
                value_col = numeric_cols[0] if len(numeric_cols) > 0 else None
                self._plot_timeseries(col, value_col, output_path)
            except Exception as e:
                print(f"跳過時間序列 {col}: {str(e)}")

        # 目標變量分析
        if target_col:
            try:
                self._plot_target_analysis(target_col, numeric_cols, categorical_cols, output_path)
            except Exception as e:
                print(f"跳過目標變量分析: {str(e)}")

        print(f"\n已成功生成 {len(self.figures)} 個圖表，保存至 {output_dir}/")
        return self.figures

    def _plot_distribution(self, col, output_dir):
        """繪製分佈圖 + QQ圖"""
        from scipy import stats
        data = self.df[col].dropna()
        if len(data) < 2:
            print(f"{col}: 有效數據不足，跳过分佈圖")
            return

        with self._set_font_context():
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            # 直方圖 + KDE
            axes[0].hist(data, bins=30, density=True, alpha=0.7, color='steelblue', edgecolor='black')
            kde = stats.gaussian_kde(data)
            x_range = np.linspace(data.min(), data.max(), 100)
            axes[0].plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')
            axes[0].set_title(f'{col} 分佈直方圖', fontsize=14, fontweight='bold')
            axes[0].set_xlabel(col, fontsize=12)
            axes[0].set_ylabel('密度', fontsize=12)
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # Q-Q 圖
            stats.probplot(data, dist="norm", plot=axes[1])
            axes[1].set_title(f'{col} Q-Q 圖', fontsize=14, fontweight='bold')
            axes[1].grid(True, alpha=0.3)
            plt.tight_layout()
            filename = output_dir / f'distribution_{col}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            self.figures.append(filename)
        plt.close(fig)

    def _plot_boxplot(self, col, output_dir):
        """繪製箱線圖"""
        data = self.df[col].dropna()
        if len(data) < 2:
            print(f"{col}: 有效數據不足，跳過箱線圖")
            return
        with self._set_font_context():
            fig, ax = plt.subplots(figsize=(10, 6))
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            outlier_count = ((data < q1 - 1.5*iqr) | (data > q3 + 1.5*iqr)).sum()

            bp = ax.boxplot(data, vert=False, patch_artist=True, widths=0.5,
                            showmeans=True, meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
            bp['boxes'][0].set_facecolor('lightblue')
            bp['boxes'][0].set_alpha(0.7)

            stats_text = (f'均值: {data.mean():.2f}\n'
                          f'中位數: {data.median():.2f}\n'
                          f'標準差: {data.std():.2f}\n'
                          f'異常值: {outlier_count}')
            ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
                    fontsize=10, verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax.set_title(f'{col} 箱線圖', fontsize=14, fontweight='bold')
            ax.set_xlabel(col, fontsize=12)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            filename = output_dir / f'boxplot_{col}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            self.figures.append(filename)
        plt.close(fig)

    def _plot_categorical(self, col, output_dir):
        """繪製類別分佈圖"""
        vc = self.df[col].value_counts().head(15)
        if len(vc) == 0:
            print(f"{col}: 類別資料為空，跳過")
            return
        with self._set_font_context():
            fig, ax = plt.subplots(figsize=(12, 7))
            bars = ax.bar(range(len(vc)), vc.values, color=plt.cm.Set3(np.linspace(0, 1, len(vc))))
            ax.set_xticks(range(len(vc)))
            ax.set_xticklabels(vc.index, rotation=45, ha='right')
            ax.set_title(f'{col} 類別分佈 (Top {len(vc)})', fontsize=14, fontweight='bold')
            ax.set_xlabel(col, fontsize=12)
            ax.set_ylabel('數量', fontsize=12)
            for i, val in enumerate(vc.values):
                ax.text(i, val, str(val), ha='center', va='bottom', fontsize=10)
            ax.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            filename = output_dir / f'categorical_{col}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            self.figures.append(filename)
        plt.close(fig)

    def _plot_correlation(self, numeric_cols, output_dir):
        """繪製相關性熱圖"""
        corr_matrix = self.df[numeric_cols].corr()
        with self._set_font_context():
            fig, ax = plt.subplots(figsize=(12, 10))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='RdBu_r',
                        center=0, square=True, linewidths=0.5, fmt='.2f',
                        cbar_kws={"shrink": 0.8}, annot_kws={'size': 10})
            ax.set_title('數值欄位相關性矩陣', fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()
            filename = output_dir / 'correlation_heatmap.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            self.figures.append(filename)
        plt.close(fig)

    def _plot_pairplot(self, numeric_cols, target_col, output_dir):
        """繪製散點圖矩陣"""
        plot_cols = numeric_cols[:4]
        with self._set_font_context():
            if target_col and target_col in self.df.columns:
                g = sns.pairplot(self.df, vars=plot_cols, hue=target_col, diag_kind='kde',
                                 plot_kws={'alpha': 0.6}, height=2.5, aspect=1)
            else:
                g = sns.pairplot(self.df[plot_cols], diag_kind='kde', plot_kws={'alpha':0.6},
                                 height=2.5, aspect=1)
            g.fig.suptitle('數值欄位散點圖矩陣', y=1.02, fontsize=16, fontweight='bold')
            filename = output_dir / 'pairplot.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            self.figures.append(filename)
        plt.close(g.fig)

    def _plot_timeseries(self, date_col, value_col, output_dir):
        """繪製時間序列圖"""
        if value_col is None:
            return
        ts_df = self.df[[date_col, value_col]].dropna()
        if len(ts_df) < 2:
            print(f"{value_col} 時間序列有效數據不足，跳過")
            return
        ts_df = ts_df.set_index(date_col).sort_index()
        time_data = ts_df[value_col]

        with self._set_font_context():
            fig, axes = plt.subplots(2,1, figsize=(14,10))
            axes[0].plot(time_data.index, time_data.values, color='steelblue', linewidth=1.5, alpha=0.8)
            axes[0].set_title(f'{value_col} 時間序列趨勢', fontsize=14, fontweight='bold')
            axes[0].set_xlabel('日期')
            axes[0].set_ylabel(value_col)
            axes[0].grid(True, alpha=0.3)

            window = min(30, max(2, len(time_data)//4))
            rolling_mean = time_data.rolling(window=window).mean()
            axes[0].plot(rolling_mean.index, rolling_mean.values, color='red', linewidth=2, label=f'{window}期移動平均')
            axes[0].legend()

            monthly = time_data.resample('M').mean()
            axes[1].bar(monthly.index, monthly.values, color='coral', alpha=0.7)
            axes[1].set_title(f'{value_col} 月度平均值', fontsize=14, fontweight='bold')
            axes[1].set_xlabel('月份')
            axes[1].set_ylabel(f'平均 {value_col}')
            axes[1].grid(True, alpha=0.3)
            plt.tight_layout()
            filename = output_dir / f'timeseries_{value_col}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            self.figures.append(filename)
        plt.close(fig)

    def _plot_target_analysis(self, target_col, numeric_cols, categorical_cols, output_dir):
        """目標變量分析圖表"""
        # 數值特徵 vs target
        if len(numeric_cols) > 0:
            n_plots = min(3, len(numeric_cols))
            with self._set_font_context():
                fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots, 5))
                if n_plots == 1:
                    axes = [axes]
                for i, col in enumerate(numeric_cols[:3]):
                    if self.df[target_col].nunique() <=5:
                        # 分類目標：箱線圖 seaborn
                        sns.boxplot(data=self.df, x=target_col, y=col, ax=axes[i])
                        axes[i].set_title(f'{col} 按 {target_col} 分組')
                    else:
                        axes[i].scatter(self.df[col], self.df[target_col], alpha=0.5, color='steelblue')
                        axes[i].set_xlabel(col)
                        axes[i].set_ylabel(target_col)
                        axes[i].set_title(f'{col} vs {target_col}')
                    axes[i].grid(True, alpha=0.3)
                plt.suptitle(f'目標變量 {target_col} 分析', fontsize=16, fontweight='bold')
                plt.tight_layout()
                filename = output_dir / 'target_analysis_numeric.png'
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                self.figures.append(filename)
            plt.close(fig)

        # 類別特徵 vs target
        cat_cols = [c for c in categorical_cols if self.df[c].nunique() <= 10]
        if len(cat_cols) > 0 and self.df[target_col].nunique() <=5:
            n_plots = min(2, len(cat_cols))
            with self._set_font_context():
                fig, axes = plt.subplots(1, n_plots, figsize=(6 * n_plots, 5))
                if n_plots ==1:
                    axes = [axes]
                for i, col in enumerate(cat_cols[:2]):
                    cross_tab = pd.crosstab(self.df[col], self.df[target_col])
                    cross_tab.plot(kind='bar', stacked=True, ax=axes[i])
                    axes[i].set_title(f'{col} vs {target_col}')
                    axes[i].set_xlabel(col)
                    axes[i].set_ylabel('數量')
                    axes[i].tick_params(axis='x', rotation=45)
                    axes[i].legend(title=target_col)
                    axes[i].grid(True, alpha=0.3)
                plt.suptitle(f'類別特徵與 {target_col} 的關係', fontsize=16, fontweight='bold')
                plt.tight_layout()
                filename = output_dir / 'target_analysis_categorical.png'
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                self.figures.append(filename)
            plt.close(fig)

# 使用示例
if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=365, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'sales': np.random.randn(365).cumsum() + 100,
        'customers': np.random.randint(50, 200, 365),
        'marketing_spend': np.random.randint(1000, 5000, 365),
        'region': np.random.choice(['北區', '南區', '東區', '西區'], 365),
        'product_category': np.random.choice(['電子', '服飾', '食品', '家居'], 365),
        'is_promotion': np.random.choice([0, 1], 365, p=[0.7, 0.3])
    })
    df['sales'] = df['sales'] + np.sin(np.arange(365) * 2 * np.pi / 365) * 20 + np.arange(365) * 0.1

    viz = DataVisualization(df)
    viz.auto_visualize("my_charts", target_col='is_promotion')
    print("\n生成的圖表:")
    for fig in viz.figures:
        print(f"  - {fig}")
