from pathlib import Path

import pygame

from game import Action, Direction, create_default_state
from agents import (
    MinimaxAgent,
    AlphaBetaAgent,
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent,
)


pygame.init()

WIDTH, HEIGHT = 1120, 740
CELL = 52
BOARD_X, BOARD_Y = 56, 153

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tank Battle")
clock = pygame.time.Clock()

BG = (243, 246, 250)
CARD = (255, 255, 255)
CARD_ALT = (248, 250, 252)
BORDER = (221, 229, 238)
TEXT = (35, 48, 65)
MUTED = (105, 121, 141)
BLUE = (55, 111, 196)
BLUE_HOVER = (77, 132, 214)
P0_COLOR = (55, 111, 196)
P1_COLOR = (190, 72, 126)
GOLD = (230, 163, 47)
WALL_COLOR = (151, 164, 181)

font = pygame.font.SysFont("segoeui", 18)
small = pygame.font.SysFont("segoeui", 15)
tiny = pygame.font.SysFont("segoeui", 13)
title_font = pygame.font.SysFont("segoeui", 30, bold=True)
section_font = pygame.font.SysFont("segoeui", 17, bold=True)

ASSET_DIR = Path(__file__).with_name("assets")
ASSET_FILES = (
    "grass.png", "wall.png", "goal.png", "box.png", "brown_box.png",
    "blue_box.png", "pink_box.png", "duck_front.png", "duck_back.png",
    "duck_left.png", "duck_right.png", "duck2_front.png", "duck2_back.png",
    "duck2_left.png", "duck2_right.png",
)
sprites = {}
scaled_sprites = {}
for filename in ASSET_FILES:
    try:
        sprites[filename] = pygame.image.load(str(ASSET_DIR / filename)).convert_alpha()
    except (pygame.error, OSError):
        sprites[filename] = None

tank_sprites = {
    0: {
        Direction.UP: "duck_back.png",
        Direction.DOWN: "duck_front.png",
        Direction.LEFT: "duck_left.png",
        Direction.RIGHT: "duck_right.png",
    },
    1: {
        Direction.UP: "duck2_back.png",
        Direction.DOWN: "duck2_front.png",
        Direction.LEFT: "duck2_left.png",
        Direction.RIGHT: "duck2_right.png",
    },
}

agent_classes = [
    MinimaxAgent,
    AlphaBetaAgent,
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent,
]
agent_names = [
    "Minimax",
    "Alpha-Beta",
    "Heuristic Minimax",
    "Heuristic Alpha-Beta",
]
selected_agents = [2, 3]

state = create_default_state()
search_depth = 2
step_delay = 850
max_actions = 160
auto_play = False
turn_count = 0
last_action = "No moves yet"
last_step_time = 0

board_card = pygame.Rect(24, 102, 520, 566)
panel_card = pygame.Rect(560, 102, 536, 566)
buttons = {
    "P0": pygame.Rect(582, 340, 238, 42),
    "P1": pygame.Rect(836, 340, 238, 42),
    "NEXT": pygame.Rect(582, 442, 154, 46),
    "PLAY": pygame.Rect(750, 442, 154, 46),
    "RESET": pygame.Rect(918, 442, 156, 46),
}


def draw_text(text, x, y, color=TEXT, used_font=font):
    image = used_font.render(str(text), True, color)
    screen.blit(image, (x, y))


def sprite(name, size):
    image = sprites.get(name)
    if image is None:
        return None
    key = (name, size)
    if key not in scaled_sprites:
        scaled_sprites[key] = pygame.transform.scale(image, (size, size))
    return scaled_sprites[key]


def draw_sprite(name, rect):
    image = sprite(name, min(rect.width, rect.height))
    if image is None:
        return False
    screen.blit(image, image.get_rect(center=rect.center))
    return True


def fit_text(value, used_font, max_width):
    value = str(value)
    if used_font.size(value)[0] <= max_width:
        return value
    while value and used_font.size(value + "…")[0] > max_width:
        value = value[:-1]
    return value + "…"


def cell_rect(row, col):
    return pygame.Rect(BOARD_X + col * CELL + 1, BOARD_Y + row * CELL + 1, CELL - 2, CELL - 2)


def draw_hp_bar(x, y, width, hp, maximum, color):
    ratio = max(0, min(hp / maximum, 1))
    pygame.draw.rect(screen, (231, 236, 243), (x, y, width, 7), border_radius=4)
    if ratio:
        pygame.draw.rect(screen, color, (x, y, max(5, int(width * ratio)), 7), border_radius=4)


def draw_board():
    draw_text("BATTLEFIELD", 42, 118, TEXT, section_font)
    draw_text("9 × 9", 477, 120, MUTED, tiny)
    for col in range(state.width):
        label = tiny.render(str(col), True, MUTED)
        screen.blit(label, label.get_rect(center=(BOARD_X + col * CELL + CELL // 2, BOARD_Y - 9)))

    for row in range(state.height):
        label = tiny.render(str(row), True, MUTED)
        screen.blit(label, label.get_rect(center=(BOARD_X - 15, BOARD_Y + row * CELL + CELL // 2)))
        for col in range(state.width):
            rect = cell_rect(row, col)
            if not draw_sprite("grass.png", rect):
                color = (231, 238, 246) if (row + col) % 2 == 0 else (221, 231, 242)
                pygame.draw.rect(screen, color, rect, border_radius=4)
            pygame.draw.rect(screen, (211, 225, 204), rect, 1, border_radius=4)

    for wall in state.walls.values():
        rect = cell_rect(wall.row, wall.col).inflate(-3, -3)
        if not draw_sprite("wall.png", rect):
            pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=7)
        badge = pygame.Rect(rect.right - 18, rect.bottom - 18, 17, 17)
        if not draw_sprite("box.png" if wall.hp == 3 else "brown_box.png", badge):
            pygame.draw.rect(screen, (64, 84, 61), badge, border_radius=4)
        label = tiny.render(str(wall.hp), True, TEXT)
        screen.blit(label, label.get_rect(center=badge.center))

    for base in state.bases:
        if not base.is_alive():
            continue
        rect = cell_rect(base.row, base.col).inflate(-4, -4)
        color = P0_COLOR if base.owner == 0 else P1_COLOR
        pygame.draw.circle(screen, color, rect.center, rect.width // 2)
        draw_sprite("goal.png", rect.inflate(-4, -4))
        badge = pygame.Rect(rect.x - 2, rect.y - 2, 21, 15)
        pygame.draw.rect(screen, color, badge, border_radius=5)
        label = tiny.render(f"B{base.owner}", True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=badge.center))

    for tank in state.tanks:
        if not tank.is_alive():
            continue
        rect = cell_rect(tank.row, tank.col)
        color = P0_COLOR if tank.owner == 0 else P1_COLOR
        pygame.draw.circle(screen, color, rect.center, 24, 2)
        name = tank_sprites[tank.owner][tank.direction]
        if not draw_sprite(name, rect.inflate(-4, -4)):
            pygame.draw.circle(screen, color, rect.center, 18)
        badge = pygame.Rect(rect.x + 1, rect.y + 1, 15, 15)
        pygame.draw.circle(screen, color, badge.center, 8)
        label = tiny.render(str(tank.owner), True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=badge.center))

    draw_bullets()
    draw_sprite("duck_front.png", pygame.Rect(40, 622, 22, 22))
    draw_text("P0", 66, 626, MUTED, tiny)
    draw_sprite("duck2_front.png", pygame.Rect(115, 622, 22, 22))
    draw_text("P1", 141, 626, MUTED, tiny)
    draw_sprite("wall.png", pygame.Rect(193, 622, 22, 22))
    draw_text("Wall", 219, 626, MUTED, tiny)
    draw_sprite("goal.png", pygame.Rect(277, 622, 22, 22))
    draw_text("Base", 303, 626, MUTED, tiny)
    pygame.draw.circle(screen, GOLD, (382, 633), 5)
    draw_text("Bullet", 393, 626, MUTED, tiny)


def draw_bullets():
    for bullet in state.bullets:
        if not state.in_bounds(bullet.row, bullet.col):
            continue
        cx = BOARD_X + bullet.col * CELL + CELL // 2
        cy = BOARD_Y + bullet.row * CELL + CELL // 2
        color = P0_COLOR if bullet.owner == 0 else P1_COLOR
        tail = (cx - bullet.direction.dcol * 8, cy - bullet.direction.drow * 8)
        pygame.draw.line(screen, color, tail, (cx, cy), 4)
        pygame.draw.circle(screen, GOLD, (cx, cy), 5)
        pygame.draw.circle(screen, (255, 255, 255), (cx - 1, cy - 1), 2)


def draw_player_card(player, x, y, width):
    color = P0_COLOR if player == 0 else P1_COLOR
    tank, base = state.tanks[player], state.bases[player]
    rect = pygame.Rect(x, y, width, 106)
    pygame.draw.rect(screen, CARD_ALT, rect, border_radius=12)
    pygame.draw.rect(screen, color if state.current_player == player else BORDER, rect, 2, border_radius=12)
    draw_text(f"PLAYER {player}", x + 14, y + 10, color, section_font)
    icon = "blue_box.png" if player == 0 else "pink_box.png"
    draw_sprite(icon, pygame.Rect(x + width - 37, y + 3, 28, 28))
    draw_text(f"Tank  {max(0, tank.hp)}/6", x + 14, y + 37, TEXT, tiny)
    draw_hp_bar(x + 100, y + 43, width - 114, tank.hp, 6, color)
    draw_text(f"Base  {max(0, base.hp)}/9", x + 14, y + 68, TEXT, tiny)
    draw_hp_bar(x + 100, y + 74, width - 114, base.hp, 9, color)


def draw_button(rect, label, active=False, disabled=False):
    if disabled:
        fill, text_color = (237, 240, 245), MUTED
    elif active:
        fill, text_color = (41, 139, 111), (255, 255, 255)
    else:
        fill = (78, 132, 214) if rect.collidepoint(pygame.mouse.get_pos()) else BLUE
        text_color = (255, 255, 255)
    pygame.draw.rect(screen, fill, rect, border_radius=9)
    pygame.draw.rect(screen, BORDER, rect, 1, border_radius=9)
    label = fit_text(label, small, rect.width - 16)
    image = small.render(label, True, text_color)
    screen.blit(image, image.get_rect(center=rect.center))


def game_finished():
    return state.is_terminal() or turn_count >= max_actions


def draw_panel():
    draw_text("MATCH", 582, 118, TEXT, section_font)
    if state.is_terminal():
        winner = state.winner()
        status = f"Player {winner} wins" if winner is not None else "Draw"
        accent = P0_COLOR if winner == 0 else P1_COLOR if winner == 1 else GOLD
    elif turn_count >= max_actions:
        status, accent = "Draw · move limit reached", GOLD
    else:
        status = f"Player {state.current_player} to move"
        accent = P0_COLOR if state.current_player == 0 else P1_COLOR
    status_rect = pygame.Rect(582, 145, 492, 38)
    pygame.draw.rect(screen, CARD_ALT, status_rect, border_radius=9)
    pygame.draw.circle(screen, accent, (600, 164), 5)
    draw_text(status, 614, 154, TEXT, small)
    mode = small.render("AUTO" if auto_play else "PAUSED", True, P0_COLOR if auto_play else MUTED)
    screen.blit(mode, mode.get_rect(midright=(1059, 164)))

    draw_player_card(0, 582, 197, 238)
    draw_player_card(1, 836, 197, 238)

    draw_text("AGENTS", 582, 321, TEXT, section_font)
    draw_text(f"Depth {search_depth} · click to switch", 855, 324, MUTED, tiny)
    draw_button(buttons["P0"], f"P0  ·  {agent_names[selected_agents[0]]}")
    draw_button(buttons["P1"], f"P1  ·  {agent_names[selected_agents[1]]}")

    can_play = not game_finished()
    draw_text("ACTIONS", 582, 417, TEXT, section_font)
    draw_button(buttons["NEXT"], "NEXT MOVE", disabled=not can_play)
    draw_button(buttons["PLAY"], "PAUSE" if auto_play else "AUTO PLAY", active=auto_play, disabled=not can_play)
    draw_button(buttons["RESET"], "RESET")
    draw_text("LAST MOVE", 582, 515, MUTED, tiny)
    draw_text(fit_text(last_action, small, 470), 582, 537, TEXT, small)
    draw_text("Q/E switch · N next · P play · R reset", 582, 625, MUTED, tiny)


def draw_game():
    screen.fill(BG)
    draw_text("TANK BATTLE", 30, 26, TEXT, title_font)
    draw_text("Choose agents, make a move, or watch the match", 32, 67, MUTED, small)
    pygame.draw.rect(screen, (229, 235, 243), board_card.move(0, 4), border_radius=15)
    pygame.draw.rect(screen, CARD, board_card, border_radius=15)
    pygame.draw.rect(screen, BORDER, board_card, 1, border_radius=15)
    pygame.draw.rect(screen, (229, 235, 243), panel_card.move(0, 4), border_radius=15)
    pygame.draw.rect(screen, CARD, panel_card, border_radius=15)
    pygame.draw.rect(screen, BORDER, panel_card, 1, border_radius=15)
    draw_board()
    draw_panel()
    pygame.display.flip()


def reset_game():
    global state, auto_play, turn_count, last_action
    state = create_default_state()
    auto_play = False
    turn_count = 0
    last_action = "No moves yet"


def ai_step():
    global state, turn_count, last_action
    if game_finished():
        return
    player = state.current_player
    agent = agent_classes[selected_agents[player]](depth=search_depth)
    action = agent.choose_action(state)
    if action not in state.get_legal_actions():
        return
    state = state.apply_action(action)
    last_action = f"Player {player} · {action.name.replace('_', ' ').title()}"
    turn_count += 1


def handle_click(position):
    global auto_play, last_step_time
    if buttons["P0"].collidepoint(position):
        selected_agents[0] = (selected_agents[0] + 1) % len(agent_classes)
        auto_play = False
    elif buttons["P1"].collidepoint(position):
        selected_agents[1] = (selected_agents[1] + 1) % len(agent_classes)
        auto_play = False
    elif buttons["NEXT"].collidepoint(position):
        auto_play = False
        ai_step()
    elif buttons["PLAY"].collidepoint(position):
        if not game_finished():
            auto_play = not auto_play
            last_step_time = pygame.time.get_ticks()
    elif buttons["RESET"].collidepoint(position):
        reset_game()


def handle_key(key):
    if key == pygame.K_r:
        reset_game()
    elif key == pygame.K_q:
        handle_click(buttons["P0"].center)
    elif key == pygame.K_e:
        handle_click(buttons["P1"].center)
    elif key == pygame.K_n:
        handle_click(buttons["NEXT"].center)
    elif key == pygame.K_p:
        handle_click(buttons["PLAY"].center)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            handle_key(event.key)

    if auto_play:
        if game_finished():
            auto_play = False
        elif pygame.time.get_ticks() - last_step_time >= step_delay:
            ai_step()
            last_step_time = pygame.time.get_ticks()

    draw_game()
    clock.tick(60)

pygame.quit()
