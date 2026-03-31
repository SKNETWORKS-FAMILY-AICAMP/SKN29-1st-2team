import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="연령대·성별 분포", layout="wide")

# ── 공통 사이드바 메뉴 ─────────────────────────
with st.sidebar:
    # st.title("🚗 TEAM PROJECT")
    # 2. 인터넷에 있는 GIF URL로 바로 불러오기
    st.image("https://cdn-icons-gif.flaticon.com/7308/7308525.gif", use_container_width=True)

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
def load_age_gender_data(_db):
    rows = _db.query("""
        SELECT ags.age, s.sido, ags.gender, SUM(ags.count) AS count
        FROM age_gender_sido AS ags
        JOIN dim_time AS t ON ags.time_id = t.time_id
        JOIN dim_sido AS s ON ags.sido_id = s.sido_id
        WHERE t.month = 12 AND t.year = 2024
        GROUP BY ags.age, s.sido, ags.gender
        ORDER BY ags.age, s.sido, ags.gender
    """)
    df = pd.DataFrame(rows)
    df["age"]   = pd.to_numeric(df["age"],   errors="coerce")
    df["count"] = pd.to_numeric(df["count"], errors="coerce")
    df["age_label"] = df["age"].astype(int).astype(str) + "대"
    return df


def show_age_gender_chart(df):
    st.caption("2024년 12월 누적 기준")

    sidos = ["전국"] + sorted(df["sido"].unique().tolist())
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_sido = st.selectbox("시도 선택", options=sidos, index=0)
    with col_f2:
        chart_type = st.radio("차트 유형", options=["대수", "비율 (%)"], horizontal=True)

    if selected_sido == "전국":
        df_filtered = (
            df.groupby(["age", "age_label", "gender"])["count"].sum().reset_index()
        )
    else:
        df_filtered = (
            df[df["sido"] == selected_sido]
            .groupby(["age", "age_label", "gender"])["count"]
            .sum()
            .reset_index()
        )

    if chart_type == "비율 (%)":
        total = df_filtered["count"].sum()
        df_filtered["ratio"] = round(df_filtered["count"] / total * 100, 2)

    col1, col2, col3 = st.columns(3)
    with col1:
        male_total = df_filtered[df_filtered["gender"] == "남성"]["count"].sum()
        st.metric(label="남성 차량 보유", value=f"{male_total:,.0f} 대")
    with col2:
        female_total = df_filtered[df_filtered["gender"] == "여성"]["count"].sum()
        st.metric(label="여성 차량 보유", value=f"{female_total:,.0f} 대")
    with col3:
        ratio = round(male_total / (male_total + female_total) * 100, 1)
        st.metric(label="남성 비율", value=f"{ratio}%")

    st.markdown("---")
    y_col     = "ratio" if chart_type == "비율 (%)" else "count"
    y_label   = "비율 (%)" if chart_type == "비율 (%)" else "등록 대수"
    age_order = [str(a) + "대" for a in sorted(df_filtered["age"].unique())]

    fig = px.bar(
        df_filtered.sort_values("age"),
        x="age_label",
        y=y_col,
        color="gender",
        title=f"연령대·성별 차량 등록 분포 ({selected_sido}) — 2024년 12월 기준",
        labels={"age_label": "연령대", y_col: y_label, "gender": "성별"},
        barmode="group",
        color_discrete_map={"남성": "#2171b5", "여성": "#fd8d3c"},
        category_orders={"age_label": age_order},
        text_auto=True,
    )
    fig.update_layout(
        title_x=0.5,
        xaxis_title="연령대",
        yaxis_title=y_label,
        legend_title="성별",
        hovermode="x unified",
    )
    if chart_type == "비율 (%)":
        fig.update_traces(hovertemplate="%{y:.2f}%")
    else:
        fig.update_traces(hovertemplate="%{y:,}대")

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("원본 데이터 보기"):
        st.dataframe(
            df_filtered[["age_label", "gender", "count"]]
            .sort_values(["age_label", "gender"])
            .reset_index(drop=True),
            use_container_width=True,
        )


def main():
    st.title("연령대·성별 차량 등록 분포")
    st.markdown("---")
    df_age_gender = load_age_gender_data(db)
    show_age_gender_chart(df_age_gender)


main()
