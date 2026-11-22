from .propagation import has_support
def select_variable(model, domains):
    unassigned = [
        var for var in domains
        if len(domains[var]) > 1
    ]

    if not unassigned:
        return None

    def degree(var):
        neighbors = model.get_neighbors(var)

        return sum(
            1 for neighbor in neighbors
            if len(domains[neighbor]) > 1
        )

    return min(
        unassigned,
        key=lambda var: (
            len(domains[var]),
            -degree(var)
        )
    )

def order_values(model, variable, domains):
    neighbors = model.get_neighbors(variable)

    def lcv_score(value):
        test_domains = {
            var: values.copy()
            for var, values in domains.items()
        }

        test_domains[variable] = {value}

        score = 0

        for neighbor in neighbors:
            if len(test_domains[neighbor]) <= 1:
                continue

            for candidate in test_domains[neighbor]:
                supported = True

                for constraint in model.get_constraints(neighbor):
                    if not has_support(
                        constraint,
                        neighbor,
                        candidate,
                        test_domains
                    ):
                        supported = False
                        break

                if supported:
                    score += 1

        return score
    return sorted(
        domains[variable],
        key=lambda value: (-lcv_score(value), value)
    )

