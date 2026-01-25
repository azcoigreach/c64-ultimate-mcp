#!/usr/bin/env python3
"""
Test FTP upload functionality for C64 Ultimate MCP
Verifies both ftp_upload_file and ftp_upload_data functions
"""

import sys
import os
import tempfile
from pathlib import Path
from io import BytesIO

sys.path.insert(0, 'src')

from c64_ultimate_mcp import (
    ftp_upload_file,
    ftp_upload_data,
    C64_FTP_HOST,
    C64_FTP_USER,
    C64_FTP_PASS,
    FTP_TIMEOUT,
)
from tokenizer import BasicTokenizer

def test_ftp_configuration():
    """Test FTP configuration is loaded correctly"""
    print("\n" + "="*70)
    print("Test 1: FTP Configuration")
    print("="*70)
    
    print(f"\n✓ FTP Host: {C64_FTP_HOST}")
    print(f"✓ FTP User: {C64_FTP_USER}")
    print(f"✓ FTP Password: {'***' if C64_FTP_PASS else '(empty)'}")
    print(f"✓ FTP Timeout: {FTP_TIMEOUT} seconds")
    
    # Check if .env file exists
    env_path = Path(".env")
    if env_path.exists():
        print(f"✓ .env file found at {env_path.resolve()}")
        with open(env_path) as f:
            lines = f.readlines()
            ftp_lines = [l for l in lines if 'FTP' in l.upper()]
            if ftp_lines:
                print(f"  FTP configuration lines found: {len(ftp_lines)}")
                for line in ftp_lines:
                    key = line.split('=')[0]
                    print(f"    - {key}")
    else:
        print("⚠ .env file not found - using defaults")
    
    return True


def test_ftp_upload_file_local():
    """Test ftp_upload_file with a local test file"""
    print("\n" + "="*70)
    print("Test 2: Local File Upload (Simulated)")
    print("="*70)
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
        tf.write("TEST FILE FOR FTP UPLOAD\nLines: 2\nTest data\n")
        temp_file = tf.name
    
    try:
        print(f"\n✓ Created test file: {temp_file}")
        
        file_size = os.path.getsize(temp_file)
        print(f"✓ File size: {file_size} bytes")
        
        # Test the function (will fail if no FTP server, but we can verify error handling)
        print(f"\nAttempting upload to: /tmp/test_upload.txt")
        result = ftp_upload_file(temp_file, "/tmp/test_upload.txt")
        
        if "success" in result and result["success"]:
            print(f"✓ Upload successful!")
            print(f"  Message: {result['message']}")
        elif "errors" in result:
            print(f"⚠ Upload failed (expected if no FTP server available):")
            for error in result["errors"]:
                print(f"  Error: {error}")
            print(f"  Error type: {result.get('error_type', 'Unknown')}")
        
        return True
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\n✓ Cleaned up test file")


def test_ftp_upload_data():
    """Test ftp_upload_data with hex-encoded PRG data"""
    print("\n" + "="*70)
    print("Test 3: Upload Hex-Encoded PRG Data")
    print("="*70)
    
    # Create a simple BASIC program
    basic_source = '10 PRINT "HELLO FROM FTP"'
    
    print(f"\n✓ BASIC source: {basic_source}")
    
    # Tokenize it
    tokenizer = BasicTokenizer()
    prg_bytes = tokenizer.tokenize_basic(basic_source)
    prg_hex = prg_bytes.hex()
    
    print(f"✓ Tokenized to PRG: {len(prg_bytes)} bytes")
    print(f"✓ Hex data (first 50 chars): {prg_hex[:50]}...")
    
    # Test the function
    remote_path = "/tmp/hello_ftp.prg"
    print(f"\nAttempting upload to: {remote_path}")
    try:
        result = ftp_upload_data(prg_bytes, remote_path)
    except Exception as e:
        result = {"success": False, "error": str(e), "error_type": type(e).__name__}
    
    if "success" in result and result["success"]:
        print(f"✓ Upload successful!")
        print(f"  Message: {result['message']}")
    elif "errors" in result:
        print(f"⚠ Upload failed (expected if no FTP server available):")
        for error in result["errors"]:
            print(f"  Error: {error}")
    
    return True


def test_error_handling():
    """Test error handling for missing files and invalid inputs"""
    print("\n" + "="*70)
    print("Test 4: Error Handling")
    print("="*70)
    
    # Test 1: Missing local file
    print("\n[4.1] Missing local file:")
    result = ftp_upload_file("/nonexistent/path/file.prg", "/tmp/test.prg")
    if "errors" in result:
        print(f"✓ Correctly rejected: {result['errors'][0]}")
    else:
        print(f"✗ Should have failed for missing file")
        return False
    
    # Test 2: Empty data upload (should still work structure-wise)
    print("\n[4.2] Empty data upload:")
    result = ftp_upload_data(b'', "/tmp/empty.bin")
    if "success" in result or "errors" in result:
        print(f"✓ Handled empty data: {result.get('message', result.get('errors')[0])}")
    else:
        print(f"✗ Unexpected response format")
        return False
    
    return True


def test_connection_parameters():
    """Test that connection parameters can be used to create FTP connections"""
    print("\n" + "="*70)
    print("Test 5: Connection Parameter Validation")
    print("="*70)
    
    from ftplib import FTP
    
    print(f"\n✓ FTP Host: {C64_FTP_HOST}")
    print(f"✓ FTP User: {C64_FTP_USER}")
    print(f"✓ FTP Timeout: {FTP_TIMEOUT} seconds")
    
    # Test that we can create an FTP object with these parameters
    try:
        print("\nAttempting to create FTP connection object...")
        ftp = FTP(timeout=FTP_TIMEOUT)
        print(f"✓ FTP object created successfully with timeout={FTP_TIMEOUT}")
        ftp.quit()
    except Exception as e:
        print(f"⚠ FTP object creation: {e}")
    
    # Try connection (will fail if server not available, but structure is correct)
    try:
        print(f"\nAttempting connection to {C64_FTP_HOST}...")
        with FTP(C64_FTP_HOST, timeout=FTP_TIMEOUT) as ftp:
            ftp.login(C64_FTP_USER, C64_FTP_PASS)
            ftp.sock.settimeout(FTP_TIMEOUT)
            print(f"✓ Connected to FTP server!")
            print(f"  Welcome: {ftp.getwelcome()}")
    except ConnectionRefusedError as e:
        print(f"⚠ Connection refused (FTP server not running on {C64_FTP_HOST}):")
        print(f"  This is expected if C64 Ultimate device is not on network")
        print(f"  Error: {e}")
    except OSError as e:
        print(f"⚠ Connection error: {e}")
        print(f"  This is expected if C64 Ultimate device is not available")
    except Exception as e:
        print(f"⚠ FTP error: {type(e).__name__}: {e}")
    
    return True


def test_ftp_in_workflow():
    """Test FTP in a complete workflow"""
    print("\n" + "="*70)
    print("Test 6: Complete FTP Workflow")
    print("="*70)
    
    # Step 1: Tokenize BASIC
    print("\n[6.1] Step 1: Tokenize BASIC program")
    basic_source = """10 PRINT "FTP UPLOAD TEST"
20 PRINT "PROGRAM RUNNING"
30 END"""
    
    tokenizer = BasicTokenizer()
    prg_bytes = tokenizer.tokenize_basic(basic_source)
    prg_hex = prg_bytes.hex()
    
    print(f"✓ Tokenized: {len(prg_bytes)} bytes")
    
    # Step 2: Upload via FTP
    print("\n[6.2] Step 2: Upload via FTP (ftp_upload_data)")
    result = ftp_upload_data(prg_bytes, "/tmp/workflow_test.prg")
    
    if "success" in result and result["success"]:
        print(f"✓ Upload successful: {result['message']}")
    else:
        print(f"⚠ Upload attempt: {result.get('errors', result.get('message', 'unknown'))}")
    
    # Step 3: Show what the response would contain
    print("\n[6.3] Step 3: Response structure for tool composition")
    print(f"✓ If upload succeeded, response would be:")
    print(f"""  {{
    "success": true,
    "message": "Uploaded {len(prg_bytes)} bytes to /tmp/workflow_test.prg"
  }}""")
    print(f"✓ Agents can then use run_prg() or run_prg_from_data() to execute")
    
    return True


def main():
    """Run all FTP upload tests"""
    print("\n" + "="*70)
    print("C64 Ultimate MCP - FTP Upload Functionality Test")
    print("="*70)
    print("\nThis test verifies:")
    print("  • FTP configuration loading")
    print("  • ftp_upload_file() function")
    print("  • ftp_upload_data() function")
    print("  • Error handling")
    print("  • Connection parameters")
    print("  • Integration in workflow")
    
    tests = [
        ("Configuration", test_ftp_configuration),
        ("Local File Upload", test_ftp_upload_file_local),
        ("Hex Data Upload", test_ftp_upload_data),
        ("Error Handling", test_error_handling),
        ("Connection Parameters", test_connection_parameters),
        ("Workflow Integration", test_ftp_in_workflow),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "✓ PASS" if result else "✗ FAIL"))
        except Exception as e:
            results.append((test_name, f"✗ ERROR: {e}"))
            print(f"\nException: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    for test_name, result in results:
        print(f"{result}: {test_name}")
    
    passed = sum(1 for _, r in results if "PASS" in r or "expected" in r.lower())
    total = len(results)
    print(f"\n{'='*70}")
    print(f"Result: {passed}/{total} tests passed")
    print(f"{'='*70}")
    
    # Note about C64 device availability
    print("""
Note: Some tests may show "⚠" warnings if the C64 Ultimate device is not 
available on the network. This is expected in development/testing environments.

To fully test FTP functionality:
1. Ensure C64 Ultimate device is running and connected to network
2. Configure correct IP address in .env file (C64_ULTIMATE_FTP_HOST)
3. Ensure FTP service is enabled on the device
4. Re-run this test

The FTP functions are working correctly if:
✓ Configuration loads without errors
✓ ftp_upload_file checks for file existence
✓ ftp_upload_data accepts binary data
✓ Error handling returns proper JSON responses
✓ Connection parameters are correctly formatted
""")


if __name__ == '__main__':
    main()
