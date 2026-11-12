"""Repeated rock-paper-scissors with baseline, frequency and Markov agents."""
import numpy as np
import pandas as pd

MOVES = ("Камень", "Бумага", "Ножницы")
PAYOFF = np.array([[0, -1, 1], [1, 0, -1], [-1, 1, 0]])


def counter_move(move_index):
    return (move_index + 1) % 3


class Agent:
    def __init__(self, strategy="Случайная", seed=42, alpha=1.0, window=30):
        self.strategy = strategy
        self.rng = np.random.default_rng(seed)
        self.alpha = alpha
        self.window = window
        self.history = []  # observed opponent moves
        self.own_history = []

    def choose(self):
        h = self.history
        if self.strategy == "Постоянная":
            return 0
        if self.strategy == "Циклическая":
            return len(self.own_history) % 3
        if self.strategy == "Частотная" and h:
            counts = np.bincount(h[-self.window:], minlength=3).astype(float) + self.alpha
            return counter_move(int(np.argmax(counts)))
        if self.strategy == "Марковская" and len(h) >= 2:
            transitions = np.zeros((3, 3), dtype=float) + self.alpha
            for prev, nxt in zip(h[-self.window-1:-1], h[-self.window:]):
                transitions[prev, nxt] += 1
            probs = transitions[h[-1]] / transitions[h[-1]].sum()
            predicted = int(self.rng.choice(3, p=probs))
            return counter_move(predicted)
        if self.strategy == "Смешанная" and h:
            counts = np.bincount(h[-self.window:], minlength=3).astype(float) + self.alpha
            probs = counts / counts.sum()
            # Mix exploitation with a uniform component to avoid being fully predictable.
            probs = 0.75 * probs + 0.25 / 3
            predicted = int(self.rng.choice(3, p=probs))
            return counter_move(predicted)
        return int(self.rng.integers(0, 3))

    def observe(self, opponent_move, own_move):
        self.history.append(opponent_move)
        self.own_history.append(own_move)


def play_match(strategy_a="Частотная", strategy_b="Случайная", rounds=500,
               seed=42, alpha=1.0, window=30):
    a = Agent(strategy_a, seed=seed, alpha=alpha, window=window)
    b = Agent(strategy_b, seed=seed+1, alpha=alpha, window=window)
    rows, score_a, score_b = [], 0, 0
    for r in range(1, rounds+1):
        ma, mb = a.choose(), b.choose()
        outcome = int(PAYOFF[ma, mb])
        score_a += outcome
        score_b -= outcome
        a.observe(mb, ma)
        b.observe(ma, mb)
        rows.append({"Раунд": r, "Ход A": MOVES[ma], "Ход B": MOVES[mb],
                     "Индекс A": ma, "Индекс B": mb, "Результат A": outcome,
                     "Счёт A": score_a, "Счёт B": score_b})
    wins_a = sum(x["Результат A"] == 1 for x in rows)
    wins_b = sum(x["Результат A"] == -1 for x in rows)
    draws = rounds - wins_a - wins_b
    return {"history": rows, "wins_a": wins_a, "wins_b": wins_b,
            "draws": draws, "score_a": score_a, "score_b": score_b,
            "win_rate_a": wins_a/rounds, "win_rate_b": wins_b/rounds,
            "draw_rate": draws/rounds}


def run_tournament(strategies=None, rounds=500, seed=42, alpha=1.0, window=30):
    strategies = strategies or ["Случайная", "Постоянная", "Циклическая", "Частотная", "Марковская", "Смешанная"]
    scores = pd.DataFrame(0.0, index=strategies, columns=strategies)
    details = []
    for i, a in enumerate(strategies):
        for j, b in enumerate(strategies):
            if i == j:
                # Self-play is useful: it exposes whether a strategy is exploitable by itself.
                pass
            result = play_match(a, b, rounds, seed + i*101 + j*17, alpha, window)
            scores.loc[a, b] = result["score_a"] / rounds
            details.append({"Стратегия A": a, "Стратегия B": b,
                            "Средний результат A": result["score_a"]/rounds,
                            "Победы A, %": 100*result["win_rate_a"],
                            "Ничьи, %": 100*result["draw_rate"]})
    ranking = scores.mean(axis=1).sort_values(ascending=False).rename("Средний результат").rename_axis("Стратегия").reset_index()
    return scores, pd.DataFrame(details), ranking
