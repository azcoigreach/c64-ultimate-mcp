# BASIC Tokenization - Quick Reference for Agents

## MCP Tools Available

### Core Tool
- **`tokenize_basic`** - Converts BASIC V2 source code to PRG binary

### Execution Tools (Compose with tokenize_basic)
- **`run_prg_from_data`** - Execute PRG from hex-encoded data (no upload)
- **`upload_prg_from_hex`** - Upload hex-encoded PRG to C64 filesystem
- **`run_prg`** - Execute PRG from C64 filesystem
- **`write_prg_from_hex`** - Save hex-encoded PRG to local disk

---

## Recommended Workflows

### Fastest: Direct Execution (DMA)
```
tokenize_basic(source: str)
  → Contains "prg_hex"
  → run_prg_from_data(data: "${prg_hex}")
```

**Best for:** Quick testing, small programs

### Standard: Upload and Run
```
tokenize_basic(source: str)
  → Contains "prg_hex"
  → upload_prg_from_hex(hex_string: "${prg_hex}", remote_path: "/USB0/prog.prg")
  → run_prg(file: "/USB0/prog.prg")
```

**Best for:** Programs that need to be stored, complex workflows

### Local Save: Three-Step
```
tokenize_basic(source: str)
  → Contains "prg_hex"
  → write_prg_from_hex(hex_string: "${prg_hex}", local_path: "./prog.prg")
  → upload_and_run_prg(local_path: "./prog.prg", remote_path: "/USB0/prog.prg")
```

**Best for:** Iterative development, local caching

---

## Error Handling

### Character Validation Error
```json
{
  "errors": [
    "Line 10: Character '😀' (Unicode U+1F600) is not valid for C64 BASIC. 
    Only ASCII/PETSCII characters (0-255) are supported. (in string literal)"
  ]
}
```

**What it means:** The BASIC source contains a Unicode character outside ASCII range

**How to fix:**
1. Check line number in error message
2. Remove or replace the invalid character
3. Use only ASCII characters (0-127) or PETSCII (0-255)
4. For special characters, use `CHR$(code)` with numeric codes
5. Retry tokenization

### Successful Response
```json
{
  "prg_hex": "010816080a0099202248454c4c4f22000000",
  "size": 18
}
```

**Next step:** Use `prg_hex` value in execution tools

---

## Valid Characters

### Always Safe
- Letters: A-Z, a-z (C64 converts to uppercase)
- Numbers: 0-9
- Symbols: `!"#$%&'()*+,-./:;<=>?@[\]^_`
- Space, Tab, Newline
- Punctuation: `{}~|` 

### Extended ASCII (0-255)
- Extended ASCII characters with codes 128-255
- Special C64 characters (graphics, colors)
- Use in strings as-is: `PRINT CHR$(160)` is valid

### NOT Allowed
- Emoji: 😀🎮🚀
- Unicode beyond U+00FF: é, ñ, ü, etc.
- Control characters: Tab in strings (but OK in code)

### Workaround for Special Characters
```basic
10 PRINT CHR$(160) REM ©
20 PRINT CHR$(174) REM ®
```

---

## BASIC Syntax Reference

### Tokenized Keywords
```
END, FOR, NEXT, DATA, INPUT#, INPUT, DIM, READ, LET, GOTO, RUN,
IF, RESTORE, GOSUB, RETURN, REM, STOP, ON, WAIT, LOAD, SAVE, VERIFY,
DEF, POKE, PRINT#, PRINT, CONT, LIST, CLR, CMD, SYS, OPEN, CLOSE,
GET, NEW, TAB(, TO, FN, SPC(, THEN, NOT, STEP, AND, OR, SGN, INT,
ABS, USR, FRE, POS, SQR, RND, LOG, EXP, COS, SIN, TAN, ATN, PEEK,
LEN, STR$, VAL, ASC, CHR$, LEFT$, RIGHT$, MID$
```

### Comments
```basic
10 REM This is a comment
20 PRINT "Hello" REM Comments after code
```

### Strings
```basic
10 PRINT "String with special chars!@#$%"
20 PRINT "Newlines not allowed in strings"
30 PRINT "Quotes must be closed"
```

---

## Example Programs

### Hello World
```basic
10 PRINT "HELLO WORLD"
20 END
```

### Loop
```basic
10 FOR I=1 TO 10
20 PRINT I
30 NEXT I
40 END
```

### Function
```basic
10 DEF FN SQUARE(X)=X*X
20 PRINT FN SQUARE(5)
30 END
```

---

## Tool Reference

### tokenize_basic
```
Input:
  source: str (BASIC V2 source code)

Output (success):
  {
    "prg_hex": str (hex-encoded PRG data),
    "size": int (PRG size in bytes)
  }

Output (error):
  {
    "errors": [str] (list of error messages)
  }
```

### run_prg_from_data
```
Input:
  data: str (hex-encoded PRG, from prg_hex)

Output:
  {
    "success": bool,
    "message": str
  }
```

### upload_prg_from_hex
```
Input:
  hex_string: str (hex-encoded PRG)
  remote_path: str (path on C64, e.g., "/USB0/prog.prg")

Output:
  {
    "success": bool,
    "message": str
  }
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Character validation error | Remove non-ASCII characters or use CHR$() |
| "byte must be in range(0, 256)" | Use version with character validation |
| Program doesn't run | Check syntax, verify line numbers |
| Unicode emoji rejected | Convert to ASCII or use CHR$(code) |
| Program too large | Split into multiple files |

---

## Getting Help

1. **Check error messages** for line number and character
2. **Validate input** before tokenizing
3. **Test simple programs** first
4. **Use existing examples** as reference: `examples/*.bas`
5. **Inspect tokenizer output** with: `{"prg_hex": "..."}`

---

**Last Updated:** January 23, 2026  
**Status:** Ready for Production  
**MCP Version:** c64-ultimate-mcp
