import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="소득 vs 외제차 비율", layout="wide")

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
def load_income_data(_db):
    rows = _db.query("""
        SELECT
            i.year, i.count, i.income, i.income_per_person,
            car.total_domestic, car.total_imported,
            r.sigungu, s.sido,
            ROUND(car.total_imported / NULLIF(car.total_domestic, 0) * 100, 2) AS imported_ratio
        FROM income AS i
        JOIN (
            SELECT t.year, cs.region_id,
                SUM(cs.passenger_private)  AS total_domestic,
                SUM(im.passenger_imported) AS total_imported
            FROM car_sigungu AS cs
            JOIN dim_time AS t ON cs.time_id = t.time_id
            LEFT JOIN imported_sigungu AS im
                ON cs.time_id = im.time_id AND cs.region_id = im.region_id
            GROUP BY t.year, cs.region_id
        ) AS car ON i.year = car.year AND i.region_id = car.region_id
        JOIN dim_region AS r ON i.region_id = r.region_id
        JOIN dim_sido   AS s ON r.sido_id   = s.sido_id
        ORDER BY i.income_per_person DESC
    """)
    df = pd.DataFrame(rows)
    num_cols = ["year", "count", "income", "income_per_person",
                "total_domestic", "total_imported", "imported_ratio"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["income_per_person", "imported_ratio"])
    df = df[df["year"] == 2024]
    df = df[~((df["sido"] == "부산") & (df["sigungu"] == "중구"))]
    return df


def show_income_scatter(df_2024):
    st.caption("소득 데이터 2024년 기준 고정")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sidos = sorted(df_2024["sido"].unique().tolist())
        selected_sido = st.multiselect("시도 선택", options=sidos, default=sidos)
    with col_f2:
        search = st.text_input("시군구 검색 (예: 강남구, 수원시)", value="")

    df_filtered = df_2024[df_2024["sido"].isin(selected_sido)].copy()
    df_filtered["highlighted"] = (
        df_filtered["sigungu"].str.contains(search, na=False) if search else False
    )

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="평균 1인당 소득",
                  value=f"{df_filtered['income_per_person'].mean():.1f} 백만원")
    with col2:
        st.metric(label="평균 외제차 비율",
                  value=f"{df_filtered['imported_ratio'].mean():.1f}%")
    with col3:
        top = df_filtered.nlargest(1, "imported_ratio")
        st.metric(label="외제차 비율 1위",
                  value=f"{top['sigungu'].values[0]} ({top['imported_ratio'].values[0]:.1f}%)")

    if search:
        matched = df_filtered[df_filtered["highlighted"]]
        if len(matched) > 0:
            st.success(f"'{search}' 검색 결과: {', '.join(matched['sigungu'].tolist())} ({len(matched)}개)")
        else:
            st.warning(f"'{search}'에 해당하는 시군구가 없습니다.")

    st.markdown("---")
    fig = px.scatter(
        df_filtered,
        x="income_per_person",
        y="imported_ratio",
        color="highlighted" if search else "sido",
        color_discrete_map=(
            {False: "lightsteelblue", True: "#084594"} if search else None
        ),
        size="total_domestic",
        hover_name="sigungu",
        hover_data={
            "sido": True,
            "income_per_person": ":.1f",
            "imported_ratio": ":.2f",
            "total_domestic": ":,",
            "total_imported": ":,",
            "highlighted": False,
        },
        title="시군구별 1인당 소득 vs 외제차 비율 (2024년 기준)",
        labels={
            "income_per_person": "1인당 소득 (백만원)",
            "imported_ratio": "외제차 비율 (%)",
            "sido": "시도",
            "total_domestic": "전체 차량",
            "total_imported": "수입 차량",
            "highlighted": "검색 결과",
        },
        opacity=0.7,
    )
    if search:
        fig.update_traces(
            selector=dict(name="True"),
            marker=dict(line=dict(width=2, color="#2171b5"), size=15, opacity=1.0),
        )
    fig.update_layout(
        title_x=0.5,
        xaxis_title="1인당 소득 (백만원)",
        yaxis_title="외제차 비율 (%)",
        legend_title="시도" if not search else "검색 결과",
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("원본 데이터 보기"):
        st.dataframe(
            df_filtered[["sido", "sigungu", "income_per_person",
                         "total_domestic", "total_imported", "imported_ratio"]]
            .sort_values("income_per_person", ascending=False)
            .reset_index(drop=True),
            use_container_width=True,
        )


def main():
    st.title("1인당 소득 vs 외제차 비율")
    st.markdown("---")
    df_income = load_income_data(db)
    show_income_scatter(df_income)


main()
