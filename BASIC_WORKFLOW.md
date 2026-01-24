# C64 BASIC Tokenization Workflow

## Overview

The C64 Ultimate MCP provides a clean, composable workflow for working with Commodore 64 BASIC V2 programs. The tokenizer converts ASCII BASIC source code into PRG (program) files that can be executed on the Commodore 64.

## Tool Architecture

### Core Tool: `tokenize_basic`

Converts BASIC V2 source code into a hex-encoded PRG binary.

**Input:**
- `source` (string): BASIC source code with line numbers

**Output:**
```json
{
  "prg_hex": "010801080a00992022...",
  "size": 52
}
```

**Example:**
```bash
tokenize_basic(source="""
10 PRINT "HELLO, WORLD!"
20 END
""")
```

## Recommended Workflows

Choose the workflow that best fits your use case:

### Option 1: Direct Execution (Fastest, No Filesystem)

Run BASIC directly on the C64 via DMA without storing to filesystem.

**Workflow:**
1. Call `tokenize_basic(source)`
2. Call `run_prg_from_data(data=prg_hex)`

**Pros:**
- Fastest execution (no FTP upload needed)
- No filesystem required
- Good for testing and development
- Memory is automatically loaded via DMA

**Cons:**
- No persistent storage on C64

**Example:**
```python
# Agent pseudocode
result = tokenize_basic(source=basic_code)
prg_hex = result["prg_hex"]
execute_result = run_prg_from_data(data=prg_hex)
```

### Option 2: Upload and Run (Persistent on C64)

Upload to C64 filesystem then execute.

**Workflow:**
1. Call `tokenize_basic(source)`
2. Call `upload_prg_from_hex(hex_string, remote_path)`
3. Call `run_prg(file)`

**Pros:**
- Program persists on C64
- Can be re-run later
- Good for demos and releases
- Separates tokenization from execution

**Cons:**
- Requires FTP upload
- Requires filesystem space on C64
- Slower than Option 1

**Example:**
```python
# Agent pseudocode
result = tokenize_basic(source=basic_code)
prg_hex = result["prg_hex"]
upload_result = upload_prg_from_hex(
    hex_string=prg_hex,
    remote_path="/usb0/myprogram.prg"
)
run_result = run_prg(file="/usb0/myprogram.prg")
```

### Option 3: Save Locally, then Upload

Save PRG locally for inspection, then upload.

**Workflow:**
1. Call `tokenize_basic(source)`
2. Call `write_prg_from_hex(hex_string, local_path)` - saves locally
3. Call `upload_file_ftp(local_path, remote_path)` - optional verification
4. Call `run_prg(file)` - on C64

**Pros:**
- Can inspect/modify PRG before running
- Good for archiving programs
- Allows local verification

**Cons:**
- More steps required
- Requires local filesystem access

**Example:**
```python
# Agent pseudocode
result = tokenize_basic(source=basic_code)
prg_hex = result["prg_hex"]
write_result = write_prg_from_hex(hex_string=prg_hex, local_path="./program.prg")
upload_result = upload_file_ftp(
    local_path="./program.prg",
    remote_path="/usb0/program.prg"
)
run_result = run_prg(file="/usb0/program.prg")
```

## Tokenizer Compatibility

The `tokenize_basic` tool is fully compatible with C64 BASIC V2 and supports:

✓ All BASIC keywords (PRINT, FOR, NEXT, GOTO, GOSUB, etc.)
✓ String literals (with proper handling of quotes)
✓ Numeric literals
✓ Operators (+, -, *, /, ^, AND, OR, etc.)
✓ REM comments (rest of line treated as literal text)
✓ Line numbers

**Note:** The tokenizer produces PRG files with load address `$0801` (2049), which is the standard BASIC program area on the Commodore 64.

## Removed Tools (Deprecated)

The following convenience wrapper tools have been removed to reduce redundancy:

### ~~`tokenize_and_run_basic`~~ (Removed)

**Why removed:** This can be easily composed as `tokenize_basic` + `run_prg_from_data`

**Migration:**
```
OLD: tokenize_and_run_basic(source=code)
NEW: 
  1. result = tokenize_basic(source=code)
  2. run_result = run_prg_from_data(data=result["prg_hex"])
```

### ~~`tokenize_upload_and_run_basic`~~ (Removed)

**Why removed:** This can be easily composed as `tokenize_basic` + `upload_prg_from_hex` + `run_prg`

**Migration:**
```
OLD: tokenize_upload_and_run_basic(source=code, remote_path="/usb0/prog.prg")
NEW:
  1. result = tokenize_basic(source=code)
  2. upload_result = upload_prg_from_hex(
       hex_string=result["prg_hex"],
       remote_path="/usb0/prog.prg"
     )
  3. run_result = run_prg(file="/usb0/prog.prg")
```

## Composition Pattern

The MCP follows a microservice pattern where:

- **Core tools** are atomic and focused (e.g., `tokenize_basic`)
- **Composition tools** handle common combinations (e.g., `upload_and_run_prg`)
- **Agents compose** tools for custom workflows

This design allows agents to:
- Mix and match tools flexibly
- Reduce redundant tool implementations
- Follow consistent patterns across the MCP

## Testing

The tokenizer has been validated against pre-compiled BASIC examples:

```
✓ test_hello.bas        → 18 bytes
✓ border.bas           → 18 bytes  
✓ sprite_bounce.bas    → 826 bytes
```

All examples produce identical output to pre-compiled PRG files, confirming format compatibility.

## Related Tools

**Assembly:**
- `assemble_asm` - Assemble 6502/6510 machine code
- `assemble_and_run_asm` - Assemble and run immediately

**Program Execution:**
- `run_prg` - Load and run a PRG file from filesystem
- `run_prg_from_data` - Run a PRG from binary data
- `upload_and_run_prg` - Upload local file and run

**Data Management:**
- `write_prg_from_hex` - Write PRG data to local file
- `upload_prg_from_hex` - Upload PRG data to C64
- `upload_file_ftp` - Upload any file via FTP

**Machine Control:**
- `reset_machine` - Soft reset
- `reboot_machine` - Hard reboot
- `read_screen` - Read C64 screen output
