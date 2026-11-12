"""Repeated rock-paper-scissors with fixed and adaptive agents."""
from collections import Counter
import numpy as np

MOVES = ("Камень", "Бумага", "Ножницы")
# Rows: our move; columns: opponent move. Positive means first player wins.
PAYOFF = np.array([[0, -1, 1], [1, 0, -1], [-1, 1, 0]])

def counter_move(move_index):
    """Index of the move that beats the given move."""
    return (move_index + 1) % 3

class Agent:
    def __init__(self, strategy="Случайная", seed=42, alpha=1.0):
        self.strategy = strategy
        self.rng = np.random.default_rng(seed)
        self.alpha = alpha
        self.history = []

    def choose(self):
        if self.strategy == "Постоянная":
            return 0
        if self.strategy == "Циклическая":
            return len(self.history) % 3
        if self.strategy == "Адаптивная" and self.history:
            counts = np.bincount(self.history[-20:], minlength=3).astype(float)
            probs = (counts + self.alpha) / (counts.sum() + 3*self.alpha)
            predicted = int(np.argmax(probs))
            return counter_move(predicted)
        return int(self.rng.integers(0, 3))

    def observe(self, own_move):
        self.history.append(own_move)

def play_match(strategy_a="Адаптивная", strategy_b="Случайная",
               rounds=500, seed=42):
    a = Agent(strategy_a, seed=seed)
    b = Agent(strategy_b, seed=seed+1)
    rows = []
    score_a = score_b = 0
    for r in range(1, rounds+1):
        ma, mb = a.choose(), b.choose()
        result = int(PAYOFF[ma, mb])
        score_a += result
        score_b -= result
        a.observe(mb)  # A learns from B
        b.observe(ma)  # B learns from A
        rows.append({"Раунд": r, "Ход A": MOVES[ma], "Ход B": MOVES[mb],
                     "Результат A": result, "Счёт A": score_a, "Счёт B": score_b})
    wins_a = sum(x["Результат A"] == 1 for x in rows)
    wins_b = sum(x["Результат A"] == -1 for x in rows)
    draws = rounds - wins_a - wins_b
    return {"history": rows, "wins_a": wins_a, "wins_b": wins_b,
            "draws": draws, "score_a": score_a, "score_b": score_b,
            "win_rate_a": wins_a/rounds, "win_rate_b": wins_b/rounds,
            "draw_rate": draws/rounds}
