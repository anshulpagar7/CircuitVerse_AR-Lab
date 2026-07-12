# python_app/hud.py
"""
CircuitVerse v2 — Glassmorphism HUD library for OpenCV.

Every panel is a real frosted-glass effect: the camera feed behind the
panel is blurred, tinted, rounded, and stroked with a soft border.
All colors are BGR.
"""

import cv2
import numpy as np

# ─────────────────────────── design tokens ───────────────────────────
ACCENT      = (255, 212, 0)     # cyan   #00d4ff
ACCENT_DIM  = (140, 110, 0)
PURPLE      = (237, 58, 124)    # violet #7c3aed
GREEN       = (129, 185, 16)    # emerald #10b981
AMBER       = (11, 158, 245)    # amber  #f59e0b
RED         = (68, 68, 239)     # red    #ef4444
TEXT        = (240, 232, 226)
MUTED       = (160, 140, 120)
PANEL_TINT  = (24, 16, 8)       # deep navy tint

FONT   = cv2.FONT_HERSHEY_DUPLEX
FONT_S = cv2.FONT_HERSHEY_SIMPLEX


# ── ASCII-safe text ──────────────────────────────────────────────────
# OpenCV's putText renders only basic ASCII (Hershey fonts). Any other
# glyph shows as a hollow "?" box. This table maps every symbol we use to
# a clean ASCII equivalent so the HUD always looks professional. Applied
# automatically inside text() and text_size() — callers can keep writing
# natural strings with Greek letters, subscripts, arrows, etc.
_ASCII_MAP = {
    # Greek letters (spelled where read as a word, single-char where a variable)
    "Ω": "Ohm", "ω": "w", "τ": "tau", "θ": "theta", "φ": "phi",
    "λ": "lambda", "Δ": "d", "μ": "u", "π": "pi", "α": "a", "β": "b",
    "ρ": "rho", "σ": "sigma", "Φ": "Phi", "Σ": "S",
    # subscripts / superscripts -> plain digits (standard ASCII chemistry: CO2)
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5",
    "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
    "⁶": "6", "⁻": "-", "ⁿ": "n",
    # math / arrows / punctuation
    "×": "x", "·": ".", "÷": "/", "−": "-", "±": "+/-",
    "→": "->", "←": "<-", "↑": "^", "↓": "v", "‹": "<", "›": ">",
    "∞": "inf", "∝": "~", "≈": "~", "≤": "<=", "≥": ">=", "≠": "!=",
    "°": "deg", "√": "sqrt", "∆": "d",
    "✓": "OK", "✕": "x", "✗": "x", "☰": "=", "…": "...",
    "—": "-", "–": "-", "‑": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
    "•": "*", "▸": ">", "○": "o", "●": "*",
}


def ascii_safe(s):
    """Convert any string to an OpenCV-renderable ASCII string."""
    if not isinstance(s, str):
        s = str(s)
    out = []
    for ch in s:
        if ord(ch) < 128:
            out.append(ch)
        else:
            out.append(_ASCII_MAP.get(ch, "?"))
    return "".join(out)


# ─────────────────────────── primitives ──────────────────────────────
_MASK_CACHE = {}
def _rounded_mask(w: int, h: int, radius: int) -> np.ndarray:
    """Anti-aliased rounded-rectangle alpha mask (float 0..1), cached by size."""
    key = (w, h, radius)
    m = _MASK_CACHE.get(key)
    if m is not None:
        return m
    mask = np.zeros((h, w), np.uint8)
    r = max(1, min(radius, w // 2, h // 2))
    cv2.rectangle(mask, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(mask, (0, r), (w, h - r), 255, -1)
    for cx, cy in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)):
        cv2.circle(mask, (cx, cy), r, 255, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(mask, (3, 3), 0).astype(np.float32) / 255.0
    m = m[..., None] if False else m  # keep 2D; caller adds axis
    if len(_MASK_CACHE) > 128:
        _MASK_CACHE.clear()
    _MASK_CACHE[key] = m
    return m


def glass_panel(frame, x, y, w, h, radius=18, tint=PANEL_TINT,
                tint_strength=0.55, blur=21, border=ACCENT, border_alpha=0.35,
                gradient=True, glow=True):
    """Frosted-glass panel drawn in place. Returns (x, y, w, h) clipped.
    Optimized: all work happens on the panel ROI (no full-frame copies),
    and the frosted blur is done at reduced cost."""
    H, W = frame.shape[:2]
    x, y = max(0, x), max(0, y)
    w, h = min(w, W - x), min(h, H - y)
    if w <= 4 or h <= 4:
        return x, y, w, h

    roi = frame[y:y + h, x:x + w]

    # frosted glass: downscale, blur small, upscale — much cheaper than a
    # large-kernel blur on the full-size ROI, and visually identical here
    sw, sh = max(1, w // 3), max(1, h // 3)
    glass = cv2.resize(roi, (sw, sh), interpolation=cv2.INTER_LINEAR)
    glass = cv2.GaussianBlur(glass, (0, 0), 2)
    glass = cv2.resize(glass, (w, h), interpolation=cv2.INTER_LINEAR)

    tint_img = np.empty_like(glass); tint_img[:] = tint
    glass = cv2.addWeighted(glass, 1 - tint_strength, tint_img, tint_strength, 0)

    # vertical gradient sheen (cached per height for speed)
    if gradient and h >= 8:
        grad = _grad_cache(h)
        glass = np.clip(glass.astype(np.float32) * grad, 0, 255).astype(np.uint8)

    # top-edge specular highlight
    hl_h = max(2, h // 10)
    glass[:hl_h] = cv2.addWeighted(glass[:hl_h], 0.86,
                                   _hl_cache(w, hl_h), 0.14, 0)

    # rounded composite (blend only inside the rounded mask)
    mask = _rounded_mask(w, h, radius)[..., None]
    np.copyto(roi, (glass * mask + roi * (1 - mask)).astype(np.uint8))

    # neon border — stroke directly on the ROI (no full-frame copy)
    _rounded_stroke_blend(roi, 0, 0, w, h, radius, border, 2, border_alpha)
    _rounded_stroke_blend(roi, 1, 1, w - 2, h - 2, radius,
                          tuple(min(255, int(c * 1.4)) for c in border),
                          1, border_alpha * 0.5)
    return x, y, w, h


# ── caches for gradient & highlight strips (keyed by size) ──
_GRAD = {}
def _grad_cache(h):
    g = _GRAD.get(h)
    if g is None:
        col = np.linspace(1.14, 0.86, h, dtype=np.float32)
        g = np.repeat(col[:, None, None], 3, axis=2)
        _GRAD[h] = g
        if len(_GRAD) > 64:
            _GRAD.clear(); _GRAD[h] = g
    return g

_HL = {}
def _hl_cache(w, hl_h):
    key = (w, hl_h)
    s = _HL.get(key)
    if s is None:
        s = np.empty((hl_h, w, 3), np.uint8); s[:] = (110, 90, 65)
        _HL[key] = s
        if len(_HL) > 64:
            _HL.clear(); _HL[key] = s
    return s


def _rounded_stroke_blend(roi, x, y, w, h, r, color, thick, alpha):
    """Draw a rounded-rect stroke onto roi, alpha-blended, without copying
    the whole frame — only a thin band around the border is touched."""
    tmp = roi.copy()
    _rounded_stroke(tmp, x, y, w, h, r, color, thick)
    cv2.addWeighted(tmp, alpha, roi, 1 - alpha, 0, roi)


def _rounded_stroke(img, x, y, w, h, r, color, thick):
    r = max(1, min(r, w // 2, h // 2))
    cv2.line(img, (x + r, y), (x + w - r, y), color, thick, cv2.LINE_AA)
    cv2.line(img, (x + r, y + h), (x + w - r, y + h), color, thick, cv2.LINE_AA)
    cv2.line(img, (x, y + r), (x, y + h - r), color, thick, cv2.LINE_AA)
    cv2.line(img, (x + w, y + r), (x + w, y + h - r), color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x + r, y + r), (r, r), 180, 0, 90, color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x + w - r, y + r), (r, r), 270, 0, 90, color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x + r, y + h - r), (r, r), 90, 0, 90, color, thick, cv2.LINE_AA)
    cv2.ellipse(img, (x + w - r, y + h - r), (r, r), 0, 0, 90, color, thick, cv2.LINE_AA)


def text(frame, s, x, y, scale=0.55, color=TEXT, thick=1, font=FONT, shadow=True):
    s = ascii_safe(s)
    if shadow:
        # tight 1px shadow, same thickness — crisp legibility without a
        # heavy offset ghost that reads as grainy at small sizes
        cv2.putText(frame, s, (x + 1, y + 1), font, scale, (0, 0, 0),
                    thick, cv2.LINE_AA)
    cv2.putText(frame, s, (x, y), font, scale, color, thick, cv2.LINE_AA)


def text_size(s, scale=0.55, thick=1, font=FONT):
    (w, h), _ = cv2.getTextSize(ascii_safe(s), font, scale, thick)
    return w, h


def chip(frame, s, x, y, color=ACCENT, scale=0.42):
    """Small pill label. Returns width consumed."""
    tw, th = text_size(s, scale, 1, FONT_S)
    w, h = tw + 18, th + 12
    glass_panel(frame, x, y, w, h, radius=h // 2,
                tint_strength=0.7, blur=9, border=color, border_alpha=0.6)
    text(frame, s, x + 9, y + h - 8, scale, color, 1, FONT_S, shadow=False)
    return w


def progress_bar(frame, x, y, w, done, total, color=ACCENT):
    h = 6
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (60, 45, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    if total > 0 and done > 0:
        fill = int(w * min(done / total, 1.0))
        cv2.rectangle(frame, (x, y), (x + fill, y + h), color, -1, cv2.LINE_AA)
        cv2.circle(frame, (x + fill, y + h // 2), 5, color, -1, cv2.LINE_AA)


def wrap_text(s, max_chars):
    """Character-based wrap (legacy). Prefer wrap_px for pixel-accurate fit."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def wrap_px(s, max_w, scale=0.52, thick=1, font=None):
    """Wrap text so each line fits within max_w pixels when rendered.
    Measures actual glyph widths (post ASCII-sanitize), so nothing overflows."""
    if font is None:
        font = FONT_S
    words = ascii_safe(s).split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        tw, _ = cv2.getTextSize(trial, font, scale, thick)[0], None
        if tw[0] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines if lines else [""]


# ─────────────────────────── composed widgets ─────────────────────────
def value_tag(frame, x, y, label, value, color=ACCENT):
    """Floating value tag next to a component, e.g. 'R1  1.0 kΩ | 5.0 mA'."""
    s = f"{label}  {value}"
    tw, _ = text_size(s, 0.45, 1, FONT_S)
    w, h = tw + 16, 26
    glass_panel(frame, x, y, w, h, radius=8, tint_strength=0.65,
                blur=9, border=color, border_alpha=0.5)
    text(frame, s, x + 8, y + 18, 0.45, TEXT, 1, FONT_S, shadow=False)
    return w, h


def rc_graph(frame, x, y, w, h, tau, v_final, t_now, charging=True):
    """Live RC charging curve inside a glass panel with a moving marker."""
    glass_panel(frame, x, y, w, h, radius=14, border=PURPLE)
    text(frame, "Vc(t) — RC CHARGING" if charging else "Vc(t) — DISCHARGE",
         x + 14, y + 24, 0.45, PURPLE, 1, FONT_S)

    gx, gy = x + 40, y + 36
    gw, gh = w - 56, h - 62
    # axes
    cv2.line(frame, (gx, gy), (gx, gy + gh), MUTED, 1, cv2.LINE_AA)
    cv2.line(frame, (gx, gy + gh), (gx + gw, gy + gh), MUTED, 1, cv2.LINE_AA)
    text(frame, f"{v_final:.0f}V", x + 8, gy + 10, 0.38, MUTED, 1, FONT_S, shadow=False)
    text(frame, "5t", gx + gw - 14, gy + gh + 16, 0.38, MUTED, 1, FONT_S, shadow=False)

    t_span = 5 * tau if tau > 0 else 1.0
    pts = []
    for i in range(gw):
        t = (i / gw) * t_span
        v = v_final * (1 - np.exp(-t / tau)) if charging else v_final * np.exp(-t / tau)
        pts.append((gx + i, gy + gh - int((v / max(v_final, 1e-9)) * gh)))
    cv2.polylines(frame, [np.array(pts, np.int32)], False, PURPLE, 2, cv2.LINE_AA)

    # live marker
    tm = min(t_now % (t_span * 1.2), t_span)
    mi = int((tm / t_span) * (gw - 1))
    mx, my = pts[mi]
    cv2.circle(frame, (mx, my), 5, ACCENT, -1, cv2.LINE_AA)
    cv2.circle(frame, (mx, my), 9, ACCENT, 1, cv2.LINE_AA)
    v_now = v_final * (1 - np.exp(-tm / tau)) if charging else v_final * np.exp(-tm / tau)
    text(frame, f"{v_now:.2f} V @ {tm*1000:.0f} ms", gx + 6, gy + 14, 0.42, ACCENT, 1, FONT_S)
