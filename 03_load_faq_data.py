import os
import time
import pandas as pd
from dotenv import load_dotenv
from db_manager import DBManager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# [크롤링] 현대자동차 차량정비 FAQ 크롤링==========================================
def get_hyundai_passenger_repair_faq():
    options = Options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.hyundai.com/kr/ko/e/customer/center/faq")
    
    wait = WebDriverWait(driver, 15)
    time.sleep(5) # 페이지 초기 안정을 위해 넉넉히 대기

    faq_data = []
    try:
        # 1. '차량정비' -> '승용' 클릭
        maintenance_tab = wait.until(EC.presence_of_element_located((By.XPATH, "//button[.//text()='차량정비']")))
        driver.execute_script("arguments[0].click();", maintenance_tab)
        time.sleep(3)

        passenger_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='승용']]")))
        driver.execute_script("arguments[0].click();", passenger_btn)
        print("✅ '승용' 카테고리 선택 완료")
        time.sleep(5) # 승용 리스트 로딩을 위해 넉넉히 대기

        # 2. 1페이지부터 3페이지까지 반복
        for page in range(1, 4):
            print(f"📄 현재 {page}페이지 수집 중...")
            
            # 페이지 이동 로직
            if page > 1:
                try:
                    page_buttons = driver.find_elements(By.CSS_SELECTOR, ".el-pager li.number")
                    target_btn = None
                    for btn in page_buttons:
                        if btn.text.strip() == str(page):
                            target_btn = btn
                            break
                    
                    if target_btn:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_btn)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", target_btn)
                        print(f"   -> {page}페이지 클릭 성공")
                        time.sleep(4) # 페이지 전환 후 데이터 갱신 대기
                    else:
                        print(f"   -> {page}번 버튼을 못 찾았습니다.")
                        break
                except Exception as e:
                    print(f"⚠️ {page}페이지 이동 에러: {e}")
                    break

            # 3. 해당 페이지 질문 수집
            # Stale Element 에러 방지를 위해 매번 목록을 갱신
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'list-item')))
            items_count = len(driver.find_elements(By.CLASS_NAME, 'list-item'))
            
            for i in range(items_count):
                try:
                    # 매 루프마다 요소를 새로 찾음
                    items = driver.find_elements(By.CLASS_NAME, 'list-item')
                    item = items[i]
                    
                    # 제목 추출
                    title_btn = item.find_element(By.CLASS_NAME, 'list-title')
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title_btn)
                    question = item.find_element(By.CLASS_NAME, 'list-content').text.strip()
                    
                    # 답변 열기
                    driver.execute_script("arguments[0].click();", title_btn)
                    
                    # 답변 텍스트가 로딩될 때까지 최대 5초 대기
                    # (0번/1번 로딩 실패 방지)
                    ans_area = wait.until(lambda d: item.find_element(By.CLASS_NAME, 'conts'))
                    time.sleep(1.5) # 애니메이션 및 데이터 바인딩 시간 보장
                    
                    answer = ans_area.text.strip()
                    
                    if not answer: # 만약 텍스트가 비어있다면 한 번 더 대기
                        time.sleep(2)
                        answer = ans_area.text.strip()

                    faq_data.append({"카테고리": "승용정비", "질문": question, "답변": answer})
                    print(f"   - {i+1}번 수집 완료")
                    
                    # 다시 닫기
                    driver.execute_script("arguments[0].click();", title_btn)
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"   - {i+1}번 처리 중 오류: {e}")
                    continue

        print(f"🎉 최종 총 {len(faq_data)}건 수집 완료!")

    finally:
        driver.quit()
    
    return pd.DataFrame(faq_data)


# [데이터 적재] DBManager를 이용한 데이터 적재==========================================
def load_faq_to_car_db():
    load_dotenv()
    
    db = DBManager(
    host     = os.getenv("DB_HOST"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    database = os.getenv("DB_NAME"),
    port     = int(os.getenv("DB_PORT"))
    )

    # 1. 테이블 생성 (만약 없다면)
    db.execute("""
        CREATE TABLE IF NOT EXISTS repair_faq (
            카테고리 VARCHAR(50),
            질문 TEXT,
            답변 TEXT
        )
    """)

    # 2. 기존 데이터 초기화 (중복 적재 방지)
    db.execute("TRUNCATE TABLE repair_faq")

    # 3. 크롤링 실행 및 DataFrame 받아오기
    print("차량정비 FAQ 크롤링 시작...")
    df_repair = get_hyundai_passenger_repair_faq()

    # 4. DBManager executemany를 활용해 벌크 인서트 (대량 저장)
    # DataFrame의 데이터를 tuple 리스트로 변환하여 삽입
    if df_repair is not None and not df_repair.empty:
        repair_values = [tuple(x) for x in df_repair.to_numpy()]
        db.executemany("INSERT INTO repair_faq (카테고리, 질문, 답변) VALUES (%s, %s, %s)", repair_values)

    # 5. 연결 종료
    db.close()
    print("✅ car_db에 FAQ 데이터 적재 완료!")

if __name__ == "__main__":
    load_faq_to_car_db()