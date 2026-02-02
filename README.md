# CheckerChesser

CheckerChesser is a powerful chess utility application that combines a local chess analysis board with real-time screen monitoring capabilities. It is designed to assist players in analyzing games, finding best moves, and testing positions.

<img width="1354" height="680" alt="image" src="https://github.com/user-attachments/assets/dc902cf0-a31c-4abf-8f85-9dda475eaac8" />
<img width="1323" height="719" alt="image" src="https://github.com/user-attachments/assets/1dc5c833-bf2b-4562-a5f7-8630c72fefab" />
<img width="1347" height="675" alt="image" src="https://github.com/user-attachments/assets/4005f25a-b1ef-42a6-a732-cad55ea27a32" />

<img width="587" height="187" alt="image" src="https://github.com/user-attachments/assets/85ca3a62-fdd3-4e7d-ad34-058520587279" />




## Core Features

### 1. Local Analysis Board
- **Full Chess Engine Integration**: Powered by **Stockfish**, one of the strongest chess engines in the world.
- **Interactive Board**: Move pieces, flip the board, and play against the AI.
- **Dual Player Mode**: Play locally against a friend or test moves for both sides.
- **Analysis Visualization**: Visualize top engine moves with colored arrows indicating strength and threat.

### 2. Board Editor
- **Custom Scenario Setup**: Manually place any piece on the board to recreate specific game states.
- **Automation Control**: The engine is strictly disabled during editing to prevent interference.
- **Piece Palette**: Intuitive drag-and-drop style interface (click-to-place) for all piece types.

### 3. Screen Analysis (Vision)
- **Real-time Monitoring**: Define a region on your screen to monitor a live chess board (e.g., from a website or video).
- **Auto-Calibration**: The application automatically detects the board structure from a standard starting position.
- **Live suggestions**: As moves are played on the screen, the app updates the internal board and suggests the best response instantly.

### 4. Turn Swapping & Customization
- **First Move Control**: Choose whether White or Black moves first (useful for variants or playing as Black from the start).
- **Play As**: Switch sides to play as Black or White against the engine.

---

## Technical Architecture & Machine Learning

### Is it based on Machine Learning?
**Yes and No.**

1.  **Chess Intelligence (Yes)**: The application utilizes **Stockfish**, which employs **NNUE (Efficiently Updatable Neural Network)** technology. This is a form of machine learning where a neural network attempts to evaluate positions, providing superior performance over classical hand-crafted evaluation functions.
2.  **Vision System (No)**: The screen analysis feature uses **Computer Vision** techniques (specifically Template Matching and Mean Squared Error comparisons), not Deep Learning. It requires a clear view of a 2D chess board to "calibrate" and match pieces against a known template.

---

## Installation

1.  **Prerequisites**:
    - Python 3.8+
    - Stockfish Engine (Executable must be placed in the project folder or specified in config).

2.  **Dependencies**:
    Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
    *(Requires: customtkinter, python-chess, mss, opencv-python, numpy)*

3.  **Setup (Stockfish Guide)**:
    This application requires the **Stockfish Chess Engine** to function.
    
    **Step-by-Step Guide:**
    1.  **Download**: Visit the official Stockfish website: [https://stockfishchess.org/download/](https://stockfishchess.org/download/)
    2.  **Select Version**: Download the version suitable for your system (usually "Windows (AVX2)" or "Windows (x64-modern)").
    3.  **Extract**: Unzip the downloaded folder. Inside, you will find an executable file (e.g., `stockfish-windows-x86-64-avx2.exe`).
    4.  **Rename**: Rename this file to simply `stockfish.exe`.
    5.  **Place File**: Move `stockfish.exe` directly into the `CheckerChesser` project folder.
    
    **Correct Folder Structure:**
    ```text
    CheckerChesser/
    ├── src/
    ├── main.py
    ├── requirements.txt
    ├── stockfish.exe  <-- PLACE HERE
    └── README.md
    ```

---

## Usage Guide

### Starting the App
Run the main script:
```bash
python main.py
```

### Modes

#### Local Game
- **Play**: Drag and drop or click squares to move pieces.
- **Analysis Mode**: Toggle `Analysis Mode` switch to see Best Move arrows overlaid on the board.
- **Two Player**: Toggle `Two Player Mode` to control both sides manually.
- **Flip Board**: Click `⟳ Flip Board` to rotate the view.

#### Board Editor
1. Toggle `Edit Mode` switch to **ON**.
2. A palette of pieces (White/Black) and a Trash Bin will appear.
3. **Left Click** a piece in the palette to select it.
4. **Left Click** any square on the board to place that piece.
5. Select the **Trash Bin** and click a square to clear it.
6. Toggle `Edit Mode` **OFF** to resume play.
   > **Note**: AI logic is paused while Edit Mode is active.

#### Screen Analysis
1. Click `Screen Analysis` in the sidebar.
2. An overlay window will appear. Drag to select the area of the chess board you want to monitor.
3. **Important**: Ensure the board on screen is at the **Starting Position** when you start monitoring. The tool needs this to calibrate piece textures.
4. Once calibrated, the app will track moves and display the best engine move in real-time.

---

## Troubleshooting

- **Engine Not Found**: Ensure `stockfish.exe` is in the folder.
- **Vision Not Working**: Make sure the board on screen is not obstructed and matches standard 2D chess pieces. Glare or unusual piece sets may confuse the template matcher.
- **Performance**: High `Best Moves` count or deep analysis may use significant CPU resources. Lower the number of moves if the app lags.



## Citation

```bibtex
@misc{CheckerChesser,
  author = {algorembrant},
  title = {CheckerChesser},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/algorembrant/CheckerChesser}},
}
```
