"""Discrete-event simulation of a multi-server bank queue (M/M/c with impatience)."""
from dataclasses import dataclass
import random
import simpy
import numpy as np


@dataclass
class QueueConfig:
    horizon: float = 480.0
    arrival_rate: float = 0.32
    service_rate: float = 0.12
    clerks: int = 4
    patience: float = 45.0
    seed: int = 42
    sample_step: float = 1.0


def simulate_bank(config: QueueConfig):
    """Run the model and return customer records, time series and exact busy-time estimates.

    Arrivals stop at ``horizon``; customers already in the system are allowed to
    finish or abandon. Queue length and busy servers are sampled every sample_step.
    """
    if config.clerks < 1 or config.arrival_rate <= 0 or config.service_rate <= 0:
        raise ValueError("Rates must be positive and at least one clerk is required.")
    if config.horizon <= 0 or config.patience < 0 or config.sample_step <= 0:
        raise ValueError("Horizon/sample step must be positive and patience non-negative.")

    rng = random.Random(config.seed)
    env = simpy.Environment()
    counters = simpy.Resource(env, capacity=config.clerks)
    records, timeline = [], []
    cid_counter = {"value": 0}

    def customer(cid):
        arrived = env.now
        with counters.request() as req:
            result = yield req | env.timeout(config.patience)
            if req not in result:
                records.append({"id": cid, "arrival": arrived, "start": np.nan,
                                "finish": env.now, "wait": config.patience,
                                "system": env.now-arrived, "served": False,
                                "clerk": None})
                return
            start = env.now
            wait = start - arrived
            clerk_id = counters.users.index(req) + 1
            service = rng.expovariate(config.service_rate)
            yield env.timeout(service)
            finish = env.now
            records.append({"id": cid, "arrival": arrived, "start": start,
                            "finish": finish, "wait": wait,
                            "system": finish-arrived, "served": True,
                            "clerk": clerk_id})

    def arrivals():
        while True:
            gap = rng.expovariate(config.arrival_rate)
            if env.now + gap > config.horizon:
                break
            yield env.timeout(gap)
            cid_counter["value"] += 1
            env.process(customer(cid_counter["value"]))

    def monitor():
        while env.now < config.horizon:
            now = env.now
            busy = counters.count
            timeline.append({"Время": now, "Очередь": len(counters.queue),
                             "Занято окон": busy, "Свободно окон": config.clerks-busy})
            yield env.timeout(min(config.sample_step, config.horizon-env.now))
        # Include the end of the arrival period in the chart.

    monitor_proc = env.process(monitor())
    env.process(arrivals())
    env.run(until=config.horizon)
    # The monitor exits at the horizon; drain all admitted customers afterwards.
    env.run()

    # Reconstruct server busy time from completed service intervals (exact over observed work).
    served = [r for r in records if r["served"]]
    busy_minutes = sum(max(0.0, min(r["finish"], config.horizon) - min(r["start"], config.horizon))
                       for r in served)
    utilization = min(1.0, busy_minutes / (config.clerks * config.horizon))
    clerk_busy = {i: 0.0 for i in range(1, config.clerks + 1)}
    for r in served:
        clerk_busy[r["clerk"]] += max(0.0, min(r["finish"], config.horizon) - min(r["start"], config.horizon))
    clerk_utilization = {i: min(1.0, value / config.horizon) for i, value in clerk_busy.items()}
    waits = [r["wait"] for r in served]
    systems = [r["system"] for r in served]
    abandoned = [r for r in records if not r["served"]]
    q_values = [x["Очередь"] for x in timeline]
    return {
        "records": sorted(records, key=lambda r: r["id"]),
        "timeline": timeline,
        "queue": [(x["Время"], x["Очередь"]) for x in timeline],
        "arrivals": len(records), "served": len(served), "abandoned": len(abandoned),
        "mean_wait": float(np.mean(waits)) if waits else 0.0,
        "median_wait": float(np.median(waits)) if waits else 0.0,
        "p90_wait": float(np.percentile(waits, 90)) if waits else 0.0,
        "mean_system": float(np.mean(systems)) if systems else 0.0,
        "max_queue": max(q_values, default=0),
        "utilization_estimate": utilization, "clerk_utilization": clerk_utilization,
        "config": config,
    }
