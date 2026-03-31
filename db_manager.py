import mysql.connector
class DBManager:
    """
    ================================================================
    DBManager - MySQL 연결 및 쿼리 실행 범용 클래스
    ================================================================
    [ 설치 ]
        pip install mysql-connector-python
    [ import ]
        from db_manager import DBManager
    [ 연결 ] => dotenv로 env파일에 저장된 정보 사용
        db = DBManager(
            host     = 'localhost',  # DB 서버 주소
            user     = 'root',       # MySQL 계정
            password = 'your_pw',    # MySQL 비밀번호
            database = 'your_db',    # 사용할 DB 이름
            port     = 3306          # 기본값 3306, 생략 가능
        )
    [ 메서드 ]
        db.execute(sql, values)  → INSERT / UPDATE / DELETE / CREATE
        db.query(sql, values)    → SELECT (결과를 리스트로 반환)
        db.close()               → 연결 종료 (사용 끝나면 반드시 호출)
    [ 사용 예시 ]
        # CREATE
        db.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS users (
                id    INT AUTO_INCREMENT PRIMARY KEY,
                name  VARCHAR(50) NOT NULL,
                age   INT
            )
        \"\"\")
        # INSERT
        db.execute(
            "INSERT INTO users (name, age) VALUES (%s, %s)",
            ('홍길동', 30)
            # %s : 값을 직접 문자열에 넣지 않고 튜플로 전달 (SQL 인젝션 방지)
        )
        # SELECT - 전체 조회
        rows = db.query("SELECT * FROM users")
        for row in rows:
            print(row)  # {'id': 1, 'name': '홍길동', 'age': 30}
        # SELECT - 조건 조회
        rows = db.query(
            "SELECT * FROM users WHERE age = %s",
            (30,)
            # 값이 1개일 때도 반드시 튜플로 → (30,) ← 뒤에 쉼표 필수
            # (30) 이렇게 쓰면 튜플이 아닌 그냥 숫자로 인식됨
        )
        # UPDATE
        db.execute(
            "UPDATE users SET age = %s WHERE name = %s",
            (31, '홍길동')
            # %s 순서와 튜플 순서가 일치해야 함
        )
        # DELETE
        db.execute(
            "DELETE FROM users WHERE name = %s",
            ('홍길동',)
        )
        # 종료
        db.close()
    [ 반환값 ]
        execute() → 성공 시 True / 실패 시 False
        query()   → 성공 시 딕셔너리 리스트 / 실패 시 빈 리스트 []
    [ 주의사항 ]
        - values 값이 1개일 때 반드시 튜플로 → ('값',) 뒤에 쉼표 필수
        - execute()는 SELECT에 사용하지 않음
        - query()는 INSERT / UPDATE / DELETE에 사용하지 않음
    ================================================================
    """
class DBManager:
    """MySQL 연결 및 CRUD 기능을 담당하는 범용 클래스 
    어떤 프로젝트에서든 import해서 바로 사용 가능"""

    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.conn = None
        self.cursor = None

        self._connect()

    def _connect(self):
        """실제 DB 연결을 수행하는 내부 메서드
        __init__에서 호출되고, 연결 끊겼을 때 재연결 용도로도 사용"""

        try:
            self.conn = mysql.connector.connect(
                host = self.host,
                user = self.user,
                password = self.password,
                database = self.database,
                port = self.port,
                charset = 'utf8mb4' # 한글 깨짐 방지
            )
            self.cursor = self.conn.cursor(dictionary = True)
            # 결과를 {'컬럼명': 값} 딕셔너리 형태로 반환
            print("DB 연결 완료")
        except Exception as e:
            print( f"DB 연결 실패 : {e}" )
            raise
    
    def execute(self, sql, values=None):
        """
        INSERT / UPDATE / DELETE / CREATE 실행
        """
        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
            print( f"실행 완료 | 영향받은 행: {self.cursor.rowcount}" )
            return True
        except Exception as e:
            if self.conn:
                print( f"실행 실패 : {e}" )
                self.conn.rollback()
                return False

    def query(self, sql, values=None):
        """SELECT 실행 결과를 리스트로 반환"""
        try:
            self.cursor.execute(sql, values)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"조회 실패 : {e}")
            return []

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("연결 종료")



    def executemany(self, sql, values_list):
        """여러 행을 한 번에 INSERT할 때 사용 (bulk insert)"""
        try:
            self.cursor.executemany(sql, values_list)
            self.conn.commit()
            print(f"bulk 실행 완료 | 영향받은 행: {self.cursor.rowcount}")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"bulk 실행 실패: {e}")
            return False