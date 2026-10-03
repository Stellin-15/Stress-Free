import customtkinter as ctk
import pyautogui
import math
import random
import threading
import time
import webbrowser
from version import APP_VERSION, APP_NAME
from updater import check_for_updates
from PIL import Image, ImageDraw
import pystray
import pywinstyles

pyautogui.FAILSAFE = False

# ── Cyberpunk Palette ──────────────────────────────────────────────────────────
BG_COLOR    = "#0D0D1A"    # dark navy — readable, not pitch black
CARD_COLOR  = "#13132A"
BORDER_DIM  = "#22224A"
NEON_YLW    = "#E8FF00"    # electric yellow — primary accent
NEON_CYAN   = "#00EEFF"    # cyan — secondary / info
NEON_RED    = "#FF0040"    # stop / danger
DIM_TEXT    = "#9090BB"    # muted labels
MID_TEXT    = "#FFFFFF"    # primary readable text — pure white
BRIGHT_TEXT = "#FFFFFF"

# Glow colour layers (yellow, outermost → brightest)
G1 = "#2A2E00"
G2 = "#686E00"
G3 = "#B8CC00"
G4 = "#E8FF00"

GLITCH_CHARS = "!#$%@*<>[]{}01アイウエカキクケ▓▒░◆◈"

IDLE_MSGS = [
    "MAXIMIZING SYNERGIES...",
    "CRUSHING IT.",
    "IN THE ZONE.",
    "OPTIMIZING OUTPUT...",
    "DEFINITELY WORKING.",
    "VERY PRODUCTIVE.",
    "GENERATING VALUE.",
    "100% FOCUSED.",
    "PEAK PERFORMANCE.",
    "DELIVERING RESULTS.",
]

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

FONT_MONO_LG = ("Consolas", 30, "bold")
FONT_MONO_MD = ("Consolas", 14, "bold")
FONT_MONO_SM = ("Consolas", 12)
FONT_MONO_XS = ("Consolas", 11)
FONT_BTN     = ("Consolas", 13, "bold")


class OrbitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("440x690")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        # Custom icon + title bar theming
        self._apply_icon()
        self._apply_titlebar()

        # State
        self.is_running    = False
        self.start_time    = None
        self.productivity  = 0
        self.dot_angle     = 0.0
        self._msg_idx      = 0
        self._scanline_y   = 0
        self._run_id       = 0       # bumped on every start; stale loops exit
        self._stop_event   = threading.Event()

        # Plain copies of the control values — the worker thread reads these,
        # never the Tk widgets (Tkinter is not thread-safe)
        self._radius  = 150.0
        self._speed   = 5.0
        self._pattern = "CIRCLE"

        self._build_ui()

        # Bindings
        self.bind('<Escape>', lambda e: self.stop_movement())
        self.bind('<Control-h>', self._boss_key)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Kick off animations
        self._boot_sequence()
        self._rotate_message()
        self._animate_scanline()
        self._setup_tray()
        check_for_updates(self._on_update_available)

    # ══ ICON & TITLEBAR ══════════════════════════════════════════════════════

    def _apply_icon(self):
        """Save a .ico file and apply it via iconbitmap — most reliable on Windows."""
        import os, tempfile
        img = self._draw_emblem(pil_size=256)

        # Save .ico (multi-size) to temp dir
        ico_path = os.path.join(tempfile.gettempdir(), "orbit_mouse_pro.ico")
        img.save(ico_path, format="ICO",
                 sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

        # Defer until after CTk finishes its own init
        self.after(0, lambda: self.iconbitmap(ico_path))

    def _apply_titlebar(self):
        """Colour the Windows title bar to match the cyberpunk theme."""
        try:
            pywinstyles.change_header_color(self, "#0D0D1A")
        except Exception:
            pass  # Graceful fallback on unsupported Windows versions

    def _draw_emblem(self, pil_size: int) -> Image.Image:
        """Shared draw routine — used for both the in-app logo and saved files."""
        S = pil_size
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx = cy = S // 2
        sc = S / 80  # scale factor (base design is 80 px)

        # Dark navy circle background
        d.ellipse([0, 0, S - 1, S - 1], fill="#0D0D1A")

        # Subtle inner grid
        step   = max(1, int(12 * sc))
        margin = max(1, int(10 * sc))
        for i in range(margin, S - margin, step):
            d.line([(margin, i), (S - margin, i)], fill="#181835", width=1)
            d.line([(i, margin), (i, S - margin)], fill="#181835", width=1)

        # Bloom ring (outermost → brightest)
        for pad_b, col, w_b in [
            (6,  "#151800", 16),
            (10, "#353C00", 10),
            (13, "#6A7600", 6),
            (14, "#B0C400", 3),
            (15, "#E8FF00", 2),
        ]:
            pad = max(1, int(pad_b * sc))
            w   = max(1, int(w_b   * sc))
            d.arc([pad, pad, S - pad, S - pad], 0, 360, fill=col, width=w)

        ring_r = cx - max(1, int(15 * sc))

        # Cardinal crosshair ticks
        tick_len = max(2, int(9 * sc))
        lw = max(1, int(1.5 * sc))
        for deg in [0, 90, 180, 270]:
            rad = math.radians(deg)
            x1 = cx + int(ring_r * math.cos(rad))
            y1 = cy + int(ring_r * math.sin(rad))
            x2 = cx + int((ring_r - tick_len) * math.cos(rad))
            y2 = cy + int((ring_r - tick_len) * math.sin(rad))
            d.line([(x1, y1), (x2, y2)], fill="#E8FF00", width=lw)

        # Centre reticle
        cs = max(2, int(5 * sc))
        d.line([(cx - cs, cy), (cx + cs, cy)], fill="#E8FF00", width=lw)
        d.line([(cx, cy - cs), (cx, cy + cs)], fill="#E8FF00", width=lw)
        cr = max(3, int(7 * sc))
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline="#E8FF00", width=lw)

        # Orbiting dot + glow at −45°
        angle = math.radians(-45)
        dx = int(cx + ring_r * math.cos(angle))
        dy = int(cy + ring_r * math.sin(angle))
        for dot_b, col in [(9, "#1A1D00"), (6, "#909A00"), (3, "#E8FF00")]:
            dr = max(1, int(dot_b * sc))
            d.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=col)

        # HUD corner brackets
        blen = max(4, int(10 * sc))
        boff = max(2, int(3  * sc))
        for (x1, y1, sx, sy) in [
            (boff,     boff,     1, 1),
            (S-boff-1, boff,    -1, 1),
            (boff,     S-boff-1, 1,-1),
            (S-boff-1, S-boff-1,-1,-1),
        ]:
            d.line([(x1, y1), (x1 + sx * blen, y1)], fill="#E8FF00", width=lw)
            d.line([(x1, y1), (x1, y1 + sy * blen)], fill="#E8FF00", width=lw)

        return img

    def _create_logo_emblem(self) -> ctk.CTkImage:
        """Returns a CTkImage for use in the app header."""
        img = self._draw_emblem(pil_size=160)
        return ctk.CTkImage(img, size=(62, 62))

    # ══ UI BUILDERS ══════════════════════════════════════════════════════════

    def _build_ui(self):
        # Top neon accent line
        ctk.CTkFrame(self, height=2, fg_color=NEON_YLW).pack(fill="x")

        # Header — horizontal: emblem | text column
        hdr_frame = ctk.CTkFrame(self, fg_color="transparent")
        hdr_frame.pack(pady=(14, 4))

        logo_row = ctk.CTkFrame(hdr_frame, fg_color="transparent")
        logo_row.pack()

        # Emblem image
        self._logo_emblem = self._create_logo_emblem()
        ctk.CTkLabel(logo_row, image=self._logo_emblem, text="").pack(
            side="left", padx=(0, 14))

        # Text column
        text_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        text_col.pack(side="left", anchor="w")

        self.header = ctk.CTkLabel(
            text_col, text="",          # filled by boot sequence
            font=FONT_MONO_LG, text_color=NEON_YLW, anchor="w"
        )
        self.header.pack(anchor="w")

        ctk.CTkLabel(
            text_col,
            text=f"v{APP_VERSION}  ◆  MOUSE AUTOMATION SYSTEM",
            font=FONT_MONO_XS, text_color=DIM_TEXT, anchor="w"
        ).pack(anchor="w")

        self.subheader = ctk.CTkLabel(
            hdr_frame, text=IDLE_MSGS[0],
            font=FONT_MONO_XS, text_color=MID_TEXT
        )
        self.subheader.pack(pady=(6, 4))

        # Central orbit canvas
        self._build_canvas()

        # Status & timer
        self.status_label = ctk.CTkLabel(
            self, text="◈  IDLE",
            font=FONT_MONO_MD, text_color=DIM_TEXT
        )
        self.status_label.pack(pady=(8, 0))

        self.timer_label = ctk.CTkLabel(
            self, text="",
            font=FONT_MONO_XS, text_color=MID_TEXT
        )
        self.timer_label.pack(pady=(2, 8))

        # Controls card
        self._build_controls_card()

        # Buttons
        self._build_buttons()

        # Footer hint
        ctk.CTkLabel(
            self, text="[CTRL+H]  HIDE WINDOW",
            font=FONT_MONO_XS, text_color=DIM_TEXT
        ).pack(pady=(4, 10))

    def _build_canvas(self):
        SIZE = 180
        self.cv_size = SIZE
        self.cv_cx   = SIZE // 2
        self.cv_cy   = SIZE // 2
        self.cv_r    = 66

        self.canvas = ctk.CTkCanvas(
            self, width=SIZE, height=SIZE,
            bg=BG_COLOR, highlightthickness=0
        )
        self.canvas.pack()

        cx, cy, r = self.cv_cx, self.cv_cy, self.cv_r
        pad = cx - r

        # Background grid
        for i in range(0, SIZE, 18):
            self.canvas.create_line(i, 0, i, SIZE, fill="#1E1E40", width=1)
            self.canvas.create_line(0, i, SIZE, i, fill="#1E1E40", width=1)

        # HUD corner brackets
        blen, boff = 14, 8
        for (x1, y1, dx, dy) in [
            (boff,        boff,        1,  1),
            (SIZE - boff, boff,       -1,  1),
            (boff,        SIZE - boff, 1, -1),
            (SIZE - boff, SIZE - boff,-1, -1),
        ]:
            self.canvas.create_line(x1, y1, x1 + dx * blen, y1,
                                    fill=NEON_YLW, width=1)
            self.canvas.create_line(x1, y1, x1, y1 + dy * blen,
                                    fill=NEON_YLW, width=1)

        # Glow rings (outermost → innermost, creates bloom)
        self.ring_g1 = self.canvas.create_oval(
            pad-8, pad-8, SIZE-pad+8, SIZE-pad+8, outline=G1, width=12)
        self.ring_g2 = self.canvas.create_oval(
            pad-4, pad-4, SIZE-pad+4, SIZE-pad+4, outline=G2, width=6)
        self.ring_g3 = self.canvas.create_oval(
            pad-2, pad-2, SIZE-pad+2, SIZE-pad+2, outline=G3, width=3)
        self.ring    = self.canvas.create_oval(
            pad, pad, SIZE-pad, SIZE-pad, outline=BORDER_DIM, width=1)

        # Moving scanline
        self.scanline = self.canvas.create_line(
            0, 0, SIZE, 0, fill="#2A2A55", width=2)

        # Dot trail — 4 ghost dots (dim → bright, oldest → newest)
        self._trail_items = []
        for glow, size in [(G1, 4), (G2, 6), (G3, 9), (G4, 12)]:
            dot = self.canvas.create_oval(-30, -30, -30+size, -30+size,
                                          fill=glow, outline="")
            self._trail_items.append((dot, size))

        # Centre pip
        self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3,
                                 fill=BORDER_DIM, outline="")

    def _build_controls_card(self):
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(padx=22, pady=4, fill="x")

        # Left accent bar
        ctk.CTkFrame(outer, width=2, fg_color=NEON_YLW).pack(
            side="left", fill="y", padx=(0, 10))

        card = ctk.CTkFrame(
            outer, fg_color=CARD_COLOR,
            corner_radius=4,
            border_width=1, border_color=BORDER_DIM
        )
        card.pack(side="left", fill="x", expand=True)

        # Pattern selector
        ctk.CTkLabel(card, text="MOVEMENT PATTERN",
                     font=FONT_MONO_XS, text_color=DIM_TEXT
                     ).pack(anchor="w", padx=14, pady=(12, 4))

        self.pattern_var = ctk.StringVar(value="CIRCLE")
        ctk.CTkSegmentedButton(
            card, values=["CIRCLE", "FIGURE-8", "JITTER"],
            variable=self.pattern_var,
            command=self._on_pattern,
            font=FONT_MONO_XS,
            fg_color=BORDER_DIM,
            selected_color=NEON_YLW,
            selected_hover_color="#C8E000",
            unselected_color=BORDER_DIM,
            unselected_hover_color="#2A2A50",
            text_color="#000000",
            text_color_disabled=MID_TEXT,
        ).pack(padx=14, pady=(0, 10), fill="x")

        ctk.CTkFrame(card, height=1, fg_color=BORDER_DIM).pack(fill="x", padx=14)

        # Radius slider
        r_row = ctk.CTkFrame(card, fg_color="transparent")
        r_row.pack(padx=14, pady=(8, 2), fill="x")
        ctk.CTkLabel(r_row, text="RADIUS",
                     font=FONT_MONO_XS, text_color=DIM_TEXT).pack(side="left")
        self.radius_val = ctk.CTkLabel(
            r_row, text="150px", font=FONT_MONO_XS, text_color=NEON_YLW)
        self.radius_val.pack(side="right")

        self.radius_slider = ctk.CTkSlider(
            card, from_=50, to=300, number_of_steps=250,
            button_color=NEON_YLW, button_hover_color="#C8E000",
            progress_color=NEON_YLW, fg_color=BORDER_DIM, height=14,
            command=self._on_radius
        )
        self.radius_slider.set(150)
        self.radius_slider.pack(padx=14, pady=(0, 8), fill="x")

        # Speed slider
        s_row = ctk.CTkFrame(card, fg_color="transparent")
        s_row.pack(padx=14, pady=(4, 2), fill="x")
        ctk.CTkLabel(s_row, text="SPEED",
                     font=FONT_MONO_XS, text_color=DIM_TEXT).pack(side="left")
        self.speed_val = ctk.CTkLabel(
            s_row, text="5", font=FONT_MONO_XS, text_color=NEON_YLW)
        self.speed_val.pack(side="right")

        self.speed_slider = ctk.CTkSlider(
            card, from_=1, to=10, number_of_steps=9,
            button_color=NEON_YLW, button_hover_color="#C8E000",
            progress_color=NEON_YLW, fg_color=BORDER_DIM, height=14,
            command=self._on_speed
        )
        self.speed_slider.set(5)
        self.speed_slider.pack(padx=14, pady=(0, 8), fill="x")

        ctk.CTkFrame(card, height=1, fg_color=BORDER_DIM).pack(fill="x", padx=14)

        # Productivity bar
        p_row = ctk.CTkFrame(card, fg_color="transparent")
        p_row.pack(padx=14, pady=(8, 2), fill="x")
        ctk.CTkLabel(p_row, text="PRODUCTIVITY INDEX",
                     font=FONT_MONO_XS, text_color=DIM_TEXT).pack(side="left")
        self.prod_label = ctk.CTkLabel(
            p_row, text="0%", font=FONT_MONO_XS, text_color=NEON_YLW)
        self.prod_label.pack(side="right")

        self.prod_bar = ctk.CTkProgressBar(
            card, progress_color=NEON_YLW, fg_color=BORDER_DIM,
            corner_radius=2, height=5
        )
        self.prod_bar.set(0)
        self.prod_bar.pack(padx=14, pady=(0, 12), fill="x")

    def _build_buttons(self):
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=22, pady=(6, 4), fill="x")

        self.start_btn = ctk.CTkButton(
            btn_frame, text="▶  ENGAGE ORBIT",
            fg_color=NEON_YLW, hover_color="#C8E000",
            text_color="#000000",
            font=FONT_BTN, height=46,
            corner_radius=4,
            command=self.start_movement
        )
        self.start_btn.pack(fill="x", pady=(0, 6))

        self.stop_btn = ctk.CTkButton(
            btn_frame, text="■  ABORT  [ESC]",
            fg_color="transparent",
            border_width=1, border_color=NEON_RED,
            text_color=NEON_RED, hover_color="#280010",
            font=FONT_BTN, height=46,
            corner_radius=4,
            command=self.stop_movement
        )
        self.stop_btn.pack(fill="x")

    # ══ CONTROL CALLBACKS ════════════════════════════════════════════════════

    def _on_radius(self, v):
        self._radius = float(v)
        self.radius_val.configure(text=f"{int(v)}px")

    def _on_speed(self, v):
        self._speed = float(v)
        self.speed_val.configure(text=str(int(v)))

    def _on_pattern(self, value):
        self._pattern = value

    def _is_current(self, run_id):
        return self.is_running and run_id == self._run_id

    # ══ ANIMATIONS ═══════════════════════════════════════════════════════════

    def _boot_sequence(self):
        """Type "ORBIT" one character at a time on startup."""
        self.header.configure(text="")
        full = "ORBIT"
        for i, _ in enumerate(full):
            self.after(i * 110, lambda t=full[:i+1]: self.header.configure(text=t))
        # Schedule recurring glitch after boot
        self.after(len(full) * 110 + 2500, self._schedule_glitch)

    def _schedule_glitch(self):
        self._glitch_text()
        self.after(random.randint(6000, 14000), self._schedule_glitch)

    def _glitch_text(self):
        """Briefly corrupt header text with random cyberpunk chars."""
        original = "ORBIT"
        frames   = 8
        for i in range(frames):
            glitched = "".join(
                random.choice(GLITCH_CHARS) if random.random() < 0.55 else c
                for c in original
            )
            self.after(
                i * 50,
                lambda t=glitched: self.header.configure(text=t, text_color=NEON_CYAN)
            )
        self.after(
            frames * 50,
            lambda: self.header.configure(text=original, text_color=NEON_YLW)
        )

    def _animate_scanline(self):
        """CRT-style scanline that sweeps down the canvas."""
        self._scanline_y = (self._scanline_y + 4) % self.cv_size
        self.canvas.coords(
            self.scanline,
            0, self._scanline_y, self.cv_size, self._scanline_y
        )
        self.after(40, self._animate_scanline)

    def _animate_dot(self, run_id):
        """Spinning dot with 4-step neon trail."""
        if not self._is_current(run_id):
            return

        cx, cy, r = self.cv_cx, self.cv_cy, self.cv_r
        speed     = self._speed
        self.dot_angle = (self.dot_angle + 0.04 + speed * 0.006) % (2 * math.pi)

        for idx, (dot_id, sz) in enumerate(self._trail_items):
            phase = self.dot_angle - (len(self._trail_items) - idx) * 0.20
            x     = cx + r * math.cos(phase)
            y     = cy + r * math.sin(phase)
            half  = sz / 2
            self.canvas.coords(dot_id, x - half, y - half, x + half, y + half)

        self.after(25, self._animate_dot, run_id)

    def _flicker_status(self, text, color, count=0):
        """Flash status label to signal a state change."""
        if count < 6:
            c = color if count % 2 == 0 else BG_COLOR
            self.status_label.configure(text_color=c)
            self.after(65, lambda: self._flicker_status(text, color, count + 1))
        else:
            self.status_label.configure(text=text, text_color=color)

    def _rotate_message(self):
        if not self.is_running:
            self._msg_idx = (self._msg_idx + 1) % len(IDLE_MSGS)
            self.subheader.configure(text=IDLE_MSGS[self._msg_idx])
        self.after(3000, self._rotate_message)

    def _tick_timer(self, run_id):
        if not self._is_current(run_id) or self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time)
        h, rem  = divmod(elapsed, 3600)
        m, s    = divmod(rem, 60)
        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        self.timer_label.configure(text=f"ELAPSED  {ts}")
        self.after(1000, self._tick_timer, run_id)

    def _tick_productivity(self, run_id):
        if not self._is_current(run_id):
            return
        self.productivity = min(99, self.productivity + random.randint(1, 3))
        self.prod_label.configure(text=f"{self.productivity}%")
        self.prod_bar.set(self.productivity / 100)
        self.after(4000, self._tick_productivity, run_id)

    # ══ MOVEMENT LOGIC ═══════════════════════════════════════════════════════

    def _get_sleep(self):
        return 0.055 - (self._speed / 10) * 0.05

    def move_logic(self, run_id, stop_event, anchor):
        """Worker thread. Orbits a fixed anchor so the path never drifts.

        Only reads plain attributes (_radius/_speed/_pattern), never Tk widgets.
        """
        steps = 80
        ax, ay = anchor
        # Circle centre sits left of the cursor so the orbit starts where the
        # cursor already is instead of jumping `radius` px on the first frame
        circle_cx = ax - self._radius
        i = 0
        while not stop_event.is_set():
            radius  = self._radius
            pattern = self._pattern
            t = (i % steps) * (2 * math.pi / steps)

            if pattern == "CIRCLE":
                x = circle_cx + radius * math.cos(t)
                y = ay + radius * math.sin(t)
            elif pattern == "FIGURE-8":
                x = ax + radius * math.sin(t)
                y = ay + (radius / 2) * math.sin(2 * t)
            else:  # JITTER
                x = ax + random.uniform(-radius, radius)
                y = ay + random.uniform(-radius, radius)

            try:
                pyautogui.moveTo(x, y, _pause=False)
            except Exception:
                if not stop_event.is_set():
                    self.after(0, self.stop_movement)
                return

            i += 1
            # wait() returns immediately on stop, unlike time.sleep()
            stop_event.wait(self._get_sleep())

    # ══ START / STOP ══════════════════════════════════════════════════════════

    def start_movement(self):
        if not self.is_running:
            self.is_running   = True
            self._run_id     += 1
            run_id            = self._run_id
            self._stop_event  = threading.Event()
            self.start_time   = time.time()
            self.productivity = 0
            self.start_btn.configure(state="disabled")
            self._flicker_status("◈  RUNNING", NEON_YLW)
            # Ring glows bright yellow when active
            self.canvas.itemconfig(self.ring, outline=NEON_YLW, width=2)
            self.canvas.itemconfig(self.ring_g1, outline=G1)
            self.canvas.itemconfig(self.ring_g2, outline=G2)
            self.canvas.itemconfig(self.ring_g3, outline=G3)
            self._tick_timer(run_id)
            self._tick_productivity(run_id)
            self._animate_dot(run_id)
            threading.Thread(
                target=self.move_logic,
                args=(run_id, self._stop_event, pyautogui.position()),
                daemon=True,
            ).start()

    def stop_movement(self):
        if not self.is_running:
            return  # ESC / tray "Stop" while idle — nothing to abort
        self.is_running = False
        self._stop_event.set()
        self.start_time = None
        self._flicker_status("◈  ABORTED", NEON_RED)
        self.timer_label.configure(text="")
        self.start_btn.configure(state="normal")
        # Dim ring back to resting state
        self.canvas.itemconfig(self.ring,    outline=BORDER_DIM, width=1)
        self.canvas.itemconfig(self.ring_g1, outline="#0A0A00")
        self.canvas.itemconfig(self.ring_g2, outline="#0A0A00")
        self.canvas.itemconfig(self.ring_g3, outline="#0A0A00")
        # Park trail dots off-screen
        for dot_id, sz in self._trail_items:
            self.canvas.coords(dot_id, -30, -30, -30 + sz, -30 + sz)

    # ══ BOSS KEY & TRAY ══════════════════════════════════════════════════════

    def _boss_key(self, _=None):
        if self.state() == "normal":
            self.withdraw()
        else:
            self.deiconify()
            self.lift()

    def _setup_tray(self):
        img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill="#E8FF00")
        menu = pystray.Menu(
            pystray.MenuItem(
                "Show Window",
                lambda: self.after(0, lambda: (self.deiconify(), self.lift())),
                default=True
            ),
            pystray.MenuItem(
                "Stop Movement",
                lambda: self.after(0, self.stop_movement)
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self.after(0, self.on_close)),
        )
        self.tray_icon = pystray.Icon("OrbitMousePro", img, APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    # ══ UPDATE BANNER ════════════════════════════════════════════════════════

    def _on_update_available(self, version, url):
        self.after(0, lambda: self._show_update_banner(version, url))

    def _show_update_banner(self, version, url):
        banner = ctk.CTkLabel(
            self,
            text=f"  ▲ UPDATE v{version} AVAILABLE — CLICK TO DOWNLOAD  ",
            font=FONT_MONO_XS, text_color=NEON_CYAN, cursor="hand2"
        )
        banner.pack(pady=(0, 4))
        banner.bind("<Button-1>", lambda e: webbrowser.open(url))

    # ══ CLOSE ════════════════════════════════════════════════════════════════

    def on_close(self):
        self.is_running = False
        self._stop_event.set()
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = OrbitApp()
    app.attributes('-topmost', True)
    app.mainloop()
