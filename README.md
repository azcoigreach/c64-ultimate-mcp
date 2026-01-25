# C64 Ultimate MCP Server

Model Context Protocol (MCP) server for developing on the Commodore 64 Ultimate device. This MCP server provides tools for AI assistants to help you program directly on your C64 Ultimate via its REST API, FTP server, and DMA capabilities.

## Features

### 🎮 Machine Control
- Reset, reboot, pause, and resume your C64
- Full machine state control

### 💾 Program Management
- Load and run PRG files from Ultimate filesystem
- Upload files via FTP and run them directly
- Run programs from binary data without filesystem storage
- Load and run cartridge (CRT) files
 - Assemble 6502/6510 source via ca65 and run immediately

### 🔧 Memory Access (DMA)
- Direct memory read/write via DMA
- Peek and poke from your development environment
- Useful for debugging and live patching

### 📀 Floppy Drive Management
- Mount and eject disk images (D64, D71, D81, G64, G71)
- Create new disk images
- Control drive settings and modes
- Support for multiple drives

### ⚙️ Configuration
- Read and modify C64 Ultimate configuration
- Save/load settings from flash
- Category-based configuration management

### 📁 File Operations
- FTP file upload to Ultimate filesystem
- Create D64, D71, and D81 disk images
- Full filesystem access

### 🖼️ Graphics Tools
- Convert PNG/JPG/BMP to C64 bitmap assets (hires or multicolor)
- Extract sprite assets from images
- Generate ASM includes or BASIC loaders (optional)
- Palette and constraint analysis with reports

## Installation

1. Clone this repository:
```bash
git clone https://github.com/azcoigreach/c64-ultimate-mcp.git
cd c64-ultimate-mcp
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure your C64 Ultimate connection:
```bash
# Create .env and set your device IP
cat > .env << 'EOF'
C64_ULTIMATE_HOST=
C64_ULTIMATE_FTP_HOST=
C64_ULTIMATE_FTP_USER=anonymous
C64_ULTIMATE_FTP_PASS=
EOF
```

## Configuration

Set the following environment variables (or use `.env` file):

- `C64_ULTIMATE_HOST` - IP address or hostname of your C64 Ultimate 
- `C64_ULTIMATE_FTP_HOST` - FTP server address (usually same as host)
- `C64_ULTIMATE_FTP_USER` - FTP username (default: anonymous)
- `C64_ULTIMATE_FTP_PASS` - FTP password (default: empty)
- `ASSEMBLER` - Assembler selection (default: `ca65`, future: `acme`, `dasm`)
- `ASSEMBLER_PATH` - Path to assembler binary (default: `ca65`)
- `LD65_PATH` - Path to ld65 linker binary (default: `ld65`)
- `ASSEMBLER_TIMEOUT` - Assembly timeout in seconds (default: 30)

Current support: ca65 (from cc65). ACME/DASM may be added later.

## Usage

### Running the MCP Server

The server communicates via stdio, designed to be used with MCP-compatible clients:

```bash
python src/c64_ultimate_mcp.py
```

### Using with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "c64-ultimate": {
      "command": "/home/azcoigreach/repos/c64-ultimate-mcp/.venv/bin/python",
      "args": [
        "/home/azcoigreach/repos/c64-ultimate-mcp/src/c64_ultimate_mcp.py"
      ],
      "env": {
        "C64_ULTIMATE_HOST": ""
      }
    }
  }
}
```

## Available Tools

### System Information
- `get_version` - Get C64 Ultimate REST API version

### Machine Control
- `reset_machine` - Soft reset the C64
- `reboot_machine` - Full reboot with cartridge re-initialization
- `pause_machine` - Pause CPU via DMA
- `resume_machine` - Resume from pause

### Program Loading
- `load_prg` - Load PRG file into memory (doesn't run)
- `run_prg` - Load and auto-run PRG file (auto-types RUN via keyboard buffer)
- `upload_and_run_prg` - Upload via FTP then run
- `run_prg_from_data` - Run PRG from hex data
- `run_cartridge` - Load and run CRT file

### Assembly
- `assemble_asm` - Assemble 6502/6510 source (default ca65) and return hex-encoded PRG
- `assemble_and_run_asm` - Assemble 6502/6510 source and immediately run via DMA (not stored)

### Memory Access
- `write_memory` - Write to C64 memory via DMA (hex format)
- `read_memory` - Read from C64 memory via DMA

### Drive Management
- `get_drives` - List all drives and their status
- `mount_disk` - Mount disk image to drive
- `eject_disk` - Eject/remove disk from drive
- `reset_drive` - Reset specific drive

### Configuration
- `get_config_categories` - List all config categories
- `get_config` - Read configuration values
- `set_config` - Set configuration value
- `save_config` - Save config to flash (persistent)
- `load_config` - Load config from flash

### Disk Images
- `create_d64` - Create new D64 image (35 or 40 tracks)
- `create_d71` - Create new D71 image
- `create_d81` - Create new D81 image

### File Operations
- `upload_file_ftp` - Upload file via FTP

### Graphics Tools
- `graphics.convert_bitmap` - Convert image to bitmap assets + manifest/report
- `graphics.convert_sprites` - Convert image to sprite assets
- `graphics.analyze` - Report per-cell color conflicts

## Example Workflows

### Quick Test - Change Screen Colors
```
Use write_memory tool:
  address: "D020"  (border color)
  data: "0E"       (light blue)
```

### Assemble and Run (ca65)
```
Use assemble_and_run_asm:
  source: """
  .segment "CODE"
  lda #$00
  sta $d020 ; border black
  sta $d021 ; background black
  rts
  """
  load_address: 2049  # $0801 default
```

Returns assembly diagnostics plus the run result. For a PRG without auto-run BASIC stub, add your own stub or inject `SYS` via keyboard buffer.

Examples in `examples/*.asm` are now ca65-compatible.

## Graphics Tools

### Convert image to multicolor bitmap assets
```bash
python -m graphics convert-bitmap \
  ./examples/title.png ./build/title_bitmap \
  --mode bitmap_multicolor \
  --emit-asm
```

Emitted files:
- `bitmap.bin` (8000 bytes)
- `screen.bin` (1000 bytes)
- `color.bin` (1000 bytes, low nibble = color RAM)
- `manifest.json` + `report.json`/`report.txt`
- Optional `bitmap.inc` for ASM integration

### Include emitted assets in an assembly project (ca65)
```asm
    .include "build/title_bitmap/bitmap.inc"
```

### BASIC loader example
```bash
python -m graphics convert-bitmap \
  ./examples/title.png ./build/title_bitmap \
  --mode bitmap_multicolor \
  --emit-basic
```

### Sprite extraction
```bash
python -m graphics convert-sprites \
  ./examples/sprites.png ./build/sprites \
  --sprite-mode multicolor
```

### MCP JSON usage
```json
{
  "tool": "graphics.convert_bitmap",
  "arguments": {
    "input_path": "/path/to/image.png",
    "mode": "bitmap_multicolor",
    "output_dir": "/path/to/output",
    "dither": false,
    "emit_asm": true
  }
}
```

### Defaults and memory layout
- Bitmap: `$2000`
- Screen RAM: `$0400`
- Color RAM: `$D800`
- Sprites: `$3000`

### Develop and Run a Program
1. Write your BASIC or assembly program locally
2. Convert BASIC to PRG using the included tokenizer, or compile assembly to PRG
3. Upload and run:
```
Use upload_and_run_prg:
  local_path: "./examples/test_hello.prg"
  remote_path: "/USB0/repos/examples/test_hello.prg"
```

### BASIC Tokenizer
- Script: [src/tokenizer.py](src/tokenizer.py)
- Usage:
```bash
/home/azcoigreach/repos/c64-ultimate-mcp/.venv/bin/python src/tokenizer.py examples/test_hello.bas examples/test_hello.prg
```
- Notes:
  - Aligned to official BASIC V2 tokens (operators, functions, REM, strings)
  - Produces standard PRG with proper line links
  - Examples provided in [examples](examples) are pre-tokenized (PRGs regenerated)

### Create and Mount a Work Disk
```
1. Use create_d64:
     path: "/usb0/workdisk.d64"
     diskname: "WORK DISK"

2. Use mount_disk:
     drive: "a"
     image: "/usb0/workdisk.d64"
     mode: "readwrite"
```

### Debug Memory Contents
```
Use read_memory:
  address: "0400"  (screen memory start)
  length: 40       (one line of screen)
```

## Development Tips

- **Filesystem Paths**: Ultimate filesystem uses Unix-style paths. USB drives typically mount at `/USB0/`, `/USB1/` (case-insensitive on device).
- **Memory Addresses**: Always use hexadecimal without `$` prefix (e.g., "D020" not "$D020")
- **PRG Files**: Standard C64 PRG format with 2-byte load address header
- **DMA Access**: Write operations are limited to 128 bytes per call
- **Disk Formats**: 
  - D64: 35 or 40 tracks (170KB/197KB)
  - D71: 70 tracks (340KB) 
  - D81: 80 tracks per side (800KB)

## API Reference

Full REST API documentation: https://1541u-documentation.readthedocs.io/en/latest/api/api_calls.html

## Troubleshooting

**Connection Issues:**
- Verify C64 Ultimate is on network and accessible
- Check IP address in configuration
- Test with: `curl http://YOUR_IP/v1/version`

**FTP Upload Fails:**
- Ensure FTP server is enabled in C64 Ultimate settings
- Check firewall settings
- Verify filesystem is writable (USB drive connected)

**Program Won't Run:**
- Verify PRG file format is correct
- Check file path exists on Ultimate filesystem
- Try using `load_prg` first to test loading without running

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.

## Resources

- [C64 Ultimate Documentation](https://1541u-documentation.readthedocs.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Ultimate 64/II+ Product Page](https://ultimate64.com/)

## Acknowledgments

- Gideon Zweijtzer for the incredible C64 Ultimate hardware and firmware
- The MCP community for the excellent protocol specification
C64 Ultimate Development MCP
