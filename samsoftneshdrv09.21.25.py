#!/usr/bin/env python3
"""
SamsoftNES v0.1 (Python 3.13)
Custom NES emulator skeleton.
- Cartridge loader (iNES)
- CPU core (6502 subset)
- PPU stub (returns test frame)
"""

import struct
import numpy as np
import os

# ==============================
# Cartridge Loader
# ==============================
class Cartridge:
    def __init__(self, path):
        # Check if file exists
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

# ==============================
# CPU (6502 Skeleton)
# ==============================
class CPU6502:
    def __init__(self, mem_read, mem_write):
        # Registers
        self.A = 0
        self.X = 0
        self.Y = 0
        self.SP = 0xFD
        self.PC = 0x8000
        self.P = 0x24
        self.cycles = 0

        # Memory callbacks
        self.mem_read = mem_read
        self.mem_write = mem_write

    def reset(self):
        lo = self.mem_read(0xFFFC)
        hi = self.mem_read(0xFFFD)
        self.PC = (hi << 8) | lo
        self.SP = 0xFD
        self.P = 0x24
        self.cycles = 7

    def step(self):
        opcode = self.mem_read(self.PC)
        self.PC += 1

        # NOP
        if opcode == 0xEA:
            self.cycles += 2
            return

        # LDA immediate
        if opcode == 0xA9:
            value = self.mem_read(self.PC)
            self.PC += 1
            self.A = value
            self._set_zn(self.A)
            self.cycles += 2
            return

        # BRK (halt)
        if opcode == 0x00:
            print("[CPU] BRK encountered")
            self.cycles += 7
            return

        print(f"[CPU] Unimplemented opcode {hex(opcode)} at {hex(self.PC-1)}")
        self.cycles += 2

    def _set_zn(self, value):
        # Update zero/negative flags
        self.P = (self.P & ~0x82) | (0x02 if value == 0 else 0) | (0x80 if value & 0x80 else 0)

# ==============================
# Bus (CPU <-> Cartridge)
# ==============================
class Bus:
    def __init__(self, cart: Cartridge):
        self.cart = cart
        self.cpu_ram = [0] * 0x0800  # 2KB

    def cpu_read(self, addr):
        if addr < 0x2000:
            return self.cpu_ram[addr % 0x0800]
        elif 0x8000 <= addr <= 0xFFFF:
            # Handle PRG ROM mirroring if needed
            prg_addr = addr - 0x8000
            if prg_addr >= len(self.cart.prg_rom):
                prg_addr %= len(self.cart.prg_rom)
            return self.cart.prg_rom[prg_addr]
        else:
            return 0

    def cpu_write(self, addr, value):
        if addr < 0x2000:
            self.cpu_ram[addr % 0x0800] = value
        # PRG ROM is read-only

# ==============================
# PPU (Stub)
# ==============================
class PPU:
    def __init__(self):
        self.frame = np.zeros((240, 256, 3), dtype=np.uint8)

    def render_test_frame(self, tick):
        # Simple color stripes to prove rendering works
        for y in range(240):
            for x in range(256):
                self.frame[y, x] = ((x + tick) % 256, y % 256, (x*y) % 256)
        return self.frame

# ==============================
# NES Console
# ==============================
class SamsoftNES:
    def __init__(self, rom_path):
        try:
            self.cart = Cartridge(rom_path)
            print(f"Loaded ROM: {rom_path}")
        except FileNotFoundError:
            print(f"ROM file not found: {rom_path}")
            print("Creating a minimal test ROM in memory...")
            self.cart = self.create_minimal_rom()
            
        self.bus = Bus(self.cart)
        self.cpu = CPU6502(self.bus.cpu_read, self.bus.cpu_write)
        self.ppu = PPU()
        self.tick = 0

    def create_minimal_rom(self):
        # Create a minimal in-memory ROM for testing
        class MinimalCartridge:
            def __init__(self):
                self.prg_rom = bytearray([0xA9, 0x42, 0xEA, 0x00])  # LDA #$42, NOP, BRK
                self.chr_rom = bytearray()
                self.mapper = 0
                
        return MinimalCartridge()

    def reset(self):
        self.cpu.reset()

    def step_frame(self):
        # Run some CPU cycles (placeholder: 1 opcode)
        self.cpu.step()
        # Return a fake PPU frame
        self.tick += 1
        return self.ppu.render_test_frame(self.tick)

# ==============================
# Demo
# ==============================
if __name__ == "__main__":
    rom_path = "roms/test.nes"
    
    # Create roms directory if it doesn't exist
    os.makedirs(os.path.dirname(rom_path), exist_ok=True)
    
    # Create a minimal test ROM if it doesn't exist
    if not os.path.exists(rom_path):
        print(f"Creating test ROM at: {rom_path}")
        with open(rom_path, "wb") as f:
            # iNES header
            f.write(b"NES\x1a")  # Magic
            f.write(b"\x01")     # 16KB PRG ROM
            f.write(b"\x00")     # 0KB CHR ROM
            f.write(b"\x00")     # Mapper 0
            f.write(b"\x00")     # Mapper continued
            f.write(b"\x00\x00\x00\x00\x00\x00\x00")  # Padding
            
            # PRG ROM - simple program that loads 0x42 into A and halts
            prg_rom = bytearray([0xA9, 0x42, 0xEA, 0x00])  # LDA #$42, NOP, BRK
            # Pad to 16KB
            prg_rom.extend([0xEA] * (16384 - len(prg_rom)))  # Fill with NOPs
            f.write(prg_rom)
    
    nes = SamsoftNES(rom_path)
    nes.reset()
    
    # Run a few cycles
    for i in range(10):
        frame = nes.step_frame()
        print(f"Step {i}: A={nes.cpu.A}, PC={hex(nes.cpu.PC)}, Cycles={nes.cpu.cycles}")
    
    print(f"Final frame shape: {frame.shape}")
