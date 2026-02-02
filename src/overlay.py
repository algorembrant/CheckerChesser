import customtkinter as ctk

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
