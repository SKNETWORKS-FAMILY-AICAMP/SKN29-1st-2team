import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="연료별 비중 변화", layout="wide")

# ── 공통 사이드바 메뉴 ─────────────────────────
with st.sidebar:
    # st.title("🚗 TEAM PROJECT")
    # st.image("https://cdn-icons-gif.flaticon.com/7308/7308525.gif", use_container_width=True)
    # st.write("---")
    # st.page_link로 클릭 시 해당 페이지로 전환
    st.page_link("app.py", label="📊 차량 등록 현황")
    st.page_link("pages/1_소득_vs_외제차.py", label="💰 소득 vs 외제차")
    st.page_link("pages/2_연료별_비중.py", label="⛽ 연료별 비중")
    st.page_link("pages/3_연령대_성별.py", label="👥 연령대 및 성별")
    st.page_link("pages/4_FAQ.py", label="💡 자동차 FAQ")

# 기본 메뉴 숨기기
st.markdown(
    """
    <style>
    /* Streamlit 기본 사이드바 메뉴 숨기기 */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_resource
def get_db():
    return DBManager(
        host     = os.getenv("DB_HOST"),
        user     = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME"),
        port     = int(os.getenv("DB_PORT", 3306)),
    )

db = get_db()


@st.cache_data
def load_fuel_data(_db):
    rows = _db.query("""
        SELECT t.year, s.sido, f.fuel, SUM(f.count) AS count
        FROM fuel_sido AS f
        JOIN dim_time AS t ON f.time_id = t.time_id
        JOIN dim_sido AS s ON f.sido_id = s.sido_id
        WHERE t.month = 12
        GROUP BY t.year, s.sido, f.fuel
        ORDER BY t.year, s.sido, count DESC
    """)
    df = pd.DataFrame(rows)
    df["year"]  = pd.to_numeric(df["year"],  errors="coerce")
    df["count"] = pd.to_numeric(df["count"], errors="coerce")
    major_fuels = [
        "휘발유", "경유", "엘피지", "하이브리드(휘발유+전기)",
        "전기", "하이브리드(경유+전기)", "수소",
    ]
    df["fuel_group"] = df["fuel"].apply(lambda x: x if x in major_fuels else "기타")
    return df


def show_fuel_chart(df):
    st.caption("누적 등록 기준 (매년 12월 기준) — ※ 2025년은 미완성 데이터입니다.")

    sidos = ["전국"] + sorted(df["sido"].unique().tolist())
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_sido = st.selectbox("시도 선택", options=sidos, index=0)
    with col_f2:
        chart_type = st.radio("차트 유형", options=["비율 (%)", "대수"], horizontal=True)

    if selected_sido == "전국":
        df_filtered = df.groupby(["year", "fuel_group"])["count"].sum().reset_index()
    else:
        df_filtered = (
            df[df["sido"] == selected_sido]
            .groupby(["year", "fuel_group"])["count"]
            .sum()
            .reset_index()
        )

    pivot_total = (
        df_filtered.groupby("year")["count"]
        .sum()
        .reset_index()
        .rename(columns={"count": "total"})
    )
    df_filtered = df_filtered.merge(pivot_total, on="year")
    df_filtered["ratio"] = round(df_filtered["count"] / df_filtered["total"] * 100, 2)

    fuel_order = [
        "휘발유", "경유", "엘피지", "하이브리드(휘발유+전기)",
        "전기", "하이브리드(경유+전기)", "수소", "기타",
    ]
    fuel_colors = {
        "휘발유":                  "#084594",
        "경유":                    "#2171b5",
        "엘피지":                  "#4292c6",
        "하이브리드(휘발유+전기)": "#74c476",
        "전기":                    "#238b45",
        "하이브리드(경유+전기)":   "#a1d99b",
        "수소":                    "#fd8d3c",
        "기타":                    "#d9d9d9",
    }

    latest = df_filtered[df_filtered["year"] == df_filtered["year"].max()]
    col1, col2, col3 = st.columns(3)
    with col1:
        ev = latest[latest["fuel_group"] == "전기"]["ratio"].values
        st.metric(label=f"{latest['year'].max()}년 전기차 비율",
                  value=f"{ev[0]:.1f}%" if len(ev) > 0 else "N/A")
    with col2:
        hybrid = latest[latest["fuel_group"] == "하이브리드(휘발유+전기)"]["ratio"].values
        st.metric(label=f"{latest['year'].max()}년 하이브리드 비율",
                  value=f"{hybrid[0]:.1f}%" if len(hybrid) > 0 else "N/A")
    with col3:
        gasoline = latest[latest["fuel_group"] == "휘발유"]["ratio"].values
        st.metric(label=f"{latest['year'].max()}년 휘발유 비율",
                  value=f"{gasoline[0]:.1f}%" if len(gasoline) > 0 else "N/A")

    st.markdown("---")
    y_col   = "ratio" if chart_type == "비율 (%)" else "count"
    y_label = "비율 (%)" if chart_type == "비율 (%)" else "등록 대수"

    fig = px.bar(
        df_filtered,
        x="year",
        y=y_col,
        color="fuel_group",
        title=f"연료별 차량 등록 비중 ({selected_sido}) — 12월 누적 기준",
        labels={"year": "연도", y_col: y_label, "fuel_group": "연료 종류"},
        barmode="stack",
        category_orders={"fuel_group": fuel_order},
        color_discrete_map=fuel_colors,
        text_auto=".1f" if chart_type == "비율 (%)" else False,
    )
    fig.update_layout(
        title_x=0.5,
        xaxis_title="연도",
        yaxis_title=y_label,
        yaxis=dict(range=[0, 100]) if chart_type == "비율 (%)" else {},
        legend_title="연료 종류",
        hovermode="x unified",
        xaxis=dict(tickmode="linear"),
    )
    if chart_type == "비율 (%)":
        fig.update_traces(hovertemplate="%{y:.2f}%")

    y_val = (
        100
        if chart_type == "비율 (%)"
        else df_filtered[df_filtered["year"] == 2025]["count"].sum()
    )
    fig.add_annotation(
        x=2025, y=y_val, text="※ 추가 수집 필요",
        showarrow=False, yanchor="bottom",
        font=dict(color="red", size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("원본 데이터 보기"):
        st.dataframe(
            df_filtered[["year", "fuel_group", "count", "ratio"]]
            .sort_values(["year", "count"], ascending=[True, False])
            .reset_index(drop=True),
            use_container_width=True,
        )


def main():
    st.title("연료별 차량 등록 비중 변화")
    st.markdown("---")
    df_fuel = load_fuel_data(db)
    show_fuel_chart(df_fuel)


main()
