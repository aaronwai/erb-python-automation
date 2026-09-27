import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class InteractiveVisualization:
    """交互式可視化類（Plotly）"""
    def __init__(self, df):
        self.df = df.copy()  # ✅ 存副本，避免外部df被修改

    def create_interactive_dashboard(self, output_file="dashboard.html", top_n_pie=6):
        """
        創建交互式儀表板
        Args:
            output_file: 輸出HTML路徑
            top_n_pie: Pie圖只顯示前N大類別，其餘歸類Others
        """
        if self.df.empty:
            print("資料框為空，無法繪製儀表板")
            return None

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('銷售趨勢', '類別分佈', '相關性矩陣', '區域銷售'),
            specs=[
                [{"secondary_y": True}, {"type": "pie"}],
                [{"type": "heatmap"}, {"type": "bar"}]
            ]
        )

        # 1. 時間序列（雙Y軸）
        if "sales" in self.df.columns:
            fig.add_trace(
                go.Scatter(x=self.df.index, y=self.df['sales'],
                           name='銷售額', line=dict(color='#1f77b4')),
                row=1, col=1
            )
            if 'profit' in self.df.columns:
                fig.add_trace(
                    go.Scatter(x=self.df.index, y=self.df['profit'],
                               name='利潤', line=dict(color='#d62728')),
                    row=1, col=1, secondary_y=True
                )
                fig.update_yaxes(title_text="利潤", secondary_y=True, row=1, col=1)
            fig.update_yaxes(title_text="銷售額", row=1, col=1)

        # 2. Pie 類別分佈（前N類，剩餘歸Others）
        if 'category' in self.df.columns:
            cat_counts = self.df['category'].value_counts()
            if len(cat_counts) > top_n_pie:
                top = cat_counts.head(top_n_pie)
                top['Others'] = cat_counts.iloc[top_n_pie:].sum()
                cat_counts = top
            fig.add_trace(
                go.Pie(labels=cat_counts.index, values=cat_counts.values, name='類別分佈'),
                row=1, col=2
            )

        # 3. 相關性熱力圖，加上hover顯示相關數值
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        if len(numeric_cols) >= 2:
            corr = self.df[numeric_cols].corr()
            fig.add_trace(
                go.Heatmap(
                    z=corr.values,
                    x=corr.columns,
                    y=corr.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=np.round(corr.values, 2),
                    hovertemplate="X: %{x}<br>Y: %{y}<br>Corr: %{z:.3f}<extra></extra>"
                ),
                row=2, col=1
            )

        # 4. 區域銷售條形圖
        if 'region' in self.df.columns and 'sales' in self.df.columns:
            region_sales = self.df.groupby('region')['sales'].sum()
            fig.add_trace(
                go.Bar(x=region_sales.index, y=region_sales.values, name='區域銷售'),
                row=2, col=2
            )

        fig.update_layout(
            title_text="交互式數據儀表板",
            height=800,
            showlegend=True
        )
        fig.write_html(output_file)
        print(f"儀表板已保存: {output_file}")
        return fig

    def create_animated_chart(self, output_file="animation.html"):
        """創建動態散點圖（不會修改self.df）"""
        if self.df.empty:
            print("資料為空，無法繪製動畫圖")
            return None
        if 'date' not in self.df.columns:
            print("缺少 date 欄位，無法建立動態圖")
            return None

        df_anim = self.df.copy()
        df_anim['year_month'] = pd.to_datetime(df_anim['date']).dt.to_period('M').astype(str)

        # ✅ 安全選擇y軸欄位，避免KeyError
        if 'profit' in df_anim.columns:
            y_col = 'profit'
        elif 'customers' in df_anim.columns:
            y_col = 'customers'
        else:
            print("缺少 profit / customers，無法設定Y軸")
            return None
        if 'sales' not in df_anim.columns:
            print("缺少 sales 欄位，無法設定X軸")
            return None

        anim_group = 'region' if 'region' in df_anim.columns else None
        size_col = 'customers' if 'customers' in df_anim.columns else None
        color_col = 'region' if 'region' in df_anim.columns else None

        fig = px.scatter(
            df_anim,
            x='sales',
            y=y_col,
            animation_frame='year_month',
            animation_group=anim_group,
            size=size_col,
            color=color_col,
            hover_name=color_col,
            log_x=True,
            size_max=55,
            range_x=[df_anim['sales'].min(), df_anim['sales'].max()],
            title="銷售動態變化"
        )
        fig.write_html(output_file)
        print(f"動態圖表已保存: {output_file}")
        return fig


# 使用示例
if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'sales': np.random.randint(1000, 10000, 100),
        'profit': np.random.randint(100, 1000, 100),
        'customers': np.random.randint(10, 100, 100),
        'region': np.random.choice(['北區', '南區', '東區', '西區'], 100),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    })
    df_indexed = df.set_index('date')

    viz = InteractiveVisualization(df_indexed)
    viz.create_interactive_dashboard("my_dashboard.html")
    viz.create_animated_chart("animation.html")
