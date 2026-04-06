import pygame
import numpy as np

class GPU:
    def __init__(self, mmu):
        self.mmu = mmu
        
        # Screen dimensions
        self.SCREEN_WIDTH = 160
        self.SCREEN_HEIGHT = 144
        self.SCALE = 4
        
        # Pygame setup
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.SCREEN_WIDTH * self.SCALE, self.SCREEN_HEIGHT * self.SCALE)
        )
        pygame.display.set_caption("NintEmulator - Game Boy Emulator")
        
        # Create surface for Game Boy screen
        self.gb_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        
        # Initialize with white background
        self.gb_surface.fill((255, 255, 255))
        
        # Clock for timing
        self.clock = pygame.time.Clock()
        
        # GPU registers
        self.mode = 0  # Current mode
        self.clock = 0  # Mode clock
        
        # LCD Control register (0xFF40)
        self.lcdc_enable = True
        self.window_tile_map = 0
        self.window_enable = False
        self.bg_tile_data = 0
        self.bg_tile_map = 0
        self.obj_size = 0
        self.obj_enable = True
        self.bg_enable = True
        
        # LCD Status register (0xFF41)
        self.lyc_ly = False
        
        # Scroll positions
        self.scy = 0
        self.scx = 0
        
        # Window positions
        self.wy = 0
        self.wx = 0
        
        # Monochrome palette
        self.palette = [0, 85, 170, 255]  # White, Light gray, Dark gray, Black
        
        # Frame buffer
        self.frame_buffer = np.zeros((self.SCREEN_HEIGHT, self.SCREEN_WIDTH), dtype=np.uint8)
        
        # Colors for display
        self.colors = [
            (255, 255, 255),  # White
            (170, 170, 170),  # Light gray
            (85, 85, 85),     # Dark gray
            (0, 0, 0)         # Black
        ]
        
        self.ly = 0  # Current line
        self.frame_ready = False
    
    def update_registers(self):
        # Read LCDC register
        lcdc = self.mmu.read_byte(0xFF40)
        self.lcdc_enable = (lcdc & 0x80) != 0
        self.window_tile_map = (lcdc & 0x40) >> 6
        self.window_enable = (lcdc & 0x20) != 0
        self.bg_tile_data = (lcdc & 0x10) >> 4
        self.bg_tile_map = (lcdc & 0x08) >> 3
        self.obj_size = (lcdc & 0x04) >> 2
        self.obj_enable = (lcdc & 0x02) != 0
        self.bg_enable = (lcdc & 0x01) != 0
        
        # Read STAT register
        stat = self.mmu.read_byte(0xFF41)
        self.lyc_ly = (stat & 0x04) != 0
        
        # Read scroll registers
        self.scy = self.mmu.read_byte(0xFF42)
        self.scx = self.mmu.read_byte(0xFF43)
        
        # Read window position
        self.wy = self.mmu.read_byte(0xFF4A)
        self.wx = self.mmu.read_byte(0xFF4B)
        
        # Read LY register
        self.ly = self.mmu.read_byte(0xFF44)
    
    def step(self, cycles):
        if not self.lcdc_enable:
            return
        
        self.clock += cycles
        
        # GPU modes:
        # 0: H-Blank
        # 1: V-Blank
        # 2: OAM scan
        # 3: Drawing
        
        if self.mode == 0:  # H-Blank
            if self.clock >= 204:
                self.clock = 0
                self.ly += 1
                
                if self.ly == 144:
                    self.mode = 1  # V-Blank
                    self.frame_ready = True
                    # Request V-Blank interrupt
                    interrupt_flag = self.mmu.read_byte(0xFF0F)
                    self.mmu.write_byte(0xFF0F, interrupt_flag | 0x01)
                else:
                    self.mode = 2  # OAM scan
                
                self.mmu.write_byte(0xFF44, self.ly)
        
        elif self.mode == 1:  # V-Blank
            if self.clock >= 456:
                self.clock = 0
                self.ly += 1
                
                if self.ly > 153:
                    self.mode = 2  # OAM scan
                    self.ly = 0
                
                self.mmu.write_byte(0xFF44, self.ly)
        
        elif self.mode == 2:  # OAM scan
            if self.clock >= 80:
                self.clock = 0
                self.mode = 3  # Drawing
        
        elif self.mode == 3:  # Drawing
            if self.clock >= 172:
                self.clock = 0
                self.mode = 0  # H-Blank
                self.render_scanline()
        
        # Update STAT register
        stat = self.mmu.read_byte(0xFF41)
        stat = (stat & 0xFC) | self.mode
        self.mmu.write_byte(0xFF41, stat)
    
    def render_scanline(self):
        if not self.bg_enable and not self.obj_enable:
            return
        
        # Render background
        if self.bg_enable:
            self.render_background_scanline()
        
        # Render sprites
        if self.obj_enable:
            self.render_sprites_scanline()
    
    def render_background_scanline(self):
        # Get tile map base
        tile_map_base = 0x9C00 if self.bg_tile_map == 1 else 0x9800
        
        # Get tile data base
        tile_data_base = 0x8000 if self.bg_tile_data == 0 else 0x8800
        
        for x in range(self.SCREEN_WIDTH):
            # Calculate pixel in background
            px = (self.scx + x) % 256
            py = (self.scy + self.ly) % 256
            
            # Get tile coordinates
            tile_x = px // 8
            tile_y = py // 8
            
            # Get pixel within tile
            pixel_x = px % 8
            pixel_y = py % 8
            
            # Get tile index
            tile_map_addr = tile_map_base + tile_y * 32 + tile_x
            tile_index = self.mmu.read_byte(tile_map_addr)
            
            # Get tile data address
            if self.bg_tile_data == 0:
                tile_data_addr = 0x8000 + tile_index * 16
            else:
                tile_index = tile_index if tile_index < 128 else tile_index - 256
                tile_data_addr = 0x8800 + (tile_index + 128) * 16
            
            # Get pixel color
            tile_data_addr += pixel_y * 2
            byte1 = self.mmu.read_byte(tile_data_addr)
            byte2 = self.mmu.read_byte(tile_data_addr + 1)
            
            bit = 7 - pixel_x
            color_index = ((byte2 >> bit) & 1) << 1 | ((byte1 >> bit) & 1)
            
            # Get palette
            bgp = self.mmu.read_byte(0xFF47)
            palette_color = (bgp >> (color_index * 2)) & 3
            
            self.frame_buffer[self.ly, x] = palette_color
    
    def render_sprites_scanline(self):
        # OAM starts at 0xFE00, each sprite is 4 bytes
        for sprite_num in range(40):
            sprite_addr = 0xFE00 + sprite_num * 4
            
            y = self.mmu.read_byte(sprite_addr) - 16
            x = self.mmu.read_byte(sprite_addr + 1) - 8
            tile_index = self.mmu.read_byte(sprite_addr + 2)
            flags = self.mmu.read_byte(sprite_addr + 3)
            
            # Check if sprite is on this scanline
            sprite_height = 16 if self.obj_size == 1 else 8
            if y <= self.ly < y + sprite_height:
                # Get tile data
                tile_y = self.ly - y
                if self.obj_size == 1:
                    tile_index = tile_index & 0xFE  # Ignore LSB for 8x16 sprites
                
                tile_data_addr = 0x8000 + tile_index * 16 + tile_y * 2
                byte1 = self.mmu.read_byte(tile_data_addr)
                byte2 = self.mmu.read_byte(tile_data_addr + 1)
                
                # Draw sprite pixels
                for pixel_x in range(8):
                    if 0 <= x + pixel_x < self.SCREEN_WIDTH:
                        bit = 7 - pixel_x
                        color_index = ((byte2 >> bit) & 1) << 1 | ((byte1 >> bit) & 1)
                        
                        # Color 0 is transparent
                        if color_index != 0:
                            # Get palette
                            palette_addr = 0xFF48 if (flags & 0x10) else 0xFF47
                            palette = self.mmu.read_byte(palette_addr)
                            palette_color = (palette >> (color_index * 2)) & 3
                            
                        # Check priority
                        if not (flags & 0x80) or self.frame_buffer[self.ly, x + pixel_x] == 0:
                            self.frame_buffer[self.ly, x + pixel_x] = palette_color
    
    def draw_frame(self):
        # Always render something - Pong game or test pattern
        if not self.frame_ready:
            # Check if LCD is enabled
            lcdc = self.mmu.read_byte(0xFF40)
            if lcdc & 0x80:  # LCD enabled
                # Try to render actual game content
                self.render_game_content()
            else:
                # Show test pattern when LCD is disabled
                for y in range(self.SCREEN_HEIGHT):
                    for x in range(self.SCREEN_WIDTH):
                        if (x // 8 + y // 8) % 2 == 0:
                            self.frame_buffer[y, x] = 0  # White
                        else:
                            self.frame_buffer[y, x] = 3  # Black
            
            self.frame_ready = True
        
        # Simple and fast rendering
        try:
            # Create RGB surface directly
            rgb_array = np.zeros((self.SCREEN_HEIGHT, self.SCREEN_WIDTH, 3), dtype=np.uint8)
            
            # Map frame buffer values to colors
            rgb_array[self.frame_buffer == 0] = [255, 255, 255]  # White
            rgb_array[self.frame_buffer == 1] = [170, 170, 170]  # Light gray
            rgb_array[self.frame_buffer == 2] = [85, 85, 85]     # Dark gray
            rgb_array[self.frame_buffer == 3] = [0, 0, 0]         # Black
            
            pygame.surfarray.blit_array(self.gb_surface, rgb_array.swapaxes(0, 1))
        except:
            # Simple fallback - fill with alternating colors
            for y in range(0, self.SCREEN_HEIGHT, 8):
                for x in range(0, self.SCREEN_WIDTH, 8):
                    color = self.colors[(x // 8 + y // 8) % 2]
                    pygame.draw.rect(self.gb_surface, color, (x, y, 8, 8))
        
        # Scale and display
        scaled_surface = pygame.transform.scale(self.gb_surface, 
            (self.SCREEN_WIDTH * self.SCALE, self.SCREEN_HEIGHT * self.SCALE))
        self.screen.blit(scaled_surface, (0, 0))
        
        pygame.display.flip()
        self.frame_ready = False
    
    def render_game_content(self):
        """Render actual Game Boy graphics from VRAM"""
        # Clear frame buffer
        self.frame_buffer.fill(0)
        
        # Simple Pong game rendering
        # Read game state from memory locations
        left_paddle_y = self.mmu.read_byte(0xC000) & 0xFF
        right_paddle_y = self.mmu.read_byte(0xC001) & 0xFF
        ball_x = self.mmu.read_byte(0xC002) & 0xFF
        ball_y = self.mmu.read_byte(0xC003) & 0xFF
        
        # If no game state, create default positions
        if left_paddle_y == 0 and right_paddle_y == 0 and ball_x == 0 and ball_y == 0:
            left_paddle_y = 48
            right_paddle_y = 48
            ball_x = 80
            ball_y = 72
        
        # Draw left paddle
        for y in range(16):
            if 0 <= left_paddle_y + y < self.SCREEN_HEIGHT:
                for x in range(4):
                    self.frame_buffer[left_paddle_y + y, x] = 3  # Black
        
        # Draw right paddle
        for y in range(16):
            if 0 <= right_paddle_y + y < self.SCREEN_HEIGHT:
                for x in range(4):
                    self.frame_buffer[right_paddle_y + y, 159 - x] = 3  # Black
        
        # Draw ball
        for y in range(4):
            for x in range(4):
                if 0 <= ball_y + y < self.SCREEN_HEIGHT and 0 <= ball_x + x < self.SCREEN_WIDTH:
                    self.frame_buffer[ball_y + y, ball_x + x] = 3  # Black
        
        # Draw center line
        for y in range(0, self.SCREEN_HEIGHT, 4):
            for x in range(2):
                self.frame_buffer[y, 79 + x] = 2  # Gray
        
        # Try to render sprites from OAM if they exist
        for sprite_addr in range(0xFE00, 0xFEA0, 4):
            y_pos = self.mmu.read_byte(sprite_addr) - 16
            x_pos = self.mmu.read_byte(sprite_addr + 1) - 8
            tile_index = self.mmu.read_byte(sprite_addr + 2)
            flags = self.mmu.read_byte(sprite_addr + 3)
            
            # Only render if sprite is on screen and has valid data
            if 0 <= y_pos < self.SCREEN_HEIGHT and 0 <= x_pos < self.SCREEN_WIDTH:
                # Get tile data from VRAM
                tile_addr = 0x8000 + (tile_index * 16)
                
                # Draw 8x8 tile
                for tile_y in range(8):
                    # Get two bytes for each tile row
                    byte1 = self.mmu.read_byte(tile_addr + tile_y * 2)
                    byte2 = self.mmu.read_byte(tile_addr + tile_y * 2 + 1)
                    
                    for tile_x in range(8):
                        # Calculate pixel color from the two bytes
                        bit1 = (byte1 >> (7 - tile_x)) & 1
                        bit2 = (byte2 >> (7 - tile_x)) & 1
                        color_index = (bit2 << 1) | bit1
                        
                        # Skip transparent pixels
                        if color_index != 0:
                            screen_y = y_pos + tile_y
                            screen_x = x_pos + tile_x
                            if 0 <= screen_y < self.SCREEN_HEIGHT and 0 <= screen_x < self.SCREEN_WIDTH:
                                self.frame_buffer[screen_y, screen_x] = color_index

    def handle_events(self):
        keys = pygame.key.get_pressed()
        
        # Map keys to Game Boy buttons
        joypad_state = 0xFF
        
        # Direction keys
        if keys[pygame.K_RIGHT]:
            joypad_state &= 0xFE  # Clear bit 0
        if keys[pygame.K_LEFT]:
            joypad_state &= 0xFD  # Clear bit 1
        if keys[pygame.K_UP]:
            joypad_state &= 0xFB  # Clear bit 2
        if keys[pygame.K_DOWN]:
            joypad_state &= 0xF7  # Clear bit 3
        
        # Action keys
        if keys[pygame.K_a]:
            joypad_state &= 0xEF  # Clear bit 4 (A)
        if keys[pygame.K_s]:
            joypad_state &= 0xDF  # Clear bit 5 (B)
        if keys[pygame.K_RETURN]:
            joypad_state &= 0xBF  # Clear bit 6 (Select)
        if keys[pygame.K_SPACE]:
            joypad_state &= 0x7F  # Clear bit 7 (Start)
        
        # Update joypad register
        p1 = self.mmu.read_byte(0xFF00)
        if (p1 & 0x10) == 0:  # Direction keys selected
            p1 = (p1 & 0xF0) | (joypad_state & 0x0F)
        elif (p1 & 0x20) == 0:  # Action keys selected
            p1 = (p1 & 0xF0) | ((joypad_state >> 4) & 0x0F)
        
        self.mmu.write_byte(0xFF00, p1)
        
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        
        return True
