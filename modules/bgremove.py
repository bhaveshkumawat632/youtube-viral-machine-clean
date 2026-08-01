"""
Remove white/light background from character PNGs using PIL flood-fill from
edges, producing transparent PNGs. Only used by VidRush animated pipeline.
"""
import os
from PIL import Image


def remove_white_bg(src, dst, thresh=240):
    """Flood-fill from the border; anything near-white becomes transparent."""
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = im.load()

    def near_white(p):
        r, g, b = p[0], p[1], p[2]
        return r >= thresh and g >= thresh and b >= thresh

    # flood fill from edges
    from collections import deque
    mask = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not mask[y][x] and near_white(px[x, y]):
                mask[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not mask[y][x] and near_white(px[x, y]):
                mask[y][x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not mask[ny][nx] and near_white(px[nx, ny]):
                mask[ny][nx] = True
                q.append((nx, ny))
    # also kill any remaining near-white pixels (interior specks)
    for y in range(h):
        for x in range(w):
            if near_white(px[x, y]):
                mask[y][x] = True
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                px[x, y] = (0, 0, 0, 0)
    im.save(dst)


def process_dir(char_dir):
    out_dir = os.path.join(char_dir, "transparent")
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(char_dir):
        if f.lower().endswith(".png") and "transparent" not in f:
            src = os.path.join(char_dir, f)
            dst = os.path.join(out_dir, f)
            if not os.path.exists(dst):
                remove_white_bg(src, dst)
                print("transparent:", f)
    return out_dir


if __name__ == "__main__":
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "character")
    print("output:", process_dir(d))
