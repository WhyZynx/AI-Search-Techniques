from dataclasses import dataclass, replace
from enum import Enum

WIN_SCORE = 1000

class Action(Enum):
    MOVE_UP = 0
    MOVE_DOWN = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3
    FIRE = 4
    STAY = 5


class Direction(Enum):
    # Giá trị là (drow, dcol): độ thay đổi hàng và cột khi đi 1 ô
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

    @property
    def drow(self):
        return self.value[0]

    @property
    def dcol(self):
        return self.value[1]


# Hành động di chuyển -> hướng tương ứng
MOVE_TO_DIRECTION = {
    Action.MOVE_UP: Direction.UP,
    Action.MOVE_DOWN: Direction.DOWN,
    Action.MOVE_LEFT: Direction.LEFT,
    Action.MOVE_RIGHT: Direction.RIGHT,
}

@dataclass
class Tank:
    row: int
    col: int
    direction: Direction
    owner: int          # 0 hoặc 1: tank này của người chơi nào
    hp: int = 6         # theo bảng trong đề

    def is_alive(self):
        return self.hp > 0
    
@dataclass
class Wall:
    row: int
    col: int
    hp: int = 3         # theo bảng trong đề


@dataclass
class Base:
    row: int
    col: int
    owner: int
    hp: int = 9         # theo bảng trong đề

    def is_alive(self):
        return self.hp > 0


@dataclass
class Bullet:
    row: int
    col: int
    direction: Direction
    owner: int          # đạn của ai bắn


class GameState:
    def __init__(self, width, height, tanks, bases, walls,
                 bullets=None, current_player=0):
        self.width = width
        self.height = height
        self.tanks = tanks              # list 2 Tank, chỉ số = owner
        self.bases = bases              # list 2 Base, chỉ số = owner
        self.walls = walls              # dict {(row, col): Wall}
        self.bullets = bullets if bullets is not None else []
        self.current_player = current_player   # ai đang đến lượt (0 hoặc 1)
        self.last_bullet_paths = []

    def copy(self):
        return GameState(
            self.width,
            self.height,
            [replace(t) for t in self.tanks],
            [replace(b) for b in self.bases],
            {pos: replace(w) for pos, w in self.walls.items()},
            [replace(b) for b in self.bullets],
            self.current_player,
        )

    def in_bounds(self, row, col):
        return 0 <= row < self.height and 0 <= col < self.width

    def tank_at(self, row, col):
        for t in self.tanks:
            if t.is_alive() and t.row == row and t.col == col:
                return t
        return None

    def base_at(self, row, col):
        for b in self.bases:
            if b.is_alive() and b.row == row and b.col == col:
                return b
        return None

    def is_blocked(self, row, col):
        # Ô mà tank KHÔNG thể đi vào
        return (not self.in_bounds(row, col)
                or (row, col) in self.walls
                or self.tank_at(row, col) is not None
                or self.base_at(row, col) is not None)

    def __str__(self):
        grid = [[".." for _ in range(self.width)] for _ in range(self.height)]
        for (r, c) in self.walls:
            grid[r][c] = "##"
        for b in self.bases:
            if b.is_alive():
                grid[b.row][b.col] = f"B{b.owner}"
        for t in self.tanks:
            if t.is_alive():
                grid[t.row][t.col] = f"T{t.owner}"
        for bl in self.bullets:
            grid[bl.row][bl.col] = "**"
        return "\n".join(" ".join(row) for row in grid)

    def get_legal_actions(self):
        # FIRE đứng đầu để sau này Alpha-Beta xét nhánh tốt trước
        return [Action.FIRE, Action.MOVE_UP, Action.MOVE_DOWN,
                Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.STAY]

    def apply_action(self, action):
        new_state = self.copy()
        new_state._do_action(action)
        if self.current_player == 1:
            new_state._move_bullets()   # hết 1 cycle (cả 2 người đã đi) thì đạn bay
        new_state.current_player = 1 - self.current_player
        return new_state

    def _do_action(self, action):
        # Thực hiện hành động của người chơi đang đến lượt (sửa trực tiếp state này)
        tank = self.tanks[self.current_player]
        if not tank.is_alive():
            return

        if action == Action.STAY:
            return

        if action == Action.FIRE:
            self.bullets.append(
                Bullet(tank.row, tank.col, tank.direction, tank.owner))
            return

        # Còn lại là 4 hành động di chuyển
        direction = MOVE_TO_DIRECTION[action]
        tank.direction = direction          # luôn quay theo hướng muốn đi
        new_row = tank.row + direction.drow
        new_col = tank.col + direction.dcol
        if not self.is_blocked(new_row, new_col):
            tank.row = new_row
            tank.col = new_col
            
    
    def _move_bullets(self):
        remaining = []
        paths = []

        for bullet in self.bullets:
            hit = False
            impact = None

            start = (bullet.row, bullet.col)
            path = []

            for _ in range(3):
                bullet.row += bullet.direction.drow
                bullet.col += bullet.direction.dcol

                current = (bullet.row, bullet.col)
                path.append(current)

                if not self.in_bounds(bullet.row, bullet.col):
                    hit_type = "boundary"

                elif (bullet.row, bullet.col) in self.walls:
                    hit_type = "wall"

                elif self.tank_at(bullet.row, bullet.col) is not None:
                    hit_type = "tank"

                elif self.base_at(bullet.row, bullet.col) is not None:
                    hit_type = "base"

                else:
                    hit_type = None

                if self._bullet_hit(bullet.row, bullet.col):
                    hit = True

                    impact = {
                        "row": bullet.row,
                        "col": bullet.col,
                        "type": hit_type
                    }

                    break

            if not hit:
                remaining.append(bullet)

            paths.append({
                "owner": bullet.owner,
                "direction": bullet.direction,
                "start": start,
                "path": path,
                "survived": not hit,
                "hit": hit,
                "impact": impact
            })

        self.bullets = remaining
        self.last_bullet_paths = paths


    def _bullet_hit(self, row, col):
        # Trả về True nếu đạn bị chặn tại ô (row, col) (và xử lý sát thương)
        if not self.in_bounds(row, col):
            return True                             # bay ra ngoài bản đồ: biến mất

        if (row, col) in self.walls:
            wall = self.walls[(row, col)]
            wall.hp -= 1
            if wall.hp <= 0:
                del self.walls[(row, col)]          # tường hết máu thì biến mất
            return True

        tank = self.tank_at(row, col)
        if tank is not None:
            tank.hp -= 1
            return True

        base = self.base_at(row, col)
        if base is not None:
            base.hp -= 1
            return True

        return False
    
    def _is_defeated(self, player):
        # Người chơi thua nếu tank HOẶC base của mình bị phá
        return (not self.tanks[player].is_alive()
                or not self.bases[player].is_alive())

    def is_terminal(self):
        return self._is_defeated(0) or self._is_defeated(1)

    def winner(self):
        # Trả về 0 hoặc 1 nếu có người thắng, None nếu chưa kết thúc hoặc hòa
        defeated0 = self._is_defeated(0)
        defeated1 = self._is_defeated(1)
        if defeated0 and not defeated1:
            return 1
        if defeated1 and not defeated0:
            return 0
        return None

    def utility(self, player):
        # Giá trị của trạng thái cuối từ góc nhìn của `player`
        w = self.winner()
        if w is None:
            return 0                        # hòa
        return WIN_SCORE if w == player else -WIN_SCORE


def create_default_state():
    # Bản đồ 9x9 để test. Người chơi 0 ở dưới, người chơi 1 ở trên.
    tanks = [
        Tank(row=6, col=4, direction=Direction.UP, owner=0),
        Tank(row=2, col=4, direction=Direction.DOWN, owner=1),
    ]
    bases = [
        Base(row=8, col=4, owner=0),
        Base(row=0, col=4, owner=1),
    ]
    wall_positions = [(7, 3), (7, 4), (7, 5),
                      (1, 3), (1, 4), (1, 5),
                      (4, 2), (4, 3), (4, 5), (4, 6)]
    walls = {pos: Wall(pos[0], pos[1]) for pos in wall_positions}
    return GameState(9, 9, tanks, bases, walls)


if __name__ == "__main__":
    s = create_default_state()
    print(s.is_terminal(), s.winner())

    # Cho tank 1 còn 1 máu rồi bắn trúng
    s.tanks[1].hp = 1
    t = s.apply_action(Action.FIRE).apply_action(Action.STAY)
    print(t.is_terminal())
    t = t.apply_action(Action.STAY).apply_action(Action.STAY)
    print(t.is_terminal(), t.winner(), t.utility(0), t.utility(1))

    # Cả hai tank cùng bị phá: hòa
    d = create_default_state()
    d.tanks[0].hp = 0
    d.tanks[1].hp = 0
    print(d.is_terminal(), d.winner(), d.utility(0))
