import mysql.connector
from db_manager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()

# ── DB 생성 ───────────────────────────────────────────────
conn = mysql.connector.connect(
    host     = os.getenv("DB_HOST"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    port     = int(os.getenv("DB_PORT"))
)
cursor = conn.cursor()
cursor.execute("DROP DATABASE IF EXISTS car_db")
cursor.execute("CREATE DATABASE IF NOT EXISTS car_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
conn.commit()
cursor.close()
conn.close()

db = DBManager(
    host     = os.getenv("DB_HOST"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    database = os.getenv("DB_NAME"),
    port     = int(os.getenv("DB_PORT"))
)

# ── 기존 테이블 삭제 (FK 순서 때문에 팩트 먼저) ──────────────
for t in [
    "income", "car_sigungu", "imported_sigungu",
    "age_gender_sido", "fuel_sido", "model_year",
    "new_foreign_domestic_sido", "cumul_sido",
    "dim_region", "dim_sido", "dim_time"
]:
    db.execute(f"DROP TABLE IF EXISTS {t}")

# ── 차원 테이블 ───────────────────────────────────────────

db.execute("""
    CREATE TABLE IF NOT EXISTS dim_sido (
        sido_id INT         NOT NULL AUTO_INCREMENT,
        sido    VARCHAR(20) NOT NULL,
        PRIMARY KEY (sido_id),
        UNIQUE KEY uq_sido (sido)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS dim_region (
        region_id INT         NOT NULL AUTO_INCREMENT,
        sido_id   INT         NOT NULL,
        sigungu   VARCHAR(20) NOT NULL,
        PRIMARY KEY (region_id),
        UNIQUE KEY uq_region (sido_id, sigungu),
        FOREIGN KEY (sido_id) REFERENCES dim_sido(sido_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS dim_time (
        time_id INT NOT NULL AUTO_INCREMENT,
        year    INT NOT NULL,
        month   INT NOT NULL,
        PRIMARY KEY (time_id),
        UNIQUE KEY uq_time (year, month)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS income (
        year              INT NOT NULL,
        region_id         INT NOT NULL,
        count             INT,
        income            BIGINT,
        income_per_person DOUBLE,
        PRIMARY KEY (year, region_id),
        FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS car_sigungu (
        time_id           INT NOT NULL,
        region_id         INT NOT NULL,
        passenger_private INT,
        passenger_total   INT,
        PRIMARY KEY (time_id, region_id),
        FOREIGN KEY (time_id)   REFERENCES dim_time(time_id),
        FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS imported_sigungu (
        time_id            INT NOT NULL,
        region_id          INT NOT NULL,
        passenger_imported INT,
        PRIMARY KEY (time_id, region_id),
        FOREIGN KEY (time_id)   REFERENCES dim_time(time_id),
        FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS age_gender_sido (
        time_id INT         NOT NULL,
        sido_id INT         NOT NULL,
        gender  VARCHAR(10) NOT NULL,
        age     INT         NOT NULL,
        count   INT,
        PRIMARY KEY (time_id, sido_id, gender, age),
        FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
        FOREIGN KEY (sido_id) REFERENCES dim_sido(sido_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS fuel_sido (
        time_id INT         NOT NULL,
        sido_id INT         NOT NULL,
        fuel    VARCHAR(50) NOT NULL,
        count   INT,
        PRIMARY KEY (time_id, sido_id, fuel),
        FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
        FOREIGN KEY (sido_id) REFERENCES dim_sido(sido_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS model_year (
        time_id    INT NOT NULL,
        model_year INT NOT NULL,
        passenger  INT,
        PRIMARY KEY (time_id, model_year),
        FOREIGN KEY (time_id) REFERENCES dim_time(time_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS new_foreign_domestic_sido (
        time_id               INT NOT NULL,
        sido_id               INT NOT NULL,
        passenger_newcar      INT,
        passenger_newimported INT,
        PRIMARY KEY (time_id, sido_id),
        FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
        FOREIGN KEY (sido_id) REFERENCES dim_sido(sido_id)
    )
""")

db.execute("""
    CREATE TABLE IF NOT EXISTS cumul_sido (
        time_id                    INT NOT NULL,
        sido_id                    INT NOT NULL,
        passenger_cumulcar         INT,
        passenger_cumulimportedcar INT,
        PRIMARY KEY (time_id, sido_id),
        FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
        FOREIGN KEY (sido_id) REFERENCES dim_sido(sido_id)
    )
""")

print("테이블 생성 완료")
db.close()