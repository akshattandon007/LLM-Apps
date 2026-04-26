"""Generate Proppy PNG icons with a cute house-character face."""
import struct, zlib, os

def make_png(size, path):
    W = H = size
    s = size

    def px(r, g, b, a=255):
        return [r, g, b, a]

    pixels = [[px(0,0,0,0)] * W for _ in range(H)]

    def circle_fill(cx, cy, r, color):
        for y in range(H):
            for x in range(W):
                if (x-cx)**2 + (y-cy)**2 <= r**2:
                    pixels[y][x] = list(color)

    def rect_fill(x1, y1, x2, y2, color):
        for y in range(max(0,y1), min(H,y2)):
            for x in range(max(0,x1), min(W,x2)):
                pixels[y][x] = list(color)

    def triangle_fill(tip_x, tip_y, base_y, half_w, color):
        for y in range(min(tip_y, base_y), max(tip_y, base_y)+1):
            t = (y - tip_y) / (base_y - tip_y + 0.001)
            w = int(t * half_w)
            for x in range(tip_x - w, tip_x + w + 1):
                if 0 <= x < W and 0 <= y < H:
                    pixels[y][x] = list(color)

    cx, cy = W//2, H//2

    # ── Palette ──────────────────────────
    CREAM    = (255, 248, 235, 255)   # warm cream body
    PEACH    = (255, 220, 170, 255)   # face/ears
    BROWN    = (160,  90,  40, 255)   # dark brown
    TERRAC   = (200, 120,  60, 255)   # terracotta accent
    WHITE    = (255, 255, 255, 255)
    OFFWHITE = (255, 245, 225, 255)
    PINK     = (255, 180, 180, 255)   # inner ear
    DARK     = ( 50,  30,  15, 255)   # outlines
    ROOF_COL = (190,  90,  50, 255)   # roof
    BLUSH    = (255, 190, 170, 255)

    # ── BODY — round house shape ──────────
    body_r = int(s * 0.38)
    body_cy = int(cy + s*0.08)
    circle_fill(cx, body_cy, body_r, CREAM)

    # ── ROOF / HAT (triangle) ─────────────
    roof_tip_y  = int(s * 0.06)
    roof_base_y = int(s * 0.40)
    roof_half   = int(s * 0.36)
    triangle_fill(cx, roof_tip_y, roof_base_y, roof_half, ROOF_COL)

    # Chimney
    chim_w = int(s*0.07); chim_h = int(s*0.12)
    chim_x = cx + int(s*0.14)
    chim_y = int(s*0.04)
    rect_fill(chim_x, chim_y, chim_x+chim_w, chim_y+chim_h, BROWN)

    # ── EARS (round) ─────────────────────
    ear_r  = int(s*0.10)
    ear_y  = int(cy - s*0.05)
    ear_lx = int(cx - s*0.32)
    ear_rx = int(cx + s*0.32)
    circle_fill(ear_lx, ear_y, ear_r, PEACH)
    circle_fill(ear_rx, ear_y, ear_r, PEACH)
    # inner ear
    ie_r = int(ear_r * 0.55)
    circle_fill(ear_lx, ear_y, ie_r, PINK)
    circle_fill(ear_rx, ear_y, ie_r, PINK)

    # ── FACE CIRCLE ───────────────────────
    face_r  = int(s * 0.28)
    face_cy = int(cy + s*0.10)
    circle_fill(cx, face_cy, face_r, PEACH)

    # ── EYES ──────────────────────────────
    eye_y  = int(face_cy - s*0.06)
    eye_ox = int(s*0.09)
    eye_r  = int(s*0.055)
    circle_fill(cx-eye_ox, eye_y, eye_r, WHITE)
    circle_fill(cx+eye_ox, eye_y, eye_r, WHITE)
    # pupils
    pu_r = int(eye_r*0.58)
    circle_fill(cx-eye_ox+1, eye_y+1, pu_r, DARK)
    circle_fill(cx+eye_ox+1, eye_y+1, pu_r, DARK)
    # eye shine
    sh_r = max(1, int(pu_r*0.38))
    circle_fill(cx-eye_ox-1, eye_y-1, sh_r, WHITE)
    circle_fill(cx+eye_ox-1, eye_y-1, sh_r, WHITE)

    # ── NOSE ──────────────────────────────
    nose_y = int(face_cy + s*0.04)
    nose_r = int(s*0.04)
    circle_fill(cx, nose_y, nose_r, BROWN)

    # ── SMILE ─────────────────────────────
    smile_y = int(face_cy + s*0.10)
    smile_w = int(s*0.14)
    # draw arc by filling bottom of an ellipse
    for dx in range(-smile_w, smile_w+1):
        arc_y = smile_y + int((dx/smile_w)**2 * s * 0.05)
        for t in range(2):
            yy = arc_y + t
            if 0 <= cx+dx < W and 0 <= yy < H:
                pixels[yy][cx+dx] = list(BROWN)

    # ── BLUSH circles ─────────────────────
    blush_y = int(face_cy + s*0.02)
    blush_r = int(s*0.065)
    blush_ox = int(s*0.175)
    circle_fill(cx-blush_ox, blush_y, blush_r, BLUSH)
    circle_fill(cx+blush_ox, blush_y, blush_r, BLUSH)
    # make blush semi-transparent by blending with face
    for y in range(H):
        for x in range(W):
            p = pixels[y][x]
            if p == list(BLUSH):
                # blend: 60% blush, 40% face colour
                pixels[y][x] = [
                    int(255*0.6 + PEACH[0]*0.4),
                    int(180*0.6 + PEACH[1]*0.4),
                    int(180*0.6 + PEACH[2]*0.4),
                    255
                ]

    # ── DOOR (tiny, bottom of body) ───────
    door_w = int(s*0.10); door_h = int(s*0.12)
    door_x = cx - door_w//2
    door_y = int(body_cy + body_r - door_h - 2)
    rect_fill(door_x, door_y, door_x+door_w, door_y+door_h, BROWN)
    # door knob
    kx = door_x + door_w - 3; ky = door_y + door_h//2
    if 0<=kx<W and 0<=ky<H:
        pixels[ky][kx] = list(TERRAC)

    # ── BUILD PNG ────────────────────────
    raw = b''
    for row in pixels:
        raw += b'\x00' + bytes([v for p in row for v in p])
    compressed = zlib.compress(raw, 9)

    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(name+data) & 0xFFFFFFFF)

    png  = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', compressed)
    png += chunk(b'IEND', b'')

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)
    print(f"  {path} ({size}x{size})")

base = '/home/claude/proppy-extension/icons'
for sz in [16, 48, 128]:
    make_png(sz, f'{base}/icon{sz}.png')
print("Icons done!")
