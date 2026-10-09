"""
부하테스트 시나리오에서 공통으로 쓰는 ID 상수.
"""

EVENT_ID = "EV-LOAD"
GRADE = "VIP"
PRICE = 10000

# A. 좌석 오버부킹: 5석을 두고 서로 다른 유저들이 경쟁
SEATS_A = [f"A{i}" for i in range(1, 6)]
USERS_A = [f"U-LOAD-A-{i:04d}" for i in range(1, 501)]

# B. 동일 유저 다중 요청: 유저 1명 고정, 좌석은 충분히
SEATS_B = [f"B{i}" for i in range(1, 11)]
USER_B_FIXED = "U-LOAD-B-FIXED"

# C. 대규모 트래픽
SEATS_C_CONTENTION = [f"C{i}" for i in range(1, 4)]
SEATS_C_BULK = [f"C-BULK-{i:05d}" for i in range(1, 20001)]
USERS_C = [f"U-LOAD-C-{i:05d}" for i in range(1, 2001)]

# D. 홀드 만료 시 재홀드: 이미 만료된 홀드를 가진 좌석 1개를 여러 유저가 재점유 시도
SEAT_D = "D1"
USER_D_GHOST = "U-LOAD-D-GHOST"
USERS_D = [f"U-LOAD-D-{i:04d}" for i in range(1, 51)]
HOLD_ID_D_EXPIRED = "HOLD-LOAD-D-EXPIRED"

# E. 예약 생성 동시 요청: 좌석 1개, 유저 1명이 이미 홀드를 가진 상태에서 동시에 예약 요청
SEAT_E = "E1"
USER_E_OWNER = "U-LOAD-E-OWNER"
HOLD_ID_E = "HOLD-LOAD-E"
