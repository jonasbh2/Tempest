import random
from itertools import accumulate

def dump_level(rows, indent=4, var_name="level"):

    pad = " " * indent
    print(f"{var_name} = [")
    for r in rows:
        print(f'{pad}"{r}",')
    print("]")



# ────────────────────────────────────────────────────────────────────
def make_island(width=160, height=60, shoreline=5, soil=3, rock_cap=20, air_rows=10,
                slope_prob=0.7, max_step=2, seed=42,
                stone_depth=6, edge_stone_depth=15, edge_width=30):

    assert air_rows + shoreline + 1 < height
    assert width > 2 * edge_width

    rng = random.Random(seed)

    sea_level = height - shoreline
    min_ground = sea_level
    max_ground = max(air_rows + 1, sea_level - rock_cap)

    # Create terrain height profile
    ground = [sea_level]
    for _ in range(1, width):
        y = ground[-1]
        if rng.random() < slope_prob:
            y += rng.randint(-max_step, max_step)
        ground.append(max(max_ground, min(y, min_ground)))

    # Create initial terrain
    terrain = [[" "] * width for _ in range(height)]
    for x, g_y in enumerate(ground):
        valley = g_y >= sea_level - 1
        terrain[g_y][x] = "S" if valley else "P"
        if valley:
            for y in range(g_y + 1, sea_level):
                terrain[y][x] = "S"
            for y in range(sea_level, height):
                terrain[y][x] = "M" if rng.random() < 0.05 else "R"
        else:
            for y in range(g_y + 1, min(g_y + 1 + soil, height)):
                terrain[y][x] = "D"
            for y in range(g_y + 1 + soil, height):
                terrain[y][x] = "M" if rng.random() < 0.05 else "R"

    # Add player spawn
    mid = width // 2
    for y in range(height):
        if terrain[y][mid] != " ":
            terrain[y - 1][mid] = "X"
            break

    # Split terrain
    left = [row[:edge_width] for row in terrain]
    center = [row[edge_width:width - edge_width] for row in terrain]
    right = [row[width - edge_width:] for row in terrain]

    # Create buffers
    def make_buffer(w, h):
        return [[
            "M" if rng.random() < 0.05 else "R"
            for _ in range(w)
        ] for _ in range(h)]

    edge_stone_buffer = make_buffer(edge_width, edge_stone_depth)

    # Add buffers to bottoms
    left_full = left + edge_stone_buffer
    center_full = center
    right_full =  right + edge_stone_buffer

    full_height = max(len(left_full), len(center_full), len(right_full))

    def pad_top(section, target_height):
        pad_rows = [[" "] * len(section[0]) for _ in range(target_height - len(section))]
        return pad_rows + section

    left_full = pad_top(left_full, full_height)
    center_full = pad_top(center_full, full_height)
    right_full = pad_top(right_full, full_height)

    # Recombine from bottom to top
    stitched = ["".join(l + c + r) for l, c, r in zip(left_full, center_full, right_full)]

    # Add a final stone buffer at the bottom
    final_stone_layer = [
        "".join("M" if rng.random() < 0.05 else "R" for _ in range(width))
        for _ in range(stone_depth)
    ]

    # Stack the original stitched level on top of the final stone layer
    stitched = stitched + final_stone_layer


    return stitched




# ------------ example -------------
rows = make_island(width=700, height=50, stone_depth=30, seed=99999)
dump_level(rows)
