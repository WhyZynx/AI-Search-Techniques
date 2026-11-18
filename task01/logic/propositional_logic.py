from typing import List, Tuple

class PropositionalLogic:

    def __init__(self, n: int):
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError("n must be a positive integer.")
        self.n = n

    def get_variable_id(self, i: int, j: int) -> int:

        self._check_position(i, j)
        return i * self.n + j + 1

    def get_position(self, var_id: int) -> Tuple[int, int]:

        self._check_id(var_id)
        i, j = divmod(var_id - 1, self.n)
        return i, j

    def get_all_variables(self) -> List[int]:

        return list(range(1, self.n * self.n + 1))

    def _check_position(self, i: int, j:int) -> None:
        if not (0 <= i < self.n and 0 <= j < self.n):
            raise ValueError(f"({i},{j}) is outside the board {self.n} x {self.n}.  ")

    def _check_id(self, var_id: int) -> None:
        if not (1 <= var_id <= self.n * self.n):
            raise ValueError(f"ID {var_id} is outside the valid range ")

    def __repr__(self) -> str:
        return f"PropositionalLogic (n={self.n})"

