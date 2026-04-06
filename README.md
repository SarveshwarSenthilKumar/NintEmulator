# NintEmulator - Game Boy Emulator

A simple Game Boy emulator written in Python with Pygame for graphics display.

## Features

- **CPU**: Sharp LR35902-compatible CPU implementation
- **Memory**: Full 64KB memory map with MBC support
- **Graphics**: GPU with tile-based rendering and sprites
- **Input**: Joypad support with keyboard mapping
- **Sound**: Basic sound framework (not fully implemented)
- **Cartridges**: Support for ROM-only and MBC cartridges
- **Built-in Game**: Includes a simple Pong game

## Installation

1. Install Python 3.7 or higher
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   or manually:
   ```bash
   pip install pygame numpy
   ```

## Usage

### Run with built-in game:
```bash
python run_emulator.py
```

### Run with a ROM file:
```bash
python run_emulator.py your_game.gb
```

### Controls
- **Arrow Keys**: D-Pad (Up, Down, Left, Right)
- **A**: A button
- **S**: B button  
- **Enter**: Select button
- **Space**: Start button
- **Escape**: Quit emulator

## Files

- `run_emulator.py` - Main launcher script
- `emulator.py` - Core emulator class
- `cpu.py` - CPU implementation
- `mmu.py` - Memory management unit
- `gpu.py` - Graphics processing unit
- `cartridge.py` - Cartridge/MBC support
- `test_game.py` - Built-in Pong game generator
- `requirements.txt` - Python dependencies

## Game Boy Compatibility

This emulator supports:
- ROM-only cartridges
- MBC1, MBC2, MBC3, MBC5 memory bank controllers
- Standard Game Boy screen resolution (160x144)
- Monochrome graphics with 4 shades
- Basic sprite rendering
- Joypad input

## Known Limitations

- Sound is not fully implemented
- Some advanced CPU instructions may be missing
- No save game support
- Limited cartridge compatibility (works best with simple homebrew)
- Performance may vary depending on your system

## Building the Test Game

The built-in Pong game can be regenerated with:
```bash
python test_game.py
```

This will create `pong.gb` in the current directory.

## Architecture

The emulator is structured with these main components:

1. **CPU**: Implements the Sharp LR35902 instruction set
2. **MMU**: Handles memory mapping and I/O registers
3. **GPU**: Renders graphics using Pygame
4. **Cartridge**: Manages ROM/RAM banking and MBCs

## Contributing

Feel free to contribute improvements, bug fixes, or additional features. The code is designed to be educational and easy to understand.

## License

This project is for educational purposes. Feel free to use and modify the code as you see fit.

## Troubleshooting

- **Import errors**: Make sure all Python files are in the same directory
- **Performance issues**: Try adjusting the cycle count in `emulator.py`
- **Display issues**: Ensure Pygame is properly installed and your graphics drivers are up to date

Enjoy playing Game Boy games! 🎮
