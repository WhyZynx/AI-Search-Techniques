from .min_conflicts import MinConflictsSolver


def run_experiments(sizes=(4, 8, 12, 20), trials=30, max_steps=10000):
    results = []
    for n in sizes:
        for heuristic in ("random", "most_conflicts"):
            runs = [
                MinConflictsSolver(
                    n,
                    heuristic=heuristic,
                    max_steps=max_steps,
                    seed=trial,
                ).solve()
                for trial in range(trials)
            ]
            results.append({
                "n": n,
                "heuristic": heuristic,
                "success_rate": sum(result.success for result in runs) / trials,
                "average_steps": sum(result.steps for result in runs) / trials,
                "average_time": sum(result.elapsed_time for result in runs) / trials,
            })
    return results


def print_results(results):
    print(f"{'N':>4} {'Heuristic':>16} {'Success rate':>14} {'Average steps':>15} {'Average time (ms)':>19}")
    for result in results:
        print(
            f"{result['n']:>4} "
            f"{result['heuristic']:>16} "
            f"{result['success_rate'] * 100:>13.1f}% "
            f"{result['average_steps']:>15.2f} "
            f"{result['average_time'] * 1000:>19.3f}"
        )


if __name__ == "__main__":
    print_results(run_experiments())
