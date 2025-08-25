import tkinter as tk
from tkinter import messagebox
import random
import os

# =========================
# CONFIG
# =========================
WORD_LENGTH = 5
MAX_ATTEMPTS = 6
WORDS_FILE = "words.txt"

# Colors
COLOR_BG = "#121213"
COLOR_TEXT = "white"
COLOR_EMPTY = "#3a3a3c"
COLOR_CORRECT = "#538d4e"
COLOR_PRESENT = "#b59f3b"
COLOR_ABSENT = "#3a3a3c"
COLOR_KEY_DEFAULT = "#818384"
COLOR_KEY_TEXT = "white"


def load_words(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found! Please make sure words.txt is in the same folder.")
    with open(file_path, "r") as f:
        words = [w.strip().upper() for w in f.readlines() if len(w.strip()) == WORD_LENGTH]
    return words


class WordleGame(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Wordle Clone")
        self.configure(bg=COLOR_BG)

        # Load words & choose secret
        self.word_list = load_words(WORDS_FILE)
        self.secret_word = random.choice(self.word_list)

        # Game state
        self.current_row = 0
        self.current_col = 0
        self.grid_letters = [["" for _ in range(WORD_LENGTH)] for _ in range(MAX_ATTEMPTS)]
        self.keyboard_state = {}  # track colors for keys

        # =========================
        # Create UI
        # =========================
        self.cells = []
        for r in range(MAX_ATTEMPTS):
            row = []
            for c in range(WORD_LENGTH):
                lbl = tk.Label(
                    self,
                    text="",
                    width=4,
                    height=2,
                    font=("Helvetica", 24, "bold"),
                    relief="solid",
                    bg=COLOR_BG,
                    fg=COLOR_TEXT,
                    bd=2
                )
                lbl.grid(row=r, column=c, padx=5, pady=5)
                row.append(lbl)
            self.cells.append(row)

        # On-screen keyboard
        self.keyboard_frame = tk.Frame(self, bg=COLOR_BG)
        self.keyboard_frame.grid(row=MAX_ATTEMPTS + 1, column=0, columnspan=WORD_LENGTH, pady=20)

        self.keyboard_buttons = {}
        layout = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for r, keys in enumerate(layout):
            row_frame = tk.Frame(self.keyboard_frame, bg=COLOR_BG)
            row_frame.pack(pady=3)
            if r == 2:  # add Enter first
                enter_btn = self.make_key(row_frame, "ENTER", wide=True, command=self.submit_guess)
                enter_btn.pack(side="left", padx=2)

            for k in keys:
                btn = self.make_key(row_frame, k, wide=False, command=lambda ch=k: self.handle_virtual_key(ch))
                btn.pack(side="left", padx=2)
                self.keyboard_buttons[k] = btn

            if r == 2:  # add Backspace last
                back_btn = self.make_key(row_frame, "⌫", wide=True, command=lambda: self.handle_virtual_key("BackSpace"))
                back_btn.pack(side="left", padx=2)

        # Key bindings
        self.bind("<Key>", self.handle_key)

    # Utility for making keyboard keys
    # def make_key(self, parent, label, wide=False, command=None):
    #     return tk.Button(
    #         parent,
    #         text=label,
    #         width=6 if wide else 4,
    #         height=2,
    #         font=("Helvetica", 12, "bold"),
    #         bg=COLOR_KEY_DEFAULT,
    #         fg=COLOR_KEY_TEXT,
    #         relief="flat",
    #         command=command,
    #         bd=0,
    #         highlightthickness=0
    #     )

    # ==============
    # Input handling
    # ==============
    def handle_virtual_key(self, key):
        if key == "BackSpace":
            event = type("Event", (), {"keysym": "BackSpace", "char": ""})
        elif key == "ENTER":
            event = type("Event", (), {"keysym": "Return", "char": ""})
        else:
            event = type("Event", (), {"keysym": key, "char": key})
        self.handle_key(event)

    def handle_key(self, event):
        if self.current_row >= MAX_ATTEMPTS:
            return  # Game over

        if event.keysym == "Return":
            self.submit_guess()
        elif event.keysym == "BackSpace":
            if self.current_col > 0:
                self.current_col -= 1
                self.grid_letters[self.current_row][self.current_col] = ""
                self.cells[self.current_row][self.current_col].config(text="")
        elif event.char.isalpha() and len(event.char) == 1:
            if self.current_col < WORD_LENGTH:
                letter = event.char.upper()
                self.grid_letters[self.current_row][self.current_col] = letter
                self.cells[self.current_row][self.current_col].config(text=letter)
                self.current_col += 1

    # ==============
    # Guess check
    # ==============
    def submit_guess(self):
        guess = "".join(self.grid_letters[self.current_row])
        if len(guess) != WORD_LENGTH:
            return  # incomplete word
        if guess not in self.word_list:
            messagebox.showwarning("Invalid", "Not in word list!")
            return

        self.reveal_guess(guess)

    def reveal_guess(self, guess):
        """Animate revealing guess colors."""
        secret = self.secret_word
        colors = [COLOR_ABSENT] * WORD_LENGTH
        secret_counts = {}

        # First pass: correct positions
        for i in range(WORD_LENGTH):
            if guess[i] == secret[i]:
                colors[i] = COLOR_CORRECT
            else:
                secret_counts[secret[i]] = secret_counts.get(secret[i], 0) + 1

        # Second pass: misplaced letters
        for i in range(WORD_LENGTH):
            if colors[i] == COLOR_CORRECT:
                continue
            if guess[i] in secret_counts and secret_counts[guess[i]] > 0:
                colors[i] = COLOR_PRESENT
                secret_counts[guess[i]] -= 1

        # Animate flip reveal
        def animate_cell(i, step=0):
            cell = self.cells[self.current_row][i]
            if step == 0:  # shrink
                cell.config(font=("Helvetica", 1, "bold"))
                self.after(100, lambda: animate_cell(i, 1))
            elif step == 1:  # reveal color
                cell.config(bg=colors[i])
                cell.config(font=("Helvetica", 24, "bold"))

                # Update keyboard
                self.update_keyboard(guess[i], colors[i])

                if i < WORD_LENGTH - 1:
                    self.after(150, lambda: animate_cell(i + 1, 0))
                else:
                    self.after(200, self.check_game_end, guess)

        animate_cell(0)

    def update_keyboard(self, letter, color):
        if letter not in self.keyboard_buttons:
            return
        current = self.keyboard_state.get(letter)
        priority = {COLOR_ABSENT: 0, COLOR_PRESENT: 1, COLOR_CORRECT: 2}
        if not current or priority[color] > priority[current]:
            self.keyboard_state[letter] = color
            self.keyboard_buttons[letter].config(
                bg=color,
                fg="white"
            )

    def check_game_end(self, guess):
        if guess == self.secret_word:
            messagebox.showinfo("Wordle", "🎉 You guessed it!")
            self.current_row = MAX_ATTEMPTS
            return

        self.current_row += 1
        self.current_col = 0

        if self.current_row == MAX_ATTEMPTS:
            messagebox.showinfo("Wordle", f"Game Over! The word was: {self.secret_word}")

    # Utility for making keyboard keys
    # Utility for making keyboard keys
    def make_key(self, parent, label, wide=False, command=None):
        lbl = tk.Label(
            parent,
            text=label,
            width=6 if wide else 4,
            height=2,
            font=("Helvetica", 12, "bold"),
            bg=COLOR_KEY_DEFAULT,
            fg=COLOR_KEY_TEXT,
            relief="raised",
            bd=2
        )
        lbl.bind("<Button-1>", lambda e: command() if command else None)
        return lbl


if __name__ == "__main__":
    app = WordleGame()
    app.mainloop()
