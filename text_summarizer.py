"""A small extractive text summarizer built with Python's standard library.

The sentence-ranking method uses word frequency and inverse sentence frequency.
It selects representative sentences and returns them in their original order.
"""
from __future__ import annotations

import math
import re
import tkinter as tk
from collections import Counter
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

STOP_WORDS = set("""a an the and or but if while with of at by for from to in on into is are was were be been being am do does did has have had can could will would should may might must this that these those it its as about after before over under between through during not no nor so than then too very also we you they he she them their our your i me my us what which who when where how all any each every more most some such only other same own up out down off again further there here because until once""".split())


def split_sentences(text: str) -> list[str]:
    """Split text at sentence punctuation, while keeping common initials intact."""
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    # A compact rule-based splitter is adequate for a small offline classroom demo.
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", clean)
    return [piece.strip() for piece in pieces if piece.strip()]


def tokenize(sentence: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", sentence.lower())


def summarize(text: str, ratio: float = 0.30) -> str:
    """Return the highest-scoring sentences, preserving their source order."""
    sentences = split_sentences(text)
    if len(sentences) <= 1:
        return text.strip()

    tokens_by_sentence = [
        [word for word in tokenize(sentence) if word not in STOP_WORDS and len(word) > 1]
        for sentence in sentences
    ]
    all_words = [word for words in tokens_by_sentence for word in words]
    if not all_words:
        return sentences[0]

    frequency = Counter(all_words)
    max_frequency = max(frequency.values())
    sentence_count = len(sentences)
    sentence_presence = Counter(
        word for words in tokens_by_sentence for word in set(words)
    )
    weights = {
        word: (count / max_frequency)
        * (math.log((sentence_count + 1) / (sentence_presence[word] + 1)) + 1)
        for word, count in frequency.items()
    }

    scores: list[float] = []
    for words in tokens_by_sentence:
        scores.append(sum(weights[word] for word in words) / max(len(words), 1))

    selected_count = max(1, min(sentence_count, math.ceil(sentence_count * ratio)))
    chosen = set(sorted(range(sentence_count), key=lambda i: scores[i], reverse=True)[:selected_count])
    return " ".join(sentence for i, sentence in enumerate(sentences) if i in chosen)


class SummarizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Article & Notes Summarizer")
        root.geometry("1000x720")
        root.minsize(760, 560)
        root.configure(bg="#f4f7fb")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=8, font=("Segoe UI", 10))
        style.configure("TLabel", background="#f4f7fb", foreground="#18324b", font=("Segoe UI", 10))
        style.configure("Heading.TLabel", font=("Segoe UI", 21, "bold"), foreground="#12304a")

        header = ttk.Frame(root, padding=(22, 18, 22, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Article & Notes Summarizer", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(header, text="Offline extractive summarization using sentence importance scores").pack(anchor="w", pady=(4, 0))

        controls = ttk.Frame(root, padding=(22, 8, 22, 8))
        controls.pack(fill="x")
        ttk.Button(controls, text="Open .txt file", command=self.open_file).pack(side="left")
        ttk.Label(controls, text="Summary length:").pack(side="left", padx=(18, 6))
        self.ratio = tk.StringVar(value="30%")
        self.ratio_box = ttk.Combobox(controls, textvariable=self.ratio, values=("20%", "30%", "40%"), width=7, state="readonly")
        self.ratio_box.pack(side="left")
        ttk.Button(controls, text="Summarize", command=self.make_summary).pack(side="left", padx=10)
        ttk.Button(controls, text="Save summary", command=self.save_summary).pack(side="left")
        ttk.Button(controls, text="Clear", command=self.clear).pack(side="right")

        panes = ttk.Panedwindow(root, orient="vertical")
        panes.pack(fill="both", expand=True, padx=22, pady=(4, 14))
        source_frame = ttk.Frame(panes, padding=8)
        result_frame = ttk.Frame(panes, padding=8)
        panes.add(source_frame, weight=3)
        panes.add(result_frame, weight=2)
        ttk.Label(source_frame, text="SOURCE TEXT").pack(anchor="w", pady=(0, 5))
        ttk.Label(result_frame, text="SUMMARY").pack(anchor="w", pady=(0, 5))
        self.source = self._text_area(source_frame)
        self.output = self._text_area(result_frame)
        self.output.configure(state="disabled")

        self.status = tk.StringVar(value="Paste an article or notes, or open a .txt file.")
        ttk.Label(root, textvariable=self.status, padding=(22, 0, 22, 12)).pack(anchor="w")

    @staticmethod
    def _text_area(parent: ttk.Frame) -> tk.Text:
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True)
        text = tk.Text(wrap, wrap="word", undo=True, font=("Segoe UI", 11), padx=10, pady=9,
                       bg="white", fg="#203448", insertbackground="#203448", relief="flat")
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return text

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                text = Path(filename).read_text(encoding="utf-8")
                self.source.delete("1.0", "end")
                self.source.insert("1.0", text)
                self.status.set(f"Loaded: {Path(filename).name}")
            except OSError as exc:
                messagebox.showerror("Could not open file", str(exc))

    def make_summary(self) -> None:
        text = self.source.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Text required", "Paste or open some text first.")
            return
        result = summarize(text, int(self.ratio.get().replace("%", "")) / 100)
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", result)
        self.output.configure(state="disabled")
        source_words = len(tokenize(text))
        result_words = len(tokenize(result))
        reduction = round((1 - result_words / source_words) * 100) if source_words else 0
        self.status.set(f"{source_words} source words  |  {result_words} summary words  |  {reduction}% shorter")

    def save_summary(self) -> None:
        result = self.output.get("1.0", "end").strip()
        if not result:
            messagebox.showinfo("No summary", "Create a summary first.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            try:
                Path(filename).write_text(result + "\n", encoding="utf-8")
                self.status.set(f"Summary saved: {Path(filename).name}")
            except OSError as exc:
                messagebox.showerror("Could not save file", str(exc))

    def clear(self) -> None:
        self.source.delete("1.0", "end")
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self.status.set("Paste an article or notes, or open a .txt file.")


if __name__ == "__main__":
    app_root = tk.Tk()
    SummarizerApp(app_root)
    app_root.mainloop()
