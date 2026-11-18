import random
import time

from game import create_default_state
from agents import (MinimaxAgent, AlphaBetaAgent,
                    HeuristicMinimaxAgent, HeuristicAlphaBetaAgent)

CONFIGS = [MinimaxAgent, AlphaBetaAgent,
           HeuristicMinimaxAgent, HeuristicAlphaBetaAgent]


def make_scenarios(n=10, seed=0):
    # Cùng một bộ thế cờ cho mọi thuật toán: chơi ngẫu nhiên vài nước từ thế mặc định
    rng = random.Random(seed)
    scenarios = [create_default_state()]
    while len(scenarios) < n:
        s = create_default_state()
        for _ in range(rng.choice([2, 4, 6, 8, 10])):
            if s.is_terminal():
                break
            s = s.apply_action(rng.choice(s.get_legal_actions()))
        if not s.is_terminal():
            scenarios.append(s)
    return scenarios


def benchmark(depths=(1, 2, 3, 4), n_scenarios=10):
    scenarios = make_scenarios(n_scenarios)
    print(f"{'Depth':<6}{'Config':<22}{'Avg nodes':>12}{'Avg time(s)':>14}{'Same action as Minimax':>26}")
    for depth in depths:
        base_actions = {}
        for cls in CONFIGS:
            agent = cls(depth)
            nodes, total_time, actions = 0, 0.0, []
            for s in scenarios:
                start = time.perf_counter()
                actions.append(agent.choose_action(s))
                total_time += time.perf_counter() - start
                nodes += agent.nodes_expanded
            key = "H" if cls in (HeuristicMinimaxAgent, HeuristicAlphaBetaAgent) else "P"
            if cls in (MinimaxAgent, HeuristicMinimaxAgent):
                base_actions[key] = actions
                same = "-"
            else:
                same = f"{sum(a == b for a, b in zip(actions, base_actions[key]))}/{len(actions)}"
            print(f"{depth:<6}{agent.name:<22}{nodes / len(scenarios):>12.0f}"
                  f"{total_time / len(scenarios):>14.4f}{same:>26}")
        print()


def play_match(agent0, agent1, max_cycles=60):
    # Trả về (winner, số cycle). winner = None nếu hòa / hết cycle
    state = create_default_state()
    agents = [agent0, agent1]
    for cycle in range(1, max_cycles + 1):
        for _ in range(2):
            action = agents[state.current_player].choose_action(state)
            state = state.apply_action(action)
            if state.is_terminal():
                return state.winner(), cycle
    return None, max_cycles


def head_to_head(depth=3):
    print(f"Đối kháng (depth={depth}, mỗi cặp đổi bên 2 lượt)")
    for i, a_cls in enumerate(CONFIGS):
        for b_cls in CONFIGS[i + 1:]:
            a_wins = b_wins = draws = 0
            for a_side in (0, 1):
                a, b = a_cls(depth), b_cls(depth)
                players = (a, b) if a_side == 0 else (b, a)
                winner, _ = play_match(*players)
                if winner is None:
                    draws += 1
                elif winner == a_side:
                    a_wins += 1
                else:
                    b_wins += 1
            print(f"{a_cls(depth).name:<22} vs {b_cls(depth).name:<22} "
                  f"{a_wins}-{b_wins} (hòa {draws})")


if __name__ == "__main__":
    benchmark()
    head_to_head()