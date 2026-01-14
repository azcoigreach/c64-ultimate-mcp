#!/usr/bin/env python3
"""
C64 BASIC V2 Tokenizer
Converts ASCII BASIC source to PRG (tokenized) format.
Aligns to the official BASIC V2 token map and handles strings, REM, and operators.
"""

import re
import sys
from pathlib import Path

# Complete C64 BASIC V2 token map (aligned to official list)
KEYWORDS = {
    "END": 0x80,
    "FOR": 0x81,
    "NEXT": 0x82,
    "DATA": 0x83,
    "INPUT#": 0x84,
    "INPUT": 0x85,
    "DIM": 0x86,
    "READ": 0x87,
    "LET": 0x88,
    "GOTO": 0x89,
    "RUN": 0x8A,
    "IF": 0x8B,
    "RESTORE": 0x8C,
    "GOSUB": 0x8D,
    "RETURN": 0x8E,
    "REM": 0x8F,
    "STOP": 0x90,
    "ON": 0x91,
    "WAIT": 0x92,
    "LOAD": 0x93,
    "SAVE": 0x94,
    "VERIFY": 0x95,
    "DEF": 0x96,
    "POKE": 0x97,
    "PRINT#": 0x98,
    "PRINT": 0x99,
    "CONT": 0x9A,
    "LIST": 0x9B,
    "CLR": 0x9C,
    "CMD": 0x9D,
    "SYS": 0x9E,
    "OPEN": 0x9F,
    "CLOSE": 0xA0,
    "GET": 0xA1,
    "NEW": 0xA2,
    "TAB(": 0xA3,
    "TO": 0xA4,
    "FN": 0xA5,
    "SPC(": 0xA6,
    "THEN": 0xA7,
    "NOT": 0xA8,
    "STEP": 0xA9,
    "+": 0xAA,
    "-": 0xAB,
    "*": 0xAC,
    "/": 0xAD,
    "^": 0xAE,
    "AND": 0xAF,
    "OR": 0xB0,
    ">": 0xB1,
    "=": 0xB2,
    "<": 0xB3,
    "SGN": 0xB4,
    "INT": 0xB5,
    "ABS": 0xB6,
    "USR": 0xB7,
    "FRE": 0xB8,
    "POS": 0xB9,
    "SQR": 0xBA,
    "RND": 0xBB,
    "LOG": 0xBC,
    "EXP": 0xBD,
    "COS": 0xBE,
    "SIN": 0xBF,
    "TAN": 0xC0,
    "ATN": 0xC1,
    "PEEK": 0xC2,
    "LEN": 0xC3,
    "STR$": 0xC4,
    "VAL": 0xC5,
    "ASC": 0xC6,
    "CHR$": 0xC7,
    "LEFT$": 0xC8,
    "RIGHT$": 0xC9,
    "MID$": 0xCA,
    "GO": 0xCB,
}


class BasicTokenizer:
    def __init__(self):
        # Sort keywords by length (longest first) for greedy matching
        self.keywords = sorted(KEYWORDS.items(), key=lambda x: -len(x[0]))

    def _is_word_char(self, ch: str) -> bool:
        return ch.isalnum() or ch == '$'

    def _boundary_ok(self, content: str, i: int, kw: str) -> bool:
        # Operators and special forms don't need boundary checks
        if kw in {"+", "-", "*", "/", "^", "=", ">", "<", "TAB(", "SPC("}:
            return True
        # 'FN' is tokenized even if followed by identifier
        if kw == "FN":
            # Only check start boundary
            if i > 0 and self._is_word_char(content[i - 1]):
                return False
            return True
        # Default: check start and end boundaries for word-like keywords
        start_ok = True
        end_ok = True
        if i > 0 and self._is_word_char(content[i - 1]):
            start_ok = False
        end_idx = i + len(kw)
        if end_idx < len(content) and self._is_word_char(content[end_idx]):
            end_ok = False
        return start_ok and end_ok

    def tokenize_line(self, content: str) -> bytearray:
        tokens = bytearray()
        i = 0
        in_string = False

        while i < len(content):
            ch = content[i]

            if in_string:
                tokens.append(ord(ch))
                if ch == '"':
                    in_string = False
                i += 1
                continue

            # Enter string literal
            if ch == '"':
                tokens.append(ord(ch))
                in_string = True
                i += 1
                continue

            # REM: rest of line is literal
            if content[i:i + 3].upper() == "REM" and self._boundary_ok(content, i, "REM"):
                tokens.append(KEYWORDS["REM"])
                i += 3
                # Copy rest of the line as-is
                while i < len(content):
                    tokens.append(ord(content[i]))
                    i += 1
                break

            # Greedy keyword match
            matched = False
            for kw, tok in self.keywords:
                if content[i:i + len(kw)].upper() == kw and self._boundary_ok(content, i, kw):
                    tokens.append(tok)
                    i += len(kw)
                    matched = True
                    break

            if matched:
                continue

            # Default: copy character
            tokens.append(ord(ch))
            i += 1

        return tokens

    def tokenize_basic(self, source: str) -> bytes:
        lines = source.strip().split('\n')

        start_addr = 0x0801
        program = bytearray()
        current_addr = start_addr

        for line in lines:
            line = line.rstrip()
            if not line or line.isspace():
                continue

            m = re.match(r'^(\d+)\s+(.*)', line)
            if not m:
                continue

            line_num = int(m.group(1))
            content = m.group(2) if m.group(2) is not None else ""

            tokens = self.tokenize_line(content)
            tokens.append(0x00)  # line end

            next_addr = current_addr + 4 + len(tokens)

            # [link][line#][tokens]
            program.extend(next_addr.to_bytes(2, 'little'))
            program.extend(line_num.to_bytes(2, 'little'))
            program.extend(tokens)

            current_addr = next_addr

        # Program terminator
        program.extend(b"\x00\x00")

        # Prepend load address
        return start_addr.to_bytes(2, 'little') + program


def main():
        if len(sys.argv) < 2:
            print("Usage: tokenizer.py <input.bas> [output.prg]")
            sys.exit(1)

        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix('.prg')

        if not input_path.exists():
            print(f"Error: {input_path} not found")
            sys.exit(1)

        source = input_path.read_text()

        tokenizer = BasicTokenizer()
        prg = tokenizer.tokenize_basic(source)

        output_path.write_bytes(prg)
        print(f"✓ Tokenized {input_path}")
        print(f"  Size: {len(prg)} bytes")
        print(f"  Output: {output_path}")


if __name__ == '__main__':
    main()
