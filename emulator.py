import sys
import os
import time
import pygame
from cpu import CPU
from mmu import MMU
from gpu import GPU
from cartridge import Cartridge
from test_game import create_pong_rom

class Emulator:
    def __init__(self):
        self.mmu = MMU()
        self.cpu = CPU(self.mmu)
        self.gpu = GPU(self.mmu)
        self.cartridge = None
        
        # Emulation speed
        self.target_speed = 1.0  # 1.0 = normal speed
        self.running = True
        
        # Performance tracking
        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0
    
    def load_rom(self, rom_data):
        """Load a ROM into the emulator"""
        self.cartridge = Cartridge(rom_data)
        self.mmu.load_cartridge(rom_data)
        
        # Print cartridge info
        info = self.cartridge.get_info()
        print(f"Loaded ROM: {info['title']}")
        print(f"Cartridge type: {info['mbc_type']}")
        print(f"ROM banks: {info['rom_banks']}")
        print(f"RAM banks: {info['ram_banks']}")
    
    def step(self):
        """Execute one CPU instruction"""
        # Store previous cycles
        prev_cycles = self.cpu.clock_m
        
        # Execute CPU instruction
        self.cpu.step()
        
        # Calculate cycles used
        cycles_used = self.cpu.clock_m - prev_cycles
        
        # Update GPU
        self.gpu.update_registers()
        self.gpu.step(cycles_used * 4)  # Convert machine cycles to clock cycles
        
        # Handle interrupts (simplified)
        self.handle_interrupts()
    
    def handle_interrupts(self):
        """Handle pending interrupts"""
        interrupt_enable = self.mmu.read_byte(0xFFFF)
        interrupt_flag = self.mmu.read_byte(0xFF0F)
        
        if interrupt_flag != 0 and self.cpu.ime:
            # V-Blank interrupt
            if (interrupt_flag & 0x01) and (interrupt_enable & 0x01):
                self.mmu.write_byte(0xFF0F, interrupt_flag & 0xFE)
                self.cpu.ime = False
                self.push_stack(self.cpu.pc)
                self.cpu.pc = 0x0040
                self.cpu.clock_m += 5
                self.cpu.clock_t += 20
    
    def push_stack(self, value):
        """Push a value onto the stack"""
        self.cpu.sp = (self.cpu.sp - 1) & 0xFFFF
        self.mmu.write_byte(self.cpu.sp, (value >> 8) & 0xFF)
        self.cpu.sp = (self.cpu.sp - 1) & 0xFFFF
        self.mmu.write_byte(self.cpu.sp, value & 0xFF)
    
    def run_frame(self):
        """Run one frame worth of instructions"""
        # Run a reasonable number of instructions per frame
        # Game Boy runs at ~4.19 MHz, so we need to balance accuracy vs performance
        instructions_per_frame = 4000  # Optimized for 60 FPS
        
        for _ in range(instructions_per_frame):
            if not self.running:
                break
            self.step()
            
            # Handle events periodically
            if _ % 1000 == 0:
                if not self.gpu.handle_events():
                    self.running = False
                    break
        
        # Force frame ready for display
        self.gpu.frame_ready = True
    
    def run(self):
        """Main emulation loop"""
        print("Starting emulator...")
        print("Controls:")
        print("  Arrow Keys: D-Pad")
        print("  A: A button")
        print("  S: B button")
        print("  Enter: Select")
        print("  Space: Start")
        print("  Escape: Quit")
        
        while self.running:
            start_time = time.time()
            
            # Run one frame
            self.run_frame()
            
            # Draw the frame
            self.gpu.draw_frame()
            
            # Calculate FPS
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.last_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_time = current_time
                pygame.display.set_caption(f"NintEmulator - Game Boy Emulator - FPS: {self.fps}")
            
            # Limit frame rate to 60 FPS
            frame_time = time.time() - start_time
            target_frame_time = 1.0 / 60.0
            if frame_time < target_frame_time:
                time.sleep(target_frame_time - frame_time)
        
        # Cleanup
        pygame.quit()
        print("Emulator stopped.")

def main():
    """Main entry point"""
    # Check if a ROM file is provided
    if len(sys.argv) > 1:
        rom_file = sys.argv[1]
        if os.path.exists(rom_file):
            with open(rom_file, "rb") as f:
                rom_data = f.read()
        else:
            print(f"ROM file not found: {rom_file}")
            return
    else:
        # Use the built-in test game
        print("No ROM file provided, using built-in Pong game...")
        rom_data = create_pong_rom()
        
        # Save the test ROM
        with open("pong.gb", "wb") as f:
            f.write(rom_data)
        print("Test ROM saved as: pong.gb")
    
    # Create and run emulator
    try:
        emulator = Emulator()
        emulator.load_rom(rom_data)
        emulator.run()
    except KeyboardInterrupt:
        print("\nEmulator interrupted by user.")
    except Exception as e:
        print(f"Error running emulator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
