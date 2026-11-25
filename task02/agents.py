import time
from collections import deque

from game import Action, Direction, create_default_state, Wall


class Agent:
    # Lớp cha chung cho mọi thuật toán điều khiển tank
    def __init__(self, name, depth):
        if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
            raise ValueError("depth must be a positive integer")
        self.name = name
        self.depth = depth              # số ply tối đa được tìm kiếm
        self.nodes_expanded = 0         # đếm số trạng thái đã duyệt (để so sánh)

    def choose_action(self, state):
        raise NotImplementedError
    
    def terminal_value(self, state, me, depth):
        # Thắng sớm tốt hơn thắng muộn, thua muộn tốt hơn thua sớm
        u = state.utility(me)
        if u > 0:
            return u + depth
        if u < 0:
            return u - depth
        return 0


class MinimaxAgent(Agent):
    def __init__(self, depth=3, name="Minimax"):
        super().__init__(name, depth)

    def evaluate(self, state, player):
        own_tank = state.tanks[player]
        other_tank = state.tanks[1 - player]
        own_base = state.bases[player]
        other_base = state.bases[1 - player]
        return (
            25 * (own_tank.hp - other_tank.hp)
            + 15 * (own_base.hp - other_base.hp)
        )

    def choose_action(self, state):
        self.nodes_expanded = 0
        me = state.current_player
        best_action = None
        best_value = float("-inf")
        for action in state.get_legal_actions():
            child = state.apply_action(action)
            value = self._minimax(child, self.depth - 1, me)
            if value > best_value:
                best_value = value
                best_action = action
        return best_action

    def _minimax(self, state, depth, me):
        self.nodes_expanded += 1
        if state.is_terminal():
            return self.terminal_value(state, me, depth) 
        if depth == 0:
            return self.evaluate(state, me)

        values = []
        for action in state.get_legal_actions():
            values.append(self._minimax(state.apply_action(action), depth - 1, me))

        if state.current_player == me:
            return max(values)          # lượt của mình: chọn nước tốt nhất cho mình
        return min(values)              # lượt địch: địch chọn nước tệ nhất cho mình
    
class AlphaBetaAgent(MinimaxAgent):
    def __init__(self, depth=3, name="Alpha-Beta"):
        super().__init__(depth, name)

    def choose_action(self, state):
        self.nodes_expanded = 0
        me = state.current_player
        best_action = None
        best_value = float("-inf")
        for action in state.get_legal_actions():
            child = state.apply_action(action)
            value = self._alphabeta(child, self.depth - 1,
                                    best_value, float("inf"), me)
            if value > best_value:
                best_value = value
                best_action = action
        return best_action

    def _alphabeta(self, state, depth, alpha, beta, me):
        self.nodes_expanded += 1
        if state.is_terminal():
            return self.terminal_value(state, me, depth)
        if depth == 0:
            return self.evaluate(state, me)

        if state.current_player == me:              # MAX
            value = float("-inf")
            for action in state.get_legal_actions():
                value = max(value, self._alphabeta(
                    state.apply_action(action), depth - 1, alpha, beta, me))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break                           # cắt tỉa beta
            return value
        else:                                       # MIN
            value = float("inf")
            for action in state.get_legal_actions():
                value = min(value, self._alphabeta(
                    state.apply_action(action), depth - 1, alpha, beta, me))
                beta = min(beta, value)
                if alpha >= beta:
                    break                           # cắt tỉa alpha
            return value


# ---------- Heuristic ----------
W_TANK_HP, W_BASE_HP = 25, 15
W_AIM_TANK, W_AIM_BASE = 8, 9
W_BULLET_TANK, W_BULLET_BASE = 25, 15
W_AIM_WALL, W_BULLET_WALL = 7, 12
W_APPROACH = 1


def first_hit(state, row, col, direction, max_steps):
    # Đi từ ô kế bên theo hướng direction, trả về thực thể đầu tiên gặp
    # (Wall / Tank / Base) trong max_steps ô, hoặc None.
    for _ in range(max_steps):
        row += direction.drow
        col += direction.dcol
        if not state.in_bounds(row, col):
            return None
        if (row, col) in state.walls:
            return state.walls[(row, col)]
        tank = state.tank_at(row, col)
        if tank is not None:
            return tank
        base = state.base_at(row, col)
        if base is not None:
            return base
    return None


def distance_to_base(state, tank, base):
    goals = set()
    for direction in (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT):
        row = base.row + direction.drow
        col = base.col + direction.dcol
        if state.in_bounds(row, col):
            goals.add((row, col))
    start = (tank.row, tank.col)
    queue = deque([(start, 0)])
    visited = {start}
    while queue:
        (row, col), distance = queue.popleft()
        if (row, col) in goals:
            return distance
        for direction in (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT):
            next_row = row + direction.drow
            next_col = col + direction.dcol
            next_cell = (next_row, next_col)
            if next_cell in visited or not state.in_bounds(next_row, next_col):
                continue
            if next_cell != start and state.is_blocked(next_row, next_col):
                continue
            visited.add(next_cell)
            queue.append((next_cell, distance + 1))
    return None


def wall_blocks_base(wall, row, col, direction, base):
    wall_row, wall_col = wall.row - row, wall.col - col
    base_row, base_col = base.row - wall.row, base.col - wall.col
    wall_steps = wall_row * direction.drow + wall_col * direction.dcol
    base_steps = base_row * direction.drow + base_col * direction.dcol
    wall_cross = wall_row * direction.dcol - wall_col * direction.drow
    base_cross = base_row * direction.dcol - base_col * direction.drow
    return wall_steps > 0 and base_steps > 0 and wall_cross == 0 and base_cross == 0


class HeuristicMixin:
    # Chỉ ghi đè evaluate(); trộn vào Minimax hoặc Alpha-Beta
    def evaluate(self, state, me):
        return self._side_score(state, me) - self._side_score(state, 1 - me)

    def _side_score(self, state, p):
        tank, base = state.tanks[p], state.bases[p]
        enemy_tank, enemy_base = state.tanks[1 - p], state.bases[1 - p]

        score = W_TANK_HP * tank.hp + W_BASE_HP * base.hp

        # đang ngắm trúng địch (theo hướng nòng súng)
        target = first_hit(state, tank.row, tank.col, tank.direction,
                           max(state.width, state.height))
        if target is enemy_tank:
            score += W_AIM_TANK
        elif target is enemy_base:
            score += W_AIM_BASE
        elif isinstance(target, Wall) and wall_blocks_base(
            target, tank.row, tank.col, tank.direction, enemy_base
        ):
            score += W_AIM_WALL

        # đạn của mình đang bay sắp trúng địch
        for bl in state.bullets:
            if bl.owner == p:
                target = first_hit(state, bl.row, bl.col, bl.direction, 3)
                if target is enemy_tank:
                    score += W_BULLET_TANK
                elif target is enemy_base:
                    score += W_BULLET_BASE
                elif isinstance(target, Wall) and wall_blocks_base(
                    target, bl.row, bl.col, bl.direction, enemy_base
                ):
                    score += W_BULLET_WALL

        distance = distance_to_base(state, tank, enemy_base)
        if distance is None:
            score -= W_APPROACH * (state.width + state.height)
        else:
            score += W_APPROACH * (state.width + state.height - distance)
        return score


class HeuristicMinimaxAgent(HeuristicMixin, MinimaxAgent):
    def __init__(self, depth=3):
        super().__init__(depth, name="Heuristic Minimax")


class HeuristicAlphaBetaAgent(HeuristicMixin, AlphaBetaAgent):
    def __init__(self, depth=3):
        super().__init__(depth, name="Heuristic Alpha-Beta")


if __name__ == "__main__":
    # Test 1: thế cờ ép thắng. Tank 1 (còn 1 HP) bị kẹt giữa 2 tường
    # và tank 0, nên không thể tránh đạn.
    s = create_default_state()
    s.tanks[1].row = 5
    s.tanks[1].col = 4
    s.tanks[1].hp = 1
    s.walls[(5, 3)] = Wall(5, 3)
    s.walls[(5, 5)] = Wall(5, 5)

    agent = MinimaxAgent(depth=2)
    print(agent.choose_action(s))
    print(agent.nodes_expanded)

    # Test 2: số trạng thái và thời gian khi tăng độ sâu
    for d in range(1, 5):
        agent = MinimaxAgent(depth=d)
        start = time.perf_counter()
        action = agent.choose_action(create_default_state())
        elapsed = time.perf_counter() - start
        print(d, action, agent.nodes_expanded, round(elapsed, 4))
