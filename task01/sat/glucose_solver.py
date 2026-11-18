import time
from typing import List, Optional, Tuple

from pysat.solvers import Glucose3

from logic.propositional_logic import PropositionalLogic

Clause = List[int]
Position = Tuple[int, int]


class GlucoseSolver:
    def __init__(self, n: int):
        # Khởi tạo Solver Glucose3 được tạo mới mỗi lần solve()
        self.n = n
        self.logic = PropositionalLogic(n)
        self._solver: Optional[Glucose3] = None
        self._model: Optional[List[int]] = None
        self._is_sat: Optional[bool] = None
        self.load_time: float = 0.0     # thời gian nạp clauses vào solver
        self.solve_time: float = 0.0    # thời gian Glucose3 giải (không gồm tạo CNF)


    #CNF trả về True nếu là SAT, trả về False nếu là UNSAT
    def solve(self, clauses: List[Clause]) -> bool:
        # Mỗi lần gọi: xóa solver cũ và kết quả cũ -> tạo glucose3 mới
        self.close()             # xóa solver cũ của lần chạy trướd
        self._model = None
        self._is_sat = None

        t0 = time.perf_counter()
        self._solver = Glucose3(bootstrap_with=clauses)
        self.load_time = time.perf_counter() - t0

        t1 = time.perf_counter()
        self._is_sat = self._solver.solve()
        self.solve_time = time.perf_counter() - t1

        # Chỉ lấy model sau khi kết quả là SAT
        if self._is_sat:
            self._model = self._solver.get_model()
        return self._is_sat


    def get_solution(self) -> Optional[List[int]]:
        return list(self._model) if self._model is not None else None


    # Decode model -> tọa độ
    def decode_solution(self) -> Optional[List[Position]]:
        # i = (ID - 1) // N, i = (ID - 1) % N
        if self._model is None:
            return None
        positions = [
            self.logic.get_position(lit)
            for lit in self._model
            if 0 < lit <= self.n * self.n
        ]
        return sorted(positions)


    def validate_solution(self, positions: Optional[List[Position]] = None) -> bool:

        if positions is None:
            positions = self.decode_solution()
        if positions is None:
            return False

        n = self.n
        if len(positions) != n or len(set(positions)) != n:
            return False
        if any(not (0 <= i < n and 0 <= j < n) for i, j in positions):
            return False

        if len({i for i, _ in positions}) != n:      # mỗi hàng một quân
            return False
        if len({j for _, j in positions}) != n:      # mỗi cột một quân
            return False

        for a in range(n):                           # đường chéo
            for b in range(a + 1, n):
                (i, j), (k, l) = positions[a], positions[b]
                if abs(i - k) == abs(j - l):
                    return False
        return True

    # Giải phóng solver
    def close(self) -> None:
        if self._solver is not None:
            self._solver.delete()
            self._solver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        self.close()

