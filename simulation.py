"""Bounded, elapsed-time model for the classroom streaming demonstration."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime

import numpy as np

MAX_ROWS = 300
MAX_COHORTS = 128
HISTORY_SECONDS = 60


@dataclass
class Cohort:
    count: int
    jam_count: int


class Simulation:
    def __init__(self, now, rate=200, capacity=300, jam=False, running=True, seed=None):
        self.started_at = self.updated_at = now
        self.active_seconds = 0.0
        self.rate, self.capacity, self.jam, self.running = rate, capacity, jam, running
        self.total = self.processed = 0
        self.incoming_fraction = self.processing_fraction = 0.0
        self.queue = deque()
        self.rows = deque(maxlen=MAX_ROWS)
        self.history = deque(maxlen=600)
        self.rng = np.random.default_rng(seed)

    @property
    def backlog(self):
        return self.total - self.processed

    @property
    def incoming_rate(self):
        return self.rate if self.running else 0

    @property
    def processing_rate(self):
        if not self.running:
            return 0
        return self.capacity if self.backlog else min(self.rate, self.capacity)

    def _enqueue(self, count):
        if not count:
            return
        jam_count = count if self.jam else 0
        if self.queue and (
            (self.jam and self.queue[-1].jam_count == self.queue[-1].count)
            or (not self.jam and self.queue[-1].jam_count == 0)
        ):
            self.queue[-1].count += count
            self.queue[-1].jam_count += jam_count
        else:
            self.queue.append(Cohort(count, jam_count))
        # Preserve exact volume and scenario proportions without storing each event.
        if len(self.queue) > MAX_COHORTS:
            first, second = self.queue.popleft(), self.queue.popleft()
            self.queue.appendleft(Cohort(
                first.count + second.count, first.jam_count + second.jam_count
            ))

    def _record_readings(self, count, jam_count):
        retained = min(count, MAX_ROWS)
        jammed = self.rng.random(retained) < (jam_count / count)
        speeds = np.where(
            jammed, self.rng.uniform(4, 20, retained), self.rng.uniform(42, 68, retained)
        )
        cars = np.where(
            jammed, self.rng.integers(45, 81, retained), self.rng.integers(8, 36, retained)
        )
        timestamp = datetime.now()
        self.rows.extend({
            "Processed at": timestamp,
            "Cars": int(cars[i]),
            "Speed (mph)": round(float(speeds[i]), 1),
        } for i in range(retained))

    def advance(self, now, *, rate, capacity, jam, running):
        """Apply the previous controls over elapsed time, then accept new controls."""
        elapsed = max(0.0, now - self.updated_at)
        self.updated_at = now
        if self.running:
            self.active_seconds += elapsed
            incoming = self.incoming_fraction + elapsed * self.rate
            count = int(incoming)
            self.incoming_fraction = incoming - count
            self.total += count
            self._enqueue(count)

            budget = self.processing_fraction + elapsed * self.capacity
            slots = int(budget)
            self.processing_fraction = budget - slots
            while slots and self.queue:
                cohort = self.queue[0]
                take = min(slots, cohort.count)
                jam_take = round(cohort.jam_count * take / cohort.count)
                self._record_readings(take, jam_take)
                cohort.count -= take
                cohort.jam_count -= jam_take
                self.processed += take
                slots -= take
                if not cohort.count:
                    self.queue.popleft()

        self.rate, self.capacity, self.jam, self.running = rate, capacity, jam, running
        seconds = now - self.started_at
        self.history.append({
            "Seconds": seconds, "Incoming": self.incoming_rate,
            "Processing": self.processing_rate, "Capacity": self.capacity,
        })
        cutoff = seconds - HISTORY_SECONDS
        while len(self.history) > 2 and self.history[1]["Seconds"] < cutoff:
            self.history.popleft()

    def analytics(self):
        if not self.rows:
            return None
        speeds = np.array([row["Speed (mph)"] for row in self.rows])
        slow_share = float((speeds < 25).mean())
        return {
            "speed": float(speeds.mean()),
            "slow_share": slow_share,
            "cars": float(np.mean([row["Cars"] for row in self.rows])),
            "congestion": len(self.rows) >= 20 and slow_share >= 0.6,
        }
