#!/usr/bin/env python3
"""
Model Context Protocol Server for Commodore 64 Ultimate
Provides tools for development on C64 Ultimate devices via REST API and FTP
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Optional, Sequence
from urllib.parse import quote, urljoin

import httpx
from dotenv import load_dotenv
from ftplib import FTP
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio
from assembler import assemble_source, DEFAULT_ASSEMBLER, SUPPORTED_ASSEMBLERS
from tokenizer import BasicTokenizer

# Load environment variables from .env file (explicit path for reliability)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(os.path.abspath(_env_path), override=False)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("c64-ultimate-mcp")

# Server instance
app = Server("c64-ultimate-mcp")

# Configuration - can be overridden via environment variables
C64_HOST = os.getenv("C64_ULTIMATE_HOST", "192.168.1.64")
C64_BASE_URL = f"http://{C64_HOST}"
C64_FTP_HOST = os.getenv("C64_ULTIMATE_FTP_HOST", C64_HOST)
C64_FTP_USER = os.getenv("C64_ULTIMATE_FTP_USER", "anonymous")
C64_FTP_PASS = os.getenv("C64_ULTIMATE_FTP_PASS", "")

# HTTP client for REST API calls
http_client = httpx.AsyncClient(timeout=30.0)

# FTP timeout (seconds)
FTP_TIMEOUT = 10


def format_url(path: str, **params) -> str:
    """Format a URL with query parameters, properly encoding values."""
    url = urljoin(C64_BASE_URL, path)
    if params:
        query_parts = []
        for key, value in params.items():
            if value is not None:
                query_parts.append(f"{key}={quote(str(value))}")
        if query_parts:
            url = f"{url}?{'&'.join(query_parts)}"
    return url


async def api_get(path: str, **params) -> dict:
    """Make a GET request to the C64 Ultimate API."""
    url = format_url(path, **params)
    logger.info(f"GET {url}")
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        return response.json() if response.headers.get('content-type', '').startswith('application/json') else {"data": response.content.hex()}
    except Exception as e:
        logger.error(f"API GET error: {e}")
        return {"errors": [str(e)]}


async def api_put(path: str, **params) -> dict:
    """Make a PUT request to the C64 Ultimate API."""
    url = format_url(path, **params)
    logger.info(f"PUT {url}")
    try:
        response = await http_client.put(url)
        response.raise_for_status()
        return response.json() if response.headers.get('content-type', '').startswith('application/json') else {"data": response.text}
    except Exception as e:
        logger.error(f"API PUT error: {e}")
        return {"errors": [str(e)]}


async def api_post(path: str, data: Optional[bytes] = None, content_type: str = "application/octet-stream", **params) -> dict:
    """Make a POST request to the C64 Ultimate API."""
    url = format_url(path, **params)
    logger.info(f"POST {url}")
    try:
        headers = {"Content-Type": content_type} if data else {}
        response = await http_client.post(url, content=data, headers=headers)
        response.raise_for_status()
        return response.json() if response.headers.get('content-type', '').startswith('application/json') else {"data": response.text}
    except Exception as e:
        logger.error(f"API POST error: {e}")
        return {"errors": [str(e)]}


def ftp_upload_file(local_path: str, remote_path: str) -> dict:
    """Upload a file via FTP to the C64 Ultimate."""
    if not os.path.exists(local_path):
        return {"errors": [f"Local file not found: {local_path}"]}
    try:
        with FTP(C64_FTP_HOST, timeout=FTP_TIMEOUT) as ftp:
            ftp.login(C64_FTP_USER, C64_FTP_PASS)
            ftp.sock.settimeout(FTP_TIMEOUT)
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_path}', f)
        return {"success": True, "message": f"Uploaded {local_path} to {remote_path}"}
    except Exception as e:
        logger.error(f"FTP upload error: {e}")
        return {"errors": [str(e)], "error_type": type(e).__name__}


def decode_screen_char(byte_val: int) -> str:
    """Decode a C64 screen code byte to ASCII character."""
    # Simplified mapping focused on uppercase letters and common chars.
    # Screen codes: 1-26 => 'A'-'Z'
    if 1 <= byte_val <= 26:
        return chr(64 + byte_val)
    # Space
    if byte_val == 32:
        return ' '
    # Digits and punctuation (approximate for typical ROM charset)
    if 48 <= byte_val <= 57:  # '0'-'9'
        return chr(byte_val)
    # Map codes 32-63 directly where useful
    if 33 <= byte_val <= 63:
        return chr(byte_val)
    # PETSCII uppercase range mirrors ASCII for many values
    if 64 <= byte_val <= 95:
        return chr(byte_val - 64)
    if 96 <= byte_val <= 127:
        return chr(byte_val - 32)
    # Fallback
    return ' '



@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for C64 Ultimate development."""
    return [
        # System Information
        Tool(
            name="get_version",
            description="Get the current version of the C64 Ultimate REST API",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        
        # Machine Control
        Tool(
            name="reset_machine",
            description="Reset the C64 machine (soft reset, doesn't change configuration)",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="reboot_machine",
            description="Reboot the C64 machine (re-initializes cartridge configuration and resets)",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="pause_machine",
            description="Pause the C64 machine by pulling DMA line low (stops CPU but not timers)",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="resume_machine",
            description="Resume the C64 machine from paused state",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        
        # Program Loading and Running
        Tool(
            name="load_prg",
            description="Load a PRG file from Ultimate filesystem into C64 memory via DMA (resets machine, does not auto-run)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description": "Path to the PRG file on the Ultimate filesystem (e.g., '/usb0/programs/test.prg')"
                    }
                },
                "required": ["file"]
            }
        ),
        Tool(
            name="run_prg",
            description="Load and automatically run a PRG file from Ultimate filesystem (resets machine, loads via DMA, then runs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description": "Path to the PRG file on the Ultimate filesystem"
                    }
                },
                "required": ["file"]
            }
        ),
        Tool(
            name="upload_and_run_prg",
            description="Upload a local PRG file via FTP and then run it on the C64",
            inputSchema={
                "type": "object",
                "properties": {
                    "local_path": {
                        "type": "string",
                        "description": "Local path to the PRG file to upload"
                    },
                    "remote_path": {
                        "type": "string",
                        "description": "Remote path on Ultimate filesystem where file will be uploaded"
                    }
                },
                "required": ["local_path", "remote_path"]
            }
        ),
        Tool(
            name="run_prg_from_data",
            description="Load and run a PRG directly from binary data (without saving to filesystem first)",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Hex-encoded PRG file data"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="run_cartridge",
            description="Load and run a cartridge (CRT) file from Ultimate filesystem",
            inputSchema={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description": "Path to the CRT file on the Ultimate filesystem"
                    }
                },
                "required": ["file"]
            }
        ),

        # Assembly (ca65)
        Tool(
            name="assemble_asm",
            description="Assemble 6502/6510 source into a PRG using the configured assembler (default: ca65)",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Assembly source code"
                    },
                    "load_address": {
                        "type": "integer",
                        "description": "Load address for the PRG (e.g., 2049 for $0801)",
                        "default": 2049
                    },
                    "assembler": {
                        "type": "string",
                        "description": "Assembler choice (currently supports ca65)",
                        "enum": sorted(list(SUPPORTED_ASSEMBLERS))
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="assemble_and_run_asm",
            description="Assemble 6502/6510 source and immediately run it on the C64 via DMA (does not store on filesystem)",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Assembly source code"
                    },
                    "load_address": {
                        "type": "integer",
                        "description": "Load address for the PRG (e.g., 2049 for $0801)",
                        "default": 2049
                    },
                    "assembler": {
                        "type": "string",
                        "description": "Assembler choice (currently supports ca65)",
                        "enum": sorted(list(SUPPORTED_ASSEMBLERS))
                    }
                },
                "required": ["source"]
            }
        ),
        
        # Memory Access (DMA)
        Tool(
            name="write_memory",
            description="Write data to C64 memory via DMA (max 128 bytes). Address and data in hexadecimal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Memory address in hex (e.g., 'D020' for border color)"
                    },
                    "data": {
                        "type": "string",
                        "description": "Hex string of bytes to write (e.g., '0E' for light blue)"
                    }
                },
                "required": ["address", "data"]
            }
        ),
        Tool(
            name="read_memory",
            description="Read data from C64 memory via DMA. Returns hex-encoded data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Memory address in hex to read from"
                    },
                    "length": {
                        "type": "integer",
                        "description": "Number of bytes to read (default: 256)",
                        "default": 256
                    }
                },
                "required": ["address"]
            }
        ),
        Tool(
            name="read_screen",
            description="Read and display the C64 screen text (40x25 characters). Useful for seeing program output.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        
        # Floppy Drive Management
        Tool(
            name="get_drives",
            description="Get information about all internal drives on the IEC bus",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="mount_disk",
            description="Mount a disk image onto a drive from Ultimate filesystem",
            inputSchema={
                "type": "object",
                "properties": {
                    "drive": {
                        "type": "string",
                        "description": "Drive identifier (e.g., 'a', 'b')",
                        "enum": ["a", "b", "softiec"]
                    },
                    "image": {
                        "type": "string",
                        "description": "Path to disk image on Ultimate filesystem"
                    },
                    "type": {
                        "type": "string",
                        "description": "Image type (d64, g64, d71, g71, d81)",
                        "enum": ["d64", "g64", "d71", "g71", "d81"]
                    },
                    "mode": {
                        "type": "string",
                        "description": "Mount mode",
                        "enum": ["readwrite", "readonly", "unlinked"],
                        "default": "readwrite"
                    }
                },
                "required": ["drive", "image"]
            }
        ),
        Tool(
            name="eject_disk",
            description="Remove/eject a mounted disk from a drive",
            inputSchema={
                "type": "object",
                "properties": {
                    "drive": {
                        "type": "string",
                        "description": "Drive identifier (e.g., 'a', 'b')",
                        "enum": ["a", "b", "softiec"]
                    }
                },
                "required": ["drive"]
            }
        ),
        Tool(
            name="reset_drive",
            description="Reset a specific floppy drive",
            inputSchema={
                "type": "object",
                "properties": {
                    "drive": {
                        "type": "string",
                        "description": "Drive identifier (e.g., 'a', 'b')",
                        "enum": ["a", "b", "softiec"]
                    }
                },
                "required": ["drive"]
            }
        ),
        
        # Configuration
        Tool(
            name="get_config_categories",
            description="Get list of all configuration categories",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="get_config",
            description="Get configuration settings for a category or specific item",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Configuration category (wildcards allowed with *)"
                    },
                    "item": {
                        "type": "string",
                        "description": "Specific configuration item (optional, wildcards allowed)"
                    }
                },
                "required": ["category"]
            }
        ),
        Tool(
            name="set_config",
            description="Set a specific configuration value",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Configuration category"
                    },
                    "item": {
                        "type": "string",
                        "description": "Configuration item name"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to set"
                    }
                },
                "required": ["category", "item", "value"]
            }
        ),
        Tool(
            name="save_config",
            description="Save current configuration to flash memory (persistent across reboots)",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="load_config",
            description="Load configuration from flash memory (restore saved settings)",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        
        # Disk Image Creation
        Tool(
            name="create_d64",
            description="Create a new D64 disk image on Ultimate filesystem",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path including filename (e.g., '/usb0/disks/newdisk.d64')"
                    },
                    "tracks": {
                        "type": "integer",
                        "description": "Number of tracks (35 or 40)",
                        "default": 35,
                        "enum": [35, 40]
                    },
                    "diskname": {
                        "type": "string",
                        "description": "Disk name in header (optional, defaults to filename)"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="create_d71",
            description="Create a new D71 disk image (1571 format, 70 tracks)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path including filename"
                    },
                    "diskname": {
                        "type": "string",
                        "description": "Disk name in header (optional)"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="create_d81",
            description="Create a new D81 disk image (1581 format, 80 tracks per side)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path including filename"
                    },
                    "diskname": {
                        "type": "string",
                        "description": "Disk name in header (optional)"
                    }
                },
                "required": ["path"]
            }
        ),
        
        # File Upload
        Tool(
            name="upload_file_ftp",
            description="Upload a local file to Ultimate filesystem via FTP",
            inputSchema={
                "type": "object",
                "properties": {
                    "local_path": {
                        "type": "string",
                        "description": "Local file path to upload"
                    },
                    "remote_path": {
                        "type": "string",
                        "description": "Remote path on Ultimate filesystem"
                    }
                },
                "required": ["local_path", "remote_path"]
            }
        ),
        # BASIC Tokenization
        Tool(
            name="tokenize_basic",
            description="Tokenize C64 BASIC V2 source into a PRG (hex-encoded)",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "BASIC source code (with line numbers)"
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="tokenize_and_run_basic",
            description="Tokenize BASIC source and run it on the C64 via DMA (no filesystem)",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "BASIC source code (with line numbers)"
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="tokenize_upload_and_run_basic",
            description="Tokenize BASIC source, upload as PRG via FTP, then run it",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "BASIC source code (with line numbers)"
                    },
                    "remote_path": {
                        "type": "string",
                        "description": "Remote path to store PRG on Ultimate filesystem"
                    }
                },
                "required": ["source", "remote_path"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for C64 Ultimate operations."""
    
    try:
        result = None
        
        # System Information
        if name == "get_version":
            result = await api_get("/v1/version")
        
        # Machine Control
        elif name == "reset_machine":
            result = await api_put("/v1/machine:reset")
        elif name == "reboot_machine":
            result = await api_put("/v1/machine:reboot")
        elif name == "pause_machine":
            result = await api_put("/v1/machine:pause")
        elif name == "resume_machine":
            result = await api_put("/v1/machine:resume")
        
        # Program Loading and Running
        elif name == "load_prg":
            result = await api_put("/v1/runners:load_prg", file=arguments["file"])
        elif name == "run_prg":
            # Normalize path: remove leading slash if present
            file_path = arguments["file"].lstrip("/")
            result = await api_put("/v1/runners:run_prg", file=file_path)
            
            # After loading, type RUN into keyboard buffer to execute BASIC programs
            # PETSCII: R=52, U=55, N=4E, RETURN=0D
            # Clear keyboard buffer length first
            await api_put("/v1/machine:writemem", address="00C6", data="00")
            await api_put("/v1/machine:writemem", address="0277", data="52554E0D")
            # Set keyboard buffer length to 4 (RUN + RETURN)
            await api_put("/v1/machine:writemem", address="00C6", data="04")
        elif name == "upload_and_run_prg":
            # Upload via FTP first
            upload_result = ftp_upload_file(arguments["local_path"], arguments["remote_path"])
            if "errors" in upload_result:
                result = upload_result
            else:
                # Then run it
                result = await api_put("/v1/runners:run_prg", file=arguments["remote_path"])
                
                # After loading, type RUN into keyboard buffer to execute BASIC programs
                # PETSCII: R=52, U=55, N=4E, RETURN=0D
                await api_put("/v1/machine:writemem", address="00C6", data="00")
                await api_put("/v1/machine:writemem", address="0277", data="52554E0D")
                await api_put("/v1/machine:writemem", address="00C6", data="04")
        elif name == "run_prg_from_data":
            data = bytes.fromhex(arguments["data"])
            result = await api_post("/v1/runners:run_prg", data=data)
            
            # After loading, type RUN into keyboard buffer to execute BASIC programs
            # PETSCII: R=52, U=55, N=4E, RETURN=0D
            await api_put("/v1/machine:writemem", address="00C6", data="00")
            await api_put("/v1/machine:writemem", address="0277", data="52554E0D")
            await api_put("/v1/machine:writemem", address="00C6", data="04")
        elif name == "run_cartridge":
            # Normalize path: remove leading slash if present
            file_path = arguments["file"].lstrip("/")
            result = await api_put("/v1/runners:run_crt", file=file_path)

        # Assembly (ca65)
        elif name == "assemble_asm":
            load_address = int(arguments.get("load_address", 0x0801))
            assembler_choice = arguments.get("assembler")
            assembly = assemble_source(
                arguments["source"],
                load_address=load_address,
                assembler=assembler_choice,
            )
            result = assembly.__dict__
        elif name == "assemble_and_run_asm":
            load_address = int(arguments.get("load_address", 0x0801))
            assembler_choice = arguments.get("assembler")
            assembly = assemble_source(
                arguments["source"],
                load_address=load_address,
                assembler=assembler_choice,
            )
            if not assembly.success:
                result = assembly.__dict__
            elif not assembly.prg_hex:
                result = {
                    "errors": ["Assembly succeeded but no PRG data was produced"],
                    "assembly": assembly.__dict__,
                }
            else:
                prg_bytes = bytes.fromhex(assembly.prg_hex)
                run_result = await api_post("/v1/runners:run_prg", data=prg_bytes)
                # After loading, type SYS <addr> + RETURN into keyboard buffer
                # Target address approximated as load_address + 0x000F (start of ML code when using a BASIC stub)
                target_addr = load_address + 0x000F
                sys_str = f"SYS{target_addr}"
                petscii = sys_str.encode("ascii") + b"\r"
                # Clear keyboard buffer length before writing
                await api_put("/v1/machine:writemem", address="00C6", data="00")
                await api_put("/v1/machine:writemem", address="0277", data=petscii.hex())
                await api_put("/v1/machine:writemem", address="00C6", data=f"{len(petscii):02x}")

                result = {
                    "assembly": assembly.__dict__,
                    "run_result": run_result,
                }
        
        # Memory Access
        elif name == "write_memory":
            result = await api_put("/v1/machine:writemem", 
                                  address=arguments["address"], 
                                  data=arguments["data"])
        elif name == "read_memory":
            length = arguments.get("length", 256)
            result = await api_get("/v1/machine:readmem", 
                                  address=arguments["address"], 
                                  length=length)
        elif name == "read_screen":
            # Read screen RAM (0x0400-0x07E7, 1000 bytes = 40x25)
            screen_data = await api_get("/v1/machine:readmem", 
                                       address="0400", 
                                       length=1000)
            if "data" in screen_data:
                # Decode hex data to screen
                screen_bytes = bytes.fromhex(screen_data["data"])
                screen_text = []
                for row in range(25):
                    line = ""
                    for col in range(40):
                        byte_val = screen_bytes[row * 40 + col]
                        # Decode C64 screen code to ASCII
                        char = decode_screen_char(byte_val)
                        line += char
                    screen_text.append(line)
                result = {
                    "screen": "\n".join(screen_text),
                    "errors": []
                }
            else:
                result = screen_data
        
        # Floppy Drive Management
        elif name == "get_drives":
            result = await api_get("/v1/drives")
        elif name == "mount_disk":
            drive = arguments["drive"]
            params = {"image": arguments["image"]}
            if "type" in arguments:
                params["type"] = arguments["type"]
            if "mode" in arguments:
                params["mode"] = arguments["mode"]
            result = await api_put(f"/v1/drives/{drive}:mount", **params)
        elif name == "eject_disk":
            result = await api_put(f"/v1/drives/{arguments['drive']}:remove")
        elif name == "reset_drive":
            result = await api_put(f"/v1/drives/{arguments['drive']}:reset")
        
        # Configuration
        elif name == "get_config_categories":
            result = await api_get("/v1/configs")
        elif name == "get_config":
            path = f"/v1/configs/{quote(arguments['category'])}"
            if "item" in arguments:
                path += f"/{quote(arguments['item'])}"
            result = await api_get(path)
        elif name == "set_config":
            path = f"/v1/configs/{quote(arguments['category'])}/{quote(arguments['item'])}"
            result = await api_put(path, value=arguments["value"])
        elif name == "save_config":
            result = await api_put("/v1/configs:save_to_flash")
        elif name == "load_config":
            result = await api_put("/v1/configs:load_from_flash")
        
        # Disk Image Creation
        elif name == "create_d64":
            params = {}
            if "tracks" in arguments:
                params["tracks"] = arguments["tracks"]
            if "diskname" in arguments:
                params["diskname"] = arguments["diskname"]
            result = await api_put(f"/v1/files/{quote(arguments['path'])}:create_d64", **params)
        elif name == "create_d71":
            params = {}
            if "diskname" in arguments:
                params["diskname"] = arguments["diskname"]
            result = await api_put(f"/v1/files/{quote(arguments['path'])}:create_d71", **params)
        elif name == "create_d81":
            params = {}
            if "diskname" in arguments:
                params["diskname"] = arguments["diskname"]
            result = await api_put(f"/v1/files/{quote(arguments['path'])}:create_d81", **params)
        
        # File Upload
        elif name == "upload_file_ftp":
            result = ftp_upload_file(arguments["local_path"], arguments["remote_path"])
        elif name == "tokenize_basic":
            tokenizer = BasicTokenizer()
            prg_bytes = tokenizer.tokenize_basic(arguments["source"])
            result = {
                "prg_hex": prg_bytes.hex(),
                "size": len(prg_bytes),
            }
        elif name == "tokenize_and_run_basic":
            tokenizer = BasicTokenizer()
            prg_bytes = tokenizer.tokenize_basic(arguments["source"])
            result = await api_post("/v1/runners:run_prg", data=prg_bytes)
            # After loading, type RUN into keyboard buffer to execute BASIC programs
            await api_put("/v1/machine:writemem", address="00C6", data="00")
            await api_put("/v1/machine:writemem", address="0277", data="52554E0D")
            await api_put("/v1/machine:writemem", address="00C6", data="04")
        elif name == "tokenize_upload_and_run_basic":
            tokenizer = BasicTokenizer()
            prg_bytes = tokenizer.tokenize_basic(arguments["source"])
            remote_path = arguments["remote_path"]
            tmp_name = f"/tmp/c64-tokenized-{abs(hash(remote_path))}.prg"
            with open(tmp_name, "wb") as f:
                f.write(prg_bytes)
            upload_result = ftp_upload_file(tmp_name, remote_path)
            if "errors" in upload_result:
                result = upload_result
            else:
                result = await api_put("/v1/runners:run_prg", file=remote_path)
                # After loading, type RUN into keyboard buffer to execute BASIC programs
                await api_put("/v1/machine:writemem", address="00C6", data="00")
                await api_put("/v1/machine:writemem", address="0277", data="52554E0D")
                await api_put("/v1/machine:writemem", address="00C6", data="04")
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Format response
        if result is None:
            result = {"error": "No result returned"}
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"errors": [str(e)]}, indent=2)
        )]


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources (documentation, examples, etc.)."""
    return [
        Resource(
            uri="c64://docs/api",
            name="C64 Ultimate API Documentation",
            mimeType="text/plain",
            description="REST API documentation for C64 Ultimate"
        ),
        Resource(
            uri="c64://docs/quickstart",
            name="Quick Start Guide",
            mimeType="text/plain",
            description="Quick start guide for C64 development"
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "c64://docs/api":
        return """C64 Ultimate REST API Overview
        
Base URL: """ + C64_BASE_URL + """

Key Endpoints:
- GET /v1/version - Get API version
- PUT /v1/machine:reset - Reset C64
- PUT /v1/machine:reboot - Reboot C64
- PUT /v1/runners:run_prg?file=<path> - Load and run PRG file
- PUT /v1/machine:writemem?address=<hex>&data=<hex> - Write to memory
- GET /v1/machine:readmem?address=<hex>&length=<n> - Read from memory
- GET /v1/drives - Get drive info
- PUT /v1/drives/<drive>:mount?image=<path> - Mount disk image

For full documentation: https://1541u-documentation.readthedocs.io/en/latest/api/api_calls.html
"""
    elif uri == "c64://docs/quickstart":
        return """Quick Start Guide for C64 Ultimate Development

1. Upload your PRG file:
   - Use upload_file_ftp to upload your compiled program
   - Example: upload_file_ftp(local_path="./myprog.prg", remote_path="/usb0/myprog.prg")

2. Run your program:
   - Use run_prg to load and execute
   - Example: run_prg(file="/usb0/myprog.prg")

3. Debug with memory access:
   - Write to memory: write_memory(address="D020", data="0E")
   - Read from memory: read_memory(address="0400", length=40)

4. Manage disk images:
   - Create: create_d64(path="/usb0/work.d64")
   - Mount: mount_disk(drive="a", image="/usb0/work.d64")

FTP Server: """ + C64_FTP_HOST + """
"""
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run the MCP server."""
    logger.info(f"Starting C64 Ultimate MCP Server")
    logger.info(f"C64 Host: {C64_HOST}")
    logger.info(f"FTP Host: {C64_FTP_HOST}")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
