import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="普通貿易統計 国別・品目別推移ダッシュボード",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 金額単位は「億円」に統一（1億円 ＝ 100,000 千円）
UNIT_SCALE = "億円"
UNIT_DIVISOR = 100_000
UNIT_LABEL = "金額（億円）"

# 最上部に戻るホバーボタン（右下固定）
st.markdown("""
<style>
#top-anchor {
    position: absolute;
    top: 0;
    left: 0;
}
.scroll-top-btn {
    position: fixed;
    bottom: 25px;
    right: 30px;
    z-index: 9999;
    background-color: #1f77b4;
    color: white !important;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    font-size: 24px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none !important;
}
.scroll-top-btn:hover {
    background-color: #0d47a1;
    transform: translateY(-4px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.4);
}
</style>
<div id="top-anchor"></div>
<a href="#top-anchor" class="scroll-top-btn" title="最上部へ戻る">↑</a>
""", unsafe_allow_html=True)

# データの読み込み
@st.cache_data
def load_data():
    file_path = 'trade_summary.csv.gz'
    if not os.path.exists(file_path):
        file_path = os.path.join('data', 'trade_summary.csv.gz')
    df = pd.read_csv(file_path, compression='gzip')
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"データファイルが見つかりません。まず `python preprocess.py` を実行してください。詳細: {e}")
    st.stop()

# ----------------- サイドバー（検索・条件設定） -----------------
st.sidebar.title("🔍 検索・絞り込み条件")

# 検索リセットボタン
if st.sidebar.button("🔄 検索条件をリセット", use_container_width=True):
    for key in ['selected_countries', 'selected_hs', 'time_granularity']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# 時間軸（年次 / 月次）
time_granularity = st.sidebar.radio(
    "推移チャートの表示単位",
    ["年次推移", "月次推移"],
    index=0,
    key="time_granularity",
    horizontal=True
)

# 主要国リスト
country_trade_totals = df_raw.groupby('国名')['年間累計_金額_千円'].sum().sort_values(ascending=False)
top_countries_list = country_trade_totals.head(20).index.tolist()
all_countries = sorted(df_raw['国名'].dropna().unique().tolist())

st.sidebar.markdown("---")
st.sidebar.subheader("国・地域の選択")

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("TOP 10 カ国"):
    st.session_state['selected_countries'] = top_countries_list[:10]
    st.rerun()
if col_btn2.button("全選択解除"):
    st.session_state['selected_countries'] = []
    st.rerun()

default_countries = st.session_state.get('selected_countries', top_countries_list[:5])
selected_countries = st.sidebar.multiselect(
    "国名を選択（空欄で全カ国）",
    options=all_countries,
    default=[c for c in default_countries if c in all_countries],
    key="selected_countries"
)

st.sidebar.markdown("---")
st.sidebar.subheader("品目の選択（HS品目大分類）")
all_hs = sorted(df_raw['HS品目大分類'].dropna().unique().tolist())

selected_hs = st.sidebar.multiselect(
    "HS品目大分類（96類）を選択（空欄で全品目）",
    options=all_hs,
    default=st.session_state.get('selected_hs', []),
    key="selected_hs"
)

# ----------------- データの絞り込み -----------------
df_filtered = df_raw.copy()
if selected_countries:
    df_filtered = df_filtered[df_filtered['国名'].isin(selected_countries)]
if selected_hs:
    df_filtered = df_filtered[df_filtered['HS品目大分類'].isin(selected_hs)]

# ----------------- メイン画面 -----------------
st.title("🚢 日本の普通貿易統計 国別・品目別推移ダッシュボード")
target_country_text = "、".join(selected_countries) if selected_countries else "全世界（全カ国・地域）"
target_hs_text = f"{len(selected_hs)} 類を選択中" if selected_hs else "全品目（96類）"
st.caption(f"**対象国・地域:** {target_country_text} ｜ **対象品目:** {target_hs_text}")

# 年次データの集計
annual_exp = df_filtered[df_filtered['輸出入区分'] == '輸出'].groupby('年')['年間累計_金額_千円'].sum() / UNIT_DIVISOR
annual_imp = df_filtered[df_filtered['輸出入区分'] == '輸入'].groupby('年')['年間累計_金額_千円'].sum() / UNIT_DIVISOR
common_years = sorted(list(set(annual_exp.index).intersection(set(annual_imp.index))))

latest_year = max(common_years) if common_years else None

if latest_year:
    latest_exp = annual_exp.get(latest_year, 0)
    latest_imp = annual_imp.get(latest_year, 0)
    latest_net = latest_exp - latest_imp
    
    st.subheader(f"📊 {latest_year}年 貿易収支サマリ")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("総輸出額", f"{latest_exp:,.1f} 億円")
    kpi2.metric("総輸入額", f"{latest_imp:,.1f} 億円")
    net_status = "🟩 貿易黒字" if latest_net >= 0 else "🟥 貿易赤字"
    kpi3.metric("貿易収支（差額: 輸出 - 輸入）", f"{latest_net:+,.1f} 億円", delta=f"{latest_net:,.1f} 億円")
    kpi4.metric("収支判定", net_status)

st.markdown("---")

# ----------------- 時系列推移チャート -----------------
st.subheader("📈 輸出入および貿易収支の時系列推移")
st.markdown("※ 凡例をクリックすると系列の表示/非表示を切り替えられます（ダブルクリックで単独表示）。")

if time_granularity == "年次推移":
    years = [y for y in common_years if y <= 2025]
    df_trend = pd.DataFrame({
        '年': years,
        '輸出額': [annual_exp.get(y, 0) for y in years],
        '輸入額': [annual_imp.get(y, 0) for y in years],
    })
    df_trend['収支差額（黒字/赤字）'] = df_trend['輸出額'] - df_trend['輸入額']
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=df_trend['年'], y=df_trend['輸出額'],
        name='輸出額', marker_color='#1f77b4',
        hovertemplate='%{x}年 輸出額: %{y:,.1f} 億円<extra></extra>'
    ))
    fig_trend.add_trace(go.Bar(
        x=df_trend['年'], y=df_trend['輸入額'],
        name='輸入額', marker_color='#ff7f0e',
        hovertemplate='%{x}年 輸入額: %{y:,.1f} 億円<extra></extra>'
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_trend['年'], y=df_trend['収支差額（黒字/赤字）'],
        name='収支差額（輸出 - 輸入）',
        mode='lines+markers',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8),
        hovertemplate='%{x}年 収支差額: %{y:+,.1f} 億円<extra></extra>'
    ))
    fig_trend.update_layout(
        barmode='group',
        xaxis=dict(title='年', tickmode='linear'),
        yaxis=dict(
            title=UNIT_LABEL,
            tickformat=',.0f',       # kやMを抑止しカンマ区切り数値
            ticksuffix=' 億円'        # 目盛りに「億円」を付与
        ),
        hovermode='x unified',
        height=450
    )
    st.plotly_chart(fig_trend, use_container_width=True)

else:  # 月次推移
    month_cols = [f'{m}月_金額_千円' for m in range(1, 13)]
    monthly_records = []
    
    years_m = sorted(df_filtered['年'].unique())
    for y in years_m:
        for m in range(1, 13):
            if y == 2026 and m > 7:
                continue
            col_name = f'{m}月_金額_千円'
            exp_val = df_filtered[(df_filtered['年'] == y) & (df_filtered['輸出入区分'] == '輸出')][col_name].sum() / UNIT_DIVISOR
            imp_val = df_filtered[(df_filtered['年'] == y) & (df_filtered['輸出入区分'] == '輸入')][col_name].sum() / UNIT_DIVISOR
            monthly_records.append({
                '年月': f"{y}-{m:02d}",
                '輸出額': exp_val,
                '輸入額': imp_val,
                '収支差額': exp_val - imp_val
            })
            
    df_monthly = pd.DataFrame(monthly_records)
    
    fig_m = go.Figure()
    fig_m.add_trace(go.Scatter(
        x=df_monthly['年月'], y=df_monthly['輸出額'],
        name='輸出額', mode='lines', line=dict(color='#1f77b4', width=2),
        hovertemplate='%{x} 輸出額: %{y:,.1f} 億円<extra></extra>'
    ))
    fig_m.add_trace(go.Scatter(
        x=df_monthly['年月'], y=df_monthly['輸入額'],
        name='輸入額', mode='lines', line=dict(color='#ff7f0e', width=2),
        hovertemplate='%{x} 輸入額: %{y:,.1f} 億円<extra></extra>'
    ))
    fig_m.add_trace(go.Bar(
        x=df_monthly['年月'], y=df_monthly['収支差額'],
        name='収支差額（Net）',
        marker_color=np.where(df_monthly['収支差額'] >= 0, '#2ca02c', '#d62728'),
        hovertemplate='%{x} 収支差額: %{y:+,.1f} 億円<extra></extra>',
        opacity=0.6
    ))
    fig_m.update_layout(
        xaxis=dict(title='年月', tickangle=-45),
        yaxis=dict(
            title=UNIT_LABEL,
            tickformat=',.0f',
            ticksuffix=' 億円'
        ),
        hovermode='x unified',
        height=450
    )
    st.plotly_chart(fig_m, use_container_width=True)

st.markdown("---")

# ----------------- 品目別 収支差額バタフライチャート -----------------
st.subheader("⚖️ 品目別の輸出入および収支差額（黒字・赤字の俯瞰）")

year_for_breakdown = st.selectbox(
    "内訳表示の対象年を選択",
    options=sorted([y for y in common_years if y <= 2025], reverse=True),
    index=0
)

df_year = df_filtered[df_filtered['年'] == year_for_breakdown]
exp_by_hs = df_year[df_year['輸出入区分'] == '輸出'].groupby('HS品目大分類')['年間累計_金額_千円'].sum() / UNIT_DIVISOR
imp_by_hs = df_year[df_year['輸出入区分'] == '輸入'].groupby('HS品目大分類')['年間累計_金額_千円'].sum() / UNIT_DIVISOR

all_active_hs = sorted(list(set(exp_by_hs.index).union(set(imp_by_hs.index))))
df_hs_summary = pd.DataFrame({
    'HS品目大分類': all_active_hs,
    '輸出額': [exp_by_hs.get(h, 0.0) for h in all_active_hs],
    '輸入額': [imp_by_hs.get(h, 0.0) for h in all_active_hs],
})
df_hs_summary['貿易収支（差額）'] = df_hs_summary['輸出額'] - df_hs_summary['輸入額']
df_hs_summary['取引規模（合計）'] = df_hs_summary['輸出額'] + df_hs_summary['輸入額']

# 上位25品目（取引規模順）
df_hs_top = df_hs_summary.sort_values(by='取引規模（合計）', ascending=False).head(25)

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("##### 輸出入バタフライチャート（左右比較）")
    fig_bf = go.Figure()
    fig_bf.add_trace(go.Bar(
        y=df_hs_top['HS品目大分類'],
        x=-df_hs_top['輸入額'],
        orientation='h',
        name='輸入額',
        marker_color='#ff7f0e',
        hovertemplate='%{y}<br>輸入額: %{customdata:,.1f} 億円<extra></extra>',
        customdata=df_hs_top['輸入額']
    ))
    fig_bf.add_trace(go.Bar(
        y=df_hs_top['HS品目大分類'],
        x=df_hs_top['輸出額'],
        orientation='h',
        name='輸出額',
        marker_color='#1f77b4',
        hovertemplate='%{y}<br>輸出額: %{x:,.1f} 億円<extra></extra>'
    ))
    fig_bf.update_layout(
        barmode='relative',
        yaxis=dict(autorange='reversed', title=''),
        xaxis=dict(
            title='← 輸入超過 ｜ 輸出超過 →',
            tickformat=',.0f',
            ticksuffix=' 億円'
        ),
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bf, use_container_width=True)

with col_chart2:
    st.markdown("##### 品目別 純収支（差額: 輸出 - 輸入）")
    df_hs_top_sorted = df_hs_top.sort_values(by='貿易収支（差額）', ascending=True)
    fig_net = go.Figure()
    fig_net.add_trace(go.Bar(
        y=df_hs_top_sorted['HS品目大分類'],
        x=df_hs_top_sorted['貿易収支（差額）'],
        orientation='h',
        marker_color=np.where(df_hs_top_sorted['貿易収支（差額）'] >= 0, '#2ca02c', '#d62728'),
        hovertemplate='%{y}<br>収支差額: %{x:+,.1f} 億円<extra></extra>',
        name='収支差額'
    ))
    fig_net.update_layout(
        yaxis=dict(title=''),
        xaxis=dict(
            title='収支差額 ※緑=黒字 / 赤=赤字',
            tickformat=',.0f',
            ticksuffix=' 億円'
        ),
        height=650,
        showlegend=False
    )
    st.plotly_chart(fig_net, use_container_width=True)

st.markdown("---")

# ----------------- 国別 収支ランキングテーブル -----------------
st.subheader("🌍 国別 取引規模・収支一覧")

valid_years = sorted([y for y in common_years if y <= 2025], reverse=True)
period_options = ["全期間累計（通算）"] + [f"{y}年" for y in valid_years]

selected_table_period = st.selectbox(
    "📊 一覧に表示する集計期間を選択",
    options=period_options,
    index=1,
    help="特定の年ごとの収支、または分析期間を通じた通算累計を切り替えます。"
)

if selected_table_period == "全期間累計（通算）":
    df_c_target = df_filtered[df_filtered['年'].isin(valid_years)]
    period_label = f"全期間累計（{min(valid_years)}〜{max(valid_years)}年）"
else:
    target_y = int(selected_table_period.replace("年", ""))
    df_c_target = df_filtered[df_filtered['年'] == target_y]
    period_label = f"{target_y}年 年間"

st.caption(f"📌 表示中: **{period_label}** の国別集計結果（単位：億円）")

exp_by_c = df_c_target[df_c_target['輸出入区分'] == '輸出'].groupby('国名')['年間累計_金額_千円'].sum() / UNIT_DIVISOR
imp_by_c = df_c_target[df_c_target['輸出入区分'] == '輸入'].groupby('国名')['年間累計_金額_千円'].sum() / UNIT_DIVISOR

all_c_active = sorted(list(set(exp_by_c.index).union(set(imp_by_c.index))))

df_c_summary = pd.DataFrame({
    '国名': all_c_active,
    '輸出額（億円）': [exp_by_c.get(c, 0.0) for c in all_c_active],
    '輸入額（億円）': [imp_by_c.get(c, 0.0) for c in all_c_active],
})

df_c_summary['収支差額（億円）'] = df_c_summary['輸出額（億円）'] - df_c_summary['輸入額（億円）']
df_c_summary['判定'] = np.where(df_c_summary['収支差額（億円）'] >= 0, '🟩 黒字', '🟥 赤字')
df_c_summary['取引規模合計'] = df_c_summary['輸出額（億円）'] + df_c_summary['輸入額（億円）']

df_c_summary = df_c_summary.sort_values(by='取引規模合計', ascending=False).drop(columns=['取引規模合計']).reset_index(drop=True)

st.dataframe(
    df_c_summary.style.format({
        '輸出額（億円）': '{:,.1f}',
        '輸入額（億円）': '{:,.1f}',
        '収支差額（億円）': '{:+,.1f}'
    }),
    use_container_width=True,
    height=450
)

csv_data = df_c_summary.to_csv(index=False).encode('utf_8_sig')
st.download_button(
    label=f"📥 {period_label} の集計テーブルをCSVでダウンロード",
    data=csv_data,
    file_name=f"trade_summary_by_country_{selected_table_period}.csv",
    mime="text/csv"
)
