import pygame
import os
import sys
import tkinter as tk
from tkinter import filedialog

# ───────────── Configuration ───────────────────────────────────────
PROJ_DEPTH = 8   # ← set this to 0–32 (how many pixels “back” the block recedes)

pygame.init()

# ──────────────── Helpers ─────────────────────────────────────────
def shear_x(surface: pygame.Surface, dx_per_row: float) -> pygame.Surface:
    """Shear horizontally: row y shifts right by dx_per_row*y pixels."""
    w, h = surface.get_size()
    # total horizontal shift = dx_per_row*(h−1), must be PROJ_DEPTH exactly
    total = int(abs(dx_per_row) * (h - 1))
    out = pygame.Surface((w + total, h), pygame.SRCALPHA)
    for y in range(h):
        row = surface.subsurface(pygame.Rect(0, y, w, 1))
        x_off = int(dx_per_row * y) + (total if dx_per_row < 0 else 0)
        out.blit(row, (x_off, y))
    return out

def shear_y(surface: pygame.Surface, dy_per_col: float) -> pygame.Surface:
    """Shear vertically: column x shifts up by dy_per_col*x pixels."""
    w, h = surface.get_size()
    total = int(abs(dy_per_col) * (w-2))
    out = pygame.Surface((w, h + total), pygame.SRCALPHA)
    for x in range(w):
        col = surface.subsurface(pygame.Rect(x, 0, 1, h))
        y_off = int(dy_per_col * x) + (total if dy_per_col < 0 else 0)
        out.blit(col, (x, y_off))
    return out

def darken(surf: pygame.Surface, amount: int = 100) -> pygame.Surface:
    """Darken by overlaying semi-transparent black."""
    mask = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))
    out = surf.copy()
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    return out

# ───────── Projector ───────────────────────────────────────────────
def make_oblique(tile32: pygame.Surface, depth: int) -> pygame.Surface:
    tw, th = tile32.get_size()
    depth = max(0, min(depth, tw, th))

    # 1) Top face: take top 'depth' rows, shear **left** so back edge shifts `depth` px
    top_slice = tile32.subsurface(pygame.Rect(0, 0, tw, depth))
    dx        = -depth / (depth - 1) if depth > 1 else 0
    top       = shear_x(top_slice, dx_per_row=dx)

    # 2) Right face: unchanged from before
    right_raw = tile32.subsurface(pygame.Rect(tw - depth, 0, depth, th))
    dy        = -depth / (depth - 1) if depth > 1 else 0
    right     = darken(shear_y(right_raw, dy_per_col=dy), amount=100)

    # 3) Composite into (tw+depth)x(th+depth)
    W, H = tw + depth, th + depth
    block = pygame.Surface((W, H), pygame.SRCALPHA)
    block.blit(top,    (-1,    0))       # top face (W×depth)
    block.blit(right,  (tw,   1))       # side face (depth×H)
    block.blit(tile32, (0,    depth))   # front face (tw×th)

    return block


# ────────────── Main GUI ───────────────────────────────────────────
def main():
    # start in script’s directory
    start_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # file picker
    root = tk.Tk(); root.withdraw()
    fname = filedialog.askopenfilename(
        initialdir=start_dir,
        title="Pick a 32×32 PNG tile",
        filetypes=[("PNG files","*.png")]
    )
    if not fname:
        return

    # dummy for convert_alpha()
    pygame.display.set_mode((1,1))
    tile = pygame.image.load(fname).convert_alpha()
    if tile.get_size() != (32, 32):
        print("Error: tile must be 32×32."); return

    # generate & save
    ob = make_oblique(tile, PROJ_DEPTH)
    out = os.path.splitext(fname)[0] + f"_oblique_d{PROJ_DEPTH}.png"
    pygame.image.save(ob, out)
    print("Saved →", out)

    # preview
    screen = pygame.display.set_mode(ob.get_size())
    pygame.display.set_caption(f"Oblique Preview (depth={PROJ_DEPTH})")
    screen.fill((30,30,30))
    screen.blit(ob, (0,0))
    pygame.display.flip()

    # wait until closed
    run = True
    while run:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False

if __name__ == "__main__":
    main()
