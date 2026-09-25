import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="貿易統計ダッシュボード｜国別・品目別推移",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- 定数 -----------------
UNIT_LABEL = "金額（億円）"
UNIT_DIVISOR = 100_000

# --- ダークテーマ基本パレット ---
BG_MAIN = "#05070B"        # ページ背景（漆黒に近いネイビー）
BG_CARD = "#1B2029"        # カード・サイドバー背景
BG_CARD_HOVER = "#232A35"  # カードのホバー背景
BORDER_COLOR = "#2E3746"   # カード・区切り線
TEXT_PRIMARY = "#F2F4F8"   # 主要テキスト（白に近いグレー）
TEXT_MUTED = "#8B93A1"     # 補助テキスト

ACCENT = "#22E6A0"         # アクセントのミントグリーン
ACCENT_HOVER = "#17C989"   # ホバー時の濃いグリーン
ACCENT_SOFT = "rgba(34,230,160,0.16)"  # 淡いグリーン背景

EXPORT_COLOR = "#60A5FA"   # 輸出：ブルー（ダーク背景用に明るめ）
IMPORT_COLOR = "#FBBF24"   # 輸入：アンバー
SURPLUS_COLOR = ACCENT     # 黒字：グリーン
DEFICIT_COLOR = "#F87171"  # 赤字：レッド
NET_LINE_COLOR = TEXT_PRIMARY  # 収支差額ライン：明るいグレー
GRID_COLOR = BORDER_COLOR
CHIP_BG = "#12161E"

# --- 立体感・光沢演出用（はっきり視認できる濃さに設定） ---
CARD_GRAD = "linear-gradient(155deg, #2A3242 0%, #1B2029 45%, #10141B 100%)"
CARD_GRAD_HOVER = "linear-gradient(155deg, #333D50 0%, #212836 45%, #12161D 100%)"
CHIP_GRAD = "linear-gradient(180deg, #232B38 0%, #0C0F15 100%)"
GLASS_BORDER = "rgba(255,255,255,0.16)"
SHADOW_CARD = "0 20px 44px -14px rgba(0,0,0,0.85), 0 0 0 1px rgba(255,255,255,0.06) inset, 0 0 28px rgba(34,230,160,0.10)"
SHADOW_CARD_HOVER = "0 26px 54px -14px rgba(0,0,0,0.9), 0 0 0 1px rgba(34,230,160,0.45), 0 0 42px rgba(34,230,160,0.28)"
GLOW_ACCENT = "0 6px 24px rgba(34,230,160,0.55), 0 0 0 1px rgba(255,255,255,0.25) inset"
TOP_STRIPE = "linear-gradient(90deg, {0} 0%, rgba(255,255,255,0.35) 55%, transparent 100%)".format(ACCENT)

CHART_FONT = dict(family="Helvetica, Arial, sans-serif", color=TEXT_PRIMARY)



# ----------------- グローバルCSS -----------------
st.markdown(f"""
<style>
    /* ページ全体：はっきり見える光暈グラデーション背景 */
    .stApp {{
        background:
            radial-gradient(1100px 520px at 8% -8%, rgba(34,230,160,0.20), transparent 60%),
            radial-gradient(900px 480px at 96% 4%, rgba(96,165,250,0.16), transparent 55%),
            radial-gradient(1300px 900px at 50% 115%, rgba(34,230,160,0.10), transparent 60%),
            {BG_MAIN};
    }}
    [data-testid="stSidebar"] {{
        background:
            radial-gradient(500px 260px at 10% 0%, rgba(34,230,160,0.14), transparent 55%),
            linear-gradient(180deg, #1A2029 0%, #0A0D12 100%);
        border-right: 1px solid {GLASS_BORDER};
        box-shadow: 10px 0 32px rgba(0,0,0,0.55);
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: transparent;
    }}
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }}
    h1, h2, h3, h4, h5, p, span, label {{
        color: {TEXT_PRIMARY};
    }}
    h1, h2, h3 {{
        font-weight: 700;
        letter-spacing: -0.01em;
    }}
    h1 {{
        background: linear-gradient(90deg, #FFFFFF 0%, {ACCENT} 120%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(34,230,160,0.25);
    }}
    /* KPIカード：はっきりした斜めグラデーション＋二重シャドウ＋上端アクセントライン */
    .kpi-card {{
        position: relative;
        overflow: hidden;
        background: {CARD_GRAD};
        border: 1px solid {GLASS_BORDER};
        border-radius: 16px;
        padding: 22px 22px 20px 22px;
        height: 100%;
        box-shadow: {SHADOW_CARD};
        transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
    }}
    .kpi-card::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: {TOP_STRIPE};
        opacity: 0.9;
    }}
    .kpi-card::after {{
        content: "";
        position: absolute;
        top: -40%; left: -10%;
        width: 70%; height: 90%;
        background: radial-gradient(circle, rgba(255,255,255,0.08), transparent 70%);
        pointer-events: none;
    }}
    .kpi-card:hover {{
        background: {CARD_GRAD_HOVER};
        box-shadow: {SHADOW_CARD_HOVER};
        transform: translateY(-4px);
    }}
    .kpi-label {{
        font-size: 0.80rem;
        color: {TEXT_MUTED};
        font-weight: 600;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .kpi-value {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        line-height: 1.2;
        text-shadow: 0 2px 12px rgba(0,0,0,0.35);
    }}
    .kpi-sub {{
        font-size: 0.78rem;
        color: {TEXT_MUTED};
        margin-top: 4px;
    }}
    .badge-surplus {{
        display: inline-block;
        background: linear-gradient(135deg, rgba(34,230,160,0.40), rgba(34,230,160,0.10));
        color: #B8FFE4;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.9rem;
        box-shadow: 0 0 0 1px rgba(34,230,160,0.55), 0 4px 18px rgba(34,230,160,0.35);
    }}
    .badge-deficit {{
        display: inline-block;
        background: linear-gradient(135deg, rgba(248,113,113,0.40), rgba(248,113,113,0.10));
        color: #FFD7D7;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.9rem;
        box-shadow: 0 0 0 1px rgba(248,113,113,0.55), 0 4px 18px rgba(248,113,113,0.30);
    }}
    .section-caption {{
        color: {TEXT_MUTED};
        font-size: 0.85rem;
        margin-top: -6px;
        margin-bottom: 10px;
    }}
    .scroll-top-btn {{
        position: fixed;
        bottom: 25px;
        right: 30px;
        z-index: 9999;
        background: linear-gradient(155deg, #3CF4B8 0%, {ACCENT} 55%, {ACCENT_HOVER} 100%);
        color: {BG_MAIN} !important;
        border: none;
        border-radius: 50%;
        width: 48px;
        height: 48px;
        font-size: 20px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: {GLOW_ACCENT};
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
    }}
    .scroll-top-btn:hover {{
        box-shadow: 0 6px 26px rgba(34,230,160,0.65), 0 0 0 1px rgba(34,230,160,0.4) inset;
        transform: translateY(-3px) scale(1.04);
    }}
    #top-anchor {{ position: absolute; top: 0; left: 0; }}

    /* タブ：グラデーション＋グロー付きセグメントコントロール */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: linear-gradient(180deg, #151B24 0%, #10141B 100%);
        border: 1px solid {GLASS_BORDER};
        padding: 6px;
        border-radius: 14px;
        margin-bottom: 4px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.4);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 46px;
        border-radius: 10px;
        padding: 0 22px;
        background-color: transparent;
        font-weight: 600;
        font-size: 0.95rem;
        color: {TEXT_MUTED};
        border: none;
        transition: all 0.15s ease;
    }}
    .stTabs [data-baseweb="tab"] p {{
        color: inherit;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {TEXT_PRIMARY};
        background-color: rgba(255,255,255,0.04);
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(155deg, rgba(34,230,160,0.35), rgba(34,230,160,0.10)) !important;
        color: #B8FFE4 !important;
        box-shadow: inset 0 0 0 1px rgba(34,230,160,0.60), 0 6px 20px rgba(34,230,160,0.35);
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab-border"] {{
        display: none;
    }}

    /* KPIの前年比デルタ */
    .kpi-delta {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.80rem;
        font-weight: 700;
        margin-top: 8px;
        padding: 3px 10px;
        border-radius: 999px;
    }}
    .delta-up {{ color: #B8FFE4; background: linear-gradient(135deg, rgba(34,230,160,0.35), rgba(34,230,160,0.08)); box-shadow: 0 0 0 1px rgba(34,230,160,0.40); }}
    .delta-down {{ color: #FFD7D7; background: linear-gradient(135deg, rgba(248,113,113,0.35), rgba(248,113,113,0.08)); box-shadow: 0 0 0 1px rgba(248,113,113,0.40); }}
    .delta-flat {{ color: {TEXT_MUTED}; background: rgba(139,147,161,0.16); box-shadow: 0 0 0 1px rgba(139,147,161,0.25); }}

    /* フィルターチップ */
    .filter-chip-label {{
        font-size: 0.78rem;
        font-weight: 700;
        color: {TEXT_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
    }}
    .stButton > button {{
        border-radius: 999px;
        border: 1px solid {GLASS_BORDER};
        background: {CHIP_GRAD};
        color: {TEXT_PRIMARY};
        font-size: 0.82rem;
        font-weight: 600;
        padding: 4px 10px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.08);
        transition: all 0.15s ease;
    }}
    .stButton > button:hover {{
        border-color: rgba(34,230,160,0.65);
        color: #B8FFE4;
        background: linear-gradient(180deg, rgba(34,230,160,0.24) 0%, #0D1017 100%);
        box-shadow: 0 6px 20px rgba(34,230,160,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
        transform: translateY(-1px);
    }}
    .stButton > button p {{
        color: inherit;
    }}

    /* サイドバーのセレクト・マルチセレクト・ラジオ類 */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: {CHIP_GRAD};
        border-color: {GLASS_BORDER};
        box-shadow: inset 0 1px 4px rgba(0,0,0,0.5);
    }}
    span[data-baseweb="tag"] {{
        background: linear-gradient(135deg, rgba(34,230,160,0.45), rgba(34,230,160,0.15)) !important;
        color: #063324 !important;
        font-weight: 700 !important;
        box-shadow: 0 0 0 1px rgba(34,230,160,0.55), 0 3px 12px rgba(34,230,160,0.30);
    }}

    /* データフレーム */
    [data-testid="stDataFrame"] {{
        border: 1px solid {GLASS_BORDER};
        border-radius: 12px;
        overflow: hidden;
        box-shadow: {SHADOW_CARD};
    }}

    /* Plotlyチャートをガラスカードで包む */
    [data-testid="stPlotlyChart"] {{
        background: {CARD_GRAD};
        border: 1px solid {GLASS_BORDER};
        border-radius: 18px;
        padding: 14px 10px 4px 10px;
        box-shadow: {SHADOW_CARD};
    }}

    /* 区切り線をグラデーションに */
    hr {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, {GLASS_BORDER} 20%, {GLASS_BORDER} 80%, transparent);
        margin: 1.2rem 0;
    }}
</style>
<div id="top-anchor"></div>
<a href="#top-anchor" class="scroll-top-btn" title="最上部へ戻る">↑</a>
""", unsafe_allow_html=True)


DELTA_ARROW = {"up": "▲", "down": "▼", "flat": "ー"}
DELTA_CLASS = {"up": "delta-up", "down": "delta-down", "flat": "delta-flat"}


def calc_delta(curr, prev):
    """前年比の方向とラベルを計算。比較対象がなければNoneを返す。"""
    if prev is None or prev == 0:
        return None
    pct = (curr - prev) / abs(prev) * 100
    direction = "up" if pct > 0.05 else ("down" if pct < -0.05 else "flat")
    return direction, f"前年比 {pct:+.1f}%"


def kpi_card(label, value, sub="", delta=None):
    delta_html = ""
    if delta is not None:
        direction, delta_text = delta
        delta_html = (
            f'<div class="kpi-delta {DELTA_CLASS[direction]}">'
            f'{DELTA_ARROW[direction]} {delta_text}</div>'
        )
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ----------------- データの読み込み -----------------
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
st.sidebar.markdown("### 検索・絞り込み条件")

if st.sidebar.button("条件をリセット", use_container_width=True):
    for key in ['selected_countries', 'selected_hs', 'time_granularity']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

time_granularity = st.sidebar.radio(
    "推移チャートの表示単位",
    ["年次推移", "月次推移"],
    index=0,
    key="time_granularity",
    horizontal=True
)

country_trade_totals = df_raw.groupby('国名')['年間累計_金額_千円'].sum().sort_values(ascending=False)
top_countries_list = country_trade_totals.head(20).index.tolist()
all_countries = sorted(df_raw['国名'].dropna().unique().tolist())

st.sidebar.markdown("---")
st.sidebar.markdown("**国・地域の選択**")

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("TOP 10", use_container_width=True):
    st.session_state['selected_countries'] = top_countries_list[:10]
    st.rerun()
if col_btn2.button("選択解除", use_container_width=True):
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
st.sidebar.markdown("**品目の選択（HS品目大分類）**")
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

# ----------------- ヘッダー -----------------
st.title("日本の貿易統計ダッシュボード")
target_country_text = "、".join(selected_countries) if selected_countries else "全世界（全カ国・地域）"
target_hs_text = f"{len(selected_hs)} 類を選択中" if selected_hs else "全品目（96類）"
st.markdown(
    f'<div class="section-caption">対象国・地域: <b>{target_country_text}</b> ｜ 対象品目: <b>{target_hs_text}</b></div>',
    unsafe_allow_html=True
)

# ----------------- アクティブフィルターチップ -----------------
def _remove_filter_value(skey, val):
    """on_clickコールバック内で実行 = ウィジェット再生成より前に安全にsession_stateを更新できる"""
    st.session_state[skey] = [v for v in st.session_state[skey] if v != val]


def _clear_all_filters():
    st.session_state['selected_countries'] = []
    st.session_state['selected_hs'] = []


chip_items = [("selected_countries", c) for c in selected_countries] + \
             [("selected_hs", h) for h in selected_hs]

if chip_items:
    st.markdown('<div class="filter-chip-label">絞り込み中のフィルター（クリックで解除）</div>', unsafe_allow_html=True)
    CHIPS_PER_ROW = 7
    for row_start in range(0, len(chip_items), CHIPS_PER_ROW):
        row_items = chip_items[row_start:row_start + CHIPS_PER_ROW]
        cols = st.columns(len(row_items))
        for col, (skey, val) in zip(cols, row_items):
            with col:
                st.button(
                    f"{val}  ✕",
                    key=f"chip_{skey}_{val}",
                    use_container_width=True,
                    on_click=_remove_filter_value,
                    args=(skey, val)
                )
    st.button("すべて解除", key="clear_all_chips", on_click=_clear_all_filters)
    st.write("")

# 年次データの集計（KPI・推移タブ共通）
annual_exp = df_filtered[df_filtered['輸出入区分'] == '輸出'].groupby('年')['年間累計_金額_千円'].sum() / UNIT_DIVISOR
annual_imp = df_filtered[df_filtered['輸出入区分'] == '輸入'].groupby('年')['年間累計_金額_千円'].sum() / UNIT_DIVISOR
common_years = sorted(list(set(annual_exp.index).intersection(set(annual_imp.index))))
valid_years = sorted([y for y in common_years if y <= 2025], reverse=True)
latest_year = valid_years[0] if valid_years else None

# ----------------- KPIサマリ（常時表示） -----------------
if latest_year:
    latest_exp = annual_exp.get(latest_year, 0)
    latest_imp = annual_imp.get(latest_year, 0)
    latest_net = latest_exp - latest_imp
    badge_html = (f'<span class="badge-surplus">黒字</span>' if latest_net >= 0
                  else f'<span class="badge-deficit">赤字</span>')

    prev_year = valid_years[1] if len(valid_years) > 1 else None
    prev_exp = annual_exp.get(prev_year, 0) if prev_year else None
    prev_imp = annual_imp.get(prev_year, 0) if prev_year else None
    prev_net = (prev_exp - prev_imp) if prev_year else None
    prev_status_text = ""
    if prev_year is not None:
        prev_status_text = f"前年（{prev_year}年）: " + ("黒字" if prev_net >= 0 else "赤字")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("総輸出額", f"{latest_exp:,.0f} 億円", f"{latest_year}年",
                  delta=calc_delta(latest_exp, prev_exp))
    with k2:
        kpi_card("総輸入額", f"{latest_imp:,.0f} 億円", f"{latest_year}年",
                  delta=calc_delta(latest_imp, prev_imp))
    with k3:
        kpi_card("貿易収支（輸出－輸入）", f"{latest_net:+,.0f} 億円", f"{latest_year}年",
                  delta=calc_delta(latest_net, prev_net))
    with k4:
        kpi_card("収支判定", badge_html, prev_status_text)

st.write("")

# ----------------- タブ構成 -----------------
tab_trend, tab_hs, tab_country = st.tabs(["📈 推移", "⚖️ 品目別内訳", "🌍 国別一覧"])

# ===== タブ1: 時系列推移 =====
with tab_trend:
    st.markdown("##### 輸出入および貿易収支の時系列推移")
    st.markdown(
        '<div class="section-caption">凡例をクリックすると系列の表示/非表示を切り替えられます（ダブルクリックで単独表示）。</div>',
        unsafe_allow_html=True
    )

    if time_granularity == "年次推移":
        years = valid_years[::-1]
        df_trend = pd.DataFrame({
            '年': years,
            '輸出額': [annual_exp.get(y, 0) for y in years],
            '輸入額': [annual_imp.get(y, 0) for y in years],
        })
        df_trend['収支差額'] = df_trend['輸出額'] - df_trend['輸入額']

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=df_trend['年'], y=df_trend['輸出額'],
            name='輸出額',
            marker=dict(color=EXPORT_COLOR, line=dict(color='rgba(255,255,255,0.18)', width=1)),
            hovertemplate='%{x}年 輸出額: %{y:,.1f} 億円<extra></extra>'
        ))
        fig_trend.add_trace(go.Bar(
            x=df_trend['年'], y=df_trend['輸入額'],
            name='輸入額',
            marker=dict(color=IMPORT_COLOR, line=dict(color='rgba(255,255,255,0.18)', width=1)),
            hovertemplate='%{x}年 輸入額: %{y:,.1f} 億円<extra></extra>'
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_trend['年'], y=df_trend['収支差額'],
            name='収支差額（輸出－輸入）',
            mode='lines+markers',
            line=dict(color=NET_LINE_COLOR, width=2.5, shape='spline'),
            marker=dict(size=8, color=BG_MAIN, line=dict(color=NET_LINE_COLOR, width=2)),
            fill='tozeroy',
            fillcolor='rgba(230,233,239,0.08)',
            hovertemplate='%{x}年 収支差額: %{y:+,.1f} 億円<extra></extra>'
        ))
        fig_trend.update_layout(
            barmode='group',
            font=CHART_FONT,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title='年', tickmode='linear', gridcolor=GRID_COLOR, showline=True, linecolor=GRID_COLOR),
            yaxis=dict(title=UNIT_LABEL, tickformat=',.0f', ticksuffix=' 億円', gridcolor=GRID_COLOR),
            hovermode='x unified',
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255,255,255,0.03)", bordercolor="rgba(255,255,255,0.08)", borderwidth=1),
            margin=dict(t=40, l=10, r=10, b=10)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    else:  # 月次推移
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
            name='輸出額', mode='lines', line=dict(color=EXPORT_COLOR, width=2.5, shape='spline'),
            fill='tozeroy', fillcolor='rgba(96,165,250,0.10)',
            hovertemplate='%{x} 輸出額: %{y:,.1f} 億円<extra></extra>'
        ))
        fig_m.add_trace(go.Scatter(
            x=df_monthly['年月'], y=df_monthly['輸入額'],
            name='輸入額', mode='lines', line=dict(color=IMPORT_COLOR, width=2.5, shape='spline'),
            fill='tozeroy', fillcolor='rgba(251,191,36,0.08)',
            hovertemplate='%{x} 輸入額: %{y:,.1f} 億円<extra></extra>'
        ))
        fig_m.add_trace(go.Bar(
            x=df_monthly['年月'], y=df_monthly['収支差額'],
            name='収支差額',
            marker=dict(
                color=np.where(df_monthly['収支差額'] >= 0, SURPLUS_COLOR, DEFICIT_COLOR),
                line=dict(color='rgba(255,255,255,0.15)', width=0.5)
            ),
            hovertemplate='%{x} 収支差額: %{y:+,.1f} 億円<extra></extra>',
            opacity=0.6
        ))
        fig_m.update_layout(
            font=CHART_FONT,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title='年月', tickangle=-45, gridcolor=GRID_COLOR),
            yaxis=dict(title=UNIT_LABEL, tickformat=',.0f', ticksuffix=' 億円', gridcolor=GRID_COLOR),
            hovermode='x unified',
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255,255,255,0.03)", bordercolor="rgba(255,255,255,0.08)", borderwidth=1),
            margin=dict(t=40, l=10, r=10, b=10)
        )
        st.plotly_chart(fig_m, use_container_width=True)

# ===== タブ2: 品目別内訳 =====
with tab_hs:
    year_for_breakdown = st.selectbox(
        "内訳表示の対象年を選択",
        options=valid_years,
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

    df_hs_top = df_hs_summary.sort_values(by='取引規模（合計）', ascending=False).head(20)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### 輸出入バタフライチャート")
        fig_bf = go.Figure()
        fig_bf.add_trace(go.Bar(
            y=df_hs_top['HS品目大分類'],
            x=-df_hs_top['輸入額'],
            orientation='h',
            name='輸入額',
            marker=dict(color=IMPORT_COLOR, line=dict(color='rgba(255,255,255,0.15)', width=0.5)),
            hovertemplate='%{y}<br>輸入額: %{customdata:,.1f} 億円<extra></extra>',
            customdata=df_hs_top['輸入額']
        ))
        fig_bf.add_trace(go.Bar(
            y=df_hs_top['HS品目大分類'],
            x=df_hs_top['輸出額'],
            orientation='h',
            name='輸出額',
            marker=dict(color=EXPORT_COLOR, line=dict(color='rgba(255,255,255,0.15)', width=0.5)),
            hovertemplate='%{y}<br>輸出額: %{x:,.1f} 億円<extra></extra>'
        ))
        fig_bf.update_layout(
            barmode='relative',
            font=CHART_FONT,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange='reversed', title=''),
            xaxis=dict(title='← 輸入超過 ｜ 輸出超過 →', tickformat=',.0f', ticksuffix=' 億円', gridcolor=GRID_COLOR),
            height=560,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255,255,255,0.03)", bordercolor="rgba(255,255,255,0.08)", borderwidth=1),
            margin=dict(t=40, l=10, r=10, b=10)
        )
        st.plotly_chart(fig_bf, use_container_width=True)

    with col_chart2:
        st.markdown("##### 品目別 純収支（輸出－輸入）")
        df_hs_top_sorted = df_hs_top.sort_values(by='貿易収支（差額）', ascending=True)
        fig_net = go.Figure()
        fig_net.add_trace(go.Bar(
            y=df_hs_top_sorted['HS品目大分類'],
            x=df_hs_top_sorted['貿易収支（差額）'],
            orientation='h',
            marker=dict(
                color=np.where(df_hs_top_sorted['貿易収支（差額）'] >= 0, SURPLUS_COLOR, DEFICIT_COLOR),
                line=dict(color='rgba(255,255,255,0.15)', width=0.5)
            ),
            hovertemplate='%{y}<br>収支差額: %{x:+,.1f} 億円<extra></extra>',
            name='収支差額'
        ))
        fig_net.update_layout(
            font=CHART_FONT,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(title=''),
            xaxis=dict(title='緑=黒字 ／ 赤=赤字', tickformat=',.0f', ticksuffix=' 億円', gridcolor=GRID_COLOR),
            height=560,
            showlegend=False,
            margin=dict(t=40, l=10, r=10, b=10)
        )
        st.plotly_chart(fig_net, use_container_width=True)

    st.markdown(
        '<div class="section-caption">取引規模（輸出＋輸入）上位20品目を表示しています。</div>',
        unsafe_allow_html=True
    )

# ===== タブ3: 国別一覧 =====
with tab_country:
    period_options = ["全期間累計（通算）"] + [f"{y}年" for y in valid_years]

    selected_table_period = st.selectbox(
        "表示する集計期間を選択",
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

    st.markdown(
        f'<div class="section-caption">表示中: <b>{period_label}</b> の国別集計結果（単位：億円）</div>',
        unsafe_allow_html=True
    )

    exp_by_c = df_c_target[df_c_target['輸出入区分'] == '輸出'].groupby('国名')['年間累計_金額_千円'].sum() / UNIT_DIVISOR
    imp_by_c = df_c_target[df_c_target['輸出入区分'] == '輸入'].groupby('国名')['年間累計_金額_千円'].sum() / UNIT_DIVISOR

    all_c_active = sorted(list(set(exp_by_c.index).union(set(imp_by_c.index))))

    df_c_summary = pd.DataFrame({
        '国名': all_c_active,
        '輸出額（億円）': [exp_by_c.get(c, 0.0) for c in all_c_active],
        '輸入額（億円）': [imp_by_c.get(c, 0.0) for c in all_c_active],
    })

    df_c_summary['収支差額（億円）'] = df_c_summary['輸出額（億円）'] - df_c_summary['輸入額（億円）']
    df_c_summary['判定'] = np.where(df_c_summary['収支差額（億円）'] >= 0, '黒字', '赤字')
    df_c_summary['取引規模合計'] = df_c_summary['輸出額（億円）'] + df_c_summary['輸入額（億円）']

    df_c_summary = df_c_summary.sort_values(by='取引規模合計', ascending=False).drop(columns=['取引規模合計']).reset_index(drop=True)

    st.dataframe(
        df_c_summary.style.format({
            '輸出額（億円）': '{:,.1f}',
            '輸入額（億円）': '{:,.1f}',
            '収支差額（億円）': '{:+,.1f}'
        }).map(
            lambda v: f'color: {SURPLUS_COLOR}; font-weight:600' if v == '黒字'
            else f'color: {DEFICIT_COLOR}; font-weight:600',
            subset=['判定']
        ),
        use_container_width=True,
        height=420
    )

    csv_data = df_c_summary.to_csv(index=False).encode('utf_8_sig')
    st.download_button(
        label=f"{period_label} の集計テーブルをCSVでダウンロード",
        data=csv_data,
        file_name=f"trade_summary_by_country_{selected_table_period}.csv",
        mime="text/csv"
    )
