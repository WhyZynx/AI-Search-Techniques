
import pygame

from game import Action, create_default_state
from agents import (
    MinimaxAgent,
    AlphaBetaAgent,
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent,
)

pygame.init()

WIDTH, HEIGHT = 1040, 680
CELL = 56
BOARD_X, BOARD_Y = 40, 95

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tank Battle - AI Visualizer")
clock = pygame.time.Clock()

BG = (15, 23, 42)
PANEL = (30, 41, 59)
GRID_1 = (40, 57, 78)
GRID_2 = (45, 64, 86)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
BLUE = (59, 130, 246)
GREEN = (52, 211, 153)
RED = (251, 113, 133)
YELLOW = (250, 204, 21)
WALL = (148, 163, 184)

font = pygame.font.SysFont("segoeui", 21)
small = pygame.font.SysFont("segoeui", 17)
title_font = pygame.font.SysFont("segoeui", 31, bold=True)

state = create_default_state()

AGENT_CLASSES = [
    MinimaxAgent,
    AlphaBetaAgent,
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent,
]

AGENT_NAMES = [
    "Minimax",
    "Alpha-Beta",
    "Heuristic Minimax",
    "Heuristic Alpha-Beta",
]

selected_agents = [2, 3]

SEARCH_DEPTH = 2
STEP_DELAY = 850
MAX_ACTIONS = 160

auto_play = False
turn_count = 0
action_history = []
last_action = "None"
last_nodes = 0
last_player = None
last_step_time = 0


buttons = {
    "P0 AI": pygame.Rect(595, 360, 195, 46),
    "P1 AI": pygame.Rect(805, 360, 195, 46),
    "NEXT": pygame.Rect(595, 423, 195, 46),
    "PLAY": pygame.Rect(805, 423, 195, 46),
    "RESET": pygame.Rect(595, 486, 405, 46),
}


def draw_text(text, x, y, color=WHITE, used_font=font):
    img = used_font.render(str(text), True, color)
    screen.blit(img, (x, y))


def cell_rect(row, col):
    return pygame.Rect(
        BOARD_X + col * CELL,
        BOARD_Y + row * CELL,
        CELL - 2,
        CELL - 2,
    )

def draw_board():
    for row in range(state.height):
        for col in range(state.width):
            color = (
                GRID_1 if (row + col) % 2 == 0
                else GRID_2
            )
            pygame.draw.rect(
                screen,
                color,
                cell_rect(row, col),
                border_radius=3,
            )


def draw_walls():
    for wall in state.walls.values():
        rect = cell_rect(wall.row, wall.col)

        pygame.draw.rect(
            screen,
            WALL,
            rect.inflate(-8, -8),
            border_radius=5,
        )

        hp_text = small.render(
            str(wall.hp), True, BG
        )
        screen.blit(
            hp_text,
            hp_text.get_rect(center=rect.center),
        )



def draw_bases():
    for base in state.bases:
        if not base.is_alive():
            continue

        rect = cell_rect(base.row, base.col)
        color = GREEN if base.owner == 0 else RED

        # Ve can cu
        pygame.draw.rect(
            screen,
            color,
            rect.inflate(-12, -12),
            border_radius=5
        )

        # Ve chu B0 hoac B1
        label = font.render(
            f"B{base.owner}", True, BG
        )
        screen.blit(
            label,
            label.get_rect(center=rect.center)
        )

        
        draw_hp_bar(
            rect.x + 7,
            rect.y + CELL - 9,
            base.hp,
            9,
            width=CELL - 14
        )


def draw_hp_bar(x, y, hp, max_hp, width=42):
   
    ratio = max(0, min(hp / max_hp, 1))

    if ratio > 0.6:
        color = GREEN
    elif ratio > 0.3:
        color = YELLOW
    else:
        color = RED

    pygame.draw.rect(
        screen,
        (65, 75, 90),
        (x, y, width, 6),
        border_radius=3
    )

    filled = int(width * ratio)

    if filled > 0:
        pygame.draw.rect(
            screen,
            color,
            (x, y, filled, 6),
            border_radius=3
        )


def draw_tanks():
    for tank in state.tanks:
        if not tank.is_alive():
            continue

        rect = cell_rect(tank.row, tank.col)
        x, y = rect.center
        color = GREEN if tank.owner == 0 else RED

        pygame.draw.circle(
            screen, color, (x, y), 19
        )

        # Ve nong sung theo huong xe
        dx = tank.direction.dcol
        dy = tank.direction.drow

        pygame.draw.line(
            screen,
            WHITE,
            (x, y),
            (x + dx * 25, y + dy * 25),
            6,
        )

        pygame.draw.circle(screen, BG, (x, y), 5)
        draw_hp_bar(x - 21, y + 23, tank.hp, 6)


def draw_bullets():
    for bullet in state.bullets:
        if not state.in_bounds(
            bullet.row, bullet.col
        ):
            continue

        rect = cell_rect(bullet.row, bullet.col)

        pygame.draw.circle(
            screen, YELLOW, rect.center, 7
        )

def draw_info():
    pygame.draw.rect(
        screen,
        PANEL,
        pygame.Rect(570, 95, 450, 510),
        border_radius=16,
    )

    draw_text(
        "CONTROL PANEL",
        595, 110, WHITE, title_font
    )

    draw_text(
        "PLAYER 0",
        595, 165, GREEN, font
    )
    draw_text(
        f"Tank: {state.tanks[0].hp}/6",
        595, 199, WHITE, small
    )
    draw_text(
        f"Base: {state.bases[0].hp}/9",
        595, 227, WHITE, small
    )

    draw_text(
        "PLAYER 1",
        805, 165, RED, font
    )
    draw_text(
        f"Tank: {state.tanks[1].hp}/6",
        805, 199, WHITE, small
    )
    draw_text(
        f"Base: {state.bases[1].hp}/9",
        805, 227, WHITE, small
    )

    draw_text(
        f"Turn: Player {state.current_player}",
        595, 271, WHITE, small
    )

    mode = "RUNNING" if auto_play else "PAUSED"
    draw_text(
        f"AI: {mode}",
        805, 271, GREEN if auto_play else MUTED,
        small,
    )

    draw_text(
        f"Actions: {turn_count}",
        595, 300, WHITE, small
    )
    draw_text(
        f"Nodes: {last_nodes}",
        805, 300, WHITE, small
    )

    draw_text(
        f"Last: {last_action}",
        595, 326, YELLOW, small
    )

    draw_text(
        "Choose AI / Next Step / Play / Reset",
        595, 555, MUTED, small
    )


def draw_buttons():
    for name, rect in buttons.items():
        color = BLUE

        if rect.collidepoint(pygame.mouse.get_pos()):
            color = (90, 155, 250)

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=9,
        )

        if name == "P0 AI":
            label = (
                "P0: " +
                AGENT_NAMES[selected_agents[0]]
            )

        elif name == "P1 AI":
            label = (
                "P1: " +
                AGENT_NAMES[selected_agents[1]]
            )

        elif name == "PLAY":
            label = "PAUSE" if auto_play else "PLAY"

        else:
            label = name

        label_font = small

        text = label_font.render(
            label, True, WHITE
        )

        screen.blit(
            text,
            text.get_rect(center=rect.center),
        )


def draw_result():
    if not state.is_terminal() and turn_count < MAX_ACTIONS:
        return

    winner = state.winner()

    if winner is None:
        message = "DRAW"
    else:
        message = f"PLAYER {winner} WINS!"

    rect = pygame.Rect(105, 290, 375, 95)

    pygame.draw.rect(
        screen, BG, rect, border_radius=15
    )

    text = title_font.render(
        message, True, YELLOW
    )

    screen.blit(
        text,
        text.get_rect(center=rect.center),
    )


def draw_history():
    draw_text(
        "RECENT ACTIONS",
        40, 614, WHITE, small
    )

    recent = action_history[-2:]

    for i, action in enumerate(recent):
        draw_text(
            action,
            40,
            640 + i * 20,
            MUTED,
            small
        )

def draw_game():
    screen.fill(BG)

    draw_text(
        "TANK BATTLE AI",
        40, 30, WHITE, title_font
    )

    draw_board()
    draw_walls()
    draw_bases()
    draw_tanks()
    draw_bullets()

    draw_info()
    draw_buttons()
    draw_history()
    draw_result()

    pygame.display.flip()


def reset_game():
    global state, auto_play, turn_count
    global last_action, last_nodes, last_player

    state = create_default_state()
    auto_play = False
    turn_count = 0
    last_action = "None"
    last_nodes = 0
    last_player = None
    action_history.clear()


def ai_step():
    global state, turn_count
    global last_action, last_nodes, last_player

    if state.is_terminal() or turn_count >= MAX_ACTIONS:
        return

    player = state.current_player
    agent_class = AGENT_CLASSES[
        selected_agents[player]
    ]

    agent = agent_class(depth=SEARCH_DEPTH)

    action = agent.choose_action(state)

    if action is None:
        return

    state = state.apply_action(action)

    last_player = player
    last_action = f"P{player}: {action.name}"
    last_nodes = agent.nodes_expanded
    turn_count += 1
    action_history.append(
        f"Turn {turn_count}: P{player} - {action.name}"
    )

    print(
        f"Turn {turn_count}: "
        f"P{player} | {agent.name} | "
        f"{action.name} | Nodes: {last_nodes}"
    )


def handle_click(pos):
    global auto_play, last_step_time

    if buttons["P0 AI"].collidepoint(pos):
        selected_agents[0] = (
            selected_agents[0] + 1
        ) % len(AGENT_CLASSES)
        auto_play = False

    elif buttons["P1 AI"].collidepoint(pos):
        selected_agents[1] = (
            selected_agents[1] + 1
        ) % len(AGENT_CLASSES)
        auto_play = False

    elif buttons["NEXT"].collidepoint(pos):
        auto_play = False
        ai_step()

    elif buttons["PLAY"].collidepoint(pos):
        if (
            not state.is_terminal()
            and turn_count < MAX_ACTIONS
        ):
            auto_play = not auto_play
            last_step_time = pygame.time.get_ticks()

    elif buttons["RESET"].collidepoint(pos):
        reset_game()


def handle_key(key):
    global auto_play, last_step_time

    if key == pygame.K_r:
        reset_game()

    elif key == pygame.K_q:
        handle_click(buttons["P0 AI"].center)

    elif key == pygame.K_e:
        handle_click(buttons["P1 AI"].center)

    elif key == pygame.K_n:
        handle_click(buttons["NEXT"].center)

    elif key == pygame.K_p:
        handle_click(buttons["PLAY"].center)


running = True

while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                handle_click(event.pos)

        elif event.type == pygame.KEYDOWN:
            handle_key(event.key)

    if auto_play:
        if (
            state.is_terminal()
            or turn_count >= MAX_ACTIONS
        ):
            auto_play = False

        else:
            now = pygame.time.get_ticks()

            if now - last_step_time >= STEP_DELAY:
                ai_step()
                last_step_time = pygame.time.get_ticks()

    draw_game()
    clock.tick(60)

pygame.quit()
