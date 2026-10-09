# seat-reservation-service
> **공연 좌석 홀드·예약** 서비스

## 🛠 기술 스택 (Tech Stack)

- **언어**: Python 3.12
- **웹 프레임워크**: FastAPI
- **ORM**: SQLAlchemy 2.0+
- **DB**: SQLite (WAL 모드)
- **분산 락**: Redis (선택) — 없으면 자동으로 인메모리 락으로 폴백
- **테스트**: pytest
- **부하테스트**: Locust (`loadtest/` 디렉토리, 개발 중 검증용 도구)

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
   python -m pytest -v
   ```

## 📤 엔드포인트 목록

아래 예시는 `scripts.seed`로 적재되는 `data/seed_data.json` 기준(`U-001`, `EV-001`, 좌석 `A1`)입니다.

### 1. 좌석 목록 조회
`GET /events/{event_id}/seats`

```bash
curl http://localhost:8000/events/EV-001/seats
```
```json
{
  "event_id": "EV-001",
  "seats": [
    {"seat_no": "A1", "grade": "VIP", "price": 150000, "status": "AVAILABLE", "occupant_user_id": null}
  ]
}
```

### 2. 좌석 단일 조회
`GET /events/{event_id}/seats/{seat_no}`

```bash
curl http://localhost:8000/events/EV-001/seats/A1
```
```json
{"seat_no": "A1", "grade": "VIP", "price": 150000, "status": "AVAILABLE", "occupant_user_id": null}
```

### 3. 좌석 홀드 생성
`POST /events/{event_id}/holds` (최대 4석, `X-User-Id` 헤더 필요)

```bash
curl -X POST http://localhost:8000/events/EV-001/holds \
  -H "X-User-Id: U-001" \
  -H "Content-Type: application/json" \
  -d '{"seat_nos": ["A1", "A2"]}'
```
```json
{
  "message": "홀드가 생성되었습니다.",
  "hold_id": "...",
  "event_id": "EV-001",
  "user_id": "U-001",
  "status": "ACTIVE",
  "created_at": "2026-01-01T10:00:00",
  "expires_at": "2026-01-01T10:05:00",
  "seats": [{"seat_no": "A1", "price": 150000}, {"seat_no": "A2", "price": 150000}]
}
```
(201 Created. 좌석이 이미 선점됐으면 409 `SEAT_UNAVAILABLE`, 4석 제한 초과 시 409 `SEAT_LIMIT_EXCEEDED`)

### 4. 홀드 단일 조회
`GET /holds/{hold_id}`

```bash
curl http://localhost:8000/holds/{hold_id}
```

### 5. 홀드 취소
`PATCH /holds/{hold_id}` (`X-User-Id` 헤더 필요, 소유자만 가능)

```bash
curl -X PATCH http://localhost:8000/holds/{hold_id} \
  -H "X-User-Id: U-001" \
  -H "Content-Type: application/json" \
  -d '{"status": "CANCELLED"}'
```
(이미 예약으로 전환된 홀드면 409 `HOLD_CONVERTED`, 소유자가 아니면 403 `NOT_OWNER`)

### 6. 예약 생성
`POST /reservations` (`X-User-Id` 헤더 필요, 홀드 소유자만 가능)

```bash
curl -X POST http://localhost:8000/reservations \
  -H "X-User-Id: U-001" \
  -H "Content-Type: application/json" \
  -d '{"hold_id": "..."}'
```
```json
{
  "reservation_id": "...",
  "hold_id": "...",
  "user_id": "U-001",
  "event_id": "EV-001",
  "total_amount": 300000,
  "seats": [{"seat_no": "A1", "price": 150000}, {"seat_no": "A2", "price": 150000}],
  "created_at": "2026-01-01T10:01:00",
  "message": "예약이 생성되었습니다."
}
```
(새로 생성되면 201, 같은 홀드로 재요청하면 200과 함께 기존 예약 반환 — 멱등. 만료된 홀드면 409 `HOLD_EXPIRED`, 취소된 홀드면 409 `HOLD_NOT_ACTIVE`)

### 7. 예약 단일 조회
`GET /reservations/{reservation_id}`

```bash
curl http://localhost:8000/reservations/{reservation_id}
```

### 8. 예약 목록 조회
`GET /reservations?user_id=&event_id=` (둘 다 선택, 조합 가능)

```bash
curl "http://localhost:8000/reservations?user_id=U-001"
curl "http://localhost:8000/reservations?event_id=EV-001"
```

> 전체 API 문서는 서버 실행 후 `http://localhost:8000/docs`(Swagger UI)에서 확인할 수 있습니다.

## 🗄️ 환경 변수

| 변수명 | 기본값      | 설명 |
|---|----------|---|
| `DATABASE_PATH` | `app.db` | SQLite 파일 경로 |
| `REDIS_URL` | -        | Redis 연결 주소. 비어 있으면 인메모리 락을 사용 |
| `CLEANUP_INTERVAL_SECONDS` | `60`     | 만료된 홀드를 정리하는 주기(초) |
| `HOLD_TTL_MINUTES` | `5`      | 홀드 유지 시간(분) |
| `MAX_SEATS_PER_USER_PER_EVENT` | `4`      | 한 사용자가 한 공연에서 가질 수 있는 최대 좌석 수 |

## 외부 인프라

Redis를 **선택적으로** 사용합니다. 동일 사용자가 동시에 여러 홀드 요청을 보냈을 때 "한 공연당 4석 제한"을
원자적으로 지키기 위한 분산 락 용도입니다 (좌석 자체의 중복 홀드 방지는 DB의 조건부 UPDATE가 담당하며
Redis와 무관하게 항상 보장됩니다. 자세한 내용은 `DECISIONS.md` 참고).

**실행 방법**
```bash
docker-compose up -d
```
`.env`의 `REDIS_URL=redis://localhost:6379`를 설정하면 사용됩니다.

**Redis가 없을 때**: `REDIS_URL`이 비어있거나 Redis에 연결할 수 없으면, 서버 시작 시 자동으로
인메모리 락(`app/core/locks.py`의 `InMemoryLock`)으로 폴백합니다. 별도 설정 없이도 서비스는
정상적으로 동작합니다 — 다만 여러 서버 인스턴스를 띄우는 환경에서는 인메모리 락이 프로세스 간에
공유되지 않으므로, 그 경우에만 Redis가 필요합니다.

## 알려진 미완성·한계

- **좌석 목록 조회(`GET /events/{id}/seats`)에 페이지네이션이 없습니다.** 공연 좌석 전체를 한 번에
  직렬화해서 반환하는데, 좌석 수가 많아지고 동시 조회 요청이 몰리면 이 API뿐
  아니라 서버 전체 처리량이 떨어지는 것을 부하테스트로 확인했습니다. (`DECISIONS.md` 참고).
- **SQLite는 단일 writer 구조**라 쓰기 동시성에 근본적인 한계가 있습니다. 부하테스트에서 커넥션 풀
  크기를 키워 처리 한계를 뒤로 미루는 것까지는 확인했지만, 더 큰 트래픽에서는 PostgreSQL 같은
  다중 writer DB로의 전환이 필요합니다.
- **Redis 장애 시 인메모리 락으로 자동 폴백**하지만, 이 경우 "4석 제한"은 서버 인스턴스 단위로만
  보장됩니다. 단일 인스턴스로 운영한다면 문제가 되지 않습니다.
- 홀드 만료 정리는 주기적 배치(`CLEANUP_INTERVAL_SECONDS`)와, 좌석을 다시 홀드/조회하는 시점의
  지연 평가(lazy evaluation) 두 가지로 처리됩니다. 배치가 늦게 돌아도 기능상 문제는 없지만, 배치
  주기 동안은 DB상 좌석 상태(`HELD`)가 실제로는 만료된 상태와 어긋나 있을 수 있습니다.
