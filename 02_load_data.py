import pandas as pd
from db_manager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()

db = DBManager(
    host     = os.getenv("DB_HOST"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    database = os.getenv("DB_NAME"),
    port     = int(os.getenv("DB_PORT"))
)

DATA_DIR = "data"

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    for enc in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"{filename} 로드 완료 ({len(df)}행)")
            return df
        except:
            continue
    raise ValueError(f"{filename} 로드 실패")

# ── dim_sido ─────────────────────────────────────────────
df02 = load_csv("02.car_sigungu_monthly.csv")
sidos = df02[["sido"]].drop_duplicates()
db.executemany(
    "INSERT IGNORE INTO dim_sido (sido) VALUES (%s)",
    [(r.sido,) for r in sidos.itertuples(index=False)]
)
print("dim_sido 완료")

# sido → sido_id 매핑 딕셔너리
sido_map = {r["sido"]: r["sido_id"] for r in db.query("SELECT sido_id, sido FROM dim_sido")}

# ── dim_region ───────────────────────────────────────────
regions = df02[["sido", "sigungu"]].drop_duplicates()
db.executemany(
    "INSERT IGNORE INTO dim_region (sido_id, sigungu) VALUES (%s, %s)",
    [(sido_map[r.sido], r.sigungu) for r in regions.itertuples(index=False)]
)
print("dim_region 완료")

# (sido_id, sigungu) → region_id 매핑 딕셔너리
region_map = {
    (r["sido_id"], r["sigungu"]): r["region_id"]
    for r in db.query("SELECT region_id, sido_id, sigungu FROM dim_region")
}

# ── dim_time ─────────────────────────────────────────────
times = df02[["year", "month"]].drop_duplicates()
db.executemany(
    "INSERT IGNORE INTO dim_time (year, month) VALUES (%s, %s)",
    [(int(r.year), int(r.month)) for r in times.itertuples(index=False)]
)
print("dim_time 완료")

# (year, month) → time_id 매핑 딕셔너리
time_map = {
    (r["year"], r["month"]): r["time_id"]
    for r in db.query("SELECT time_id, year, month FROM dim_time")
}

# ── income ───────────────────────────────────────────────
df = load_csv("00.income_sigungu_yearly.csv")
db.executemany(
    """INSERT IGNORE INTO income
       (year, region_id, count, income, income_per_person)
       VALUES (%s, %s, %s, %s, %s)""",
    [(int(r.year),
      region_map[(sido_map[r.sido], r.sigungu)],
      int(r.count), int(r.income), float(r.income_per_person))
     for r in df.itertuples(index=False)]
)
print("income 완료")

# ── car_sigungu ──────────────────────────────────────────
df = load_csv("02.car_sigungu_monthly.csv")
db.executemany(
    """INSERT IGNORE INTO car_sigungu
       (time_id, region_id, passenger_private, passenger_total)
       VALUES (%s, %s, %s, %s)""",
    [(time_map[(int(r.year), int(r.month))],
      region_map[(sido_map[r.sido], r.sigungu)],
      int(r.passenger_private), int(r.passenger_total))
     for r in df.itertuples(index=False)]
)
print("car_sigungu 완료")

# ── imported_sigungu ─────────────────────────────────────
df = load_csv("03.car_importedcar_sigungu_monthly.csv")
db.executemany(
    """INSERT IGNORE INTO imported_sigungu
       (time_id, region_id, passenger_imported)
       VALUES (%s, %s, %s)""",
    [(time_map[(int(r.year), int(r.month))],
      region_map[(sido_map[r.sido], r.sigungu)],
      int(r.passenger_imported))
     for r in df.itertuples(index=False)
     if (sido_map.get(r.sido), r.sigungu) in region_map]  # 매핑 없는 행 스킵
)
print("imported_sigungu 완료")

# ── age_gender_sido ──────────────────────────────────────
df = load_csv("04.car_sido_culmulagegender_totmonthly.csv")
db.executemany(
    """INSERT IGNORE INTO age_gender_sido
       (time_id, sido_id, gender, age, count)
       VALUES (%s, %s, %s, %s, %s)""",
    [(time_map[(int(r.year), int(r.month))],
      sido_map[r.sido],
      r.gender, int(r.age), int(r.count))
     for r in df.itertuples(index=False)]
)
print("age_gender_sido 완료")

# ── fuel_sido ────────────────────────────────────────────
df = load_csv("10.car_fuel_sido_totmonthly.csv")
df_passenger = df[df["type"] == "승용"]
db.executemany(
    """INSERT IGNORE INTO fuel_sido
       (time_id, sido_id, fuel, count)
       VALUES (%s, %s, %s, %s)""",
    [(time_map[(int(r.year), int(r.month))],
      sido_map[r.sido],
      r.fuel, int(r.count))
     for r in df_passenger.itertuples(index=False)]
)
print("fuel_sido 완료")

# ── model_year ───────────────────────────────────────────
df = load_csv("15.car_culmulmodyear_totmonthly.csv")
db.executemany(
    """INSERT IGNORE INTO model_year
       (time_id, model_year, passenger)
       VALUES (%s, %s, %s)""",
    [(time_map[(int(r.year), int(r.month))],
      int(r.model_year), int(r.passenger))
     for r in df.itertuples(index=False)]
)
print("model_year 완료")

# ── new_foreign_domestic_sido ────────────────────────────
df = load_csv("20.car_sido_newreg_totmonthly.csv")
db.executemany(
    """INSERT IGNORE INTO new_foreign_domestic_sido
       (time_id, sido_id, passenger_newcar, passenger_newimported)
       VALUES (%s, %s, %s, %s)""",
    [(time_map[(int(r.year), int(r.month))],
      sido_map[r.sido],
      int(r.passenger_newcar), int(r.passenger_newimported))
     for r in df.itertuples(index=False)]
)
print("new_foreign_domestic_sido 완료")

# ── cumul_sido ───────────────────────────────────────────
df = load_csv("21.car_sido_newcumulcar_totmonthly.csv")
db.executemany(
    """INSERT IGNORE INTO cumul_sido
       (time_id, sido_id, passenger_cumulcar, passenger_cumulimportedcar)
       VALUES (%s, %s, %s, %s)""",
    [(time_map[(int(r.year), int(r.month))],
      sido_map[r.sido],
      int(r.passenger_cumulcar), int(r.passenger_cumulimportedcar))
     for r in df.itertuples(index=False)]
)
print("cumul_sido 완료")

print("\n🎉 모든 데이터 적재 완료")
db.close()