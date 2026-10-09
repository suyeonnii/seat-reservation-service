import random

from locust import HttpUser, between, task

from loadtest import constants as c


class LoadUser(HttpUser):
    """
    시나리오 C: 대규모 트래픽
    """

    wait_time = between(0.1, 0.5)

    @task(3)
    def hold_bulk_seat(self) -> None:
        seat_no = random.choice(c.SEATS_C_BULK)
        self.client.post(
            f"/events/{c.EVENT_ID}/holds",
            json={"seat_nos": [seat_no]},
            headers={"X-User-Id": random.choice(c.USERS_C)},
            name="/events/[id]/holds (C-넓은풀)",
        )

    @task(1)
    def hold_contention_seat(self) -> None:
        seat_no = random.choice(c.SEATS_C_CONTENTION)
        self.client.post(
            f"/events/{c.EVENT_ID}/holds",
            json={"seat_nos": [seat_no]},
            headers={"X-User-Id": random.choice(c.USERS_C)},
            name="/events/[id]/holds (C-좁은풀경쟁)",
        )
