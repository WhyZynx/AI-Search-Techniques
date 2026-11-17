import random
import time
from dataclasses import dataclass


@dataclass
class MinConflictsResult:
    solution: list
    steps: int
    elapsed_time: float
    success: bool


class MinConflictsSolver:
    def __init__(self, n, heuristic="random", max_steps=10000, seed=None):
        if n < 1:
            raise ValueError("n must be at least 1")
        if heuristic not in {"random", "most_conflicts"}:
            raise ValueError("heuristic must be 'random' or 'most_conflicts'")
        self.n = n
        self.heuristic = heuristic
        self.max_steps = max_steps
        self.random = random.Random(seed)

    def _conflict_count(self, board, col, row):
        conflicts = 0
        for other_col, other_row in enumerate(board):
            if other_col == col:
                continue
            if other_row == row or abs(other_row - row) == abs(other_col - col):
                conflicts += 1
        return conflicts

    def _conflicted_columns(self, board):
        return [
            col for col, row in enumerate(board)
            if self._conflict_count(board, col, row) > 0
        ]

    def _choose_column(self, board, conflicted_columns):
        if self.heuristic == "random":
            return self.random.choice(conflicted_columns)
        conflict_counts = {
            col: self._conflict_count(board, col, board[col])
            for col in conflicted_columns
        }
        highest = max(conflict_counts.values())
        candidates = [col for col, count in conflict_counts.items() if count == highest]
        return self.random.choice(candidates)

    def _choose_row(self, board, col):
        scores = [self._conflict_count(board, col, row) for row in range(self.n)]
        lowest = min(scores)
        candidates = [row for row, score in enumerate(scores) if score == lowest]
        return self.random.choice(candidates)

    def solve(self):
        start = time.perf_counter()
        board = [self.random.randrange(self.n) for _ in range(self.n)]
        steps = 0

        while steps <= self.max_steps:
            conflicted_columns = self._conflicted_columns(board)
            if not conflicted_columns:
                return MinConflictsResult(
                    board, steps, time.perf_counter() - start, True
                )
            if steps == self.max_steps:
                break
            col = self._choose_column(board, conflicted_columns)
            board[col] = self._choose_row(board, col)
            steps += 1

        return MinConflictsResult(
            board, steps, time.perf_counter() - start, False
        )
