
import os
import sys
import pygame

sys.path.insert(
    0, os.path.dirname(os.path.dirname(__file__))
)

from kakuro_model import KakuroModel
from solver.backtracking import solve

pygame.init()


WIDTH, HEIGHT = 1080, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kakuro AI Solver")
clock = pygame.time.Clock()


BG = (255, 255, 255)

NAVY = (210, 210, 210)
NAVY_ALT = (190, 190, 190)

WHITE = (255, 255, 255)
TEXT = (25, 25, 25)
MUTED = (90, 90, 90)

BORDER = (25, 25, 25)
BLUE = (60, 110, 180)

GREEN = (210, 235, 210)
YELLOW = (255, 245, 190)
RED = (245, 205, 205)

PANEL = (255, 255, 255)

font = pygame.font.SysFont("segoeui", 24)
small_font = pygame.font.SysFont("segoeui", 17)
tiny_font = pygame.font.SysFont("segoeui", 13)
number_font = pygame.font.SysFont("segoeui", 30, bold=True)
title_font = pygame.font.SysFont("segoeui", 34, bold=True)

BOARD_X = 65
BOARD_Y = 145
BOARD_MAX_SIZE = 540

grid = [
    ["#", "#", {"down": 44}, {"down": 16},  {"down": 9}, "#",{"down": 15},{"down": 44},"#"],
    ["#",{"right": 22},".", ".", ".",{"right": 3, "down": 11},".", ".",{"down": 14}],
    ["#",{"right": 28, "down": 17},".", ".", ".", ".", ".", ".", "."],
    [{"right": 14},".", ".", "#",{"right": 20, "down": 12},".", ".", ".", "."],
    [{"right": 17},".", ".",{"right": 22, "down": 29},".", ".", ".", ".",{"down": 7}],
    ["#",{"right": 28, "down": 12},".", ".", ".", ".",{"right": 12},".", "."],
    [{"right": 14},".", ".", ".", ".",{"down": 7},{"right": 6, "down": 12},".", "."],
    [{"right": 39},".", ".", ".", ".", ".", ".", ".","#"],
    ["#",{"right": 16},".", ".",{"right": 8},".", ".", ".","#"]
]

model = KakuroModel(grid)

rows = len(grid)
cols = max(len(row) for row in grid)

CELL_SIZE = min(
    90,
    BOARD_MAX_SIZE // max(rows, cols)
)

BOARD_WIDTH = cols * CELL_SIZE
BOARD_HEIGHT = rows * CELL_SIZE

solution = None
trace = []
current_step = -1
selected_cell = (1, 1)
status = "Ready to solve"


buttons = {
    "Solve": pygame.Rect(680, 175, 150, 48),
    "Reset": pygame.Rect(845, 175, 150, 48),
    "Previous": pygame.Rect(680, 235, 150, 48),
    "Next": pygame.Rect(845, 235, 150, 48)
}


def draw_text(text, x, y, color=TEXT, used_font=None):
    used_font = used_font or font
    img = used_font.render(str(text), True, color)
    screen.blit(img, (x, y))


def draw_clue(rect, clue):
    x, y = rect.x, rect.y
    s = rect.width

    pygame.draw.line(screen, (25, 25, 25),(x, y),(x + s, y + s),2)

    clue_font = pygame.font.SysFont(
        "segoeui",
        max(12, int(s * 0.25)),
        bold=True
    )

    if "right" in clue:
        label = clue_font.render(
            str(clue["right"]), True, TEXT
        )
        target = (
            x + int(s * 0.74),
            y + int(s * 0.25)
        )
        screen.blit(
            label,
            label.get_rect(center=target)
        )

    if "down" in clue:
        label = clue_font.render(
            str(clue["down"]), True, TEXT
        )
        target = (
            x + int(s * 0.26),
            y + int(s * 0.75)
        )
        screen.blit(
            label,
            label.get_rect(center=target)
        )


def get_event():
    if 0 <= current_step < len(trace):
        return trace[current_step]
    return None


def get_domains():
    if current_step < 0 or not trace:
        return {
            var: sorted(values)
            for var, values in model.domains.items()
        }

    return trace[current_step]["domains"]

def draw_board():
    domains = get_domains()
    active_event = get_event()

    active_cell = None
    if active_event:
        active_cell = active_event.get("cell")

    # Nen khung ban choi
    shadow_rect = pygame.Rect(
        BOARD_X - 8,
        BOARD_Y - 4,
        BOARD_WIDTH + 16,
        BOARD_HEIGHT + 16
    )

    pygame.draw.rect(
        screen,
        (203, 214, 227),
        shadow_rect.move(0, 5),
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        NAVY,
        shadow_rect,
        border_radius=12
    )

    for row in range(rows):
        for col in range(len(grid[row])):
            cell = grid[row][col]

            x = BOARD_X + col * CELL_SIZE
            y = BOARD_Y + row * CELL_SIZE

            rect = pygame.Rect(
                x, y, CELL_SIZE, CELL_SIZE
            )
            color = WHITE if cell == "." else NAVY

            # Highlight theo su kien AI
            if cell == "." and (row, col) == active_cell:
                event_type = active_event["type"]

                color = {
                    "propagation": GREEN,
                    "try": YELLOW,
                    "backtrack": RED
                }.get(event_type, WHITE)

            pygame.draw.rect(screen, color, rect)

            pygame.draw.rect(
                screen, BORDER, rect, 2
            )

            if isinstance(cell, dict):
                draw_clue(rect, cell)

            elif cell == "#":
                draw_clue(rect, {})

            elif cell == ".":
                values = domains.get((row, col), [])

                if len(values) == 1:
                    label = number_font.render(
                        str(values[0]), True, TEXT
                    )
                    screen.blit(
                        label,
                        label.get_rect(center=rect.center)
                    )

              
                elif len(values) > 1:
                    mini_size = max(
                        10, int(CELL_SIZE * 0.17)
                    )

                    mini_font = pygame.font.SysFont(
                        "segoeui", mini_size
                    )

                    for value in values:
                        mini_row = (value - 1) // 3
                        mini_col = (value - 1) % 3

                        center_x = (
                            x + (mini_col + 0.5)
                            * CELL_SIZE / 3
                        )

                        center_y = (
                            y + (mini_row + 0.5)
                            * CELL_SIZE / 3
                        )

                        label = mini_font.render(
                            str(value), True, MUTED
                        )

                        screen.blit(
                            label,
                            label.get_rect(
                                center=(center_x, center_y)
                            )
                        )

            # Vien o dang duoc chon
            if cell == "." and (row, col) == selected_cell:
                pygame.draw.rect(
                    screen, BLUE, rect, 3
                )


def draw_button(name, rect):
    mouse_pos = pygame.mouse.get_pos()

    color = BLUE
    if rect.collidepoint(mouse_pos):
        color = (39, 102, 205)

    pygame.draw.rect(
        screen, color, rect, border_radius=9
    )

    text = small_font.render(
        name, True, WHITE
    )

    screen.blit(
        text,
        text.get_rect(center=rect.center)
    )


def draw_sidebar():
    panel = pygame.Rect(650, 140, 380, 500)

    pygame.draw.rect(
        screen, PANEL, panel, border_radius=16
    )

    

    for name, rect in buttons.items():
        draw_button(name, rect)

    total = len(trace)
    progress = current_step + 1 if total else 0

    draw_text(
        f"Step: {progress} / {total}",
        680, 325, TEXT, font
    )

    # Thanh tien do
    pygame.draw.rect(
        screen, (222, 230, 239),
        (680, 365, 315, 12),
        border_radius=6
    )

    if total > 0 and progress > 0:
        filled = int(315 * progress / total)

        pygame.draw.rect(
            screen, BLUE,
            (680, 365, filled, 12),
            border_radius=6
        )

    event = get_event()

    if event:
        event_type = event["type"]

        color = {
            "propagation": (29, 150, 91),
            "try": (175, 125, 0),
            "backtrack": (210, 65, 65),
            "solution": (29, 150, 91)
        }.get(event_type, TEXT)

        draw_text(
            f"Event: {event_type.upper()}",
            680, 405, color, small_font
        )

        if "cell" in event:
            draw_text(
                f"Cell: {event['cell']}",
                680, 440, MUTED, small_font
            )

        if event_type == "propagation":
            draw_text(
                f"Removed: {event['removed']}",
                680, 470, MUTED, small_font
            )
    else:
        draw_text(
            status, 680, 410, MUTED, small_font
        )


    draw_text(
        f"Selected cell: {selected_cell}",
        680, 525, TEXT, small_font
    )

    values = get_domains().get(selected_cell, [])

    draw_text(
        "Domain:",
        680, 560, MUTED, small_font
    )

    draw_text(
        str(values),
        680, 587, (29, 150, 91), small_font
    )



def handle_click(pos):
    global solution, trace
    global current_step, selected_cell, status

    if buttons["Solve"].collidepoint(pos):
        solution, trace = solve(
            model, return_trace=True
        )
        current_step = -1

        status = (
            "Solution found"
            if solution is not None
            else "No solution"
        )

    elif buttons["Reset"].collidepoint(pos):
        solution = None
        trace = []
        current_step = -1
        status = "Ready to solve"

    elif buttons["Next"].collidepoint(pos):
        if current_step < len(trace) - 1:
            current_step += 1

    elif buttons["Previous"].collidepoint(pos):
        if current_step >= 0:
            current_step -= 1

    else:
        for row in range(rows):
            for col in range(len(grid[row])):
                if grid[row][col] != ".":
                    continue

                rect = pygame.Rect(
                    BOARD_X + col * CELL_SIZE,
                    BOARD_Y + row * CELL_SIZE,
                    CELL_SIZE, CELL_SIZE
                )

                if rect.collidepoint(pos):
                    selected_cell = (row, col)

running = True

while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                handle_click(event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                if current_step < len(trace) - 1:
                    current_step += 1

            elif event.key == pygame.K_LEFT:
                if current_step >= 0:
                    current_step -= 1

    screen.fill(BG)

    draw_text(
        "KAKURO AI SOLVER",
        65, 35, TEXT, title_font
    )

    draw_text(
        "Constraint Satisfaction Problem Visualizer",
        67, 87, MUTED, small_font
    )

    draw_board()
    draw_sidebar()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
