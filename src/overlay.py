import customtkinter as ctk
import tkinter as tk
import chess
import win32gui
import win32con
import win32api

class SelectionOverlay(ctk.CTkToplevel):
    def __init__(self, master, on_select_callback):
        super().__init__(master)
        
        self.on_select_callback = on_select_callback
        
        self.attributes("-alpha", 0.3)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.configure(bg="black")
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.canvas = ctk.CTkCanvas(self, cursor="cross", bg="grey15", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Exit on Escape
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        # Calculate region
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(self.start_x - end_x)
        height = abs(self.start_y - end_y)
        
        if width > 50 and height > 50:
            self.on_select_callback({'left': left, 'top': top, 'width': width, 'height': height})
            self.destroy()
        else:
            # Too small, just reset
            pass

class ProjectionOverlay(ctk.CTkToplevel):
    def __init__(self, region):
        """
        region: {'left': int, 'top': int, 'width': int, 'height': int}
        """
        super().__init__()
        
        self.region = region
        # Position exactly over the board
        self.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")
        
        # Remove title bar
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Transparency setup for Windows
        # We use a specific color as the transparent key.
        self.transparent_color = "#000001" # Very nearly black
        self.configure(bg=self.transparent_color)
        self.wm_attributes("-transparentcolor", self.transparent_color)
        
        # Canvas for drawing
        self.canvas = tk.Canvas(self, bg=self.transparent_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Make click-through
        self.make_click_through()
        
    def make_click_through(self):
        hwnd = win32gui.GetParent(self.winfo_id())
        # If GetParent returns 0, try the window id directly (sometimes needed for Toplevels without parents)
        if hwnd == 0:
            hwnd = self.winfo_id()
            
        styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        styles = styles | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, styles)
        
    def draw_best_move(self, move):
        """
        Draw an arrow for the best move.
        move: python-chess Move object (e.g. e2e4)
        """
        self.canvas.delete("all")
        
        if not move:
            return

        # Calculate coordinates
        # File 0-7 (a-h), Rank 0-7 (1-8)
        # 0,0 is bottom-left (a1)
        
        sq_w = self.region['width'] / 8
        sq_h = self.region['height'] / 8
        
        start_sq = move.from_square
        end_sq = move.to_square
        
        # Convert to x,y (top-left origin for drawing)
        # File (x) is same
        # Rank (y) needs flip: Rank 0 is at bottom (y moves down) -> Rank 7 is top (y=0)
        # Rank r -> visual row (7-r)
        
        x1 = (chess.square_file(start_sq) + 0.5) * sq_w
        y1 = ((7 - chess.square_rank(start_sq)) + 0.5) * sq_h
        
        x2 = (chess.square_file(end_sq) + 0.5) * sq_w
        y2 = ((7 - chess.square_rank(end_sq)) + 0.5) * sq_h
        
        # Draw Arrow
        self.canvas.create_line(x1, y1, x2, y2, fill="#00ff00", width=6, arrow=tk.LAST, arrowshape=(16, 20, 6), tag="arrow")
        
        # Draw Circle on target
        r = min(sq_w, sq_h) * 0.2
        self.canvas.create_oval(x2-r, y2-r, x2+r, y2+r, outline="#00ff00", width=4, tag="arrow")

    def clear(self):
        self.canvas.delete("all")
