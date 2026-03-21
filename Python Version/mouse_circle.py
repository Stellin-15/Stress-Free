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

pyautogui.FAILSAFE = False

# ── Color Palette ─────────────────────────────────────────────────────────────
BG_COLOR     = "#0A0A0B"
CARD_COLOR   = "#111113"
BORDER_COLOR = "#1E1E22"
ACCENT_COLOR = "#00C896"
ACCENT_HOVER = "#00A87E"
STOP_COLOR   = "#FF4757"
STOP_HOVER   = "#CC2233"
DIM_TEXT     = "#4A4A55"
BRIGHT_TEXT  = "#E8E8EE"

# ── Funny idle messages ───────────────────────────────────────────────────────
IDLE_MESSAGES = [
    "Maximizing synergies...",
    "Crushing it.",
    "In the zone.",
    "Optimizing output...",
    "Definitely working.",
    "Very productive.",
    "Generating value.",
    "100% focused.",
    "Delivering results.",
    "Peak performance.",
]

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class OrbitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("420x620")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        # ── State ──────────────────────────────────────────────────────────────
        self.is_running   = False
        self.start_time   = None
        self.productivity = 0
        self.dot_angle    = 0.0
        self._msg_index   = 0
        self._pulse_step  = 0
        self._pulse_colors = ["#1E1E22", "#252529", "#2A2A30", "#252529"]

        # ── Build UI ───────────────────────────────────────────────────────────
        self._build_header()
        self._build_canvas()
        self._build_controls()
        self._build_buttons()
        self._build_footer()

        # ── Bindings ───────────────────────────────────────────────────────────
        self.bind('<Escape>', lambda e: self.stop_movement())
        self.bind('<Control-h>', self._boss_key)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ── Start animations & tray ───────────────────────────────────────────
        self._rotate_message()
        self._pulse_ring()
        self._setup_tray()

        # ── Update check ──────────────────────────────────────────────────────
        check_for_updates(self._on_update_available)

    # ══ UI BUILDERS ══════════════════════════════════════════════════════════

    def _build_header(self):
        self.header = ctk.CTkLabel(
            self, text="ORBIT",
            font=("Consolas", 30, "bold"),
            text_color=ACCENT_COLOR
        )
        self.header.pack(pady=(22, 2))

        self.subheader = ctk.CTkLabel(
            self, text=IDLE_MESSAGES[0],
            font=("Consolas", 11),
            text_color=DIM_TEXT
        )
        self.subheader.pack(pady=(0, 14))

    def _build_canvas(self):
        """Central animated orbit visualiser."""
        canvas_size = 160
        self.canvas = ctk.CTkCanvas(
            self, width=canvas_size, height=canvas_size,
            bg=BG_COLOR, highlightthickness=0
        )
        self.canvas.pack()

        cx = cy = canvas_size // 2
        r = 60
        pad = cx - r

        # Static dim ring
        self.ring = self.canvas.create_oval(
            pad, pad, canvas_size - pad, canvas_size - pad,
            outline=BORDER_COLOR, width=2
        )
        # Travelling dot (hidden at start)
        self.dot = self.canvas.create_oval(-10, -10, -2, -2, fill=ACCENT_COLOR, outline="")
        # Centre crosshair dots
        dot_r = 3
        self.canvas.create_oval(cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r,
                                 fill=BORDER_COLOR, outline="")

        # Status label below canvas
        self.status_label = ctk.CTkLabel(
            self, text="● Idle",
            font=("Consolas", 13),
            text_color=DIM_TEXT
        )
        self.status_label.pack(pady=(10, 0))

        self.timer_label = ctk.CTkLabel(
            self, text="",
            font=("Consolas", 10),
            text_color=DIM_TEXT
        )
        self.timer_label.pack(pady=(1, 12))

    def _build_controls(self):
        card = ctk.CTkFrame(
            self, fg_color=CARD_COLOR,
            corner_radius=12,
            border_width=1, border_color=BORDER_COLOR
        )
        card.pack(padx=24, pady=0, fill="x")

        # Pattern selector
        self.pattern_var = ctk.StringVar(value="Circle")
        pattern_btn = ctk.CTkSegmentedButton(
            card, values=["Circle", "Figure-8", "Jitter"],
            variable=self.pattern_var,
            font=("Consolas", 11),
            fg_color=BORDER_COLOR,
            selected_color=ACCENT_COLOR,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=BORDER_COLOR,
            unselected_hover_color="#2A2A30",
            text_color=BRIGHT_TEXT,
        )
        pattern_btn.pack(padx=16, pady=(14, 10), fill="x")

        # Radius slider
        r_row = ctk.CTkFrame(card, fg_color="transparent")
        r_row.pack(padx=16, pady=(4, 0), fill="x")
        ctk.CTkLabel(r_row, text="RADIUS", font=("Consolas", 10),
                     text_color=DIM_TEXT).pack(side="left")
        self.radius_val_label = ctk.CTkLabel(
            r_row, text="150 px", font=("Consolas", 10), text_color=ACCENT_COLOR
        )
        self.radius_val_label.pack(side="right")

        self.radius_slider = ctk.CTkSlider(
            card, from_=50, to=300, number_of_steps=250,
            button_color=ACCENT_COLOR, button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR,
            command=self._on_radius_change
        )
        self.radius_slider.set(150)
        self.radius_slider.pack(padx=16, pady=(4, 8), fill="x")

        # Speed slider
        s_row = ctk.CTkFrame(card, fg_color="transparent")
        s_row.pack(padx=16, pady=(4, 0), fill="x")
        ctk.CTkLabel(s_row, text="SPEED", font=("Consolas", 10),
                     text_color=DIM_TEXT).pack(side="left")
        self.speed_val_label = ctk.CTkLabel(
            s_row, text="5", font=("Consolas", 10), text_color=ACCENT_COLOR
        )
        self.speed_val_label.pack(side="right")

        self.speed_slider = ctk.CTkSlider(
            card, from_=1, to=10, number_of_steps=9,
            button_color=ACCENT_COLOR, button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR,
            command=self._on_speed_change
        )
        self.speed_slider.set(5)
        self.speed_slider.pack(padx=16, pady=(4, 8), fill="x")

        # Productivity bar
        p_row = ctk.CTkFrame(card, fg_color="transparent")
        p_row.pack(padx=16, pady=(4, 0), fill="x")
        ctk.CTkLabel(p_row, text="PRODUCTIVITY", font=("Consolas", 10),
                     text_color=DIM_TEXT).pack(side="left")
        self.prod_label = ctk.CTkLabel(
            p_row, text="0%", font=("Consolas", 10), text_color=ACCENT_COLOR
        )
        self.prod_label.pack(side="right")

        self.prod_bar = ctk.CTkProgressBar(
            card, progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR,
            corner_radius=4, height=6
        )
        self.prod_bar.set(0)
        self.prod_bar.pack(padx=16, pady=(4, 14), fill="x")

    def _build_buttons(self):
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=24, pady=12, fill="x")

        self.start_btn = ctk.CTkButton(
            btn_frame, text="START MOVEMENT",
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
            text_color="#000000",
            font=("Segoe UI", 13, "bold"), height=44,
            corner_radius=10,
            command=self.start_movement
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

        self.stop_btn = ctk.CTkButton(
            btn_frame, text="STOP  (ESC)",
            fg_color="transparent", border_width=1, border_color=STOP_COLOR,
            text_color=STOP_COLOR, hover_color=STOP_HOVER,
            font=("Segoe UI", 13, "bold"), height=44,
            corner_radius=10,
            command=self.stop_movement
        )
        self.stop_btn.pack(fill="x")

    def _build_footer(self):
        ctk.CTkLabel(
            self, text="Ctrl+H  —  hide window",
            font=("Consolas", 9), text_color=DIM_TEXT
        ).pack(pady=(0, 10))

    # ══ SLIDER CALLBACKS ═════════════════════════════════════════════════════

    def _on_radius_change(self, value):
        self.radius_val_label.configure(text=f"{int(value)} px")

    def _on_speed_change(self, value):
        self.speed_val_label.configure(text=str(int(value)))

    # ══ MOVEMENT LOGIC ═══════════════════════════════════════════════════════

    def _get_sleep(self):
        # Speed 1 → 0.05s delay, speed 10 → 0.005s delay
        speed = self.speed_slider.get()
        return 0.055 - (speed / 10) * 0.05

    def move_logic(self):
        steps = 80

        while self.is_running:
            cx, cy = pyautogui.position()
            radius = self.radius_slider.get()
            pattern = self.pattern_var.get()
            sleep = self._get_sleep()

            for i in range(steps):
                if not self.is_running:
                    break

                t = i * (2 * math.pi / steps)

                if pattern == "Circle":
                    x = cx + radius * math.cos(t)
                    y = cy + radius * math.sin(t)
                elif pattern == "Figure-8":
                    x = cx + radius * math.sin(t)
                    y = cy + (radius / 2) * math.sin(2 * t)
                else:  # Jitter
                    x = cx + random.uniform(-radius, radius)
                    y = cy + random.uniform(-radius, radius)

                try:
                    pyautogui.moveTo(x, y, _pause=False)
                except Exception:
                    self.stop_movement()
                    return

                time.sleep(sleep)

    # ══ START / STOP ══════════════════════════════════════════════════════════

    def start_movement(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self.productivity = 0
            self.status_label.configure(text="● RUNNING", text_color=ACCENT_COLOR)
            self.start_btn.configure(state="disabled")
            self._tick_timer()
            self._tick_productivity()
            self._animate_dot()
            threading.Thread(target=self.move_logic, daemon=True).start()

    def stop_movement(self):
        self.is_running = False
        self.start_time = None
        self.status_label.configure(text="● Stopped", text_color=DIM_TEXT)
        self.timer_label.configure(text="")
        self.start_btn.configure(state="normal")
        # Hide dot
        self.canvas.coords(self.dot, -10, -10, -2, -2)

    # ══ ANIMATIONS & TIMERS ══════════════════════════════════════════════════

    def _tick_timer(self):
        if not self.is_running or self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        if h:
            self.timer_label.configure(text=f"{h}:{m:02d}:{s:02d}")
        else:
            self.timer_label.configure(text=f"{m:02d}:{s:02d}")
        self.after(1000, self._tick_timer)

    def _tick_productivity(self):
        if not self.is_running:
            return
        self.productivity = min(99, self.productivity + random.randint(1, 3))
        self.prod_label.configure(text=f"{self.productivity}%")
        self.prod_bar.set(self.productivity / 100)
        self.after(4000, self._tick_productivity)

    def _animate_dot(self):
        if not self.is_running:
            return
        canvas_r = 60
        cx = cy = 80  # canvas centre (160/2)
        dot_r = 5
        x = cx + canvas_r * math.cos(self.dot_angle)
        y = cy + canvas_r * math.sin(self.dot_angle)
        self.canvas.coords(self.dot, x - dot_r, y - dot_r, x + dot_r, y + dot_r)
        speed = self.speed_slider.get()
        self.dot_angle += 0.06 + speed * 0.005
        self.after(30, self._animate_dot)

    def _pulse_ring(self):
        color = self._pulse_colors[self._pulse_step % len(self._pulse_colors)]
        self.canvas.itemconfig(self.ring, outline=color)
        self._pulse_step += 1
        self.after(700, self._pulse_ring)

    def _rotate_message(self):
        if not self.is_running:
            self._msg_index = (self._msg_index + 1) % len(IDLE_MESSAGES)
            self.subheader.configure(text=IDLE_MESSAGES[self._msg_index])
        self.after(3000, self._rotate_message)

    # ══ BOSS KEY & TRAY ══════════════════════════════════════════════════════

    def _boss_key(self, _event=None):
        if self.state() == "normal":
            self.withdraw()
        else:
            self.deiconify()
            self.lift()

    def _setup_tray(self):
        # Draw a teal circle as the tray icon
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill="#00C896")

        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self._tray_show, default=True),
            pystray.MenuItem("Stop Movement", lambda: self.after(0, self.stop_movement)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self.after(0, self.on_close)),
        )
        self.tray_icon = pystray.Icon("OrbitMousePro", img, "Orbit Mouse Pro", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _tray_show(self):
        self.after(0, lambda: (self.deiconify(), self.lift()))

    # ══ UPDATE BANNER ════════════════════════════════════════════════════════

    def _on_update_available(self, version, url):
        self.after(0, lambda: self._show_update_banner(version, url))

    def _show_update_banner(self, version, url):
        banner = ctk.CTkLabel(
            self,
            text=f"  Update v{version} available — click to download  ",
            font=("Consolas", 10),
            text_color="#F59E0B",
            cursor="hand2"
        )
        banner.pack(pady=(0, 6))
        banner.bind("<Button-1>", lambda e: webbrowser.open(url))

    # ══ CLOSE ════════════════════════════════════════════════════════════════

    def on_close(self):
        self.is_running = False
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = OrbitApp()
    app.attributes('-topmost', True)
    app.mainloop()
