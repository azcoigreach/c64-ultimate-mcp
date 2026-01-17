# Copilot Instructions for C64 Ultimate MCP

## Overview
This document provides essential guidance for AI coding agents working with the C64 Ultimate MCP codebase. Understanding the architecture, workflows, and conventions will enable effective contributions and usage of the system.

## Architecture
The C64 Ultimate MCP is structured around a Model Context Protocol (MCP) server that interfaces with the Commodore 64 Ultimate device. Key components include:
- **Machine Control**: Manage the C64's state (reset, reboot, pause).
- **Program Management**: Load and execute PRG files, manage FTP uploads, and handle cartridge files.
- **Memory Access**: Direct memory manipulation via DMA for debugging and live patching.
- **Drive Management**: Control floppy drives and disk images.

### Data Flow
1. **Client Requests**: Clients send requests to the MCP server via REST API.
2. **Command Execution**: The server processes commands, interacting with the C64 hardware as needed.
3. **Response Handling**: Results are returned to the client, including diagnostics and execution results.

## Developer Workflows
### Setting Up the Environment
1. Clone the repository:
   ```bash
   git clone https://github.com/azcoigreach/c64-ultimate-mcp.git
   cd c64-ultimate-mcp
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure the C64 Ultimate connection in a `.env` file.

### Running the MCP Server
To start the server, run:
```bash
python src/c64_ultimate_mcp.py
```

### Common Commands
- **Load and Run PRG**: Use `upload_and_run_prg` to upload and execute a program.
- **Assemble and Run**: Use `assemble_and_run_asm` for immediate execution of assembly code.
- **Memory Access**: Use `write_memory` and `read_memory` for direct memory manipulation.

## Project-Specific Conventions
- **File Paths**: Use Unix-style paths for the Ultimate filesystem (e.g., `/USB0/`).
- **Memory Addresses**: Specify addresses in hexadecimal without the `$` prefix (e.g., `D020`).
- **PRG Format**: Ensure PRG files conform to the standard C64 format with a 2-byte load address header.

## Integration Points
- **External Dependencies**: The project relies on `httpx` for HTTP requests and `python-dotenv` for environment variable management.
- **Cross-Component Communication**: The server communicates with clients via REST API, handling commands and returning results.

## Example Patterns
### Quick Test - Change Screen Colors
```bash
Use write_memory tool:
  address: "D020"  (border color)
  data: "0E"       (light blue)
```

### Develop and Run a Program
1. Write your BASIC or assembly program locally.
2. Convert BASIC to PRG or compile assembly.
3. Upload and run:
```bash
Use upload_and_run_prg:
  local_path: "./examples/test_hello.prg"
  remote_path: "/USB0/repos/examples/test_hello.prg"
```

## Conclusion
This document serves as a foundational guide for AI coding agents. For further details, refer to the [README.md](README.md) and the [API documentation](https://1541u-documentation.readthedocs.io/en/latest/api/api_calls.html).