class KakuroConstraint:
    def __init__(self, cells, total):
        self.cells = tuple(cells)
        self.total = total

    def is_satisfied(self, assignment):
        values = [assignment[cell] for cell in self.cells if cell in assignment]
        if len(values) != len(set(values)):
            return False
        if len(values) == len(self.cells):
            return sum(values) == self.total
        remaining_count = len(self.cells) - len(values)
        available = [value for value in range(1, 10) if value not in values]
        if len(available) < remaining_count:
            return False
        remaining_total = self.total - sum(values)
        minimum = sum(available[:remaining_count])
        maximum = sum(available[-remaining_count:]) if remaining_count else 0
        return minimum <= remaining_total <= maximum


class KakuroModel:
    def __init__(self, grid):
        self.grid = grid
        self.variables = {}
        self.domains = {}
        self.constraints = []
        self.constraints_by_variable = {}
        self._create_variables()
        self._create_constraints()
        self._index_constraints()

    def _create_variables(self):
        for row, cells in enumerate(self.grid):
            for col, cell in enumerate(cells):
                if cell == ".":
                    variable = (row, col)
                    self.variables[variable] = variable
                    self.domains[variable] = set(range(1, 10))

    def _create_constraints(self):
        for row, cells in enumerate(self.grid):
            for col, cell in enumerate(cells):
                if not isinstance(cell, dict):
                    continue
                if cell.get("right") is not None:
                    run = self._find_run(row, col, 0, 1)
                    if run:
                        self.constraints.append(KakuroConstraint(run, cell["right"]))
                if cell.get("down") is not None:
                    run = self._find_run(row, col, 1, 0)
                    if run:
                        self.constraints.append(KakuroConstraint(run, cell["down"]))

    def _find_run(self, row, col, row_step, col_step):
        run = []
        row += row_step
        col += col_step
        while row < len(self.grid) and col < len(self.grid[row]):
            if self.grid[row][col] != ".":
                break
            run.append((row, col))
            row += row_step
            col += col_step
        return run

    def _index_constraints(self):
        for variable in self.variables:
            self.constraints_by_variable[variable] = []
        for constraint in self.constraints:
            for variable in constraint.cells:
                self.constraints_by_variable[variable].append(constraint)

    def get_constraints(self, variable):
        return self.constraints_by_variable.get(variable, [])

    def get_neighbors(self, variable):
        neighbors = set()
        for constraint in self.get_constraints(variable):
            neighbors.update(constraint.cells)
        neighbors.discard(variable)
        return neighbors

    def is_consistent(self, assignment):
        for variable, value in assignment.items():
            if variable not in self.domains or value not in self.domains[variable]:
                return False
        return all(constraint.is_satisfied(assignment) for constraint in self.constraints)

    def is_solution_valid(self, assignment):
        return (
            set(assignment) == set(self.variables)
            and self.is_consistent(assignment)
            and all(
                len(constraint.cells) > 0
                and sum(assignment[cell] for cell in constraint.cells) == constraint.total
                and len({assignment[cell] for cell in constraint.cells}) == len(constraint.cells)
                for constraint in self.constraints
            )
        )
