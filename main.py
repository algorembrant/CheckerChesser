import customtkinter as ctk
from src.gui import ChessApp

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = ChessApp()
    app.mainloop()
 