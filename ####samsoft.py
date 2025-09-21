#!/usr/bin/env python3
"""
SamsoftEmu NES v1.0 (Tkinter GUI Frontend)
Frontend for a future FCEUX-class emulator.
Optimized version with better performance and UI
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

class SamsoftEmuNESGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SamsoftEmu NES v1.0")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")
        self.root.minsize(600, 400)  # Minimum window size

        # Emulator state placeholders
        self.rom_path = None
        self.is_running = False
        self.version = "1.0"

        # UI setup
        self.create_menu()
        self.create_toolbar()
        self.create_main_area()
        self.create_statusbar()

        # Configure grid weights for proper resizing
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def create_menu(self):
        menubar = tk.Menu(self.root, bg="#2d2d2d", fg="white", tearoff=0)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        file_menu.add_command(label="Open ROM", command=self.open_rom, accelerator="Ctrl+O")
        file_menu.add_command(label="Reset Emulator", command=self.reset_emulator, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        # Emulation menu
        emulation_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        emulation_menu.add_command(label="Run", command=self.run_emulator, accelerator="F5")
        emulation_menu.add_command(label="Pause", command=self.pause_emulator, accelerator="F6")
        emulation_menu.add_command(label="Reset", command=self.reset_emulator, accelerator="F7")
        emulation_menu.add_command(label="Stop", command=self.stop_emulator, accelerator="F8")
        menubar.add_cascade(label="Emulation", menu=emulation_menu)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        tools_menu.add_command(label="Debugger", command=self.launch_debugger, accelerator="Ctrl+D")
        tools_menu.add_command(label="Cheats", command=self.launch_cheats, accelerator="Ctrl+H")
        tools_menu.add_command(label="TAS Tools", command=self.launch_tas_tools, accelerator="Ctrl+T")
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)
        
        # Bind keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.open_rom())
        self.root.bind("<Control-r>", lambda e: self.reset_emulator())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<F5>", lambda e: self.run_emulator())
        self.root.bind("<F6>", lambda e: self.pause_emulator())
        self.root.bind("<F7>", lambda e: self.reset_emulator())
        self.root.bind("<F8>", lambda e: self.stop_emulator())
        self.root.bind("<Control-d>", lambda e: self.launch_debugger())
        self.root.bind("<Control-h>", lambda e: self.launch_cheats())
        self.root.bind("<Control-t>", lambda e: self.launch_tas_tools())

    def create_toolbar(self):
        # Use a frame with grid for better toolbar organization
        toolbar = tk.Frame(self.root, bg="#2d2d2d", height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        toolbar.grid_columnconfigure(0, weight=1)
        
        # Left side buttons
        left_frame = tk.Frame(toolbar, bg="#2d2d2d")
        left_frame.grid(row=0, column=0, sticky="w")
        
        open_btn = tk.Button(left_frame, text="📂 Open", command=self.open_rom,
                             bg="#3a3a3a", fg="white", relief=tk.FLAT, cursor="hand2", width=8)
        open_btn.grid(row=0, column=0, padx=5, pady=5)

        self.run_btn = tk.Button(left_frame, text="▶ Run", command=self.run_emulator,
                                 bg="#4CAF50", fg="white", relief=tk.FLAT, cursor="hand2", width=8)
        self.run_btn.grid(row=0, column=1, padx=5, pady=5)

        self.pause_btn = tk.Button(left_frame, text="⏸ Pause", command=self.pause_emulator,
                                   bg="#FF9800", fg="white", relief=tk.FLAT, cursor="hand2", width=8, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=2, padx=5, pady=5)

        reset_btn = tk.Button(left_frame, text="⟳ Reset", command=self.reset_emulator,
                              bg="#2196F3", fg="white", relief=tk.FLAT, cursor="hand2", width=8)
        reset_btn.grid(row=0, column=3, padx=5, pady=5)

        self.stop_btn = tk.Button(left_frame, text="■ Stop", command=self.stop_emulator,
                                  bg="#f44336", fg="white", relief=tk.FLAT, cursor="hand2", width=8, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Right side info
        right_frame = tk.Frame(toolbar, bg="#2d2d2d")
        right_frame.grid(row=0, column=1, sticky="e")
        
        self.rom_info = tk.Label(right_frame, text="No ROM loaded", bg="#2d2d2d", fg="white")
        self.rom_info.grid(row=0, column=0, padx=10, pady=5)

    def create_main_area(self):
        # Create a paned window for resizable sections
        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Display area (placeholder for future game display)
        display_frame = ttk.LabelFrame(main_pane, text="Display")
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)
        
        display_placeholder = tk.Label(display_frame, text="Game display will appear here", 
                                      bg="#000000", fg="#AAAAAA", font=("Arial", 14))
        display_placeholder.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Console area
        console_frame = ttk.LabelFrame(main_pane, text="Emulator Log")
        console_frame.grid_rowconfigure(0, weight=1)
        console_frame.grid_columnconfigure(0, weight=1)
        
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD,
                                                 font=("Consolas", 9),
                                                 bg="#0d0d0d", fg="#00ff00",
                                                 insertbackground="white",
                                                 height=10)
        self.console.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.console.config(state=tk.DISABLED)
        
        # Add frames to paned window
        main_pane.add(display_frame, weight=3)  # Display area takes 3/4 of space
        main_pane.add(console_frame, weight=1)  # Console takes 1/4 of space
        
        self.log("SamsoftEmu NES v1.0 GUI Ready")

    def create_statusbar(self):
        status_frame = tk.Frame(self.root, bg="#2d2d2d", height=20)
        status_frame.grid(row=2, column=0, sticky="ew")
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready – No ROM loaded")
        status_bar = tk.Label(status_frame, textvariable=self.status_var,
                              bd=1, relief=tk.SUNKEN, anchor=tk.W,
                              bg="#2d2d2d", fg="white")
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # FPS counter (placeholder)
        fps_label = tk.Label(status_frame, text="FPS: --", 
                            bd=1, relief=tk.SUNKEN, anchor=tk.E,
                            bg="#2d2d2d", fg="white", width=10)
        fps_label.pack(side=tk.RIGHT, padx=2)

    def log(self, msg):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    # Emulator actions
    def open_rom(self):
        filetypes = [("NES ROMs", "*.nes"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select NES ROM", filetypes=filetypes)
        if filename:
            self.rom_path = filename
            self.status_var.set(f"Loaded ROM: {os.path.basename(filename)}")
            self.rom_info.config(text=os.path.basename(filename))
            self.log(f"[ROM] Loaded: {filename}")
            
            # Enable run button
            self.run_btn.config(state=tk.NORMAL)

    def run_emulator(self):
        if not self.rom_path:
            messagebox.showwarning("No ROM", "Please load a ROM first!")
            return
            
        self.is_running = True
        self.status_var.set(f"Running: {os.path.basename(self.rom_path)}")
        
        # Update button states
        self.run_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log(f"[SYSTEM] Emulating {os.path.basename(self.rom_path)} (stub backend)")
        # TODO: plug in CPU6502/PPU/APU backend

    def pause_emulator(self):
        if self.is_running:
            self.is_running = False
            self.status_var.set(f"Paused: {os.path.basename(self.rom_path)}")
            
            # Update button states
            self.run_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            
            self.log("[SYSTEM] Emulation paused")
        else:
            self.log("[WARN] Pause called but emulator not running")

    def reset_emulator(self):
        if self.is_running:
            self.log("[SYSTEM] Emulator reset")
            self.status_var.set("Reset")
        else:
            self.log("[WARN] Reset called but emulator not running")

    def stop_emulator(self):
        if self.is_running:
            self.is_running = False
            self.status_var.set("Stopped")
            
            # Update button states
            self.run_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            
            self.log("[SYSTEM] Emulator stopped")
        else:
            self.log("[WARN] Stop called but emulator not running")

    def launch_debugger(self):
        self.log("[TOOLS] Debugger opened (stub)")

    def launch_cheats(self):
        self.log("[TOOLS] Cheats manager opened (stub)")

    def launch_tas_tools(self):
        self.log("[TOOLS] TAS tools opened (stub)")

    def show_about(self):
        about_text = (
            "SamsoftEmu NES v1.0\n"
            "Tkinter GUI Frontend\n"
            "AI Core Edition\n\n"
            "A frontend for a future FCEUX-class NES emulator"
        )
        messagebox.showinfo("About SamsoftEmu NES", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = SamsoftEmuNESGUI(root)
    root.mainloop()
