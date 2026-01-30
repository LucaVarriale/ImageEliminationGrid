import pygame
import os
import random
from PIL import Image

# =====================
# CONFIG
# =====================
IMAGE_FOLDER = "C:/Users/lucav/Documents/TradingCardFree/images"
SUPPORTED = (".png", ".jpg", ".jpeg", ".webp")

START_WIDTH = 1200
START_HEIGHT = 800

GRID_COLS = 4
GRID_ROWS = 4
GRID_COUNT = GRID_COLS * GRID_ROWS  # 16

FADE_ALPHA = int(255 * 0.1)   # 10% opacity for losers
FADE_SPEED = 12

MOVE_SPEED = 0.12
SCALE_SPEED = 0.08
FINAL_SCALE = 4.0

BG_COLOR = (0, 0, 0)

PADDING = 8        # spacing BETWEEN cells (same x/y)
EDGE_PADDING = 24  # spacing between grid and window border (same x/y)

# =====================
# INIT
# =====================
pygame.init()
screen = pygame.display.set_mode(
    (START_WIDTH, START_HEIGHT),
    pygame.RESIZABLE
)
pygame.display.set_caption("Last Image Standing")
clock = pygame.time.Clock()

# =====================
# LOAD IMAGES
# =====================
def load_images():
    imgs = []
    for f in os.listdir(IMAGE_FOLDER):
        if f.lower().endswith(SUPPORTED):
            img = Image.open(os.path.join(IMAGE_FOLDER, f)).convert("RGBA")
            imgs.append(img)
    return imgs

def pil_to_surface(img):
    return pygame.image.fromstring(
        img.tobytes(), img.size, img.mode
    ).convert_alpha()

all_images = load_images()

# =====================
# ITEM
# =====================
class Item:
    def __init__(self, pil_img):
        self.pil = pil_img
        self.surface = pil_to_surface(pil_img)

        self.x = self.y = 0
        self.tx = self.ty = 0

        self.w = 100
        self.h = 100

        self.scale = 1.0
        self.target_scale = 1.0

        self.alpha = 255
        self.eliminated = False

    def update(self):
        self.x += (self.tx - self.x) * MOVE_SPEED
        self.y += (self.ty - self.y) * MOVE_SPEED
        self.scale += (self.target_scale - self.scale) * SCALE_SPEED

        if self.eliminated and self.alpha > FADE_ALPHA:
            self.alpha = max(FADE_ALPHA, self.alpha - FADE_SPEED)

    def draw(self):
        base_w, base_h = scale_contain(self.pil, self.w, self.h)
        w = int(base_w * self.scale)
        h = int(base_h * self.scale)

        surf = pygame.transform.smoothscale(self.surface, (w, h))
        surf.set_alpha(self.alpha)
        screen.blit(surf, surf.get_rect(center=(self.x, self.y)))

def scale_contain(img, max_w, max_h):
    iw, ih = img.size
    r = iw / ih

    if max_w / max_h > r:
        h = max_h
        w = int(h * r)
    else:
        w = max_w
        h = int(w / r)

    return w, h

# =====================
# STATE
# =====================
items = []
active = []
running = False
finished = False
show_only_winner = False
winner = None

# =====================
# LAYOUT (RECTANGULAR + OUTER PADDING)
# =====================
def layout_grid():
    w, h = screen.get_size()

    usable_w = w - EDGE_PADDING * 2
    usable_h = h - EDGE_PADDING * 2

    cell_w = (usable_w - PADDING * (GRID_COLS - 1)) / GRID_COLS
    cell_h = (usable_h - PADDING * (GRID_ROWS - 1)) / GRID_ROWS

    grid_w = cell_w * GRID_COLS + PADDING * (GRID_COLS - 1)
    grid_h = cell_h * GRID_ROWS + PADDING * (GRID_ROWS - 1)

    start_x = EDGE_PADDING + (usable_w - grid_w) / 2
    start_y = EDGE_PADDING + (usable_h - grid_h) / 2

    for i, item in enumerate(items):
        col = i % GRID_COLS
        row = i // GRID_COLS

        item.w = int(cell_w)
        item.h = int(cell_h)

        item.tx = start_x + col * (cell_w + PADDING) + cell_w / 2
        item.ty = start_y + row * (cell_h + PADDING) + cell_h / 2

# =====================
# RESET
# =====================
def reset():
    global items, active, running, finished, show_only_winner, winner

    chosen = random.sample(all_images, min(GRID_COUNT, len(all_images)))
    random.shuffle(chosen)

    items = [Item(img) for img in chosen]
    active = items.copy()

    running = False
    finished = False
    show_only_winner = False
    winner = None

    layout_grid()

# =====================
# ELIMINATION
# =====================
def eliminate_one():
    global finished, show_only_winner, winner

    if len(active) <= 1:
        finished = True
        show_only_winner = True
        winner = active[0]

        winner.eliminated = False
        winner.alpha = 255

        w, h = screen.get_size()
        winner.tx = w / 2
        winner.ty = h / 2
        winner.target_scale = FINAL_SCALE
        return

    victim = random.choice(active)
    active.remove(victim)
    victim.eliminated = True

# =====================
# MAIN LOOP
# =====================
reset()

timer = 0
ELIMINATION_DELAY = 200  # ms

while True:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            if not show_only_winner:
                layout_grid()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            quit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if finished:
                    reset()
                elif not running:
                    running = True
            elif event.button == 3:
                pygame.quit()
                quit()

    if running and not finished:
        timer += dt
        if timer >= ELIMINATION_DELAY:
            timer = 0
            eliminate_one()

    screen.fill(BG_COLOR)

    if show_only_winner and winner is not None:
        winner.update()
        winner.draw()
    else:
        for item in items:
            item.update()
            item.draw()

    pygame.display.flip()
