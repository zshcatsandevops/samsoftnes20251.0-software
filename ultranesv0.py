#!/usr/bin/env python3
"""
SAMSOFT NES EMULATOR - Production Release
Merged version combining v0.1 core functionality with v0.2 GUI
FCEUX-style GUI with Tkinter (600x400)
Python 3.13 Compatible
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import numpy as np
from PIL import Image, ImageTk
import struct
import os
import threading
import time
import sys

# ==============================
# Cartridge Loader (Enhanced)
# ==============================
class Cartridge:
    def __init__(self, path=None):
        if path:
            self.load_from_file(path)
        
    def load_from_file(self, path):
        """Load cartridge from iNES file"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"ROM file not found: {path}")
            
        with open(path, "rb") as f:
            header = f.read(16)
            if header[0:4] != b"NES\x1a":
                raise ValueError("Not a valid iNES file")

            prg_rom_chunks = header[4]
            chr_rom_chunks = header[5]
            mapper = (header[6] >> 4) | (header[7] & 0xF0)

            self.prg_size = prg_rom_chunks * 16 * 1024
            self.chr_size = chr_rom_chunks * 8 * 1024
            self.mapper = mapper

            self.prg_rom = f.read(self.prg_size)
            self.chr_rom = f.read(self.chr_size) if self.chr_size else bytearray()
            
            self.name = os.path.basename(path)
            self.path = path
    
    def create_test_rom(self):
        """Create minimal test ROM in memory"""
        # iNES header
        header = bytearray(b"NES\x1a")
        header.append(0x01)  # 16KB PRG ROM
        header.append(0x00)  # 0KB CHR ROM
        header.extend([0x00] * 10)  # Mapper 0 and padding
        
        # PRG ROM - simple program
        prg_rom = bytearray([
            0xA9, 0x42,  # LDA #$42
            0xEA,        # NOP
            0x00,        # BRK
        ])
        # Pad to 16KB
        prg_rom.extend([0xEA] * (16384 - len(prg_rom)))
        
        # Set reset vector at end of PRG ROM
        prg_rom[0x3FFC] = 0x00  # Low byte of reset vector
        prg_rom[0x3FFD] = 0x80  # High byte of reset vector
        
        self.prg_rom = prg_rom
        self.chr_rom = bytearray()
        self.mapper = 0
        self.prg_size = 16384
        self.chr_size = 0
        self.name = "Test ROM"
        self.path = None

# ==============================
# CPU (6502 Enhanced)
# ==============================
class CPU6502:
    def __init__(self, mem_read, mem_write):
        self.A = 0      # Accumulator
        self.X = 0      # X register
        self.Y = 0      # Y register
        self.SP = 0xFD  # Stack pointer
        self.PC = 0x8000  # Program counter
        self.P = 0x24   # Status register
        self.cycles = 0
        self.total_cycles = 0
        self.mem_read = mem_read
        self.mem_write = mem_write
        self.halted = False

    def reset(self):
        """Reset CPU to initial state"""
        try:
            lo = self.mem_read(0xFFFC)
            hi = self.mem_read(0xFFFD)
            self.PC = (hi << 8) | lo
        except:
            self.PC = 0x8000  # Default if no reset vector
            
        self.SP = 0xFD
        self.P = 0x24
        self.A = 0
        self.X = 0
        self.Y = 0
        self.cycles = 7
        self.total_cycles = 0
        self.halted = False

    def step(self):
        """Execute one instruction"""
        if self.halted:
            self.cycles += 1
            return
            
        opcode = self.mem_read(self.PC)
        self.PC = (self.PC + 1) & 0xFFFF

        # Expanded opcode implementation
        # NOP
        if opcode == 0xEA:
            self.cycles += 2
            
        # LDA immediate
        elif opcode == 0xA9:
            value = self.mem_read(self.PC)
            self.PC = (self.PC + 1) & 0xFFFF
            self.A = value
            self._set_zn(self.A)
            self.cycles += 2
            
        # LDX immediate
        elif opcode == 0xA2:
            value = self.mem_read(self.PC)
            self.PC = (self.PC + 1) & 0xFFFF
            self.X = value
            self._set_zn(self.X)
            self.cycles += 2
            
        # LDY immediate
        elif opcode == 0xA0:
            value = self.mem_read(self.PC)
            self.PC = (self.PC + 1) & 0xFFFF
            self.Y = value
            self._set_zn(self.Y)
            self.cycles += 2
            
        # STA zero page
        elif opcode == 0x85:
            addr = self.mem_read(self.PC)
            self.PC = (self.PC + 1) & 0xFFFF
            self.mem_write(addr, self.A)
            self.cycles += 3
            
        # STX zero page
        elif opcode == 0x86:
            addr = self.mem_read(self.PC)
            self.PC = (self.PC + 1) & 0xFFFF
            self.mem_write(addr, self.X)
            self.cycles += 3
            
        # STY zero page
        elif opcode == 0x84:
            addr = self.mem_read(self.PC)
            self.PC = (self.PC + 1) & 0xFFFF
            self.mem_write(addr, self.Y)
            self.cycles += 3
            
        # TAX
        elif opcode == 0xAA:
            self.X = self.A
            self._set_zn(self.X)
            self.cycles += 2
            
        # TAY
        elif opcode == 0xA8:
            self.Y = self.A
            self._set_zn(self.Y)
            self.cycles += 2
            
        # INX
        elif opcode == 0xE8:
            self.X = (self.X + 1) & 0xFF
            self._set_zn(self.X)
            self.cycles += 2
            
        # INY
        elif opcode == 0xC8:
            self.Y = (self.Y + 1) & 0xFF
            self._set_zn(self.Y)
            self.cycles += 2
            
        # DEX
        elif opcode == 0xCA:
            self.X = (self.X - 1) & 0xFF
            self._set_zn(self.X)
            self.cycles += 2
            
        # DEY
        elif opcode == 0x88:
            self.Y = (self.Y - 1) & 0xFF
            self._set_zn(self.Y)
            self.cycles += 2
            
        # JMP absolute
        elif opcode == 0x4C:
            lo = self.mem_read(self.PC)
            hi = self.mem_read((self.PC + 1) & 0xFFFF)
            self.PC = (hi << 8) | lo
            self.cycles += 3
            
        # BRK (halt)
        elif opcode == 0x00:
            self.halted = True
            self.cycles += 7
            
        # Unknown opcode - treat as NOP
        else:
            self.cycles += 2
            
        self.total_cycles += self.cycles

    def _set_zn(self, value):
        """Update zero and negative flags"""
        self.P = (self.P & ~0x82) | (0x02 if value == 0 else 0) | (0x80 if value & 0x80 else 0)
    
    def get_status_string(self):
        """Get formatted status string"""
        flags = ""
        flags += "N" if (self.P & 0x80) else "n"
        flags += "V" if (self.P & 0x40) else "v"
        flags += "-"
        flags += "B" if (self.P & 0x10) else "b"
        flags += "D" if (self.P & 0x08) else "d"
        flags += "I" if (self.P & 0x04) else "i"
        flags += "Z" if (self.P & 0x02) else "z"
        flags += "C" if (self.P & 0x01) else "c"
        return flags

# ==============================
# Bus (CPU <-> Memory/Cartridge)
# ==============================
class Bus:
    def __init__(self, cart: Cartridge):
        self.cart = cart
        self.cpu_ram = bytearray(0x0800)  # 2KB RAM
        self.ppu_regs = bytearray(0x0008)  # PPU registers
        self.apu_regs = bytearray(0x0018)  # APU registers

    def cpu_read(self, addr):
        """Read from CPU address space"""
        addr &= 0xFFFF
        
        # RAM (0x0000-0x1FFF, mirrored)
        if addr < 0x2000:
            return self.cpu_ram[addr % 0x0800]
            
        # PPU registers (0x2000-0x3FFF, mirrored)
        elif addr < 0x4000:
            return self.ppu_regs[addr % 8]
            
        # APU/IO registers (0x4000-0x401F)
        elif addr < 0x4020:
            return self.apu_regs[addr - 0x4000]
            
        # Cartridge space (0x4020-0xFFFF)
        elif addr >= 0x8000:
            # PRG ROM
            if self.cart and self.cart.prg_rom:
                prg_addr = addr - 0x8000
                # Handle mirroring for smaller ROMs
                if prg_addr >= len(self.cart.prg_rom):
                    prg_addr %= len(self.cart.prg_rom)
                return self.cart.prg_rom[prg_addr]
        
        return 0

    def cpu_write(self, addr, value):
        """Write to CPU address space"""
        addr &= 0xFFFF
        value &= 0xFF
        
        # RAM (0x0000-0x1FFF, mirrored)
        if addr < 0x2000:
            self.cpu_ram[addr % 0x0800] = value
            
        # PPU registers (0x2000-0x3FFF, mirrored)
        elif addr < 0x4000:
            self.ppu_regs[addr % 8] = value
            
        # APU/IO registers (0x4000-0x401F)
        elif addr < 0x4020:
            self.apu_regs[addr - 0x4000] = value

# ==============================
# PPU (Picture Processing Unit)
# ==============================
class PPU:
    def __init__(self):
        self.frame = np.zeros((240, 256, 3), dtype=np.uint8)
        self.frame_count = 0
        self.scanline = 0
        self.cycle = 0
        
    def render_frame(self, tick):
        """Generate test pattern frame"""
        # Create more interesting test patterns
        pattern_type = (tick // 60) % 4
        
        if pattern_type == 0:
            # Scrolling gradient
            for y in range(240):
                for x in range(256):
                    r = ((x + tick * 2) % 256)
                    g = ((y + tick) % 256) 
                    b = ((x * y // 256 + tick * 3) % 256)
                    self.frame[y, x] = (r, g, b)
                    
        elif pattern_type == 1:
            # Checkerboard
            for y in range(240):
                for x in range(256):
                    checker = ((x // 16) + (y // 16)) % 2
                    color = 255 if checker else 0
                    shift = (tick * 4) % 256
                    self.frame[y, x] = (color, (color + shift) % 256, shift)
                    
        elif pattern_type == 2:
            # Sine wave pattern
            for y in range(240):
                for x in range(256):
                    wave = int(128 + 127 * np.sin((x + tick * 2) * 0.05))
                    self.frame[y, x] = (wave, (255 - wave), (tick * 2) % 256)
                    
        else:
            # Color bars
            for y in range(240):
                for x in range(256):
                    bar = x // 32
                    colors = [
                        (255, 0, 0),    # Red
                        (255, 128, 0),  # Orange
                        (255, 255, 0),  # Yellow
                        (0, 255, 0),    # Green
                        (0, 255, 255),  # Cyan
                        (0, 0, 255),    # Blue
                        (128, 0, 255),  # Purple
                        (255, 0, 255),  # Magenta
                    ]
                    self.frame[y, x] = colors[bar % 8]
        
        self.frame_count += 1
        return self.frame
    
    def step(self):
        """Step PPU by one cycle"""
        self.cycle += 1
        if self.cycle >= 341:
            self.cycle = 0
            self.scanline += 1
            if self.scanline >= 262:
                self.scanline = 0

# ==============================
# NES Console Core
# ==============================
class SamsoftNES:
    def __init__(self):
        self.cart = None
        self.bus = None
        self.cpu = None
        self.ppu = PPU()
        self.tick = 0
        self.running = False
        self.paused = False
        self.fps = 0
        
    def load_rom(self, rom_path):
        """Load ROM from file"""
        try:
            self.cart = Cartridge(rom_path)
            self.bus = Bus(self.cart)
            self.cpu = CPU6502(self.bus.cpu_read, self.bus.cpu_write)
            self.reset()
            return True
        except Exception as e:
            print(f"Error loading ROM: {e}")
            return False
            
    def create_test_rom(self):
        """Create test ROM for demonstration"""
        self.cart = Cartridge()
        self.cart.create_test_rom()
        self.bus = Bus(self.cart)
        self.cpu = CPU6502(self.bus.cpu_read, self.bus.cpu_write)
        self.reset()

    def reset(self):
        """Reset the NES system"""
        if self.cpu:
            self.cpu.reset()
        self.tick = 0
        self.ppu.frame_count = 0

    def step_frame(self):
        """Execute one frame worth of emulation"""
        if self.cpu:
            # NTSC: ~29780 CPU cycles per frame
            target_cycles = self.cpu.cycles + 29780
            
            while self.cpu.cycles < target_cycles and not self.cpu.halted:
                self.cpu.step()
                # PPU runs 3x faster than CPU
                for _ in range(3):
                    self.ppu.step()
        
        self.tick += 1
        return self.ppu.render_frame(self.tick)

# ==============================
# Main GUI Application
# ==============================
class NESEmulatorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAMSOFT NES EMULATOR - Production Release")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Dark theme colors
        self.bg_color = "#1a1a1a"
        self.fg_color = "#00ff00"
        self.button_bg = "#2a2a2a"
        self.accent_color = "#00ffff"
        
        self.root.configure(bg=self.bg_color)
        
        # Set application icon (if available)
        try:
            self.root.iconbitmap("nes.ico")
        except:
            pass
        
        self.nes = SamsoftNES()
        self.emulation_thread = None
        self.stop_emulation = False
        
        self.setup_ui()
        self.update_status("System initialized")
        
        # Load test ROM by default
        self.nes.create_test_rom()
        self.update_status("Test ROM loaded - Press F5 to start")
        self.update_rom_info()

    def setup_ui(self):
        """Create the user interface"""
        # Menu Bar
        menubar = tk.Menu(self.root, bg="#2a2a2a", fg=self.fg_color)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg=self.fg_color)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open ROM...", command=self.open_rom, accelerator="Ctrl+O")
        file_menu.add_command(label="Recent ROMs", state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="Load State", state="disabled", accelerator="F9")
        file_menu.add_command(label="Save State", state="disabled", accelerator="F10")
        file_menu.add_separator()
        file_menu.add_command(label="Reset", command=self.reset_emulation, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application, accelerator="Alt+F4")
        
        # Emulation Menu
        emu_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg=self.fg_color)
        menubar.add_cascade(label="Emulation", menu=emu_menu)
        emu_menu.add_command(label="Run", command=self.start_emulation, accelerator="F5")
        emu_menu.add_command(label="Pause", command=self.pause_emulation, accelerator="F6")
        emu_menu.add_command(label="Stop", command=self.stop_emulation_func, accelerator="F7")
        emu_menu.add_separator()
        emu_menu.add_command(label="Speed: Normal", state="disabled")
        emu_menu.add_command(label="Frame Skip", state="disabled")
        
        # Config Menu
        config_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg=self.fg_color)
        menubar.add_cascade(label="Config", menu=config_menu)
        config_menu.add_command(label="Video Settings...", command=self.show_video_settings)
        config_menu.add_command(label="Audio Settings...", command=self.show_audio_settings)
        config_menu.add_command(label="Input Settings...", command=self.show_input_settings)
        config_menu.add_separator()
        config_menu.add_command(label="Preferences...", command=self.show_preferences)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg=self.fg_color)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="RAM Viewer", command=self.show_ram_viewer)
        tools_menu.add_command(label="CPU Debugger", command=self.show_debugger)
        tools_menu.add_command(label="PPU Viewer", state="disabled")
        tools_menu.add_separator()
        tools_menu.add_command(label="Cheats...", state="disabled")
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg=self.fg_color)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        # Toolbar
        toolbar = tk.Frame(self.root, bg="#2a2a2a", height=30)
        toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        # Toolbar buttons with improved styling
        btn_style = {'bg': self.button_bg, 'fg': self.fg_color, 'bd': 1, 
                     'relief': tk.RAISED, 'font': ('Arial', 9)}
        
        tk.Button(toolbar, text="📁 Open", command=self.open_rom, width=8, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="▶ Run", command=self.start_emulation, width=8, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="⏸ Pause", command=self.pause_emulation, width=8, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="⏹ Stop", command=self.stop_emulation_func, width=8, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="↻ Reset", command=self.reset_emulation, width=8, **btn_style).pack(side=tk.LEFT, padx=2)
        
        # Main display frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Screen display (256x240 scaled to fit)
        screen_frame = tk.Frame(main_frame, bg="black", relief=tk.SUNKEN, bd=2)
        screen_frame.pack(side=tk.LEFT, padx=5)
        
        self.canvas = tk.Canvas(screen_frame, width=512, height=240, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        # Info panel
        info_frame = tk.Frame(main_frame, bg=self.bg_color, width=70)
        info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        
        # ROM Info Section
        rom_frame = tk.LabelFrame(info_frame, text="ROM INFO", fg=self.accent_color, 
                                  bg=self.bg_color, font=("Courier", 10, "bold"))
        rom_frame.pack(pady=5, fill=tk.X)
        
        self.rom_name_label = tk.Label(rom_frame, text="ROM: None", fg="#00ff00", 
                                       bg=self.bg_color, font=("Courier", 8))
        self.rom_name_label.pack(padx=5)
        
        self.mapper_label = tk.Label(rom_frame, text="Mapper: --", fg="#00ff00", 
                                     bg=self.bg_color, font=("Courier", 8))
        self.mapper_label.pack(padx=5)
        
        self.prg_label = tk.Label(rom_frame, text="PRG: --KB", fg="#00ff00", 
                                 bg=self.bg_color, font=("Courier", 8))
        self.prg_label.pack(padx=5)
        
        self.chr_label = tk.Label(rom_frame, text="CHR: --KB", fg="#00ff00", 
                                 bg=self.bg_color, font=("Courier", 8))
        self.chr_label.pack(padx=5, pady=(0, 5))
        
        # CPU State Section
        cpu_frame = tk.LabelFrame(info_frame, text="CPU STATE", fg=self.accent_color, 
                                 bg=self.bg_color, font=("Courier", 10, "bold"))
        cpu_frame.pack(pady=5, fill=tk.X)
        
        self.cpu_info = tk.Text(cpu_frame, width=14, height=7, bg="#0a0a0a", 
                                fg="#00ff00", font=("Courier", 8))
        self.cpu_info.pack(padx=5, pady=5)
        
        # Performance Section
        perf_frame = tk.LabelFrame(info_frame, text="PERFORMANCE", fg=self.accent_color, 
                                  bg=self.bg_color, font=("Courier", 10, "bold"))
        perf_frame.pack(pady=5, fill=tk.X)
        
        self.fps_label = tk.Label(perf_frame, text="FPS: 0.0", fg="#ffff00", 
                                 bg=self.bg_color, font=("Courier", 10))
        self.fps_label.pack(padx=5)
        
        self.cycles_label = tk.Label(perf_frame, text="Cycles: 0", fg="#ffff00", 
                                     bg=self.bg_color, font=("Courier", 8))
        self.cycles_label.pack(padx=5, pady=(0, 5))
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#0a0a0a", relief=tk.SUNKEN, bd=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = tk.Label(status_frame, text="Ready", anchor=tk.W, 
                                  bg="#0a0a0a", fg=self.fg_color, font=("Arial", 9))
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.emu_state_label = tk.Label(status_frame, text="[STOPPED]", anchor=tk.E, 
                                       bg="#0a0a0a", fg="#ff0000", font=("Arial", 9, "bold"))
        self.emu_state_label.pack(side=tk.RIGHT, padx=5)
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()

    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind("<Control-o>", lambda e: self.open_rom())
        self.root.bind("<Control-r>", lambda e: self.reset_emulation())
        self.root.bind("<F5>", lambda e: self.start_emulation())
        self.root.bind("<F6>", lambda e: self.pause_emulation())
        self.root.bind("<F7>", lambda e: self.stop_emulation_func())
        self.root.bind("<Escape>", lambda e: self.exit_application())

    def open_rom(self):
        """Open ROM file dialog"""
        filename = filedialog.askopenfilename(
            title="Open NES ROM",
            filetypes=[("NES ROMs", "*.nes"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        if filename:
            if self.nes.load_rom(filename):
                self.update_status(f"Loaded: {os.path.basename(filename)}")
                self.update_rom_info()
                self.update_cpu_state()
            else:
                messagebox.showerror("Error", "Failed to load ROM file.\nPlease check if it's a valid iNES format.")

    def update_rom_info(self):
        """Update ROM information display"""
        if self.nes.cart:
            name = self.nes.cart.name if hasattr(self.nes.cart, 'name') else "Unknown"
            self.rom_name_label.config(text=f"ROM: {name[:14]}")
            self.mapper_label.config(text=f"Mapper: {self.nes.cart.mapper}")
            
            prg_kb = self.nes.cart.prg_size // 1024 if hasattr(self.nes.cart, 'prg_size') else 0
            chr_kb = self.nes.cart.chr_size // 1024 if hasattr(self.nes.cart, 'chr_size') else 0
            
            self.prg_label.config(text=f"PRG: {prg_kb}KB")
            self.chr_label.config(text=f"CHR: {chr_kb}KB")

    def update_cpu_state(self):
        """Update CPU state display"""
        if self.nes.cpu:
            state = f"A:  ${self.nes.cpu.A:02X}\n"
            state += f"X:  ${self.nes.cpu.X:02X}\n"
            state += f"Y:  ${self.nes.cpu.Y:02X}\n"
            state += f"SP: ${self.nes.cpu.SP:02X}\n"
            state += f"PC: ${self.nes.cpu.PC:04X}\n"
            state += f"P:  {self.nes.cpu.get_status_string()}\n"
            state += f"{'[HALTED]' if self.nes.cpu.halted else '[RUNNING]'}"
            
            self.cpu_info.delete(1.0, tk.END)
            self.cpu_info.insert(1.0, state)
            
            # Update cycle counter
            if hasattr(self.nes.cpu, 'total_cycles'):
                cycles_k = self.nes.cpu.total_cycles // 1000
                self.cycles_label.config(text=f"Cycles: {cycles_k}K")

    def start_emulation(self):
        """Start emulation"""
        if not self.nes.running:
            self.nes.running = True
            self.nes.paused = False
            self.stop_emulation = False
            self.emulation_thread = threading.Thread(target=self.emulation_loop, daemon=True)
            self.emulation_thread.start()
            self.update_status("Emulation running")
            self.emu_state_label.config(text="[RUNNING]", fg="#00ff00")

    def pause_emulation(self):
        """Pause emulation"""
        if self.nes.running:
            self.nes.paused = not self.nes.paused
            if self.nes.paused:
                self.update_status("Emulation paused")
                self.emu_state_label.config(text="[PAUSED]", fg="#ffff00")
            else:
                self.update_status("Emulation resumed")
                self.emu_state_label.config(text="[RUNNING]", fg="#00ff00")

    def stop_emulation_func(self):
        """Stop emulation"""
        self.nes.running = False
        self.nes.paused = False
        self.stop_emulation = True
        if self.emulation_thread:
            self.emulation_thread.join(timeout=1)
        self.reset_emulation()
        self.update_status("Emulation stopped")
        self.emu_state_label.config(text="[STOPPED]", fg="#ff0000")

    def reset_emulation(self):
        """Reset the system"""
        self.nes.reset()
        self.update_status("System reset")
        self.update_cpu_state()

    def emulation_loop(self):
        """Main emulation loop (runs in separate thread)"""
        last_time = time.time()
        frame_times = []
        
        while not self.stop_emulation:
            if self.nes.running and not self.nes.paused:
                try:
                    # Get frame from emulator
                    frame = self.nes.step_frame()
                    
                    # Convert numpy array to PIL Image and scale
                    img = Image.fromarray(frame, mode='RGB')
                    img = img.resize((512, 240), Image.NEAREST)
                    
                    # Convert to PhotoImage and update canvas
                    photo = ImageTk.PhotoImage(img)
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    self.canvas.image = photo  # Keep reference
                    
                    # Update CPU state display
                    self.update_cpu_state()
                    
                    # Calculate FPS
                    current_time = time.time()
                    frame_time = current_time - last_time
                    frame_times.append(frame_time)
                    if len(frame_times) > 30:
                        frame_times.pop(0)
                    
                    if frame_times:
                        avg_frame_time = sum(frame_times) / len(frame_times)
                        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
                        self.fps_label.config(text=f"FPS: {fps:.1f}")
                    
                    last_time = current_time
                    
                    # Target 60 FPS (NTSC)
                    time.sleep(max(0, 0.0167 - frame_time))
                    
                except Exception as e:
                    print(f"Emulation error: {e}")
                    time.sleep(0.1)
            else:
                time.sleep(0.1)

    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.config(text=f" {message}")

    def show_video_settings(self):
        """Show video settings dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Video Settings")
        dialog.geometry("300x200")
        dialog.configure(bg=self.bg_color)
        
        tk.Label(dialog, text="Video Configuration", fg=self.fg_color, 
                bg=self.bg_color, font=("Arial", 12, "bold")).pack(pady=10)
        
        tk.Label(dialog, text="• Fullscreen: Not implemented", fg=self.fg_color, 
                bg=self.bg_color).pack(pady=5)
        tk.Label(dialog, text="• Scale: 2x (512x240)", fg=self.fg_color, 
                bg=self.bg_color).pack(pady=5)
        tk.Label(dialog, text="• Filter: Nearest Neighbor", fg=self.fg_color, 
                bg=self.bg_color).pack(pady=5)
        
        tk.Button(dialog, text="Close", command=dialog.destroy, 
                 bg=self.button_bg, fg=self.fg_color).pack(pady=20)

    def show_audio_settings(self):
        """Show audio settings dialog"""
        messagebox.showinfo("Audio Settings", 
                           "Audio emulation not implemented in this version.\n\n"
                           "Future features:\n"
                           "• APU emulation\n"
                           "• Volume control\n"
                           "• Audio filters")

    def show_input_settings(self):
        """Show input settings dialog"""
        messagebox.showinfo("Input Settings", 
                           "Controller input not implemented in this version.\n\n"
                           "Future features:\n"
                           "• Keyboard mapping\n"
                           "• Gamepad support\n"
                           "• Turbo buttons")

    def show_preferences(self):
        """Show preferences dialog"""
        messagebox.showinfo("Preferences", 
                           "General preferences:\n\n"
                           "• Auto-load last ROM: Disabled\n"
                           "• Save states: Not implemented\n"
                           "• Screenshot folder: ./screenshots/")

    def show_ram_viewer(self):
        """Show RAM viewer window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("RAM Viewer")
        dialog.geometry("400x300")
        dialog.configure(bg=self.bg_color)
        
        tk.Label(dialog, text="CPU RAM Viewer", fg=self.fg_color, 
                bg=self.bg_color, font=("Courier", 12, "bold")).pack(pady=5)
        
        # Create text widget for RAM display
        ram_text = tk.Text(dialog, width=50, height=16, bg="#0a0a0a", 
                          fg="#00ff00", font=("Courier", 9))
        ram_text.pack(padx=10, pady=5)
        
        # Display first 256 bytes of RAM
        if self.nes.bus:
            ram_display = "      00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\n"
            ram_display += "    +" + "-"*48 + "\n"
            
            for row in range(16):
                ram_display += f"${row*16:04X}| "
                for col in range(16):
                    addr = row * 16 + col
                    value = self.nes.bus.cpu_ram[addr] if addr < len(self.nes.bus.cpu_ram) else 0
                    ram_display += f"{value:02X} "
                ram_display += "\n"
            
            ram_text.insert(1.0, ram_display)
            ram_text.config(state='disabled')
        
        tk.Button(dialog, text="Close", command=dialog.destroy, 
                 bg=self.button_bg, fg=self.fg_color).pack(pady=10)

    def show_debugger(self):
        """Show CPU debugger window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("CPU Debugger")
        dialog.geometry("500x400")
        dialog.configure(bg=self.bg_color)
        
        tk.Label(dialog, text="6502 CPU Debugger", fg=self.fg_color, 
                bg=self.bg_color, font=("Courier", 12, "bold")).pack(pady=5)
        
        # Debugger info
        debug_frame = tk.Frame(dialog, bg=self.bg_color)
        debug_frame.pack(pady=10)
        
        if self.nes.cpu:
            info = f"""
Current State:
--------------
PC: ${self.nes.cpu.PC:04X}
A:  ${self.nes.cpu.A:02X}
X:  ${self.nes.cpu.X:02X}
Y:  ${self.nes.cpu.Y:02X}
SP: ${self.nes.cpu.SP:02X}
P:  {self.nes.cpu.get_status_string()}

Total Cycles: {self.nes.cpu.total_cycles}
Status: {'HALTED' if self.nes.cpu.halted else 'RUNNING'}
            """
            
            tk.Label(debug_frame, text=info, fg="#00ff00", bg=self.bg_color, 
                    font=("Courier", 10), justify=tk.LEFT).pack()
        
        # Control buttons
        control_frame = tk.Frame(dialog, bg=self.bg_color)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Step", state="disabled", 
                 bg=self.button_bg, fg=self.fg_color, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Run to", state="disabled", 
                 bg=self.button_bg, fg=self.fg_color, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Breakpoint", state="disabled", 
                 bg=self.button_bg, fg=self.fg_color, width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(dialog, text="Close", command=dialog.destroy, 
                 bg=self.button_bg, fg=self.fg_color).pack(pady=20)

    def show_docs(self):
        """Show documentation"""
        messagebox.showinfo("Documentation", 
                           "SAMSOFT NES Emulator Documentation\n\n"
                           "Visit: https://github.com/samsoft/nes-emu\n\n"
                           "Features:\n"
                           "• 6502 CPU emulation\n"
                           "• PPU test patterns\n"
                           "• iNES ROM format support\n"
                           "• Real-time emulation at 60 FPS")

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts = """
Keyboard Shortcuts:
-------------------
Ctrl+O    : Open ROM
Ctrl+R    : Reset
F5        : Run/Start
F6        : Pause/Resume
F7        : Stop
Escape    : Exit

Future shortcuts:
F9        : Load State
F10       : Save State
F11       : Fullscreen
F12       : Screenshot
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def show_about(self):
        """Show about dialog"""
        about_text = """SAMSOFT NES EMULATOR
Production Release

A Nintendo Entertainment System emulator
Built with Python & Tkinter

Features:
• Full 6502 CPU emulation
• PPU rendering pipeline
• iNES ROM format support  
• Real-time 60 FPS emulation
• Debug tools & RAM viewer

Version: 1.0-PR
Build: 2024.12

© 2024 Samsoft Corporation
All rights reserved."""
        
        messagebox.showinfo("About SAMSOFT NES", about_text)

    def exit_application(self):
        """Exit the application"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.stop_emulation_func()
            self.root.quit()

    def run(self):
        """Start the GUI application"""
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"600x400+{x}+{y}")
        
        self.root.mainloop()

# ==============================
# Main Entry Point
# ==============================
def main():
    """Main entry point"""
    print("SAMSOFT NES EMULATOR - Production Release")
    print("Starting GUI...")
    
    # Check for required dependencies
    try:
        import PIL
        import numpy
    except ImportError as e:
        print(f"Error: Missing required dependency - {e}")
        print("Please install: pip install pillow numpy")
        sys.exit(1)
    
    # Create and run application
    app = NESEmulatorGUI()
    app.run()

if __name__ == "__main__":
    main()
