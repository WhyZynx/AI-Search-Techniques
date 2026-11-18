import csv
import statistics
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from logic.cnf_generator import CNFGenerator
from sat.glucose_solver import GlucoseSolver
from logic.propositional_logic import PropositionalLogic

Clause = List[int]
Result = Dict[str, Any]

CSV_FIELDS = [
    "n",
    "variables",
    "clauses",
    "generation_time",      # trung bình (giây)
    "solver_time",          # trung bình (giây)
    "result",               # SAT / UNSAT
    "is_valid",             # True / False / N/A (khi UNSAT)
    "solver_time_std",      # độ lệch chuẩn giữa các lần chạy (giây)
    "solver_time_min",      # lần chạy nhanh nhất (giây)
    "runs",                 # số lần lặp
]


class SATExperiment:
    def __init__(
        self,
        n_values: Iterable[int] = range(4, 11),
        repeats: int = 5,
        warmup: bool = True,
    ):

        if repeats < 1:
            raise ValueError("repeats >= 1")
        self.n_values = list(n_values)
        self.repeats = repeats
        self.warmup = warmup
        self.results: List[Result] = []

    def measure_solver_time(
        self, n: int, clauses: List[Clause]
    ) -> Tuple[float, bool, Optional[bool]]:

        with GlucoseSolver(n) as solver:
            is_sat = solver.solve(clauses)
            solver_time = solver.solve_time

            is_valid: Optional[bool] = None
            if is_sat:
                positions = solver.decode_solution()       
                is_valid = solver.validate_solution(positions)  
        return solver_time, is_sat, is_valid


    def _one_run(self, n: int) -> Dict[str, Any]:
        logic = PropositionalLogic(n)                       # bước 1
        generator = CNFGenerator(n)                         # bước 2

        t0 = time.perf_counter()
        clauses = generator.generate_all_constraints()      # bước 3
        generation_time = time.perf_counter() - t0

        clause_count = generator.get_clause_count()         # bước 4
        variables = len(logic.get_all_variables())

        solver_time, is_sat, is_valid = self.measure_solver_time(n, clauses)  # bước 5-9

        return {
            "variables": variables,
            "clauses": clause_count,
            "generation_time": generation_time,
            "solver_time": solver_time,
            "is_sat": is_sat,
            "is_valid": is_valid,
        }

    #Test 1 giá trị n
    def run_single_test(self, n: int) -> Result:
        if self.warmup:
            self._one_run(n)                                # bỏ kết quả

        runs = [self._one_run(n) for _ in range(self.repeats)]

        # Số biến, số clause, kết quả SAT/UNSAT phải giống nhau ở mọi lần chạy
        assert len({r["clauses"] for r in runs}) == 1
        assert len({r["is_sat"] for r in runs}) == 1

        is_sat = runs[0]["is_sat"]
        solver_times = [r["solver_time"] for r in runs]
        gen_times = [r["generation_time"] for r in runs]

        if is_sat:
            is_valid: Any = all(r["is_valid"] for r in runs)
        else:
            is_valid = "N/A"

        result: Result = {
            "n": n,
            "variables": runs[0]["variables"],
            "clauses": runs[0]["clauses"],
            "generation_time": statistics.mean(gen_times),
            "solver_time": statistics.mean(solver_times),
            "result": "SAT" if is_sat else "UNSAT",
            "is_valid": is_valid,
            "solver_time_std": statistics.stdev(solver_times) if len(solver_times) > 1 else 0.0,
            "solver_time_min": min(solver_times),
            "runs": self.repeats,
        }
        return result


    # Test nhiều giá trị n
    def run_multiple_tests(self, verbose: bool = True) -> List[Result]:
        """Lặp run_single_test cho từng N trong n_values."""
        self.results = []
        for n in self.n_values:
            res = self.run_single_test(n)
            self.results.append(res)
            if verbose:
                print(
                    f"N={res['n']:>2} | vars={res['variables']:>3} | "
                    f"clauses={res['clauses']:>5} | "
                    f"gen={res['generation_time']*1000:8.3f} ms | "
                    f"solve={res['solver_time']*1000:8.3f} ms | "
                    f"{res['result']:<5} | valid={res['is_valid']}"
                )
        return self.results


    def collect_results(self) -> Dict[str, Any]:

        if not self.results:
            self.run_multiple_tests(verbose=False)

        rows = list(self.results)
        solver_times = [r["solver_time"] for r in rows]
        slowest = max(rows, key=lambda r: r["solver_time"])
        summary = {
            "total_tests": len(rows),
            "repeats_per_n": self.repeats,
            "all_sat": all(r["result"] == "SAT" for r in rows),
            "all_valid": all(r["is_valid"] in (True, "N/A") for r in rows),
            "total_solver_time": sum(solver_times),
            "slowest_n": slowest["n"],
            "slowest_solver_time": slowest["solver_time"],
        }
        return {"rows": rows, "summary": summary}


    def export_results(self, filename: str = "sat_results.csv") -> str:
        if not self.results:
            self.run_multiple_tests(verbose=False)

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for r in self.results:
                row = dict(r)
                for key in ("generation_time", "solver_time",
                            "solver_time_std", "solver_time_min"):
                    row[key] = f"{r[key]:.6f}"
                writer.writerow(row)
        return filename