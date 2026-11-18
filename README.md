# AI Search Techniques

**Final project for Introduction to Artificial Intelligence**

Ton Duc Thang University · Faculty of Information Technology

This repository contains AI search implementations for N-Queens and a Constraint Satisfaction Problem (CSP) model for Kakuro.

## Project modules

| Task | Implementation | Main files |
| --- | --- | --- |
| N-Queens — propositional logic | CNF generation, Glucose3 solving, solution validation, and SAT experiments | `task01/logic/`, `task01/sat/`, `task01/experiments/` |
| N-Queens — local search | Min-Conflicts with `random` and `most_conflicts` variable-selection strategies | `task01/min_conflicts.py`, `task01/min_conflicts_experiment.py` |
| Kakuro — CSP model | Variables, domains, sum and all-different constraints, and consistency checks | `task03/kakuro_model.py` |

The Tank Battle entry point is reserved in `task02/`. The Kakuro solver and graphical interface are separate integration work.

## Requirements

- Python 3.9 or newer
- Dependencies listed in `requirements.txt` (`python-sat` provides the Glucose3 solver)

Create and activate a virtual environment from the repository root, then install dependencies from `requirements.txt`.

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For Command Prompt, use the equivalent activation command:

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

When you are done, run `deactivate` to leave the virtual environment.

## Run N-Queens

Start the interactive SAT solver from the `task01` directory:

```bash
cd task01
python main.py
```

Choose **1** to solve a board. Enter a board size to see the CNF clause count, Glucose3 result, queen positions, and validation status.

Choose **2** to run SAT experiments. For example, enter `4-10` to test increasing board sizes, then enter the number of runs per size. The results are exported to `sat_results.csv` by default. The repository includes the recorded N=4–10 results in `task01/sat_results.csv`.

## Run Min-Conflicts experiments

Run this command from the repository root:

```bash
python -m task01.min_conflicts_experiment
```

The experiment compares the standard random conflicted-variable choice with the `most_conflicts` heuristic over multiple board sizes. It reports success rate, average steps, and average runtime.

## Use the Kakuro CSP model

A white cell is written as `"."`. A clue cell is a dictionary with an optional `"right"` sum and/or `"down"` sum. The model uses `(row, column)` tuples as variable identifiers and gives each white cell the domain `{1, ..., 9}`.

```python
from task03.kakuro_model import KakuroModel

grid = [
    ["#", {"down": 4}, {"down": 6}],
    [{"right": 3}, ".", "."],
    [{"right": 7}, ".", "."],
]

model = KakuroModel(grid)
solution = {
    (1, 1): 1,
    (1, 2): 2,
    (2, 1): 3,
    (2, 2): 4,
}
print(model.is_solution_valid(solution))
```

Each run enforces its clue sum and prohibits repeated digits. `is_consistent()` checks partial assignments; `is_solution_valid()` checks a complete assignment.
