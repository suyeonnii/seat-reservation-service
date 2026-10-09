# 부하테스트 하네스

운영 DB(`app.db`)를 건드리지 않도록 `loadtest.db`로 격리해서 실행합니다.

## 0. 사전 준비 (한 번만)
```bash
pip install locust
docker-compose up -d        # Redis 기동
```

## 1. 테스트용 서버 기동
시나리오를 바꿀 때마다 아래 두 단계(시딩 → 서버 재기동)를 반복합니다.
서버는 운영 서버(8000)와 겹치지 않게 8001 포트로 띄웁니다.

```bash
DATABASE_PATH=loadtest.db python -m loadtest.seed_scenario <a|b|c|d|e>

DATABASE_PATH=loadtest.db REDIS_URL=redis://localhost:6379 \
    uvicorn app.main:app --port 8001
```

## 2. 시나리오 실행

### A. 좌석 쟁탈전 (Locust)
```bash
locust -f loadtest/locustfile_a.py --headless -u 300 -r 300 -t 10s --host http://localhost:8001
```
검증: 성공(201) 건수가 정확히 5건인지 Locust 결과 요약에서 확인.

### B. 동일 유저 다중 요청 (race_test)
```bash
DATABASE_PATH=loadtest.db python -m loadtest.race_test b --host http://localhost:8001
```

### C. 대규모 트래픽 (Locust, -u 값을 바꿔가며 반복)
```bash
locust -f loadtest/locustfile_c.py --headless -u 50  -r 50  -t 20s --host http://localhost:8001
locust -f loadtest/locustfile_c.py --headless -u 200 -r 200 -t 20s --host http://localhost:8001
locust -f loadtest/locustfile_c.py --headless -u 500 -r 500 -t 20s --host http://localhost:8001
```
각 단계의 RPS / 응답시간(p95, p99) / 실패율을 기록.

### D. 홀드 만료 경계 레이스 (race_test)
```bash
DATABASE_PATH=loadtest.db python -m loadtest.race_test d --host http://localhost:8001
```

### E. 예약 생성 동시 요청 (race_test)
```bash
DATABASE_PATH=loadtest.db python -m loadtest.race_test e --host http://localhost:8001
```

## 3. 정리
```bash
rm -f loadtest.db loadtest.db-shm loadtest.db-wal
```
