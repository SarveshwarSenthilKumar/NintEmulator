# Simple Game Boy ROM - Pong Game
# This creates a basic Pong game that can be loaded into the emulator

def create_pong_rom():
    # Game Boy ROM header
    rom = bytearray(0x8000)  # 32KB ROM (2 banks)
    
    # Nintendo logo (required for authentic ROM)
    nintendo_logo = [
        0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B,
        0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D,
        0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E,
        0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99,
        0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC,
        0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E
    ]
    
    # Write Nintendo logo at 0x0104
    for i, byte in enumerate(nintendo_logo):
        rom[0x0104 + i] = byte
    
    # ROM title (16 bytes max)
    title = "PONG GAME"
    for i, char in enumerate(title):
        rom[0x0134 + i] = ord(char)
    
    # Cartridge type: ROM only
    rom[0x0147] = 0x00
    
    # ROM size: 32KB (2 banks)
    rom[0x0148] = 0x01
    
    # RAM size: None
    rom[0x0149] = 0x00
    
    # Destination code: Non-Japanese
    rom[0x014A] = 0x01
    
    # Licensee code: New licensee
    rom[0x014B] = 0x33
    rom[0x0144] = 0x33
    
    # SGB flag: No SGB
    rom[0x0146] = 0x00
    
    # Header checksum (will be calculated later)
    
    # Global checksum (will be calculated later)
    
    # Game code starts at 0x0150
    pc = 0x0150
    
    # Initialize Game Boy hardware
    # Disable boot ROM
    rom[pc] = 0x3E  # LD A, 0x01
    rom[pc + 1] = 0x01
    pc += 2
    rom[pc] = 0xE0  # LDH (0xFF50), A
    rom[pc + 1] = 0x50
    pc += 2
    
    # Set up LCD
    rom[pc] = 0x3E  # LD A, 0x91
    rom[pc + 1] = 0x91
    pc += 2
    rom[pc] = 0xE0  # LDH (0xFF40), A (LCDC)
    rom[pc + 1] = 0x40
    pc += 2
    
    # Set up palette
    rom[pc] = 0x3E  # LD A, 0xE4
    rom[pc + 1] = 0xE4
    pc += 2
    rom[pc] = 0xE0  # LDH (0xFF47), A (BGP)
    rom[pc + 1] = 0x47
    pc += 2
    
    # Clear VRAM
    rom[pc] = 0x21  # LD HL, 0x8000
    rom[pc + 1] = 0x00
    rom[pc + 2] = 0x80
    pc += 3
    rom[pc] = 0x11  # LD DE, 0x2000 (8KB)
    rom[pc + 1] = 0x00
    rom[pc + 2] = 0x20
    pc += 3
    rom[pc] = 0x3E  # LD A, 0x00
    rom[pc + 1] = 0x00
    pc += 2
    
    # Clear loop
    clear_loop_start = pc
    rom[pc] = 0x22  # LD (HL+), A
    pc += 1
    rom[pc] = 0x1B  # DEC DE
    pc += 1
    rom[pc] = 0x7A  # LD A, D
    pc += 1
    rom[pc] = 0xB3  # OR E
    pc += 1
    jump_offset = clear_loop_start - (pc + 2)
    rom[pc] = 0x20  # JR NZ, clear_loop
    rom[pc + 1] = jump_offset & 0xFF
    pc += 2
    
    # Load tiles for paddles and ball
    # Tile 0: Left paddle (8x8)
    paddle_tile = [
        0xFF, 0xFF,  # ########
        0xFF, 0xFF,  # ########
        0xFF, 0xFF,  # ########
        0xFF, 0xFF,  # ########
        0xFF, 0xFF,  # ########
        0xFF, 0xFF,  # ########
        0xFF, 0xFF,  # ########
        0xFF, 0xFF   # ########
    ]
    
    # Write paddle tile to VRAM at 0x8010
    tile_addr = 0x8010
    rom[pc] = 0x21  # LD HL, tile_addr
    rom[pc + 1] = tile_addr & 0xFF
    rom[pc + 2] = (tile_addr >> 8) & 0xFF
    pc += 3
    
    for byte in paddle_tile:
        rom[pc] = 0x3E  # LD A, byte
        rom[pc + 1] = byte
        pc += 2
        rom[pc] = 0x22  # LD (HL+), A
        pc += 1
    
    # Tile 1: Ball (8x8)
    ball_tile = [
        0x3C, 0x3C,  # ####
        0x42, 0x42,  # #   #
        0x81, 0x81,  # #     #
        0x81, 0x81,  # #     #
        0x81, 0x81,  # #     #
        0x81, 0x81,  # #     #
        0x42, 0x42,  # #   #
        0x3C, 0x3C   # ####
    ]
    
    # Write ball tile to VRAM at 0x8020
    tile_addr = 0x8020
    rom[pc] = 0x21  # LD HL, tile_addr
    rom[pc + 1] = tile_addr & 0xFF
    rom[pc + 2] = (tile_addr >> 8) & 0xFF
    pc += 3
    
    for byte in ball_tile:
        rom[pc] = 0x3E  # LD A, byte
        rom[pc + 1] = byte
        pc += 2
        rom[pc] = 0x22  # LD (HL+), A
        pc += 1
    
    # Enable LCD
    rom[pc] = 0x3E  # Main game loop
    rom[pc + 1] = 1
    pc += 2
    rom[pc] = 0x22  # LD (HL+), A
    pc += 1
    
    rom[pc] = 0x3E  # LD A, 0x00 (flags)
    rom[pc + 1] = 0x00
    pc += 2
    rom[pc] = 0x22  # LD (HL+), A
    pc += 1
    
    # Main game loop
    game_loop = pc
    
    # Wait for V-Blank
    rom[pc] = 0xAF  # XOR A
    pc += 1
    rom[pc] = 0xE0  # LDH (0xFF44), A
    rom[pc + 1] = 0x44
    pc += 2
    
    wait_vblank = pc
    rom[pc] = 0xF0  # LDH A, (0xFF44)
    rom[pc + 1] = 0x44
    pc += 2
    rom[pc] = 0xFE  # CP 144
    rom[pc + 1] = 144
    pc += 2
    jump_offset = wait_vblank - (pc + 2)
    rom[pc] = 0x20  # JR NZ, wait_vblank
    rom[pc + 1] = jump_offset & 0xFF
    pc += 2
    
    # Read joypad
    rom[pc] = 0x3E  # LD A, 0x20 (select button keys)
    rom[pc + 1] = 0x20
    pc += 2
    rom[pc] = 0xE0  # LDH (0xFF00), A
    rom[pc + 1] = 0x00
    pc += 2
    
    rom[pc] = 0xF0  # LDH A, (0xFF00)
    rom[pc + 1] = 0x00
    pc += 2
    rom[pc] = 0x2F  # CPL
    pc += 1
    rom[pc] = 0xE0  # LDH (0xFF80), A (store in HRAM)
    rom[pc + 1] = 0x80
    pc += 2
    
    # Simple game logic would go here
    # For now, just jump back to game loop
    rom[pc] = 0xC3  # JP game_loop
    rom[pc + 1] = game_loop & 0xFF
    rom[pc + 2] = (game_loop >> 8) & 0xFF
    pc += 3
    
    # Calculate header checksum
    checksum = 0
    for i in range(0x0134, 0x014D):
        checksum = checksum - rom[i] - 1
    rom[0x014D] = checksum & 0xFF
    
    # Calculate global checksum
    global_checksum = 0
    for i in range(len(rom)):
        if i != 0x014E and i != 0x014F:  # Skip checksum bytes
            global_checksum += rom[i]
    rom[0x014E] = (global_checksum >> 8) & 0xFF
    rom[0x014F] = global_checksum & 0xFF
    
    return bytes(rom)

if __name__ == "__main__":
    rom_data = create_pong_rom()
    
    # Save the ROM
    with open("pong.gb", "wb") as f:
        f.write(rom_data)
    
    print("Pong ROM created: pong.gb")
    print(f"ROM size: {len(rom_data)} bytes")
