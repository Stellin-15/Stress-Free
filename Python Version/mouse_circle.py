import tkinter as tk 
import time
import math
import pyautogui 
import threading
import keyboard  # For global hotkeys

class MouseApp:
    def __init__(self, root):
        self.root = root 
        self.root.title("Mouse Circle Mover")
        self.root.geometry("500x500")
        
        self.is_running = False # variable to stop the loop 
     
        # UI Elements 
        
        self.label = tk.Label(root, text = "Mouse Controller", font=("Helvetica", 16))
        self.label.pack(pady = 10)
        
        self.instruction = tk.Label(root, text = "Shortcut: Press 'ESC' to Stop.\nClick 'Continue Work' to stop.", font=("Helvetica",12))
        self.instruction.pack(pady = 10)
        
        self.start_button = tk.Button(root, text = "Start Free Time !", font = ("Helvetica", 14), command = self.start_moving, bg = "green", fg = "white", width = 15)
        self.start_button.pack(pady = 10)
        
        self.stop_button = tk.Button(root, text = "Continue Work!", font = ("Helvetica", 14), command = self.stop_movement, bg = "red", fg = "white", width = 15)
        self.stop_button.pack(pady = 10)
        
        self.status = tk.Label(root, text = "Status: Idle", fg="blue")
        self.status.pack(pady = 10)
        
        #also done to ensure that it can used when the window is minimized
        keyboard.add_hotkey('esc', self.stop_movement)  # Bind ESC key to stop movement
    
    
    def move_logic(self):
        
        radius = 150
        stops = 60 
        
        cx, cy = pyautogui.position() # get current mouse position
        
        while self.is_running:
            for i in range(stops):
                if not self.is_running:
                    break
                
                angle = 2 * math.pi * i / stops
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                
                
                pyautogui.moveTo(x, y)
            
            time.sleep(0.05) # wait before starting the next circle
            
    def start_moving(self):
        if not self.is_running:
            self.is_running = True
            self.status.config(text="Status: Moving in Circle",fg = "green")
            
            threading.Thread(target=self.move_logic, daemon=True).start()  # Use a thread so the GUI doesn't freeze
    
    def stop_movement(self):
        if self.is_running:
            self.is_running = False
            self.status.config(text="Status: Idle", fg="blue") 


if __name__ == "__main__":
    root = tk.Tk()
    app = MouseApp(root)
    root.mainloop()  
        