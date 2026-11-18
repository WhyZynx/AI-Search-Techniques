import time
from typing import List, Optional

from logic.cnf_generator import CNFGenerator
from sat.glucose_solver import GlucoseSolver
from experiments.sat_experiment import SATExperiment

DEFAULT_CSV = "sat_results.csv"
DEFAULT_N_VALUES = list(range(4, 11))
DEFAULT_REPEATS = 5

def ask_int(prompt: str, min_value: int = 1, default: Optional[int] = None) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            value = int(raw)
            if value >= min_value:
                return value
            print(f" Please enter an integer greater than or equal to {min_value}.")
        except ValueError:
            print(" Invalid value. Please enter an integer.")

def parse_n_list(text: str) -> List[int]:
    values = set()
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            a, b = int(start), int(end)
            if a > b:
                raise ValueError(f"Invalid range: {part}")
            values.update(range(a, b + 1))
        else:
            values.add(int(part))

    result = sorted(values)
    if not result or result[0] < 1:
        raise ValueError("N must be a positive integer.")

    return result

def print_board(n: int, positions: List[tuple]) -> None:
    queens = set(positions)
    for i in range(n):
        print("  " + " ".join("Q" if (i, j) in queens else "." for j in range(n)))

def mode_solve() -> None:
    n = ask_int("Enter N (board size): ")

    if n > 30:
        print(f" Note: N = {n} is quite large. The number of clauses increases rapidly, so solving may take longer.")

    generator = CNFGenerator(n)
    t0 = time.perf_counter()
    clauses = generator.generate_all_constraints()
    generation_time = time.perf_counter() - t0

    print(f"\nCNF generated: {n * n} variables, {generator.get_clause_count()} clauses "
          f"({generation_time * 1000:.3f} ms)")

    with GlucoseSolver(n) as solver:
        is_sat = solver.solve(clauses)

        print(f"Glucose3 result: {'SAT' if is_sat else 'UNSAT'} "
              f"({solver.solve_time * 1000:.3f} ms)")

        if not is_sat:
            print(f"\nNo valid arrangement of {n} queens satisfies all constraints.")
            return

        positions = solver.decode_solution()

        print("\nQueen positions (row, column), using zero-based indexing:")
        print("  " + ", ".join(f"({i},{j})" for i, j in positions))

        print("\nChessboard:")
        print_board(n, positions)

        is_valid = solver.validate_solution(positions)
        print(f"\nSolution validation: {'VALID' if is_valid else 'INVALID'}")

def mode_experiments() -> None:
    default_text = "4-10"

    raw = input(
        f"Enter N values (e.g., 4-10 or 4,6,8) [default: {default_text}]: "
    ).strip()

    try:
        n_values = parse_n_list(raw or default_text)
    except ValueError as e:
        print(f" Invalid N list: {e}")
        return

    repeats = ask_int(
        f"Number of runs for each N [default: {DEFAULT_REPEATS}]: ",
        default=DEFAULT_REPEATS
    )

    csv_name = input(
        f"CSV file name [default: {DEFAULT_CSV}]: "
    ).strip() or DEFAULT_CSV

    print(f"\nRunning benchmark: N = {n_values}, {repeats} runs for each N\n")

    experiment = SATExperiment(n_values=n_values, repeats=repeats)
    experiment.run_multiple_tests()

    data = experiment.collect_results()
    s = data["summary"]

    print("\nSummary:")
    print(f"  Total N values tested : {s['total_tests']}")
    print(f"  Repeats per N         : {s['repeats_per_n']}")
    print(f"  All results are SAT   : {s['all_sat']}")
    print(f"  All solutions valid   : {s['all_valid']}")
    print(f"  Slowest N             : {s['slowest_n']} "
          f"({s['slowest_solver_time'] * 1000:.3f} ms)")

    path = experiment.export_results(csv_name)
    print(f"\nResults exported to: {path}")

MENU = """
----------------------------------
  N-Queens using SAT (Glucose3)
----------------------------------
  1. Solve N-Queens
  2. Run Experiments
  0. Exit
"""

def main() -> None:
    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        if choice == "1":
            mode_solve()
        elif choice == "2":
            mode_experiments()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print(" Invalid choice. Please enter 1, 2, or 0.")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram terminated.")
