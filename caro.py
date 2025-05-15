import tkinter as tk
from tkinter import messagebox
import threading
import copy
import time

ROWS, COLS = 15, 15
CELL_SIZE = 40
BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE

PLAYER_X = 'X'  # Người chơi
PLAYER_O = 'O'  # AI
EMPTY = ' '

WIN_CONDITION = 5
MAX_DEPTH = 2  # Độ sâu Minimax

class CaroGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Caro Game - Player vs Player or AI")

        self.canvas = tk.Canvas(root, width=BOARD_WIDTH, height=BOARD_HEIGHT, bg="white")
        self.canvas.pack()

        self.status_label = tk.Label(root, text="Choose mode: Player vs Player or Player vs AI")
        self.status_label.pack()

        self.play_again_button = tk.Button(root, text="Play Again", command=self.play_again)
        self.play_again_button.pack()
        self.play_again_button.config(state='disabled')

        self.mode = None
        self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.history = []

        self.current_player = PLAYER_X
        self.game_over = False
        self.ai_thread = None

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.ask_game_mode()
        self.draw_board()

    def ask_game_mode(self):
        mode = messagebox.askquestion("Game Mode", "Do you want to play vs AI? (Yes for AI, No for 2 Player)")
        self.mode = 'ai' if mode == 'yes' else 'pvp'
        self.status_label.config(text=f"Mode: {'Player vs AI' if self.mode == 'ai' else 'Player vs Player'}")

    def draw_board(self):
        self.canvas.delete("all")
        for i in range(ROWS):
            for j in range(COLS):
                x0 = j * CELL_SIZE
                y0 = i * CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE
                self.canvas.create_rectangle(x0, y0, x1, y1, outline="black")
                if self.board[i][j] != EMPTY:
                    self.canvas.create_text(x0 + CELL_SIZE/2, y0 + CELL_SIZE/2,
                                            text=self.board[i][j], font=("Arial", 18, "bold"),
                                            fill="red" if self.board[i][j] == PLAYER_X else "blue")

    def on_canvas_click(self, event):
        if self.game_over:
            return

        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE

        if 0 <= row < ROWS and 0 <= col < COLS and self.board[row][col] == EMPTY:
            if self.mode == 'ai' and self.current_player == PLAYER_O:
                return
            self.make_move(row, col)
            if not self.game_over and self.mode == 'ai' and self.current_player == PLAYER_O:
                self.status_label.config(text="AI is thinking...")
                self.root.update()
                self.ai_thread = threading.Thread(target=self.ai_move)
                self.ai_thread.start()

    def make_move(self, row, col):
        if self.board[row][col] != EMPTY or self.game_over:
            return

        self.board[row][col] = self.current_player
        self.history.append((row, col))
        self.draw_board()

        if self.check_winner(row, col):
            self.status_label.config(text=f"Player {self.current_player} wins!")
            self.save_history()
            self.game_over = True
            self.play_again_button.config(state='normal')
            return

        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
        self.status_label.config(text=f"Turn: Player {self.current_player}")

    def ai_move(self):
        score, move = self.find_best_move()
        time.sleep(0.3)
        if move and not self.game_over:
            self.make_move(*move)
        else:
            self.status_label.config(text="Game Over - Draw")
            self.game_over = True
            self.play_again_button.config(state='normal')

    def play_again(self):
        self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.history.clear()
        self.current_player = PLAYER_X
        self.game_over = False
        self.play_again_button.config(state='disabled')
        self.status_label.config(text=f"Turn: Player {self.current_player}")
        self.draw_board()

    def save_history(self):
        with open("caro_history.txt", "a") as f:
            f.write(f"Winner: {self.current_player}\n")
            for r, c in self.history:
                f.write(f"{r},{c} -> {self.board[r][c]}\n")
            f.write("\n")

    def check_winner(self, row, col):
        def count_direction(dx, dy):
            count = 1
            for d in [1, -1]:
                x, y = row + d*dx, col + d*dy
                while 0 <= x < ROWS and 0 <= y < COLS and self.board[x][y] == self.current_player:
                    count += 1
                    x += d*dx
                    y += d*dy
            return count

        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            if count_direction(dx, dy) >= WIN_CONDITION:
                return True
        return False

    def find_best_move(self):
        def minimax(board, depth, alpha, beta, maximizing_player):
            if depth == 0 or self.is_terminal(board):
                return self.evaluate_board(board), None

            if maximizing_player:
                max_eval = float('-inf')
                best_move = None
                for r, c in self.get_candidate_moves(board):
                    board[r][c] = PLAYER_O
                    eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
                    board[r][c] = EMPTY
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = (r, c)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                return max_eval, best_move
            else:
                min_eval = float('inf')
                best_move = None
                for r, c in self.get_candidate_moves(board):
                    board[r][c] = PLAYER_X
                    eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
                    board[r][c] = EMPTY
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = (r, c)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                return min_eval, best_move

        return minimax(copy.deepcopy(self.board), MAX_DEPTH, float('-inf'), float('inf'), True)

    def get_candidate_moves(self, board):
        candidates = set()
        for i in range(ROWS):
            for j in range(COLS):
                if board[i][j] == EMPTY and self.has_neighbor(board, i, j):
                    candidates.add((i, j))
        if not candidates:
            candidates.add((ROWS // 2, COLS // 2))
        return list(candidates)

    def has_neighbor(self, board, row, col):
        for i in range(-2, 3):
            for j in range(-2, 3):
                r, c = row + i, col + j
                if 0 <= r < ROWS and 0 <= c < COLS and board[r][c] != EMPTY:
                    return True
        return False

    def is_terminal(self, board):
        for i in range(ROWS):
            for j in range(COLS):
                if board[i][j] != EMPTY:
                    player = board[i][j]
                    if self.check_winner_at(board, i, j, player):
                        return True
        return False

    def check_winner_at(self, board, row, col, player):
        def count_direction(dx, dy):
            count = 1
            for d in [1, -1]:
                x, y = row + d*dx, col + d*dy
                while 0 <= x < ROWS and 0 <= y < COLS and board[x][y] == player:
                    count += 1
                    x += d*dx
                    y += d*dy
            return count

        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            if count_direction(dx, dy) >= WIN_CONDITION:
                return True
        return False

    def evaluate_board(self, board):
        def score_line(line, player):
            opponent = PLAYER_X if player == PLAYER_O else PLAYER_O
            score = 0
            patterns = {
                player*5: 1000000,
                ' ' + player*4 + ' ': 500000,
                player*4 + ' ': 100000,
                ' ' + player*4: 100000,
                player*3 + ' ': 10000,
                ' ' + player*3: 10000,
                ' ' + player*3 + ' ': 20000,
                player*2 + ' ': 1000,
                ' ' + player*2: 1000,
                ' ' + player*2 + ' ': 1500,
            }
            opponent_patterns = {
                opponent*5: -1000000,
                ' ' + opponent*4 + ' ': -500000,
                opponent*4 + ' ': -100000,
                ' ' + opponent*4: -100000,
                opponent*3 + ' ': -10000,
                ' ' + opponent*3: -10000,
                ' ' + opponent*3 + ' ': -20000,
                opponent*2 + ' ': -1000,
                ' ' + opponent*2: -1000,
                ' ' + opponent*2 + ' ': -1500,
            }
            for pattern, val in patterns.items():
                score += line.count(pattern) * val
            for pattern, val in opponent_patterns.items():
                score += line.count(pattern) * val
            return score

        total_score = 0

        for i in range(ROWS):
            row_str = ''.join(board[i])
            total_score += score_line(row_str, PLAYER_O)

        for j in range(COLS):
            col_str = ''.join(board[i][j] for i in range(ROWS))
            total_score += score_line(col_str, PLAYER_O)

        for k in range(-ROWS + 1, COLS):
            diag1 = ''.join(board[i][i - k] for i in range(max(k, 0), min(ROWS, COLS + k)))
            total_score += score_line(diag1, PLAYER_O)

        for k in range(ROWS + COLS - 1):
            diag2 = ''.join(board[i][k - i] for i in range(max(0, k - COLS + 1), min(ROWS, k + 1)) if 0 <= k - i < COLS)
            total_score += score_line(diag2, PLAYER_O)

        return total_score

if __name__ == '__main__':
    root = tk.Tk()
    game = CaroGame(root)
    root.mainloop()
