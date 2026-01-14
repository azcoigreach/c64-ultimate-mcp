"""Utility functions for assembling 6502 code into PRG files.

Currently supports ca65 via subprocess, producing a PRG with a two-byte load
address header. Designed to allow swapping assemblers via environment
configuration in the future.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("c64-ultimate-mcp.assembler")

DEFAULT_ASSEMBLER = os.getenv("ASSEMBLER", "ca65").lower()
ASSEMBLER_PATH = os.getenv("ASSEMBLER_PATH", "ca65")
LD65_PATH = os.getenv("LD65_PATH", "ld65")
ASSEMBLER_TIMEOUT = int(os.getenv("ASSEMBLER_TIMEOUT", "30"))
SUPPORTED_ASSEMBLERS = {"ca65"}


@dataclass
class AssemblyResult:
    success: bool
    assembler: str
    load_address: int
    prg_hex: Optional[str]
    stdout: str
    stderr: str
    errors: list[str]


def _make_ld65_config(config_path: Path, load_address: int) -> None:
    """Write a minimal ld65 config that emits a flat binary image."""
    size = 0x10000 - load_address
    cfg = f"""
MEMORY {{
    MAIN: start = ${load_address:04X}, size = ${size:04X}, file = %O;
}}

SEGMENTS {{
    CODE: load = MAIN, type = ro, start = ${load_address:04X};
    RODATA: load = MAIN, type = ro, optional = yes;
    DATA: load = MAIN, type = rw, optional = yes;
    BSS: load = MAIN, type = bss, optional = yes;
    ZEROPAGE: load = MAIN, type = zp, optional = yes;
}}
"""
    config_path.write_text(cfg, encoding="ascii")


def assemble_source(source: str, load_address: int = 0x0801, assembler: Optional[str] = None) -> AssemblyResult:
    """Assemble 6502 source into PRG data using the configured assembler (ca65).

    Returns hex-encoded PRG contents (including the two-byte load address) plus
    stdout/stderr for diagnostics.
    """
    chosen = (assembler or DEFAULT_ASSEMBLER).lower()
    if chosen not in SUPPORTED_ASSEMBLERS:
        return AssemblyResult(
            success=False,
            assembler=chosen,
            load_address=load_address,
            prg_hex=None,
            stdout="",
            stderr="",
            errors=[f"Assembler '{chosen}' is not supported yet. Supported: {sorted(SUPPORTED_ASSEMBLERS)}"],
        )

    if not (0 <= load_address <= 0xFFFF):
        return AssemblyResult(
            success=False,
            assembler=chosen,
            load_address=load_address,
            prg_hex=None,
            stdout="",
            stderr="",
            errors=["load_address must be between 0x0000 and 0xFFFF"],
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_path = tmp / "program.asm"
        obj_path = tmp / "program.o"
        bin_path = tmp / "program.bin"
        cfg_path = tmp / "ld65.cfg"

        src_path.write_text(source, encoding="utf-8")
        _make_ld65_config(cfg_path, load_address)

        ca65_cmd = [ASSEMBLER_PATH, str(src_path), "-o", str(obj_path)]
        ld65_cmd = [LD65_PATH, "-C", str(cfg_path), "-o", str(bin_path), str(obj_path)]

        try:
            ca65_run = subprocess.run(
                ca65_cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=ASSEMBLER_TIMEOUT,
            )
        except FileNotFoundError:
            return AssemblyResult(
                success=False,
                assembler=chosen,
                load_address=load_address,
                prg_hex=None,
                stdout="",
                stderr="",
                errors=[f"Assembler executable not found: {ASSEMBLER_PATH}"],
            )
        except subprocess.TimeoutExpired:
            return AssemblyResult(
                success=False,
                assembler=chosen,
                load_address=load_address,
                prg_hex=None,
                stdout="",
                stderr="",
                errors=["Assembly timed out while running ca65"],
            )

        if ca65_run.returncode != 0:
            return AssemblyResult(
                success=False,
                assembler=chosen,
                load_address=load_address,
                prg_hex=None,
                stdout=ca65_run.stdout,
                stderr=ca65_run.stderr,
                errors=["ca65 failed"] + ([ca65_run.stderr.strip()] if ca65_run.stderr.strip() else []),
            )

        try:
            ld65_run = subprocess.run(
                ld65_cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=ASSEMBLER_TIMEOUT,
            )
        except FileNotFoundError:
            return AssemblyResult(
                success=False,
                assembler=chosen,
                load_address=load_address,
                prg_hex=None,
                stdout=ca65_run.stdout,
                stderr="",
                errors=[f"Linker executable not found: {LD65_PATH}"],
            )
        except subprocess.TimeoutExpired:
            return AssemblyResult(
                success=False,
                assembler=chosen,
                load_address=load_address,
                prg_hex=None,
                stdout=ca65_run.stdout,
                stderr="",
                errors=["Link step timed out while running ld65"],
            )

        if ld65_run.returncode != 0:
            return AssemblyResult(
                success=False,
                assembler=chosen,
                load_address=load_address,
                prg_hex=None,
                stdout=ca65_run.stdout + ld65_run.stdout,
                stderr=ld65_run.stderr,
                errors=["ld65 failed"] + ([ld65_run.stderr.strip()] if ld65_run.stderr.strip() else []),
            )

        payload = bin_path.read_bytes()
        prg = load_address.to_bytes(2, "little") + payload

        return AssemblyResult(
            success=True,
            assembler=chosen,
            load_address=load_address,
            prg_hex=prg.hex(),
            stdout=ca65_run.stdout + ld65_run.stdout,
            stderr=ca65_run.stderr + ld65_run.stderr,
            errors=[],
        )
