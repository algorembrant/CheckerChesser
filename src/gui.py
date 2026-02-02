import customtkinter as ctk
import threading
import chess
import time
from src.game_state import GameState
from src.engine import EngineHandler
from src.board_ui import BoardUI
from src.overlay import SelectionOverlay
from src.vision import VisionHandler

class ChessApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("CheckerChesser")
        self.geometry("900x650")
        
        # Initialize Logic
        self.game_state = GameState()
        self.engine = EngineHandler()
        self.vision = VisionHandler()
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Content
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="CheckerChesser", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.new_game_btn = ctk.CTkButton(self.sidebar, text="New Local Game", command=self.start_local_game)
        self.new_game_btn.grid(row=1, column=0, padx=20, pady=10)
        
        self.analysis_btn = ctk.CTkButton(self.sidebar, text="Screen Analysis", command=self.start_screen_analysis)
        self.analysis_btn.grid(row=2, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Idle", anchor="w")
        self.status_label.grid(row=3, column=0, padx=20, pady=(20, 0), sticky="ew")

        # Content Area
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Init Engine
        self.init_engine_thread()
        
        # Current Board View
        self.board_ui = None
        self.start_local_game()

    def init_engine_thread(self):
        def _init():
            success, msg = self.engine.initialize_engine()
            self.after(0, lambda: self.status_label.configure(text="Engine: Ready" if success else "Engine: Not Found"))
            if not success:
                print(msg)
        threading.Thread(target=_init, daemon=True).start()

    def start_local_game(self):
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.game_state.reset()
        self.board_ui = BoardUI(self.content_frame, self.game_state, width=600, height=600)
        self.board_ui.grid(row=0, column=0, padx=20, pady=20)
        
        # Analysis Controls
        self.analysis_var = ctk.BooleanVar(value=False)
        self.analysis_switch = ctk.CTkSwitch(self.content_frame, text="Analysis Mode (ML Preview)", 
                                             variable=self.analysis_var, command=self.toggle_analysis)
        self.analysis_switch.grid(row=1, column=0, pady=10)
        
        # Bind move event
        self.bind("<<MoveMade>>", self.on_move_made)
        self.status_label.configure(text="Mode: Local Play")

    def start_screen_analysis(self):
        self.status_label.configure(text="Select Region...")
        self.withdraw() # Hide main win
        
        # Function called when region is selected
        def on_selection(region):
            self.deiconify() # Show main win
            self.process_screen_region(region)

        SelectionOverlay(self, on_selection)

    def process_screen_region(self, region):
        self.status_label.configure(text="Analyzing...")
        
        # Placeholder for analysis view
        for widget in self.content_frame.winfo_children():
             widget.destroy()
        
        analysis_label = ctk.CTkLabel(self.content_frame, text=f"Analyzing Region: {region}...\n(Vision Not Fully Implemented)", font=("Arial", 16))
        analysis_label.grid(row=0, column=0)
        
        def _analyze():
            # 1. Capture and Recognize
            img = self.vision.capture_screen(region)
            fen = self.vision.get_fen_from_image(img) # currently dummy
            
            # 2. Engine prediction
            best_move = self.engine.get_best_move(fen) # Fen is valid dummy
            
            # 3. Update UI
            self.after(0, lambda: self.show_analysis_result(fen, best_move))

        threading.Thread(target=_analyze, daemon=True).start()

    def show_analysis_result(self, fen, best_move):
        self.status_label.configure(text=f"Best Move: {best_move}")
        
        for widget in self.content_frame.winfo_children():
             widget.destroy()

        result_label = ctk.CTkLabel(self.content_frame, text=f"Suggested Move: {best_move}", font=("Arial", 24, "bold"))
        result_label.grid(row=0, column=0, pady=20)
        
        fen_label = ctk.CTkLabel(self.content_frame, text=f"FEN detected: {fen}", wraplength=400)
        fen_label.grid(row=1, column=0, pady=10)
        
    def toggle_analysis(self):
        if self.analysis_var.get():
            self.update_analysis()
        else:
            self.board_ui.canvas.delete("arrow")

    def update_analysis(self):
        if not self.analysis_var.get():
            return
            
        def _analyze():
            fen = self.game_state.get_fen()
            # Fetch top 3 moves
            top_moves = self.engine.get_top_moves(fen, limit=3)
            self.after(0, lambda: self.board_ui.display_analysis(top_moves))
            
        threading.Thread(target=_analyze, daemon=True).start()

    def on_move_made(self, event=None):
        # Check for game over
        if self.game_state.is_game_over():
            result = self.game_state.board.result()
            self.status_label.configure(text=f"Game Over: {result}")
            return

        # If it's AI turn (Black), make move. 
        # For this demo, let's say "Local Game" is Human vs Human if we want to use Analysis freely?
        # Or Human vs AI. The original code suggested Human vs AI (AI move triggered).
        # Let's keep Human vs AI but allow analysis.
        
        if self.analysis_var.get():
            self.update_analysis()

        if self.game_state.board.turn == chess.BLACK:
            # Trigger AI move
            self.status_label.configure(text="Thinking...")
            threading.Thread(target=self.make_ai_move, daemon=True).start()
        else:
            self.status_label.configure(text="Your Turn")

    def make_ai_move(self):
        # AI plays best move
        best_move = self.engine.get_best_move(self.game_state.get_fen())
        if best_move:
            self.game_state.board.push(best_move)
            self.after(0, self.update_board_after_ai)
        else:
            self.after(0, lambda: self.status_label.configure(text="Engine Error"))

    def update_board_after_ai(self):
        self.board_ui.draw_board()
        self.status_label.configure(text="Your Turn")
        
        if self.analysis_var.get():
            self.update_analysis()
            
        if self.game_state.is_game_over():
            self.status_label.configure(text=f"Game Over: {self.game_state.board.result()}")
