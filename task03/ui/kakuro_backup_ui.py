
import os
import sys
import pygame

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(__file__))
)

from kakuro_model import KakuroModel
from solver.backtracking import solve

pygame.init()

WIDTH, HEIGHT = 850, 620
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kakuro AI Solver")

WHITE = (255, 255, 255)
BLACK = (45, 55, 72)
BLUE = (59, 130, 246)
GREEN = (187, 247, 208)
BG = (235, 240, 245)
TEXT = (30, 41, 59)

CELL_SIZE = 90
START_X = 50
START_Y = 90

font = pygame.font.SysFont("arial", 23)
small_font = pygame.font.SysFont("arial", 18)
title_font = pygame.font.SysFont("arial", 30)

grid = [
    ["#", {"down": 4}, {"down": 6}],
    [{"right": 3}, ".", "."],
    [{"right": 7}, ".", "."]
]

model = KakuroModel(grid)

solution = None
trace = []
current_step = -1
selected_cell = (1, 1)

solve_button = pygame.Rect(420, 120, 160, 45)
next_button = pygame.Rect(590, 120, 160, 45)
prev_button = pygame.Rect(420, 180, 160, 45)


def get_current_domains():
    if current_step < 0 or not trace:
        return {
            var: sorted(values)
            for var, values in model.domains.items()
        }

    return trace[current_step]["domains"]


def draw_button(rect, label):
    pygame.draw.rect(screen, BLUE, rect, border_radius=8)
    text = font.render(label, True, WHITE)

    screen.blit(
        text,
        text.get_rect(center=rect.center)
    )


def draw_board():
    domains = get_current_domains()

    active_cell = None

    if current_step >= 0:
        active_cell = trace[current_step].get("cell")

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            cell = grid[row][col]

            x = START_X + col * CELL_SIZE
            y = START_Y + row * CELL_SIZE

            rect = pygame.Rect(
                x, y, CELL_SIZE, CELL_SIZE
            )

            color = WHITE if cell == "." else BLACK

            if (row, col) == active_cell:
                color = GREEN

            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLUE, rect, 2)

            if isinstance(cell, dict):
                if "right" in cell:
                    label = f"R:{cell['right']}"
                elif "down" in cell:
                    label = f"D:{cell['down']}"
                else:
                    label = ""

                text = small_font.render(label, True, WHITE)
                screen.blit(text, (x + 8, y + 30))

            elif cell == ".":
                values = domains.get((row, col), [])

                if len(values) == 1:
                    # Domain chỉ còn 1 số
                    text = font.render(
                        str(values[0]), True, TEXT
                    )
                    screen.blit(
                        text,
                        text.get_rect(center=rect.center)
                    )

                elif len(values) > 1:
                    mini_font = pygame.font.SysFont("arial", 15)

                    for value in values:
                
                        index = value - 1

                        mini_row = index // 3
                        mini_col = index % 3

                        text = mini_font.render(
                            str(value), True, (100, 116, 139)
                        )

                        text_x = x + 18 + mini_col * 27
                        text_y = y + 10 + mini_row * 25

                        screen.blit(text, (text_x, text_y))


def draw_info():
    title = title_font.render(
        "KAKURO AI SOLVER", True, TEXT
    )
    screen.blit(title, (50, 30))

    draw_button(solve_button, "Solve")
    draw_button(next_button, "Next")
    draw_button(prev_button, "Previous")

    step_text = f"Step: {current_step + 1}/{len(trace)}"

    screen.blit(
        font.render(step_text, True, TEXT),
        (420, 260)
    )

    if current_step >= 0:
        event = trace[current_step]

        screen.blit(
            font.render(
                f"Event: {event['type']}",
                True, TEXT
            ),
            (420, 300)
        )

    domains = get_current_domains()
    values = domains.get(selected_cell, [])

    screen.blit(
        small_font.render(
            f"Selected: {selected_cell}",
            True, TEXT
        ),
        (420, 370)
    )

    screen.blit(
        small_font.render(
            f"Domain: {values}",
            True, TEXT
        ),
        (420, 405)
    )


running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if solve_button.collidepoint(pos):
                solution, trace = solve(
                    model, return_trace=True
                )
                current_step = -1

            elif next_button.collidepoint(pos):
                if current_step < len(trace) - 1:
                    current_step += 1

            elif prev_button.collidepoint(pos):
                if current_step >= 0:
                    current_step -= 1

            else:
                for row in range(len(grid)):
                    for col in range(len(grid[row])):
                        if grid[row][col] != ".":
                            continue

                        rect = pygame.Rect(
                            START_X + col * CELL_SIZE,
                            START_Y + row * CELL_SIZE,
                            CELL_SIZE,
                            CELL_SIZE
                        )

                        if rect.collidepoint(pos):
                            selected_cell = (row, col)

    screen.fill(BG)
    draw_board()
    draw_info()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
