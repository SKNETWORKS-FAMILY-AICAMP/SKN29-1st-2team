import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="차량 등록 현황 대시보드", layout="wide")

# ── 공통 사이드바 메뉴 ─────────────────────────
with st.sidebar:
    # st.title("🚗 TEAM PROJECT")
    # 2. 인터넷에 있는 GIF URL로 바로 불러오기
    st.image("https://cdn-icons-gif.flaticon.com/7308/7308525.gif", use_container_width=True)
    st.write("---")
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


# ── 데이터 로드 ───────────────────────────────────────────
@st.cache_data
def load_newreg_data(_db):
    rows = _db.query("""
        SELECT
            year,
            SUM(passenger_newcar)      AS newcar,
            SUM(passenger_newimported) AS newimported
        FROM new_foreign_domestic_sido AS newfd
        JOIN dim_time AS t ON newfd.time_id = t.time_id
        JOIN dim_sido AS s ON newfd.sido_id = s.sido_id
        GROUP BY year
        ORDER BY year DESC
    """)
    df = pd.DataFrame(rows)
    df["year"]        = pd.to_numeric(df["year"],        errors="coerce")
    df["newcar"]      = pd.to_numeric(df["newcar"],      errors="coerce")
    df["newimported"] = pd.to_numeric(df["newimported"], errors="coerce")
    return df


# ── 메인 현황 카드 ────────────────────────────────────────
def show_main_dashboard(df):
    totalnew_do = df.iloc[0]["newcar"]
    totalnew_fo = df.iloc[0]["newimported"]
    total_do    = df["newcar"].sum()
    total_fo    = df["newimported"].sum()

    st.header("국산차 vs 외제차 현황")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("국산차")
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            st.metric(label="누적 등록",      value=f"{round(total_do / 1_000_000, 2)}M")
        with col1_2:
            st.metric(label="2025 신규 등록", value=f"{round(totalnew_do / 1_000_000, 2)}M")
        with col1_3:
            st.metric(label="신규 등록 비율", value=f"{round(totalnew_do / total_do * 100)}%")

    with col2:
        st.subheader("외제차")
        col2_1, col2_2, col2_3 = st.columns(3)
        with col2_1:
            st.metric(label="누적 등록",      value=f"{round(total_fo / 1_000_000, 2)}M")
        with col2_2:
            st.metric(label="2025 신규",      value=f"{round(totalnew_fo / 1_000_000, 2)}M")
        with col2_3:
            st.metric(label="신규 등록 비율", value=f"{round(totalnew_fo / total_fo * 100)}%")


# ── 연도별 신규등록 비율 라인 차트 ────────────────────────
def show_line_chart(df):
    st.header("연도별 신규등록 비율 비교 (국산/외제차)")

    total_do = df["newcar"].sum()
    total_fo = df["newimported"].sum()

    df_chart = df.sort_values("year").reset_index(drop=True).copy()
    df_chart["국산차 비율"] = round(df_chart["newcar"]      / total_do * 100, 2)
    df_chart["외제차 비율"] = round(df_chart["newimported"] / total_fo * 100, 2)
    df_chart = df_chart.rename(columns={"year": "연도"})

    fig = px.line(
        df_chart,
        x="연도",
        y=["국산차 비율", "외제차 비율"],
        title="연도별 국산차 vs 외제차 신규등록 비율 (전체 대비)",
        markers=True,
        labels={"value": "비율 (%)", "variable": "구분"},
    )
    fig.update_layout(
        title_x=0.5,
        xaxis_title="연도",
        yaxis_title="비율 (%)",
        legend_title="구분",
        hovermode="x unified",
    )
    fig.update_traces(hovertemplate="%{y:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


# ── 판매 Top 5 ────────────────────────────────────────────
def show_top5():
    st.header("판매 Top 5")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("국산차 Top 5")
        domestic_top5 = [
            {"순위": 1, "차량명": "쏘렌토",   "판매 대수": 100002, "image": "https://autoimg.danawa.com/photo/4563/model_200.png"},
            {"순위": 2, "차량명": "카니발",   "판매 대수": 78218,  "image": "https://autoimg.danawa.com/photo/4586/model_200.png"},
            {"순위": 3, "차량명": "아반떼",   "판매 대수": 77636,  "image": "https://autoimg.danawa.com/photo/4455/model_200.png"},
            {"순위": 4, "차량명": "스포티지", "판매 대수": 74517,  "image": "https://autoimg.danawa.com/photo/4684/model_200.png"},
            {"순위": 5, "차량명": "그랜저",   "판매 대수": 71775,  "image": "https://autoimg.danawa.com/photo/4188/model_200.png"},
        ]
        for item in domestic_top5:
            img_col, data_col = st.columns([1, 3])
            with img_col:
                st.image(item["image"], use_container_width=True)
            with data_col:
                st.metric(
                    label=f"{item['순위']}위  {item['차량명']}",
                    value=f"{item['판매 대수']:,}대",
                )

    with col2:
        st.subheader("외제차 Top 5")
        foreign_top5 = [
            {"순위": 1, "차량명": "Model Y",   "판매 대수": 48187, "image": "https://autoimg.danawa.com/photo/4466/model_200.png"},
            {"순위": 2, "차량명": "E Class",   "판매 대수": 28688, "image": "https://autoimg.danawa.com/photo/4516/model_200.png"},
            {"순위": 3, "차량명": "5 Series",  "판매 대수": 23876, "image": "https://autoimg.danawa.com/photo/4517/model_200.png"},
            {"순위": 4, "차량명": "GLC Class", "판매 대수": 9331,  "image": "https://autoimg.danawa.com/photo/4373/model_200.png"},
            {"순위": 5, "차량명": "Model 3",   "판매 대수": 8825,  "image": "https://autoimg.danawa.com/photo/4610/model_200.png"},
        ]
        for item in foreign_top5:
            img_col, data_col = st.columns([1, 3])
            with img_col:
                st.image(item["image"], use_container_width=True)
            with data_col:
                st.metric(
                    label=f"{item['순위']}위  {item['차량명']}",
                    value=f"{item['판매 대수']:,}대",
                )


# ── 실행 ─────────────────────────────────────────────────
def main():
    st.title("차량 등록 현황 대시보드")
    st.markdown("---")

    df_newreg = load_newreg_data(db)

    show_main_dashboard(df_newreg)
    st.markdown("---")
    show_line_chart(df_newreg)
    st.markdown("---")
    show_top5()


main()
