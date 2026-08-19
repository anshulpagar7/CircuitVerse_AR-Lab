# domains/coa.py
"""
Computer Organization & Architecture scenes — digital logic and computer
architecture experiments drawn as live animated vector diagrams.

Adders:      RippleCarryScene, CarryLookAheadScene, WallaceTreeScene
Sequential:  FlipFlopScene, RegisterCounterScene
Multipliers: CombMultiplierScene, BoothScene
ALU:         ALUScene
Memory:      MemoryDesignScene, AssociativeCacheScene, DirectMappedScene
CPU:         CPUScene
Minimization:KarnaughScene, QuineMcCluskeyScene
"""

import math
import time
import cv2
import numpy as np

from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, FONT_S)
from . import Scene

# digital palette
HI   = (120, 255, 170)      # logic 1 (green)
LO   = (110, 110, 130)      # logic 0 (grey)
BUS  = (255, 190, 90)       # data bus (amber)
CTRL = (200, 130, 255)      # control (purple)
WIREC = (150, 170, 200)


# ─────────────────────── shared digital toolkit ───────────────────────
def sidebar(frame, W, rows, title, border=ACCENT, y0=92):
    x0 = W - 264
    h = 58 + 30 * len(rows)
    glass_panel(frame, x0, y0, 248, h, radius=16, border=border)
    text(frame, title, x0 + 16, y0 + 28, 0.5, border, 1, FONT_S)
    cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
    for i, (k, v, col) in enumerate(rows):
        yy = y0 + 64 + i * 30
        text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
        vw, _ = text_size(v, 0.48, 1, FONT_S)
        text(frame, v, x0 + 232 - vw, yy, 0.48, col, 1, FONT_S)


def bit_wire(frame, p1, p2, val, t=0.0, flow=True):
    """Signal wire coloured by logic level, with travelling pulse when high."""
    col = HI if val else LO
    if val:
        ov = frame.copy()
        cv2.line(ov, p1, p2, col, 7, cv2.LINE_AA)
        cv2.addWeighted(ov, 0.20, frame, 0.80, 0, frame)
    cv2.line(frame, p1, p2, (35, 45, 40) if val else (40, 40, 50), 4, cv2.LINE_AA)
    cv2.line(frame, p1, p2, col, 2, cv2.LINE_AA)
    if val and flow:
        length = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
        if length > 20:
            u = (t * 0.8) % 1.0
            x = int(p1[0]+(p2[0]-p1[0])*u); y = int(p1[1]+(p2[1]-p1[1])*u)
            cv2.circle(frame, (x, y), 3, (200, 255, 220), -1, cv2.LINE_AA)


def bit_box(frame, x, y, val, label="", w=34, h=34, col=None):
    """A single bit cell showing 0/1, glowing if 1."""
    c = col or (HI if val else (60, 62, 78))
    if val:
        glow = frame.copy()
        cv2.rectangle(glow, (x-2, y-2), (x+w+2, y+h+2), HI, -1)
        cv2.addWeighted(glow, 0.18, frame, 0.82, 0, frame)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (26, 30, 40), -1, cv2.LINE_AA)
    cv2.rectangle(frame, (x, y), (x+w, y+h), c, 2, cv2.LINE_AA)
    s = str(val)
    tw, _ = text_size(s, 0.6, 1, FONT_S)
    text(frame, s, x+(w-tw)//2, y+h-9, 0.6, HI if val else MUTED, 1, FONT_S)
    if label:
        lw, _ = text_size(label, 0.34, 1, FONT_S)
        text(frame, label, x+(w-lw)//2, y-6, 0.34, MUTED, 1, FONT_S, shadow=False)


def bit_row(frame, x, y, bits, labels=None, cell=34, gap=6, prefix=""):
    """Draw a row of bits MSB..LSB left to right. Returns total width."""
    if prefix:
        text(frame, prefix, x-text_size(prefix,0.46,1,FONT_S)[0]-10, y+cell-9,
             0.46, TEXT, 1, FONT_S)
    for i, b in enumerate(bits):
        lbl = labels[i] if labels else ""
        bit_box(frame, x+i*(cell+gap), y, b, lbl, cell, cell)
    return len(bits)*(cell+gap)


def gate(frame, cx, cy, kind, active=False, scale=1.0):
    """Draw a logic gate symbol. kind in AND/OR/XOR/NOT/NAND/NOR."""
    col = HI if active else WIREC
    s = int(30*scale)
    if kind in ("AND", "NAND"):
        cv2.line(frame, (cx-s, cy-s), (cx, cy-s), col, 2, cv2.LINE_AA)
        cv2.line(frame, (cx-s, cy+s), (cx, cy+s), col, 2, cv2.LINE_AA)
        cv2.line(frame, (cx-s, cy-s), (cx-s, cy+s), col, 2, cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy), (s, s), 0, -90, 90, col, 2, cv2.LINE_AA)
        if kind == "NAND":
            cv2.circle(frame, (cx+s+6, cy), 5, col, 2, cv2.LINE_AA)
    elif kind in ("OR", "NOR", "XOR"):
        if kind == "XOR":
            cv2.ellipse(frame, (cx-s-8, cy), (10, s), 0, -90, 90, col, 2, cv2.LINE_AA)
        cv2.ellipse(frame, (cx-s, cy), (10, s), 0, -90, 90, col, 2, cv2.LINE_AA)
        # body curves
        pts_top = [(cx-s, cy-s), (cx, cy-s+4), (cx+s, cy)]
        pts_bot = [(cx-s, cy+s), (cx, cy+s-4), (cx+s, cy)]
        cv2.polylines(frame, [np.array(pts_top, np.int32)], False, col, 2, cv2.LINE_AA)
        cv2.polylines(frame, [np.array(pts_bot, np.int32)], False, col, 2, cv2.LINE_AA)
        if kind == "NOR":
            cv2.circle(frame, (cx+s+6, cy), 5, col, 2, cv2.LINE_AA)
    elif kind == "NOT":
        pts = np.array([(cx-s, cy-s), (cx-s, cy+s), (cx+s, cy)], np.int32)
        cv2.polylines(frame, [pts], True, col, 2, cv2.LINE_AA)
        cv2.circle(frame, (cx+s+6, cy), 5, col, 2, cv2.LINE_AA)
    lbl = kind
    text(frame, lbl, cx-14, cy+4, 0.36, col, 1, FONT_S, shadow=False)


def block(frame, x, y, w, h, label, col=ACCENT, active=False, sub=""):
    """A labelled architecture block (register, ALU, mux, etc.)."""
    glass_panel(frame, x, y, w, h, radius=10, border=col if not active else HI,
                tint_strength=0.5, blur=7, border_alpha=0.9 if active else 0.5)
    tw, _ = text_size(label, 0.5, 1, FONT_S)
    text(frame, label, x+(w-tw)//2, y+h//2+2, 0.5, TEXT, 1, FONT_S)
    if sub:
        sw, _ = text_size(sub, 0.36, 1, FONT_S)
        text(frame, sub, x+(w-sw)//2, y+h-8, 0.36, MUTED, 1, FONT_S, shadow=False)


def to_bits(n, width):
    return [(n >> (width-1-i)) & 1 for i in range(width)]


# ═══════════════════════════ Ripple Carry Adder ════════════════════
class RippleCarryScene(Scene):
    """4-bit ripple carry adder — carry propagates stage by stage."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.A = self.sim.get("a", 0b1011)
        self.B = self.sim.get("b", 0b0110)
        self.width = 4

    def render(self, frame):
        t = self.elapsed()
        A = to_bits(self.A, self.width); B = to_bits(self.B, self.width)
        total = self.A + self.B
        S = to_bits(total & 0b1111, self.width)
        cout = (total >> self.width) & 1

        # how far the carry has rippled (animation)
        stage = min(int(t*1.2), self.width) if "add" in self.animations else 0

        cx = int(self.W*0.5); top = int(self.H*0.30)
        # operand rows
        bit_row(frame, cx-4*46, top, A, prefix="A")
        bit_row(frame, cx-4*46, top+50, B, prefix="B")

        # full adder stages left(MSB)..right(LSB) -> draw LSB first visually right
        fa_y = top+130
        carry = 0
        carries = [0]
        for i in range(self.width):
            # LSB is index width-1
            bi = self.width-1-i
            fx = cx + (i - self.width/2)*120 + 60
            lit = i < stage or "add" not in self.animations
            block(frame, int(fx-46), fa_y, 92, 56, f"FA{i}", ACCENT, active=lit)
            a=A[bi]; b=B[bi]
            s=(a^b^carry); nc=(a&b)|(carry&(a^b))
            # carry wire to next stage
            if i < self.width-1:
                nxt = cx + ((i+1) - self.width/2)*120 + 60
                bit_wire(frame, (int(fx-46), fa_y+28), (int(nxt+46), fa_y+28),
                         nc if lit else 0, t)
            # sum bit below
            bit_box(frame, int(fx-17), fa_y+80, s if lit else 0, f"S{i}")
            carry = nc; carries.append(nc)

        # carry out
        cob = cout if (stage>=self.width or "add" not in self.animations) else 0
        bit_box(frame, cx-4*46-60, fa_y+80, cob, "Cout", col=AMBER if cob else None)

        # result
        bit_row(frame, cx-4*46, int(self.H*0.72), S, prefix="Sum")

        sidebar(frame, self.W, [
            ("A", f"{self.A:04b} = {self.A}", HI),
            ("B", f"{self.B:04b} = {self.B}", HI),
            ("SUM", f"{total & 0b1111:04b}", GREEN),
            ("CARRY OUT", str(cout), AMBER),
            ("DELAY", f"{self.width} FA stages", MUTED),
        ], "RIPPLE CARRY ADDER")
        if "add" in self.animations and stage < self.width:
            chip(frame, f"carry rippling... stage {stage}/{self.width}", cx-90,
                 int(self.H*0.80), AMBER, 0.42)
        return frame


# ═══════════════════════ Carry Look-Ahead Adder ════════════════════
class CarryLookAheadScene(Scene):
    """Carry look-ahead — all carries computed in parallel from G and P."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.A = self.sim.get("a", 0b1011); self.B = self.sim.get("b", 0b0110)
        self.width = 4

    def render(self, frame):
        t = self.elapsed()
        A = to_bits(self.A, self.width); B = to_bits(self.B, self.width)
        total = self.A + self.B
        cx = int(self.W*0.5); top = int(self.H*0.30)
        bit_row(frame, cx-4*46, top, A, prefix="A")
        bit_row(frame, cx-4*46, top+50, B, prefix="B")

        # generate / propagate per bit
        gy = top+124
        text(frame, "Gi = Ai . Bi     Pi = Ai (+) Bi", cx-160, gy-8, 0.44, CTRL, 1, FONT_S)
        for i in range(self.width):
            bi=self.width-1-i
            fx=cx+(i-self.width/2)*120+60
            g=A[bi]&B[bi]; p=A[bi]^B[bi]
            block(frame, int(fx-40), gy, 80, 44, f"G{i}P{i}", CTRL, active="add" in self.animations)
            bit_box(frame, int(fx-38), gy+54, g, f"G{i}", 30,30)
            bit_box(frame, int(fx+8), gy+54, p, f"P{i}", 30,30)

        # CLA block computes all carries at once
        cla_y = gy+120
        allcarry = "add" in self.animations and t>1.0
        block(frame, cx-200, cla_y, 400, 50,
              "CARRY LOOK-AHEAD LOGIC  (all carries in parallel)",
              AMBER, active=allcarry)
        # carries
        S=to_bits(total & 0b1111,self.width); cout=(total>>self.width)&1
        for i in range(self.width):
            fx=cx+(i-self.width/2)*120+60
            bit_box(frame, int(fx-17), cla_y+70, S[i] if allcarry else 0, f"S{i}")

        sidebar(frame, self.W, [
            ("A + B", f"{self.A}+{self.B}={total}", HI),
            ("SUM", f"{total & 0b1111:04b}", GREEN),
            ("CARRY OUT", str(cout), AMBER),
            ("SPEED", "O(1) carry", GREEN),
            ("vs RIPPLE", "no wait", CTRL),
        ], "CARRY LOOK-AHEAD")
        if allcarry:
            chip(frame, "all carries generated simultaneously", cx-110,
                 int(self.H*0.84), GREEN, 0.42)
        return frame


# ═══════════════════════════ Wallace Tree ══════════════════════════
class WallaceTreeScene(Scene):
    """Wallace tree multiplier — partial products reduced in layers."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.A = self.sim.get("a", 0b1101); self.B = self.sim.get("b", 0b1011)
        self.width = 4

    def render(self, frame):
        t = self.elapsed()
        cx = int(self.W*0.42); top = int(self.H*0.20)
        prod = self.A*self.B
        # partial products as dots (dot diagram)
        text(frame, f"A={self.A:04b}  B={self.B:04b}", cx-90, top-10, 0.5, HI, 1, FONT_S)
        A=to_bits(self.A,4); B=to_bits(self.B,4)
        layer = min(int(t*0.8), 3) if "reduce" in self.animations else 0

        # draw 3 reduction layers of dots collapsing
        rows = [8,6,4,2]  # dots per layer (illustrative)
        for L in range(4):
            yy = top + 30 + L*70
            n = rows[L]
            active = L <= layer
            col = HI if active else (70,72,90)
            text(frame, ["PARTIAL PRODUCTS","LAYER 1 (3:2)","LAYER 2 (3:2)","FINAL ADDER"][L],
                 cx-230, yy+6, 0.4, AMBER if active else MUTED, 1, FONT_S, shadow=False)
            for d in range(n):
                dx = cx - n*14 + d*28 + 40
                if active:
                    cv2.circle(frame, (dx, yy), 7, col, -1, cv2.LINE_AA)
                    cv2.circle(frame, (dx, yy), 10, (60,180,110), 1, cv2.LINE_AA)
                else:
                    cv2.circle(frame, (dx, yy), 6, col, 1, cv2.LINE_AA)
            # arrows to next
            if L<3 and active:
                cv2.arrowedLine(frame,(cx+40,yy+14),(cx+40,yy+56),CTRL,2,cv2.LINE_AA,tipLength=0.3)

        bit_row(frame, cx-4*46+40, int(self.H*0.80), to_bits(prod,8), prefix="P")
        sidebar(frame, self.W, [
            ("A x B", f"{self.A}x{self.B}", HI),
            ("PRODUCT", f"{prod}", GREEN),
            ("BINARY", f"{prod:08b}", GREEN),
            ("METHOD", "3:2 CSA tree", CTRL),
            ("DELAY", "O(log n)", AMBER),
        ], "WALLACE TREE")
        return frame


# ═══════════════════════════ Flip Flop ═════════════════════════════
class FlipFlopScene(Scene):
    """D flip-flop — captures D on the clock edge, with a live timing diagram."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)

    def render(self, frame):
        t = self.elapsed()
        cx = int(self.W*0.30); cy = int(self.H*0.48)
        running = "clock" in self.animations
        phase = (t*1.2) % 4 if running else 0
        clk = 1 if (phase % 2) < 1 else 0
        d = 1 if int(phase) in (1,2) else 0
        # Q updates on rising edge (phase crossing even integer)
        q = 1 if int(phase) in (1,2) else 0

        # flip-flop block
        block(frame, cx-70, cy-70, 140, 140, "D  FF", ACCENT, active=running)
        bit_wire(frame, (cx-160, cy-40), (cx-70, cy-40), d, t)
        text(frame, "D", cx-180, cy-34, 0.5, HI if d else MUTED, 1, FONT_S)
        # clock input with edge triangle
        bit_wire(frame, (cx-160, cy+40), (cx-70, cy+40), clk, t)
        text(frame, "CLK", cx-205, cy+46, 0.5, HI if clk else MUTED, 1, FONT_S)
        cv2.drawMarker(frame,(cx-70,cy+40),ACCENT,cv2.MARKER_TRIANGLE_UP,10,2)
        # outputs Q, Q'
        bit_wire(frame, (cx+70, cy-40), (cx+160, cy-40), q, t)
        text(frame, "Q", cx+168, cy-34, 0.5, HI if q else MUTED, 1, FONT_S)
        bit_wire(frame, (cx+70, cy+40), (cx+160, cy+40), 1-q, t)
        text(frame, "Q'", cx+168, cy+46, 0.5, HI if (1-q) else MUTED, 1, FONT_S)

        # timing diagram
        gx, gy, gw = int(self.W*0.52), int(self.H*0.30), 360
        glass_panel(frame, gx-14, gy-24, gw+28, 220, radius=14, border=CTRL)
        text(frame, "TIMING DIAGRAM", gx, gy-4, 0.44, CTRL, 1, FONT_S)
        for row,(name,sig) in enumerate([("CLK",lambda p:1 if (p%2)<1 else 0),
                                          ("D",  lambda p:1 if int(p) in (1,2) else 0),
                                          ("Q",  lambda p:1 if int(p) in (1,2) else 0)]):
            yb = gy+40+row*56
            text(frame, name, gx-2, yb+6, 0.4, TEXT, 1, FONT_S)
            prev=None
            for px in range(gw-40):
                p=(px/(gw-40))*4
                v=sig(p)
                yy=yb-14 if v else yb+14
                xx=gx+40+px
                if prev is not None:
                    cv2.line(frame,(xx-1,prev),(xx,yy),HI,2,cv2.LINE_AA)
                prev=yy
            # live cursor
            if running:
                curx=gx+40+int((phase/4)*(gw-40))
                cv2.line(frame,(curx,yb-20),(curx,yb+20),AMBER,1,cv2.LINE_AA)

        sidebar(frame, self.W, [
            ("TYPE", "D flip-flop", ACCENT),
            ("CLK", str(clk), HI),
            ("D input", str(d), HI),
            ("Q output", str(q), GREEN),
            ("TRIGGER", "rising edge", CTRL),
        ], "FLIP-FLOP SYNTHESIS")
        return frame


# ═══════════════════════ Registers & Counters ══════════════════════
class RegisterCounterScene(Scene):
    """4-bit synchronous counter — increments each clock, shown as a register."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)

    def render(self, frame):
        t = self.elapsed()
        running = "count" in self.animations
        val = int(t*1.5) % 16 if running else 0
        bits = to_bits(val, 4)
        cx=int(self.W*0.42); cy=int(self.H*0.50)

        # register of 4 flip-flops
        text(frame, "4-BIT SYNCHRONOUS COUNTER", cx-160, cy-70, 0.5, ACCENT, 1, FONT_S)
        for i in range(4):
            fx=cx-4*70+i*80+40
            block(frame, fx-30, cy-40, 60, 80, f"FF{3-i}", ACCENT, active=running)
            bit_box(frame, fx-17, cy+60, bits[i], f"Q{3-i}")
            # clock line
            cv2.line(frame,(fx,cy+40),(fx,cy+52),CTRL,2,cv2.LINE_AA)
        # common clock bus
        cv2.line(frame,(cx-4*70+40,cy+52),(cx+4*70-40,cy+52),CTRL,2,cv2.LINE_AA)
        text(frame,"CLK",cx-4*70-14,cy+58,0.44,CTRL,1,FONT_S)

        # decimal display
        glass_panel(frame, cx-70, int(self.H*0.72), 140, 60, radius=12, border=GREEN)
        s=str(val); tw,_=text_size(s,1.1,2)
        text(frame, s, cx-tw//2, int(self.H*0.72)+44, 1.1, GREEN, 2)

        sidebar(frame, self.W, [
            ("COUNT", f"{val}", GREEN),
            ("BINARY", f"{val:04b}", HI),
            ("MODULUS", "16 (mod-16)", ACCENT),
            ("TYPE", "synchronous", CTRL),
            ("NEXT", f"{(val+1)%16}", MUTED),
        ], "REGISTERS & COUNTERS")
        return frame


# ══════════════════════ Combinational Multiplier ═══════════════════
class CombMultiplierScene(Scene):
    """Array multiplier — partial products added in an AND-gate array grid."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.A=self.sim.get("a",0b1101); self.B=self.sim.get("b",0b1011)

    def render(self, frame):
        t=self.elapsed()
        A=to_bits(self.A,4); B=to_bits(self.B,4)
        cx=int(self.W*0.40); top=int(self.H*0.28)
        prod=self.A*self.B
        text(frame,f"A={self.A:04b}  B={self.B:04b}",cx-90,top-8,0.5,HI,1,FONT_S)
        reveal = min(int(t*4),16) if "multiply" in self.animations else 16
        # partial product grid: rows = B bits, cols = A bits
        k=0
        for r in range(4):
            for c in range(4):
                gx=cx-4*44+c*44+40; gy=top+30+r*44
                pp = A[c]&B[r]
                shown = k<reveal
                if shown:
                    bit_box(frame,gx,gy,pp,"",34,34)
                k+=1
            text(frame,f"x B{3-r}",cx-4*44-30,top+30+r*44+24,0.36,MUTED,1,FONT_S,shadow=False)
        # result
        bit_row(frame, cx-4*46+30, int(self.H*0.80), to_bits(prod,8), prefix="P")
        sidebar(frame, self.W, [
            ("A x B", f"{self.A}x{self.B}", HI),
            ("PRODUCT", f"{prod}", GREEN),
            ("BINARY", f"{prod:08b}", GREEN),
            ("GATES", "4x4 AND array", ACCENT),
            ("ADDERS", "carry-save rows", CTRL),
        ], "ARRAY MULTIPLIER")
        return frame


# ═══════════════════════════ Booth Multiplier ══════════════════════
class BoothScene(Scene):
    """Booth's algorithm — signed multiply via recoding, step trace."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.M=self.sim.get("m",3); self.Q=self.sim.get("q",-4); self.width=4

    def render(self, frame):
        t=self.elapsed()
        cx=int(self.W*0.42); top=int(self.H*0.28)
        text(frame,f"Multiplicand M = {self.M}   Multiplier Q = {self.Q}",
             cx-190,top-10,0.5,HI,1,FONT_S)
        # booth recoding table (simplified illustrative steps)
        steps=[("Initialize","A=0000 Q=1100 Q-1=0"),
               ("Q0Q-1=00","shift right (ASR)"),
               ("Q0Q-1=10","A=A-M then shift"),
               ("Q0Q-1=01","A=A+M then shift"),
               ("Result","product = M x Q = "+str(self.M*self.Q))]
        show=min(int(t*0.9)+1,len(steps)) if "run" in self.animations else 1
        for i,(op,desc) in enumerate(steps):
            if i>=show: break
            yy=top+30+i*54
            active=(i==show-1)
            block(frame,cx-230,yy,180,44,op,AMBER if active else ACCENT,active=active)
            text(frame,desc,cx-30,yy+28,0.44,TEXT if active else MUTED,1,FONT_S)
        sidebar(frame, self.W, [
            ("M", f"{self.M}", HI),
            ("Q", f"{self.Q}", HI),
            ("PRODUCT", f"{self.M*self.Q}", GREEN),
            ("METHOD", "Booth recoding", CTRL),
            ("HANDLES", "signed nums", AMBER),
        ], "BOOTH'S MULTIPLIER")
        if "run" in self.animations and show>=len(steps):
            chip(frame,f"signed product = {self.M*self.Q}",cx-70,int(self.H*0.86),GREEN,0.42)
        return frame


# ═══════════════════════════════ ALU ═══════════════════════════════
class ALUScene(Scene):
    """Arithmetic Logic Unit — opcode selects the operation on A and B."""
    OPS=[("000","ADD",lambda a,b:a+b),("001","SUB",lambda a,b:a-b),
         ("010","AND",lambda a,b:a&b),("011","OR",lambda a,b:a|b),
         ("100","XOR",lambda a,b:a^b),("101","NOT A",lambda a,b:(~a)&0xF)]
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.A=self.sim.get("a",0b1010); self.B=self.sim.get("b",0b0110)

    def render(self, frame):
        t=self.elapsed()
        idx=int(t*0.6)%len(self.OPS) if "compute" in self.animations else 0
        opc,name,fn=self.OPS[idx]
        res=fn(self.A,self.B)&0xF
        cx=int(self.W*0.42); cy=int(self.H*0.52)

        # A and B buses in
        bit_row(frame, cx-260, cy-110, to_bits(self.A,4), prefix="A")
        bit_row(frame, cx-260, cy+70, to_bits(self.B,4), prefix="B")
        # trapezoid ALU body
        pts=np.array([(cx-70,cy-90),(cx+70,cy-50),(cx+70,cy+50),(cx-70,cy+90),
                      (cx-70,cy+20),(cx-40,cy),(cx-70,cy-20)],np.int32)
        glow=frame.copy(); cv2.fillPoly(glow,[pts],(40,60,90))
        cv2.addWeighted(glow,0.5,frame,0.5,0,frame)
        cv2.polylines(frame,[pts],True,ACCENT,2,cv2.LINE_AA)
        text(frame,"ALU",cx-24,cy+6,0.7,ACCENT,2)
        text(frame,name,cx-24,cy+34,0.5,HI,1,FONT_S)
        # opcode control from top
        text(frame,f"OP = {opc}",cx-34,cy-70,0.44,CTRL,1,FONT_S)
        cv2.arrowedLine(frame,(cx,cy-140),(cx,cy-92),CTRL,2,cv2.LINE_AA,tipLength=0.3)
        # result out
        bit_row(frame, cx+120, cy-17, to_bits(res,4), prefix="")
        text(frame,"RESULT",cx+120,cy-24,0.4,GREEN,1,FONT_S)

        sidebar(frame, self.W, [
            ("A", f"{self.A:04b}", HI),
            ("B", f"{self.B:04b}", HI),
            ("OPCODE", opc, CTRL),
            ("OP", name, ACCENT),
            ("RESULT", f"{res:04b}", GREEN),
        ], "ARITHMETIC LOGIC UNIT")
        return frame


# ═══════════════════════════ Memory Design ═════════════════════════
class MemoryDesignScene(Scene):
    """Memory array — address decoder selects a word line; data read out."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.words=8; self.wordbits=4

    def render(self, frame):
        t=self.elapsed()
        addr=int(t*0.8)%self.words if "access" in self.animations else 2
        cx=int(self.W*0.44); top=int(self.H*0.26)
        # address input
        bit_row(frame, cx-260, top, to_bits(addr,3), prefix="ADDR")
        # decoder
        block(frame, cx-260, top+56, 90, 60, "3:8\nDECODER", CTRL, active="access" in self.animations)
        # memory cells grid: words x wordbits
        gx=cx-40; gy=top+40
        data=[(0b1010+(w*3))&0xF for w in range(self.words)]
        for w in range(self.words):
            yy=gy+w*40
            sel=(w==addr)
            # word-line
            col=HI if sel else (70,72,90)
            cv2.line(frame,(cx-160,yy+17),(gx,yy+17),col,2 if sel else 1,cv2.LINE_AA)
            text(frame,f"W{w}",cx-185,yy+22,0.36,col,1,FONT_S,shadow=False)
            for b in range(self.wordbits):
                bx=gx+b*44
                bit=to_bits(data[w],self.wordbits)[b]
                bit_box(frame,bx,yy,bit if sel else bit, "",34,34,
                        col=HI if sel else None)
        # data out
        bit_row(frame, cx+230, gy+addr*40, to_bits(data[addr],4), prefix="")
        text(frame,"DATA OUT",cx+230,gy+addr*40-8,0.4,GREEN,1,FONT_S)

        sidebar(frame, self.W, [
            ("CAPACITY", f"{self.words}x{self.wordbits} bit", ACCENT),
            ("ADDRESS", f"{addr:03b} = {addr}", HI),
            ("WORD LINE", f"W{addr}", CTRL),
            ("DATA", f"{data[addr]:04b}", GREEN),
            ("DECODER", "3-to-8", MUTED),
        ], "MEMORY DESIGN")
        return frame


# ══════════════════════ Associative Cache ══════════════════════════
class AssociativeCacheScene(Scene):
    """Fully associative cache — tag compared against all lines in parallel."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.lines=4
        self.tags=[0b1011,0b0110,0b1101,0b0011]

    def render(self, frame):
        t=self.elapsed()
        seq=[0b1101,0b1111,0b0110,0b1010]
        req=seq[int(t*0.6)%len(seq)] if "lookup" in self.animations else 0b1101
        cx=int(self.W*0.42); top=int(self.H*0.28)
        hit_line=self.tags.index(req) if req in self.tags else -1
        # requested tag
        bit_row(frame, cx-200, top, to_bits(req,4), prefix="TAG")
        text(frame,"compared with ALL lines simultaneously",cx-200,top+52,0.42,CTRL,1,FONT_S)
        # cache lines with comparators
        for i in range(self.lines):
            yy=top+80+i*60
            hit=(i==hit_line)
            block(frame, cx-200, yy, 120, 46, f"Line {i}: {self.tags[i]:04b}",
                  GREEN if hit else ACCENT, active=hit)
            # comparator
            gate(frame, cx-30, yy+23, "XOR", active=hit)
            cv2.line(frame,(cx,yy+23),(cx+50,yy+23),HI if hit else (70,72,90),2,cv2.LINE_AA)
            res="HIT" if hit else "miss"
            text(frame,res,cx+58,yy+28,0.46,GREEN if hit else MUTED,1,FONT_S)
        verdict = "HIT" if hit_line>=0 else "MISS"
        sidebar(frame, self.W, [
            ("REQUEST TAG", f"{req:04b}", HI),
            ("LINES", f"{self.lines} (all checked)", ACCENT),
            ("RESULT", verdict, GREEN if hit_line>=0 else RED),
            ("HIT LINE", f"L{hit_line}" if hit_line>=0 else "-", GREEN),
            ("MAPPING", "fully assoc.", CTRL),
        ], "ASSOCIATIVE CACHE")
        return frame


# ══════════════════════ Direct Mapped Cache ════════════════════════
class DirectMappedScene(Scene):
    """Direct-mapped cache — index selects one line; tag then compared."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.lines=4

    def render(self, frame):
        t=self.elapsed()
        addrs=[0b101011,0b011001,0b110110,0b001000]
        addr=addrs[int(t*0.6)%len(addrs)] if "lookup" in self.animations else addrs[0]
        tag=(addr>>2)&0b1111; index=addr&0b11
        cx=int(self.W*0.42); top=int(self.H*0.27)
        # address breakdown
        text(frame,"ADDRESS",cx-240,top-4,0.44,HI,1,FONT_S)
        bit_row(frame, cx-160, top, to_bits(tag,4), prefix="")
        text(frame,"TAG",cx-150,top-8,0.34,AMBER,1,FONT_S,shadow=False)
        bit_row(frame, cx-160+4*40+16, top, to_bits(index,2), prefix="")
        text(frame,"IDX",cx-150+4*40+16,top-8,0.34,CTRL,1,FONT_S,shadow=False)

        # cache table — index picks exactly one line
        stored_tags=[0b1010,0b0110,0b1101,0b0010]
        for i in range(self.lines):
            yy=top+80+i*56
            sel=(i==index)
            hit=sel and (stored_tags[i]==tag)
            col=GREEN if hit else (AMBER if sel else ACCENT)
            block(frame, cx-160, yy, 150, 44,
                  f"[{i}] tag={stored_tags[i]:04b}", col, active=sel)
            if sel:
                cv2.arrowedLine(frame,(cx-210,top+40),(cx-165,yy+22),CTRL,2,cv2.LINE_AA,tipLength=0.2)
                gate(frame,cx+40,yy+22,"XOR",active=hit)
                text(frame,"HIT" if hit else "MISS",cx+80,yy+27,0.46,
                     GREEN if hit else RED,1,FONT_S)
        hit = stored_tags[index]==tag
        sidebar(frame, self.W, [
            ("TAG", f"{tag:04b}", AMBER),
            ("INDEX", f"{index:02b} -> L{index}", CTRL),
            ("STORED", f"{stored_tags[index]:04b}", ACCENT),
            ("RESULT", "HIT" if hit else "MISS", GREEN if hit else RED),
            ("MAPPING", "1 line only", MUTED),
        ], "DIRECT-MAPPED CACHE")
        return frame


# ═══════════════════════════════ CPU ═══════════════════════════════
class CPUScene(Scene):
    """Simple CPU datapath — fetch/decode/execute cycle animated."""
    STAGES=["FETCH","DECODE","EXECUTE","MEM","WRITE-BACK"]
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)

    def render(self, frame):
        t=self.elapsed()
        stage=int(t*0.8)%5 if "run" in self.animations else 0
        cx=int(self.W*0.42); cy=int(self.H*0.54)
        # stage banner ABOVE the datapath (clear of the top concept panel)
        glass_panel(frame,cx-140,cy-190,280,46,radius=14,border=CTRL)
        text(frame,f"STAGE: {self.STAGES[stage]}",cx-110,cy-160,0.6,CTRL,1,FONT_S)
        # datapath blocks
        comps=[("PC",cx-320,cy-110,70,44,0),
               ("INSTR\nMEM",cx-220,cy-110,80,60,0),
               ("REG\nFILE",cx-90,cy-40,90,90,1),
               ("ALU",cx+70,cy-20,80,80,2),
               ("DATA\nMEM",cx+200,cy-40,90,70,3),
               ("WB",cx+330,cy-20,60,44,4)]
        for name,x,y,w,h,st in comps:
            block(frame,x,y,w,h,name.replace("\n"," "),ACCENT,active=(st==stage))
        # connecting bus arrows
        links=[(cx-250,cy-88,cx-220,cy-88),(cx-140,cy-80,cx-90,cy-20),
               (cx,cy+5,cx+70,cy+20),(cx+150,cy+20,cx+200,cy-5),
               (cx+290,cy-5,cx+330,cy+2)]
        for i,(x1,y1,x2,y2) in enumerate(links):
            active=i<stage
            cv2.arrowedLine(frame,(int(x1),int(y1)),(int(x2),int(y2)),
                            BUS if active else (70,72,90),2,cv2.LINE_AA,tipLength=0.2)
        # pipeline progress dots
        for i,s in enumerate(self.STAGES):
            dx=cx-160+i*70
            c=HI if i<=stage else (70,72,90)
            cv2.circle(frame,(dx,cy+130),8,c,-1 if i<=stage else 1,cv2.LINE_AA)
            text(frame,s[:4],dx-16,cy+158,0.32,c,1,FONT_S,shadow=False)

        sidebar(frame, self.W, [
            ("STAGE", self.STAGES[stage], CTRL),
            ("CYCLE", f"{stage+1}/5", HI),
            ("PC", "increments", ACCENT),
            ("DATAPATH", "single-cycle", GREEN),
            ("NEXT", self.STAGES[(stage+1)%5], MUTED),
        ], "CPU DESIGN")
        return frame


# ═══════════════════════════ Karnaugh Map ══════════════════════════
class KarnaughScene(Scene):
    """K-map — 4-variable map with a highlighted grouping for minimization."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        # example function minterms
        self.minterms={0,1,2,3,5,7,8,10}

    def render(self, frame):
        t=self.elapsed()
        cx=int(self.W*0.38); top=int(self.H*0.30)
        cell=64
        gray=[0,1,3,2]  # gray code order
        # header labels
        text(frame,"AB \\ CD",cx-60,top-10,0.44,HI,1,FONT_S)
        for c in range(4):
            text(frame,f"{gray[c]:02b}",cx+c*cell+22,top-10,0.4,CTRL,1,FONT_S,shadow=False)
        for r in range(4):
            text(frame,f"{gray[r]:02b}",cx-40,top+r*cell+38,0.4,CTRL,1,FONT_S,shadow=False)
        # grouping animation reveal
        show_group = "group" in self.animations and t>1.5
        for r in range(4):
            for c in range(4):
                # minterm index from AB (rows) CD (cols) in gray order
                ab=gray[r]; cd=gray[c]; m=(ab<<2)|cd
                x=cx+c*cell; y=top+r*cell
                one=m in self.minterms
                col=HI if one else (60,62,78)
                cv2.rectangle(frame,(x,y),(x+cell-4,y+cell-4),(26,30,40),-1,cv2.LINE_AA)
                cv2.rectangle(frame,(x,y),(x+cell-4,y+cell-4),col,2,cv2.LINE_AA)
                v="1" if one else "0"
                text(frame,v,x+cell//2-6,y+cell//2+8,0.6,HI if one else MUTED,1,FONT_S)
                text(frame,f"m{m}",x+4,y+14,0.3,MUTED,1,FONT_S,shadow=False)
        # highlight a group (first column pair: CD=00 across some rows)
        if show_group:
            cv2.rectangle(frame,(cx-3,top-3),(cx+cell-1,top+4*cell-1),AMBER,3,cv2.LINE_AA)
            chip(frame,"group of 4 -> one term",cx-3,top+4*cell+12,AMBER,0.42)

        sidebar(frame, self.W, [
            ("VARIABLES", "4 (A,B,C,D)", ACCENT),
            ("MINTERMS", f"{len(self.minterms)}", HI),
            ("GROUPS", "powers of 2", CTRL),
            ("GOAL", "fewest terms", GREEN),
            ("RESULT", "simplified SOP", AMBER),
        ], "KARNAUGH MAP")
        return frame


# ══════════════════════ Quine-McCluskey ════════════════════════════
class QuineMcCluskeyScene(Scene):
    """Quine-McCluskey — tabular minimization grouping by number of 1s."""
    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.minterms=[0,1,2,5,6,7]

    def render(self, frame):
        t=self.elapsed()
        cx=int(self.W*0.40); top=int(self.H*0.27)
        # group minterms by count of 1s
        groups={}
        for m in self.minterms:
            g=bin(m).count("1"); groups.setdefault(g,[]).append(m)
        text(frame,"STEP 1: group minterms by number of 1s",cx-240,top-8,0.46,CTRL,1,FONT_S)
        reveal=min(int(t*0.8)+1,len(groups)+2) if "run" in self.animations else 99
        y=top+24
        for gi,(g,ms) in enumerate(sorted(groups.items())):
            if gi>=reveal: break
            block(frame,cx-240,y,90,40,f"{g} one(s)",ACCENT,active=True)
            for j,m in enumerate(ms):
                bit_row(frame, cx-130+j*180, y+3, to_bits(m,3), prefix="")
                text(frame,f"m{m}",cx-130+j*180,y-6,0.32,MUTED,1,FONT_S,shadow=False)
            y+=54
        if "run" in self.animations and t>3.5:
            block(frame,cx-240,y+6,420,44,"STEP 2: combine adjacent -> prime implicants",
                  AMBER,active=True)
        sidebar(frame, self.W, [
            ("MINTERMS", f"{len(self.minterms)}", HI),
            ("METHOD", "tabular", ACCENT),
            ("GROUP BY", "# of 1s", CTRL),
            ("COMBINE", "differ by 1 bit", AMBER),
            ("OUTPUT", "prime implicants", GREEN),
        ], "QUINE-McCLUSKEY")
        return frame
