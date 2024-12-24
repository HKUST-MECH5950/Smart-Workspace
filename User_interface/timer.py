import time
import tkinter as tk

class timer:
    def __init__(self, interval):
        if interval is tk.StringVar:
            raise TypeError(f"interval must be a tk.StringVar but got {type(interval)}.")
        self.interval = interval
        self.last_update = time.time()
    
    def check(self, now):
        if (now - self.last_update) > int(self.interval.get()):
            self.last_update = now
            return True
        else:
            return False