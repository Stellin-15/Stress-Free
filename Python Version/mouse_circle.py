import customtkinter as ctk
import pyautogui
import math
import threading
import keyboard
import time

# --- CONFIGURATION & COLORS ---
# You can change these Hex codes to try different themes!
BG_COLOR = "#1A1A1B"        # Main Background
CARD_COLOR = "#2D2D2E"      # Inner container color
ACCENT_COLOR = "#3B82F6"    # Primary Button (Blue)
ACCENT_HOVER = "#2563EB"    # Button Hover state
STOP_COLOR = "#EF4444"      # Stop Button (Red)

ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("blue")

class ProfessionalMouseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Orbit Mouse Pro")
        self.geometry("400x320")
        self.configure(fg_color=BG_COLOR)

        self.is_running = False

        # --- UI LAYOUT ---
        # Header
        self.header = ctk.CTkLabel(self, text="ORBIT", font=("Inter", 24, "bold"), text_color=ACCENT_COLOR)
        self.header.pack(pady=(20, 5))
        
        self.subheader = ctk.CTkLabel(self, text="Mouse Automation Tool", font=("Inter", 12), text_color="gray")
        self.subheader.pack(pady=(0, 20))

        # Main Card (The box in the middle)
        self.main_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.main_frame.pack(padx=30, pady=10, fill="both", expand=True)

        # Status Indicator
        self.status_dot = ctk.CTkLabel(self.main_frame, text="● Idle", font=("Inter", 13), text_color="gray")
        self.status_dot.pack(pady=(15, 10))

        # Start Button
        self.start_btn = ctk.CTkButton(
            self.main_frame, text="START MOVEMENT", 
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
            font=("Inter", 14, "bold"), height=40,
            command=self.start_movement
        )
        self.start_btn.pack(pady=10, padx=20, fill="x")

        # Stop Button
        self.stop_btn = ctk.CTkButton(
            self.main_frame, text="STOP (ESC)", 
            fg_color="transparent", border_width=2, border_color=STOP_COLOR,
            text_color=STOP_COLOR, hover_color="#442222",
            font=("Inter", 14, "bold"), height=40,
            command=self.stop_movement
        )
        self.stop_btn.pack(pady=10, padx=20, fill="x")

        # Shortcut Listener
        keyboard.add_hotkey('esc', self.stop_movement)

    def move_logic(self):
        radius = 150
        steps = 80 # Higher steps = smoother movement
        cx, cy = pyautogui.position()
        
        while self.is_running:
            for i in range(steps):
                if not self.is_running: break
                
                angle = math.radians(i * (360 / steps))
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                
                # Move duration 0 ensures it's snappy but math steps make it smooth
                pyautogui.moveTo(x, y, _pause=False)
            time.sleep(0.01)

    def start_movement(self):
        if not self.is_running:
            self.is_running = True
            self.status_dot.configure(text="● RUNNING", text_color="#10B981")
            self.start_btn.configure(state="disabled")
            threading.Thread(target=self.move_logic, daemon=True).start()

    def stop_movement(self):
        self.is_running = False
        self.status_dot.configure(text="● Stopped", text_color="gray")
        self.start_btn.configure(state="normal")

if __name__ == "__main__":
    app = ProfessionalMouseApp()
    # Forces window to stay on top
    app.attributes('-topmost', True)
    app.mainloop()