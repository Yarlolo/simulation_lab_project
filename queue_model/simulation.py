"""Discrete-event simulation of a bank service system."""
from dataclasses import dataclass
from collections import deque
import random
import simpy
import numpy as np

@dataclass
class QueueConfig:
    horizon: float = 480.0          # minutes
    arrival_rate: float = 0.32      # customers per minute
    service_rate: float = 0.12      # services per minute per clerk
    clerks: int = 4
    patience: float = 45.0          # maximum waiting time, minutes
    seed: int = 42

def simulate_bank(config: QueueConfig):
    """M/M/c-like system with Poisson arrivals, exponential service and impatience."""
    if config.clerks < 1 or config.arrival_rate <= 0 or config.service_rate <= 0:
        raise ValueError("Rates must be positive and at least one clerk is required.")
    rng = random.Random(config.seed)
    env = simpy.Environment()
    counters = simpy.Resource(env, capacity=config.clerks)
    records = []
    queue_sizes = []

    def monitor():
        while True:
            queue_sizes.append((env.now, len(counters.queue)))
            yield env.timeout(1)

    def customer(cid):
        arrived = env.now
        with counters.request() as req:
            result = yield req | env.timeout(config.patience)
            if req not in result:
                records.append({"id": cid, "arrival": arrived, "start": None,
                                "finish": env.now, "wait": config.patience,
                                "system": config.patience, "served": False})
                return
            start = env.now
            wait = start - arrived
            service = rng.expovariate(config.service_rate)
            yield env.timeout(service)
            finish = env.now
            records.append({"id": cid, "arrival": arrived, "start": start,
                            "finish": finish, "wait": wait,
                            "system": finish-arrived, "served": True})

    def arrivals():
        cid = 0
        while env.now < config.horizon:
            yield env.timeout(rng.expovariate(config.arrival_rate))
            if env.now <= config.horizon:
                cid += 1
                env.process(customer(cid))

    env.process(monitor())
    env.process(arrivals())
    env.run(until=config.horizon + max(config.patience, 1))

    served = [r for r in records if r["served"] and r["finish"] <= config.horizon + config.patience]
    abandoned = [r for r in records if not r["served"]]
    waits = [r["wait"] for r in served]
    systems = [r["system"] for r in served]
    util = min(1.0, len(served) / max(config.clerks * config.horizon * config.service_rate, 1e-9))
    return {
        "records": records,
        "queue": queue_sizes,
        "arrivals": len(records),
        "served": len(served),
        "abandoned": len(abandoned),
        "mean_wait": float(np.mean(waits)) if waits else 0.0,
        "mean_system": float(np.mean(systems)) if systems else 0.0,
        "max_queue": max((q for _, q in queue_sizes), default=0),
        "utilization_estimate": util,
        "config": config,
    }
