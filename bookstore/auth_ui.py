import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from .integrations import Authentication
from .models import Account
from .storage import Store
from .voice import PHRASE, VoiceClassifier, record_sample


def voice_session(parent, store: Store, *, register: bool = False) -> Account | None:
    title = "Register by voice" if register else "Sign in by voice"
    classifier = VoiceClassifier(store)
    try:
        if register:
            username = simpledialog.askstring(title, "Choose a username.", parent=parent)
            if username is None:
                return None
            samples = []
            for index in range(1, 4):
                sample = capture(parent, title, f"Sample {index} of 3")
                if sample is None:
                    return None
                samples.append(sample)
            classifier.enroll(username, samples)
            messagebox.showinfo(title, "Account created. Choose Sign in to test it.", parent=parent)
            return None
        sample = capture(parent, title, "Voice sample")
        return Authentication(store, classifier).sign_in("voice", sample) if sample else None
    except (OSError, ValueError, PermissionError, sqlite3.Error) as error:
        messagebox.showerror(title, str(error), parent=parent)
        return None


def capture(parent, title: str, label: str) -> bytes | None:
    if not messagebox.askokcancel(
        title, f"{label}\n\nSay the following when the recording prompt appears:\n{PHRASE}",
        parent=parent,
    ):
        return None

    window = tk.Toplevel(parent)
    window.title(title)
    window.transient(parent)
    ttk.Label(window, text=f"Recording for 3 seconds…\n{PHRASE}", padding=18).pack()
    window.update()
    try:
        return record_sample()
    finally:
        window.destroy()
