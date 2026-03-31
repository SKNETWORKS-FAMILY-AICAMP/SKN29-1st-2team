import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from db_manager import DBManager  # 팀원분이 만든 DBManager 임포트

load_dotenv()

st.set_page_config(page_title="FAQ", layout="wide")

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

# 데이터 로딩 (캐싱 처리 - DB 연결을 최소화하여 속도 향상)
@st.cache_data
def load_data():
    # 팀 표준 DBManager로 DB 연결 (03_load_faq_data.py와 동일한 방식)
    db = DBManager(
        host     = os.getenv("DB_HOST"),
        user     = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME"), # .env에 설정된 DB (예: car_db)
        port     = int(os.getenv("DB_PORT", 3306))
    )
    
    # query 메서드로 데이터 조회
    query = "SELECT * FROM repair_faq" 
    rows = db.query(query)
    
    db.close() # 작업 후 연결 종료
    
    # DBManager가 반환한 리스트(딕셔너리)를 pandas DataFrame으로 변환
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame() # 데이터가 없을 경우 빈 데이터프레임 반환

# --- UI 레이아웃 시작 ---
# (참고) pages 폴더 내의 파일이므로 st.set_page_config는 주석 처리합니다. 메인 app.py 설정이 적용됩니다.
# st.set_page_config(page_title="자동차 FAQ 시스템", layout="wide")

# # 사이드바 (팀 프로젝트 구조상 자동 생성되지만, 추가 내용을 넣고 싶다면 유지)
# with st.sidebar:
#     st.title("🚗 TEAM PROJECT")
#     st.write("---")
#     st.page_link("app.py", label="📊 메인 대시보드")
#     st.page_link("pages/1_소득_vs_외제차.py", label="💰 소득 vs 외제차")
#     st.page_link("pages/2_연료별_비중.py", label="⛽ 연료별 비중")
#     st.page_link("pages/3_연령대_성별.py", label="👥 연령대 및 성별")
#     st.page_link("pages/4_FAQ.py", label="💡 자동차 FAQ")

# 메인 타이틀
st.title("❓ FAQ")
st.write("자동차 구매와 관리에 필요한 모든 궁금증을 해결해보세요!")

# 카테고리 선택 버튼 (상단 2개 버튼)
if 'category' not in st.session_state:
    st.session_state.category = '정비' # 기본값

col1, col2 = st.columns(2)

with col1:
    if st.button("🛠️ 차량정비", use_container_width=True, type="primary" if st.session_state.category == '정비' else "secondary"):
        st.session_state.category = '정비'
        st.rerun()
with col2:
    if st.button("💸 구매보조금", use_container_width=True, type="primary" if st.session_state.category == '보조금' else "secondary"):
        st.session_state.category = '보조금'
        st.rerun()

# --- [구매보조금] 선택 시 내부 탭 노출 ---
if st.session_state.category == '보조금':
    tab1, tab2 = st.tabs(["대상 및 절차", "지자체 보조금"])

    with tab1:
        st.subheader("보조금 지원 대상")
        st.write("• 중앙행정기관을 제외한 개인, 법인, 공공기관, 지방자치단체, 지방공기업 등")
        st.write("• 국고보조금 외 지방보조금을 추가로 지원하는 지방자치단체는 관할 자치단체 내 거주 등 자격조건 부여 가능")

        st.subheader("보조금 지원 차량")
        st.write("**아래의 사항을 충족하는 전기자동차**")
        st.write("• 「자동차관리법」, 「대기환경보전법」, 「소음·진동관리법」 등 관계법령에 따라 자동차와 관련된 각종 인증을 모두 완료한 차량")
        st.write("• 「전기자동차 보급대상 평가에 관한 규정」에 따른 전기차의 평가항목 및 기준에 적합한 차량")

        st.subheader("전기차 보조금 신청절차")
        st.info("1️⃣ 보급사업 공고")
        st.info("2️⃣ 전기자동차 구매계약")
        st.info("3️⃣ 구매지원 신청서 접수")
        st.info("4️⃣ 대상자 선정·통보")
        st.info("5️⃣ 차량 출고 및 등록")
        st.info("6️⃣ 보조금 신청")
        st.info("7️⃣ 보조금 지급")

    with tab2:
        st.subheader("📍 2026년 지자체별 전기차, 수소차 보조금")
        st.caption("(단위 : 만원, 승용기준)")

        # 기존처럼 데이터프레임 하드코딩 방식으로 깔끔하게 출력
        data = {
            "시도": ["서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시", 
                    "세종특별자치시", "경기도", "강원특별자치도", "충청북도", "충청남도", "전북특별자치도", "전라남도", 
                    "경상북도", "경상남도", "제주특별자치도"],
            "전기자동차": ["60", "280", "250", "230", "330", "250", "290", "200", "200~484", "288", 
                        "580~649.6", "700", "630", "450~850", "600~1,100", "520~910", "400"],
            "수소자동차": ["700", "1,100", "1,000", "1,000", "1,000", "1,000", "1,150", "997", 
                        "1,000~1,250", "1,200", "1,100~1,254", "1,000~1,500", "1,200", "1,200~1,500", 
                        "1,000", "1,060~1,250", "-"]
        }

        df_local = pd.DataFrame(data)
        st.dataframe(df_local, use_container_width=True, hide_index=True)

# --- [차량정비] 선택 시 내부 탭 노출 ---
else:
    search_query = st.text_input("", placeholder="▷ 질문이나 답변 키워드를 입력하세요.")

    try:
        all_df = load_data()

        if not all_df.empty:
            # DB의 '카테고리' 컬럼 값이 '승용정비'이므로 '정비'라는 키워드로 필터링
            filtered_df = all_df[all_df['카테고리'].str.contains(st.session_state.category, na=False)]

            # 검색어 필터링
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['질문'].str.contains(search_query, case=False, na=False) | 
                    filtered_df['답변'].str.contains(search_query, case=False, na=False)
                ]

            # 결과 개수 표시
            st.caption(f"현재 총 {len(filtered_df)}건의 FAQ가 검색되었습니다.")

            # FAQ 리스트 출력 (Expander 활용)
            if not filtered_df.empty:
                for idx, row in filtered_df.iterrows():
                    with st.expander(f"⭐ {row['질문']}"):
                        st.write(row['답변'])
            else:
                st.warning("검색 조건에 맞는 FAQ 내용이 없습니다.")
        else:
            st.info("데이터베이스에 아직 FAQ 데이터가 적재되지 않았습니다.")

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")