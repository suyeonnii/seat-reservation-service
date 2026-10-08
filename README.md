# seat-reservation-service
> **공연 좌석 홀드·예약** 서비스

## 🛠 기술 스택 (Tech Stack)

## 📁 폴더 구조 (Directory Structure)
```
app/
├── main.py              # FastAPI 앱 생성, 라우터 등록
├── core/                 # 공통 기반 (DB 연결, 설정, 예외, 락)
├── users/, events/       # 참조 데이터 모델
├── seats/                # 좌석 조회
├── holds/                # 홀드 생성·취소, 4석 제한, 정리 작업
└── reservations/         # 예약 생성·조회
scripts/                  # DB 생성, 시드 적재
data/                     # 제공된 시드 데이터
tests/                    # pytest
```

## ⚙️ 설치 및 실행 방법 (Getting Started)
### 사전 요구사항 (Prerequisites)
- Python 3.12 (3.11 이상이면 동일하게 동작합니다)

### 로컬 실행 가이드
####  1. 가상환경 생성 및 활성화
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

#### 2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

#### 3. 환경 변수 설정 (각 변수의 의미는 아래 환경 변수 섹션 참고)
   ```bash
   cp .env.example .env
   ```

#### 4. DB 초기화 및 시드 적재
   ```bash
   python -m scripts.init_db
   python -m scripts.seed
   ```

#### 5. 서버 실행
   ```bash
   uvicorn app.main:app --reload
   ```
서버가 뜨면 `http://localhost:8000/docs`에서 API 문서를 확인할 수 있습니다.

#### ️6. 테스트 실행
   ```bash
   pytest
   ```

## 📤 엔드포인트 목록

## 🗄️ 환경 변수

| 변수명 | 기본값      | 설명 |
|---|----------|---|
| `DATABASE_PATH` | `app.db` | SQLite 파일 경로 |
| `REDIS_URL` | -        | Redis 연결 주소. 비어 있으면 인메모리 락을 사용 |
| `CLEANUP_INTERVAL_SECONDS` | `60`     | 만료된 홀드를 정리하는 주기(초) |
| `HOLD_TTL_MINUTES` | `5`      | 홀드 유지 시간(분) |
| `MAX_SEATS_PER_USER_PER_EVENT` | `4`      | 한 사용자가 한 공연에서 가질 수 있는 최대 좌석 수 |

## 외부 인프라

## 알려진 미완성·한계
