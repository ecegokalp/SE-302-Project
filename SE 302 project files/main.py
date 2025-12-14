# main.py
import tkinter as tk
from gui import ExamSchedulerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ExamSchedulerApp(root)
    root.mainloop()