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
        self.resizable(False, False)
        self.configure(bg="#121213")

        # Load words & choose secret
        self.word_list = load_words(WORDS_FILE)
        self.secret_word = random.choice(self.word_list)

        # Keep track of guesses
        self.current_row = 0
        self.current_col = 0
        self.grid_letters = [["" for _ in range(WORD_LENGTH)] for _ in range(MAX_ATTEMPTS)]

        # GUI grid
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
                    bg="#121213",
                    fg="white",
                    bd=2
                )
                lbl.grid(row=r, column=c, padx=5, pady=5)
                row.append(lbl)
            self.cells.append(row)

        # Key bindings
        self.bind("<Key>", self.handle_key)

    def handle_key(self, event):
        """Handle keyboard input."""
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

    def submit_guess(self):
        """Check the guess and update UI colors."""
        guess = "".join(self.grid_letters[self.current_row])
        if len(guess) != WORD_LENGTH:
            return  # incomplete word

        guess = guess.upper()
        secret = self.secret_word

        # Coloring logic
        colors = ["#3a3a3c"] * WORD_LENGTH  # default gray
        secret_counts = {}

        # First pass: correct positions
        for i in range(WORD_LENGTH):
            if guess[i] == secret[i]:
                colors[i] = "#538d4e"  # green
            else:
                secret_counts[secret[i]] = secret_counts.get(secret[i], 0) + 1

        # Second pass: check for misplaced letters
        for i in range(WORD_LENGTH):
            if colors[i] == "#538d4e":  # already correct
                continue
            if guess[i] in secret_counts and secret_counts[guess[i]] > 0:
                colors[i] = "#b59f3b"  # yellow
                secret_counts[guess[i]] -= 1

        # Apply colors
        for i in range(WORD_LENGTH):
            self.cells[self.current_row][i].config(bg=colors[i])

        # Check win/lose condition
        if guess == secret:
            messagebox.showinfo("Wordle", "🎉 You guessed it!")
            self.current_row = MAX_ATTEMPTS  # lock game
            return

        self.current_row += 1
        self.current_col = 0

        if self.current_row == MAX_ATTEMPTS:
            messagebox.showinfo("Wordle", f"Game Over! The word was: {secret}")


if __name__ == "__main__":
    app = WordleGame()
    app.mainloop()
