import struct

class CPU:
    def __init__(self, mmu):
        self.mmu = mmu
        
        # Registers
        self.a = 0x01  # Accumulator
        self.f = 0xB0  # Flags
        self.b = 0x00
        self.c = 0x13
        self.d = 0x00
        self.e = 0xD8
        self.h = 0x01
        self.l = 0x4D
        
        # Special registers
        self.sp = 0xFFFE  # Stack pointer
        self.pc = 0x0100  # Program counter
        
        # Flags
        self.flag_z = False  # Zero
        self.flag_n = False  # Subtraction
        self.flag_h = False  # Half carry
        self.flag_c = False  # Carry
        
        # Clock
        self.clock_m = 0  # Machine cycles
        self.clock_t = 0  # Clock cycles
        
        # Interrupt enable
        self.ime = False
        self.halt = False
        
    def get_bc(self):
        return (self.b << 8) | self.c
    
    def set_bc(self, value):
        self.b = (value >> 8) & 0xFF
        self.c = value & 0xFF
    
    def get_de(self):
        return (self.d << 8) | self.e
    
    def set_de(self, value):
        self.d = (value >> 8) & 0xFF
        self.e = value & 0xFF
    
    def get_hl(self):
        return (self.h << 8) | self.l
    
    def set_hl(self, value):
        self.h = (value >> 8) & 0xFF
        self.l = value & 0xFF
    
    def get_af(self):
        return (self.a << 8) | self.f
    
    def set_af(self, value):
        self.a = (value >> 8) & 0xFF
        self.f = value & 0xF0  # Lower nibble of F is always 0
        
    def update_flags(self, z=None, n=None, h=None, c=None):
        if z is not None:
            self.flag_z = z
        if n is not None:
            self.flag_n = n
        if h is not None:
            self.flag_h = h
        if c is not None:
            self.flag_c = c
            
        # Update F register
        self.f = 0
        if self.flag_z:
            self.f |= 0x80
        if self.flag_n:
            self.f |= 0x40
        if self.flag_h:
            self.f |= 0x20
        if self.flag_c:
            self.f |= 0x10
    
    def step(self):
        if self.halt:
            self.clock_m = 1
            self.clock_t = 4
            return
            
        opcode = self.mmu.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        
        # Execute instruction
        self.execute_instruction(opcode)
    
    def execute_instruction(self, opcode):
        # Basic instruction set (simplified for demo)
        if opcode == 0x00:  # NOP
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x3E:  # LD A, d8
            self.a = self.mmu.read_byte(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.clock_m = 2
            self.clock_t = 8
            
        elif opcode == 0x06:  # LD B, d8
            self.b = self.mmu.read_byte(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.clock_m = 2
            self.clock_t = 8
            
        elif opcode == 0x0E:  # LD C, d8
            self.c = self.mmu.read_byte(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.clock_m = 2
            self.clock_t = 8
            
        elif opcode == 0x7F:  # LD A, A
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x78:  # LD A, B
            self.a = self.b
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x79:  # LD A, C
            self.a = self.c
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x47:  # LD B, A
            self.b = self.a
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x4F:  # LD C, A
            self.c = self.a
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x87:  # ADD A, A
            result = self.a + self.a
            self.flag_c = result > 0xFF
            self.flag_h = (self.a & 0xF) + (self.a & 0xF) > 0xF
            self.a = result & 0xFF
            self.flag_z = self.a == 0
            self.flag_n = False
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x80:  # ADD A, B
            result = self.a + self.b
            self.flag_c = result > 0xFF
            self.flag_h = (self.a & 0xF) + (self.b & 0xF) > 0xF
            self.a = result & 0xFF
            self.flag_z = self.a == 0
            self.flag_n = False
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x81:  # ADD A, C
            result = self.a + self.c
            self.flag_c = result > 0xFF
            self.flag_h = (self.a & 0xF) + (self.c & 0xF) > 0xF
            self.a = result & 0xFF
            self.flag_z = self.a == 0
            self.flag_n = False
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x76:  # HALT
            self.halt = True
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0xC3:  # JP a16
            addr = self.mmu.read_word(self.pc)
            self.pc = addr
            self.clock_m = 3
            self.clock_t = 12
            
        elif opcode == 0xE0:  # LDH (a8), A
            addr = 0xFF00 | self.mmu.read_byte(self.pc)
            self.mmu.write_byte(addr, self.a)
            self.pc = (self.pc + 1) & 0xFFFF
            self.clock_m = 2
            self.clock_t = 12
            
        elif opcode == 0xF0:  # LDH A, (a8)
            addr = 0xFF00 | self.mmu.read_byte(self.pc)
            self.a = self.mmu.read_byte(addr)
            self.pc = (self.pc + 1) & 0xFFFF
            self.clock_m = 2
            self.clock_t = 12
            
        elif opcode == 0xFE:  # CP d8
            value = self.mmu.read_byte(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            result = self.a - value
            self.flag_z = (result & 0xFF) == 0
            self.flag_n = True
            self.flag_h = (self.a & 0xF) < (value & 0xF)
            self.flag_c = self.a < value
            self.clock_m = 2
            self.clock_t = 8
            
        elif opcode == 0x2F:  # CPL
            self.a = ~self.a & 0xFF
            self.flag_n = True
            self.flag_h = True
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0xAF:  # XOR A
            self.a = 0
            self.flag_z = True
            self.flag_n = False
            self.flag_h = False
            self.flag_c = False
            self.clock_m = 1
            self.clock_t = 4
            
        elif opcode == 0x20:  # JR NZ, r8
            offset = self.mmu.read_byte(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            if not self.flag_z:
                self.pc = (self.pc + offset) & 0xFFFF
            self.clock_m = 2
            self.clock_t = 8
            
        elif opcode == 0xFA:  # LD A, a16
            addr = self.mmu.read_word(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.a = self.mmu.read_byte(addr)
            self.clock_m = 4
            self.clock_t = 16
            
        else:
            # Unknown instruction
            print(f"Unknown opcode: 0x{opcode:02X} at PC=0x{self.pc-1:04X}")
            self.clock_m = 1
            self.clock_t = 4
