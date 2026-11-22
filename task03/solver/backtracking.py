
from .propagation import propagate
from .heuristics import select_variable, order_values


def snapshot(domains):
    return {
        var: sorted(values)
        for var, values in domains.items()
    }


def solve(model, return_trace=False):
    domains = {
        var: values.copy()
        for var, values in model.domains.items()
    }

    trace = [] if return_trace else None

    solution = backtrack(model, domains, trace)

    if return_trace:
        return solution, trace

    return solution


def backtrack(model, domains, trace=None):
    if not propagate(model, domains, trace):
        return None

    variable = select_variable(model, domains)

    if variable is None:
        assignment = {
            var: next(iter(values))
            for var, values in domains.items()
        }

        if model.is_solution_valid(assignment):
            if trace is not None:
                trace.append({
                    "type": "solution",
                    "assignment": assignment.copy(),
                    "domains": snapshot(domains)
                })
            return assignment

        return None

    if trace is not None:
        trace.append({
            "type": "select",
            "cell": variable,
            "domains": snapshot(domains)
        })

    for value in order_values(model, variable, domains):
        new_domains = {
            var: values.copy()
            for var, values in domains.items()
        }

        new_domains[variable] = {value}

        if trace is not None:
            trace.append({
                "type": "try",
                "cell": variable,
                "value": value,
                "domains": snapshot(new_domains)
            })

        result = backtrack(model, new_domains, trace)

        if result is not None:
            return result

        if trace is not None:
            trace.append({
                "type": "backtrack",
                "cell": variable,
                "value": value,
                "domains": snapshot(domains)
            })

    return None
