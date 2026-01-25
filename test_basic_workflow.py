#!/usr/bin/env python3
"""
Test script to validate the BASIC tokenization workflow
Shows how agents should compose tools to process BASIC programs
"""

import sys
sys.path.insert(0, 'src')

from tokenizer import BasicTokenizer
import json

# Example BASIC programs
HELLO_WORLD = """10 PRINT "HELLO, WORLD!"
20 PRINT "THIS IS C64 BASIC"
"""

BORDER_DEMO = """10 FOR I=0 TO 15
20 POKE 53280,I
30 NEXT I
40 PRINT "COLOR CYCLE DONE"
"""

def test_workflow(name: str, source: str):
    """Test the recommended BASIC workflow"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    
    # Step 1: Tokenize BASIC to PRG
    print("\n[Step 1] Tokenize BASIC source to PRG")
    tokenizer = BasicTokenizer()
    prg_bytes = tokenizer.tokenize_basic(source)
    prg_hex = prg_bytes.hex()
    
    print(f"  ✓ Tokenized {len(source)} chars → {len(prg_bytes)} bytes")
    print(f"  ✓ PRG hex (first 50 chars): {prg_hex[:50]}...")
    
    # Output what agents would receive from tokenize_basic tool
    tool_result = {
        "prg_hex": prg_hex,
        "size": len(prg_bytes),
    }
    print(f"  ✓ Tool returns: {json.dumps(tool_result, indent=4)[:200]}...")
    
    # Step 2a: Option A - Run directly via DMA (using run_prg_from_data)
    print("\n[Step 2a] Recommended: Run directly via DMA")
    print("  Compose tools: tokenize_basic → run_prg_from_data")
    print("  • Call tokenize_basic(source) to get prg_hex")
    print("  • Call run_prg_from_data(data=prg_hex)")
    print("  • Benefits: No filesystem, immediate execution, no FTP needed")
    
    # Step 2b: Option B - Save locally (using write_prg_from_hex)  
    print("\n[Step 2b] Optional: Save to local file for inspection")
    print("  Compose tools: tokenize_basic → write_prg_from_hex")
    print("  • Call tokenize_basic(source) to get prg_hex")
    print("  • Call write_prg_from_hex(hex_string=prg_hex, local_path='...prg')")
    print("  • Benefits: Persists file locally for debugging/archiving")
    
    # Step 2c: Option C - Upload and run (using upload_prg_from_hex + run_prg)
    print("\n[Step 2c] Optional: Upload to C64 filesystem then run")
    print("  Compose tools: tokenize_basic → upload_prg_from_hex → run_prg")
    print("  • Call tokenize_basic(source) to get prg_hex")
    print("  • Call upload_prg_from_hex(hex_string=prg_hex, remote_path='/usb0/prog.prg')")
    print("  • Call run_prg(file='/usb0/prog.prg')")
    print("  • Benefits: Persists file on C64, can be run later without Mac")
    
    # Step 2d: Option D - Direct local→C64 workflow (using upload_and_run_prg)
    print("\n[Step 2d] Alternative: Direct local file upload and run")
    print("  Note: Only for when you have a local .prg file already")
    print("  Compose: write_prg_from_hex → upload_and_run_prg")
    
    print("\n" + "="*60)
    print("✓ Workflow test complete")
    print("="*60)


def validate_syntax():
    """Validate tokenizer produces valid PRG syntax"""
    print("\n" + "="*60)
    print("Validation: PRG Format Check")
    print("="*60)
    
    source = '10 PRINT "TEST"'
    tokenizer = BasicTokenizer()
    prg = tokenizer.tokenize_basic(source)
    
    # Check: PRG should start with 2-byte load address (0x01 0x08 = 0x0801)
    if prg[0:2] == b'\x01\x08':
        print(f"✓ Load address correct: $0801")
    else:
        print(f"✗ Load address incorrect: {prg[:2].hex()}")
        return False
    
    # Check: PRG should end with double zero (program terminator)
    if prg[-2:] == b'\x00\x00':
        print(f"✓ Program terminator present")
    else:
        print(f"✗ Program terminator missing: {prg[-2:].hex()}")
        return False
    
    # Check: Should match pre-compiled example
    import os
    if os.path.exists('examples/test_hello.bas'):
        with open('examples/test_hello.bas') as f:
            test_src = f.read()
        with open('examples/test_hello.prg', 'rb') as f:
            expected = f.read()
        
        test_prg = tokenizer.tokenize_basic(test_src)
        if test_prg == expected:
            print(f"✓ Matches pre-compiled example (test_hello.bas)")
        else:
            print(f"✗ Does not match pre-compiled example")
            return False
    
    print("\n✓ All validation checks passed")
    return True


if __name__ == '__main__':
    print("\n" + "="*60)
    print("C64 BASIC Tokenization Workflow Test")
    print("="*60)
    print("\nThis test demonstrates the recommended MCP tool composition")
    print("for working with C64 BASIC programs.")
    
    # Run validation
    if not validate_syntax():
        sys.exit(1)
    
    # Test different workflows
    test_workflow("Hello World", HELLO_WORLD)
    test_workflow("Border Demo", BORDER_DEMO)
    
    print("\n" + "="*60)
    print("Summary: MCP Tool Composition for BASIC Programs")
    print("="*60)
    print("""
CORE TOOL:
  • tokenize_basic(source) → returns prg_hex

EXECUTION OPTIONS (choose one):

  Option 1 - Direct DMA (fastest, no filesystem):
    tokenize_basic(source)
    → run_prg_from_data(data=prg_hex)

  Option 2 - Save locally then run on C64:
    tokenize_basic(source)
    → write_prg_from_hex(hex_string=prg_hex, local_path='...')
    → upload_file_ftp(local_path='...', remote_path='/usb0/...')
    → run_prg(file='/usb0/...')

  Option 3 - Direct hex to C64 upload:
    tokenize_basic(source)
    → upload_prg_from_hex(hex_string=prg_hex, remote_path='/usb0/...')
    → run_prg(file='/usb0/...')

REMOVED REDUNDANT TOOLS:
  ✗ tokenize_and_run_basic (use: tokenize_basic + run_prg_from_data)
  ✗ tokenize_upload_and_run_basic (use: tokenize_basic + upload_prg_from_hex + run_prg)

WHY REMOVED:
  - These convenience wrappers could be composed from existing tools
  - Keeping them would create redundancy in the tool landscape
  - Agents can easily compose these operations together
  - Follows microservice pattern: small, atomic tools that compose well
""")
    print("="*60)
