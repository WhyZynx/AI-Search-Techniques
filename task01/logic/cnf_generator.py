from itertools import combinations
from math import comb
from typing import List

from logic.propositional_logic import PropositionalLogic

Clause = List[int]

class CNFGenerator:
    def __init__(self, n: int):
        self.n = n
        self.logic = PropositionalLogic(n)
        self._clauses: List[Clause] = []   # lưu kết quả của generate_all_constraints
        
    @staticmethod
    def _exactly_one(group: List[int]) -> List[Clause]:
        clauses = [list(group)]                          # (Q1 v Q2 v ... )
        for a, b in combinations(group, 2):              # mỗi cặp đúng 1 lần
            clauses.append([-a, -b])                     # (~Qa v ~Qb)
        return clauses

    #Ràng buộc hàng
    def generate_row_constraints(self) -> List[Clause]:
        clauses: List[Clause] = []
        for i in range(self.n):
            group = [self.logic.get_variable_id(i, j) for j in range(self.n)]
            clauses.extend(self._exactly_one(group))
        return clauses

    #Ràng buộc cột
    def generate_column_constraints(self) -> List[Clause]:
        """Mỗi cột có đúng một quân hậu."""
        clauses: List[Clause] = []
        for j in range(self.n):
            group = [self.logic.get_variable_id(i, j) for i in range(self.n)]
            clauses.extend(self._exactly_one(group))
        return clauses

    #Ràng buộc đường chéo
    def generate_diagonal_constraints(self) -> List[Clause]:
        clauses: List[Clause] = []
        total = self.n * self.n
        for id1 in range(1, total + 1):
            i, j = self.logic.get_position(id1)
            for id2 in range(id1 + 1, total + 1):        # id2 > id1: tránh trùng
                k, l = self.logic.get_position(id2)
                if abs(i - k) == abs(j - l):
                    clauses.append([-id1, -id2])
        return clauses

    # Kết hợp tất cả (ràng buộc hàng + cột + đường chéo)
    def generate_all_constraints(self) -> List[Clause]:
        self._clauses = (
            self.generate_row_constraints()
            + self.generate_column_constraints()
            + self.generate_diagonal_constraints()
        )
        return self._clauses

    # Đếm số Clause
    def get_clause_count(self) -> int:
        if not self._clauses:
            self.generate_all_constraints()
        return len(self._clauses)

    @staticmethod
    def expected_clause_count(n: int) -> int:
        # C(N) = 2N + 2(N+1)*C(N,2) + 4*C(N,3)
        return 2 * n + 2 * (n + 1) * comb(n, 2) + 4 * comb(n, 3)
