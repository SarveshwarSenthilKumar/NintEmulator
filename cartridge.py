class Cartridge:
    def __init__(self, rom_data):
        self.rom_data = rom_data
        self.rom_size = len(rom_data)
        
        # Parse header
        self.title = self._get_title()
        self.cartridge_type = self._get_cartridge_type()
        self.rom_size_code = self._get_rom_size()
        self.ram_size_code = self._get_ram_size()
        
        # Calculate actual sizes
        self.rom_banks = self._calculate_rom_banks()
        self.ram_banks = self._calculate_ram_banks()
        
        # MBC (Memory Bank Controller) setup
        self.mbc_type = self._detect_mbc_type()
        
        # RAM for external cartridge
        self.ram = [0] * (0x2000 * self.ram_banks) if self.ram_banks > 0 else []
        
        # MBC registers
        self.rom_bank = 1
        self.ram_bank = 0
        self.ram_enabled = False
        self.mode = 0
    
    def _get_title(self):
        # Title is at 0x134-0x143 (16 bytes max)
        title_bytes = self.rom_data[0x134:0x144]
        title = ""
        for byte in title_bytes:
            if byte == 0:
                break
            title += chr(byte)
        return title
    
    def _get_cartridge_type(self):
        return self.rom_data[0x147]
    
    def _get_rom_size(self):
        return self.rom_data[0x148]
    
    def _get_ram_size(self):
        return self.rom_data[0x149]
    
    def _calculate_rom_banks(self):
        size_code = self.rom_size_code
        if size_code == 0:
            return 2
        elif size_code == 1:
            return 4
        elif size_code == 2:
            return 8
        elif size_code == 3:
            return 16
        elif size_code == 4:
            return 32
        elif size_code == 5:
            return 64
        elif size_code == 6:
            return 128
        elif size_code == 7:
            return 256
        elif size_code == 8:
            return 512
        else:
            return 2  # Default to 2 banks
    
    def _calculate_ram_banks(self):
        size_code = self.ram_size_code
        if size_code == 0:
            return 0
        elif size_code == 1:
            return 1
        elif size_code == 2:
            return 1
        elif size_code == 3:
            return 4
        elif size_code == 4:
            return 16
        else:
            return 0
    
    def _detect_mbc_type(self):
        cart_type = self.cartridge_type
        
        if cart_type == 0x00:
            return "ROM_ONLY"
        elif cart_type in [0x01, 0x02, 0x03]:
            return "MBC1"
        elif cart_type in [0x05, 0x06]:
            return "MBC2"
        elif cart_type in [0x0F, 0x10, 0x11, 0x12, 0x13]:
            return "MBC3"
        elif cart_type in [0x15, 0x16, 0x17]:
            return "MBC4"
        elif cart_type in [0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E]:
            return "MBC5"
        else:
            return "UNKNOWN"
    
    def read_rom(self, address):
        # ROM Bank 0 (0x0000-0x3FFF)
        if address < 0x4000:
            return self.rom_data[address]
        
        # ROM Bank N (0x4000-0x7FFF)
        elif address < 0x8000:
            bank_address = (self.rom_bank % self.rom_banks) * 0x4000 + (address - 0x4000)
            if bank_address < len(self.rom_data):
                return self.rom_data[bank_address]
            else:
                return 0xFF
        
        return 0xFF
    
    def write_rom(self, address, value):
        # Handle MBC writes
        if self.mbc_type == "MBC1":
            self._mbc1_write(address, value)
        elif self.mbc_type == "MBC2":
            self._mbc2_write(address, value)
        elif self.mbc_type == "MBC3":
            self._mbc3_write(address, value)
        elif self.mbc_type == "MBC5":
            self._mbc5_write(address, value)
    
    def _mbc1_write(self, address, value):
        # ROM bank select (0x2000-0x3FFF)
        if 0x2000 <= address < 0x4000:
            bank_bits = value & 0x1F
            if bank_bits == 0:
                bank_bits = 1
            self.rom_bank = (self.rom_bank & 0x60) | bank_bits
        
        # RAM bank select / upper ROM bank bits (0x4000-0x5FFF)
        elif 0x4000 <= address < 0x6000:
            if self.mode == 0:
                # ROM banking mode - upper bits of ROM bank
                upper_bits = (value & 0x03) << 5
                self.rom_bank = (self.rom_bank & 0x1F) | upper_bits
            else:
                # RAM banking mode - RAM bank select
                self.ram_bank = value & 0x03
        
        # Banking mode select (0x6000-0x7FFF)
        elif 0x6000 <= address < 0x8000:
            self.mode = value & 0x01
            if self.mode == 0:
                self.ram_bank = 0
        
        # RAM enable (0x0000-0x1FFF)
        elif 0x0000 <= address < 0x2000:
            self.ram_enabled = (value & 0x0F) == 0x0A
    
    def _mbc2_write(self, address, value):
        # MBC2 has built-in RAM
        if 0x0000 <= address < 0x2000:
            # RAM enable
            self.ram_enabled = (value & 0x0F) == 0x0A
        elif 0x2000 <= address < 0x4000:
            # ROM bank select (only 4 bits)
            self.rom_bank = value & 0x0F
            if self.rom_bank == 0:
                self.rom_bank = 1
    
    def _mbc3_write(self, address, value):
        # Similar to MBC1 but with RTC support
        if 0x0000 <= address < 0x2000:
            self.ram_enabled = (value & 0x0F) == 0x0A
        elif 0x2000 <= address < 0x4000:
            bank_bits = value & 0x7F
            if bank_bits == 0:
                bank_bits = 1
            self.rom_bank = bank_bits
        elif 0x4000 <= address < 0x6000:
            if value <= 0x03:
                self.ram_bank = value
            else:
                # RTC register select
                pass
        elif 0x6000 <= address < 0x8000:
            # Latch clock data
            pass
    
    def _mbc5_write(self, address, value):
        if 0x0000 <= address < 0x2000:
            self.ram_enabled = (value & 0x0F) == 0x0A
        elif 0x2000 <= address < 0x3000:
            # ROM bank select (lower 8 bits)
            self.rom_bank = (self.rom_bank & 0x100) | value
        elif 0x3000 <= address < 0x4000:
            # ROM bank select (9th bit)
            self.rom_bank = (self.rom_bank & 0xFF) | ((value & 0x01) << 8)
        elif 0x4000 <= address < 0x6000:
            self.ram_bank = value & 0x0F
    
    def read_ram(self, address):
        if not self.ram_enabled or self.ram_banks == 0:
            return 0xFF
        
        # External RAM (0xA000-0xBFFF)
        if 0xA000 <= address < 0xC000:
            ram_address = (self.ram_bank % self.ram_banks) * 0x2000 + (address - 0xA000)
            if ram_address < len(self.ram):
                return self.ram[ram_address]
        
        return 0xFF
    
    def write_ram(self, address, value):
        if not self.ram_enabled or self.ram_banks == 0:
            return
        
        # External RAM (0xA000-0xBFFF)
        if 0xA000 <= address < 0xC000:
            ram_address = (self.ram_bank % self.ram_banks) * 0x2000 + (address - 0xA000)
            if ram_address < len(self.ram):
                self.ram[ram_address] = value
    
    def get_info(self):
        return {
            "title": self.title,
            "cartridge_type": self.cartridge_type,
            "mbc_type": self.mbc_type,
            "rom_size": self.rom_size_code,
            "rom_banks": self.rom_banks,
            "ram_size": self.ram_size_code,
            "ram_banks": self.ram_banks
        }
