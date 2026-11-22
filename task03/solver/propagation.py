from collections import deque

def has_support(constraint, variable, value, domains):
    if value not in domains[variable]:
        return False
    assignment = {variable: value}

    remaining_cells = []

    for cell in constraint.cells:
        if cell not in assignment :
            remaining_cells.append(cell)

    def explore(index):
        if index == len(remaining_cells):
            return constraint.is_satisfied(assignment)
        
        cell = remaining_cells[index]
        for candidate in domains[cell]:
            assignment[cell] = candidate
            if constraint.is_satisfied(assignment):
                if explore(index + 1):
                    del assignment[cell]
                    return True
            del assignment[cell]
        return False
    return explore(0)

def revise(constraint, variable, domains):
    changed = False

    for value in domains[variable].copy():

        if not has_support(constraint, variable, value, domains):
            domains[variable].remove(value)
            changed = True

    return changed



def propagate(model, domains, trace=None):
    queue = deque()
    in_queue = set()

    for constraint in model.constraints:
        for variable in constraint.cells:
            item = (constraint, variable)
            queue.append(item)
            in_queue.add(item)

    if any(len(d) == 0 for d in domains.values()):
        return False

    while queue:
        constraint, variable = queue.popleft()
        in_queue.remove((constraint, variable))

        before = domains[variable].copy()

        changed = revise(constraint, variable, domains)

        if changed:
            after = domains[variable].copy()

            if trace is not None:
                trace.append({
                    "type": "propagation",
                    "cell": variable,
                    "before": sorted(before),
                    "after": sorted(after),
                    "removed": sorted(before - after),
                    "domains": {
                        v: sorted(d)
                        for v, d in domains.items()
                    }
                })

            if len(domains[variable]) == 0:
                return False

            for related in model.get_constraints(variable):
                for cell in related.cells:
                    item = (related, cell)

                    if item not in in_queue:
                        queue.append(item)
                        in_queue.add(item)

    return True


