# C64 Ultimate MCP Examples

This directory contains example programs demonstrating C64 Ultimate MCP usage.

## Example Files

### Basic Examples

#### border.bas
Simple BASIC program that changes the border color to red.
- Demonstrates: POKE to VIC-II registers
- Difficulty: Beginner
- **Run:** `upload_and_run_prg` with `border.prg`

#### test_hello.bas
BASIC program that prints "HELLO" on screen.
- Demonstrates: Simple PRINT statement
- Difficulty: Beginner
- **Run:** `upload_and_run_prg` with `test_hello.prg`

#### hello.asm
Assembly language "Hello World" program that:
- Changes screen and border colors
- Displays a message on screen using direct memory writes
- Demonstrates basic 6502 assembly and memory access

**To use:**
1. Assemble with ACME: `acme -f cbm -o hello.prg hello.asm`
2. Upload and run via MCP: use `upload_and_run_prg` tool

### Advanced Examples

#### sprite_bounce.bas ✅ WORKING
Animated bouncing ball using hardware sprites.
- Demonstrates: Sprite setup, sprite data, collision detection, animation loop
- Features: Defines sprite shape, sets position, implements physics
- Difficulty: Intermediate
- **Run:** `upload_and_run_prg` with `sprite_bounce.prg`

#### sid_music.bas ✅ WORKING
Simple melody player using the SID sound chip.
- Demonstrates: SID chip programming, frequency control, waveform selection
- Features: Plays 8-note melody in loop, uses triangle wave
- Difficulty: Intermediate  
- **Run:** `upload_and_run_prg` with `sid_music.prg`

#### scroller.bas ⚠️ IN PROGRESS
Classic demo-style horizontal text scroller.
- **Status:** Tokenizer has issues with string functions - being debugged
- Demonstrates: Text scrolling, color cycling, screen memory manipulation
- Difficulty: Intermediate

#### comprehensive_demo.bas ⚠️ IN PROGRESS
Complete demo combining multiple C64 features.
- **Status:** Tokenizer has issues with complex expressions - being debugged
- Demonstrates: Sprites, SID music, color cycling, collision detection
- Difficulty: Intermediate/Advanced

#### raster_bars.asm (Advanced)
Colorful raster bar effect using raster interrupts.
- Demonstrates: Raster interrupts, VIC-II timing, IRQ handling
- Features: Synchronized color bars, classic demo effect
- Difficulty: Advanced
- **To assemble:** `acme -f cbm -o raster_bars.prg raster_bars.asm`
- **Run:** `upload_and_run_prg` with `raster_bars.prg`

## Quick Start - Testing the Examples

### Convert BASIC to PRG
All `.bas` files need to be converted to `.prg` format before running:

```bash
python src/tokenizer.py examples/border.bas examples/border.prg
```

### Run an Example
Use the MCP tool to upload and run:

```
Tool: upload_and_run_prg
  local_path: "/path/to/examples/sprite_bounce.prg"
  remote_path: "/Temp/sprite_bounce.prg"
```

## Workflow Examples

### Example 1: Quick Color Test
Test if your MCP connection works by changing border color:

```
Tool: write_memory
  address: "D020"
  data: "02"
```

This changes the border to red. Try values 00-0F for different colors.

### Example 2: Deploy and Run a Program

```
1. Tool: upload_file_ftp
     local_path: "./examples/hello.prg"
     remote_path: "/usb0/dev/hello.prg"

2. Tool: run_prg
     file: "/usb0/dev/hello.prg"
```

### Example 3: Create Work Environment

```
1. Tool: create_d64
     path: "/usb0/dev/workspace.d64"
     diskname: "MY WORKSPACE"

2. Tool: mount_disk
     drive: "a"
     image: "/usb0/dev/workspace.d64"
     mode: "readwrite"

3. Now you can save programs to disk 8: from your running code
```

### Example 4: Debug Running Program

Read screen memory to see what's displayed:

```
Tool: read_memory
  address: "0400"
  length: 1000
```

This reads the entire screen RAM. The response will be hex-encoded.

### Example 5: Live Patching

Change a program's behavior while it's running:

```
Tool: pause_machine

Tool: write_memory
  address: "0810"
  data: "A900"  # LDA #$00

Tool: resume_machine
```

## Color Reference

C64 Color Values (for border/background):
- 00 = Black
- 01 = White
- 02 = Red
- 03 = Cyan
- 04 = Purple
- 05 = Green
- 06 = Blue
- 07 = Yellow
- 08 = Orange
- 09 = Brown
- 0A = Light Red
- 0B = Dark Gray
- 0C = Gray
- 0D = Light Green
- 0E = Light Blue
- 0F = Light Gray

## Memory Map Quick Reference

Important C64 memory locations:
- $0400-$07E7 (1024-2023): Screen RAM
- $D800-$DBE7 (55296-56295): Color RAM
- $D020 (53280): Border color
- $D021 (53281): Background color
- $0801: BASIC program start
- $C000: Machine code area (safe for custom code)

## Development Tips

1. **Iterative Development**: Use the MCP to quickly upload and test changes
2. **FTP for Bulk Uploads**: Upload multiple files at once via FTP
3. **Memory Inspection**: Read memory to verify your program loaded correctly
4. **Disk Images**: Keep organized with different D64s for different projects
5. **Save Configs**: Use `save_config` after setting up your preferred drive settings

## AI-Assisted Development

This MCP is designed to work with AI assistants like Claude. You can ask the AI to:
- "Create a C64 program that displays 'HELLO' and upload it to my C64 Ultimate"
- "Debug why my program isn't displaying correctly - read screen memory"
- "Set up a development environment with a blank D64 mounted to drive 8"
- "Convert this Python algorithm to 6502 assembly and run it on my C64"

The AI can use the MCP tools to automatically handle compilation, upload, and execution!
