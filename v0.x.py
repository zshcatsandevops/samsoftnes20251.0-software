#!/usr/bin/env python3
"""
SamsoftEmu NES v1.0 (Tkinter GUI Frontend with Custom Stub)
- Drop-in replacement for nes_py so Pyright stops complaining
- GUI runs even without a real emulator
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import numpy as np

# ---------------- Custom Stub Emulator ----------------
class NES:
    def __init__(self, rom_path=None):
        self.rom_path = rom_path
        self.frame_count = 0

    def load_rom(self, rom_path):
        self.rom_path = rom_path
        print(f"[NES_STUB] Loaded ROM: {rom_path}")

    def step(self, action=0):
        """Return a dummy frame: (240, 256, 3) numpy array"""
        self.frame_count += 1
        h, w = 240, 256
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Simple animated gradient
        frame[:, :, 0] = (self.frame_count * 2) % 255  # pulse red
        frame[:, :, 1] = np.linspace(0, 255, w, dtype=np.uint8)[None, :]
        frame[:, :, 2] = np.linspace(0, 255, h, dtype=np.uint8)[:, None]

        return frame, 0, False, {}

    def reset(self):
        self.frame_count = 0
        print("[NES_STUB] Reset emulator")

    def shutdown(self):
        print("[NES_STUB] Emulator shutdown")


# ---------------- GUI Frontend ----------------
class SamsoftEmuNESGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SamsoftEmu NES v1.0")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")

        # Emulator state
        self.rom_path = None
        self.is_running = False
        self.is_paused = False
        self.emulator = None
        self.fps_counter = 0
        self.fps_time = time.time()
        self.fps = 0

        # Display config
        self.nes_width = 256
        self.nes_height = 240
        self.scale = 2

        # UI setup
        self.create_menu()
        self.create_main_area()
        self.create_statusbar()

        self.update_fps()

    # ---------- UI ----------
    def create_menu(self):
        menubar = tk.Menu(self.root, bg="#2d2d2d", fg="white", tearoff=0)

        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        file_menu.add_command(label="Open ROM", command=self.open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        emu_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        emu_menu.add_command(label="Run", command=self.run_emulator)
        emu_menu.add_command(label="Pause", command=self.pause_emulator)
        emu_menu.add_command(label="Stop", command=self.stop_emulator)
        menubar.add_cascade(label="Emulation", menu=emu_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def create_main_area(self):
        self.display_canvas = tk.Canvas(
            self.root,
            width=self.nes_width * self.scale,
            height=self.nes_height * self.scale,
            bg="black"
        )
        self.display_canvas.pack(fill="both", expand=True)

        self.console = scrolledtext.ScrolledText(self.root, wrap=tk.WORD,
            font=("Consolas", 9), bg="#0d0d0d", fg="#00ff00", height=8)
        self.console.pack(fill="x")

        self.placeholder_img = Image.new("RGB", (self.nes_width, self.nes_height), "black")
        self.tk_img = ImageTk.PhotoImage(self.placeholder_img.resize(
            (self.nes_width*self.scale, self.nes_height*self.scale), Image.NEAREST))
        self.display_image = self.display_canvas.create_image(
            self.nes_width, self.nes_height, image=self.tk_img)

    def create_statusbar(self):
        bar = tk.Frame(self.root, bg="#2d2d2d")
        bar.pack(side=tk.BOTTOM, fill="x")
        self.status_var = tk.StringVar(value="Ready – No ROM")
        tk.Label(bar, textvariable=self.status_var, bg="#2d2d2d", fg="white").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value="FPS: --")
        tk.Label(bar, textvariable=self.fps_var, bg="#2d2d2d", fg="white").pack(side=tk.RIGHT)

    # ---------- Emulator ----------
    def open_rom(self):
        rom = filedialog.askopenfilename(title="Select NES ROM", filetypes=[("NES ROM", "*.nes")])
        if rom:
            self.rom_path = rom
            self.log(f"[ROM] Loaded {os.path.basename(rom)}")
            self.status_var.set(f"Loaded ROM: {os.path.basename(rom)}")

    def emulation_loop(self):
        self.emulator = NES(self.rom_path)
        self.emulator.load_rom(self.rom_path or "dummy.nes")

        while self.is_running and not self.is_paused:
            frame, _, _, _ = self.emulator.step(0)
            self.root.after(0, self.update_display, frame)
            time.sleep(1/60)

        self.log("[EMU] Loop ended")

    def run_emulator(self):
        if self.is_running:
            self.is_paused = False
            self.log("[EMU] Resumed")
            return
        self.is_running, self.is_paused = True, False
        threading.Thread(target=self.emulation_loop, daemon=True).start()
        self.status_var.set("Running")

    def pause_emulator(self):
        self.is_paused = True
        self.status_var.set("Paused")
        self.log("[EMU] Paused")

    def stop_emulator(self):
        self.is_running = False
        self.status_var.set("Stopped")
        self.log("[EMU] Stopped")

    # ---------- Display ----------
    def update_display(self, frame):
        img = Image.fromarray(frame)
        scaled = img.resize((self.nes_width*self.scale, self.nes_height*self.scale), Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(scaled)
        self.display_canvas.itemconfig(self.display_image, image=self.tk_img)
        self.fps_counter += 1

    def update_fps(self):
        now = time.time()
        if now - self.fps_time >= 1:
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.fps_time = now
            self.fps_var.set(f"FPS: {self.fps}")
        self.root.after(1000, self.update_fps)

    # ---------- Logging ----------
    def log(self, msg):
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)

    def show_about(self):
        messagebox.showinfo("About",
            "SamsoftEmu NES v1.0\n"
            "Custom stub backend (no real emulation).\n"
            "Frames are dummy gradients.\n"
            "Future-ready: replace NES class with real backend later.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SamsoftEmuNESGUI(root)
    root.mainloop()
