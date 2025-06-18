#!/usr/bin/env python3
"""
Test script for the Claude code analysis API endpoint in opsight.py
"""

import requests
import json
import os

def test_claude_analysis_api():
    """Test the /analyze/code endpoint"""
    
    # API endpoint (adjust if running on different host/port)
    api_url = "http://localhost:5000/analyze/code"
    
    # Test cases
    test_cases = [
        {
            "name": "Analyze current directory",
            "payload": {
                "directory": ".",
                "prompt": "What does this codebase do? Provide a summary of the main components.",
                "max_files": 10,
                "extensions": [".py"]
            }
        },
        {
            "name": "Security analysis",
            "payload": {
                "directory": ".",
                "prompt": "Are there any potential security issues in this code? Look for hardcoded credentials, SQL injection risks, or other vulnerabilities.",
                "max_files": 5,
                "extensions": [".py", ".js"],
                "max_file_size": 50
            }
        },
        {
            "name": "Architecture review",
            "payload": {
                "directory": ".",
                "prompt": "Describe the software architecture. What design patterns are used and how are the components organized?",
                "max_files": 15
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            # Make the API request
            response = requests.post(
                api_url, 
                json=test_case['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=120  # Claude analysis can take a while
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Directory: {result['directory']}")
                print(f"Prompt: {result['prompt'][:100]}...")
                print(f"Analysis Options: {result['analysis_options']}")
                print(f"\nClaude's Analysis:")
                print("-" * 50)
                print(result['analysis'])
                
            else:
                print(f"❌ Error {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"Error: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure opsight.py is running on localhost:5000")
            print("   Start it with: python opsight.py")
        except requests.exceptions.Timeout:
            print("❌ Timeout: Claude analysis took too long (>120s)")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def test_error_cases():
    """Test error handling"""
    api_url = "http://localhost:5000/analyze/code"
    
    error_test_cases = [
        {
            "name": "Missing directory",
            "payload": {
                "prompt": "Analyze this code"
            },
            "expected_error": "Missing required parameter: directory"
        },
        {
            "name": "Missing prompt", 
            "payload": {
                "directory": "."
            },
            "expected_error": "Missing required parameter: prompt"
        },
        {
            "name": "Non-existent directory",
            "payload": {
                "directory": "/path/that/does/not/exist",
                "prompt": "Analyze this"
            },
            "expected_error": "Directory does not exist"
        }
    ]
    
    print(f"\n{'='*60}")
    print("Testing Error Cases")
    print(f"{'='*60}")
    
    for test_case in error_test_cases:
        print(f"\nTest: {test_case['name']}")
        
        try:
            response = requests.post(
                api_url,
                json=test_case['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get('error', '')
                if test_case['expected_error'] in error_message:
                    print(f"✅ Correctly returned 400 error: {error_message}")
                else:
                    print(f"⚠️  Expected error containing '{test_case['expected_error']}', got: {error_message}")
            else:
                print(f"❌ Expected 400 error, got {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure opsight.py is running")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Claude Code Analysis API Test")
    print("=" * 60)
    print("This script tests the new /analyze/code endpoint in opsight.py")
    print("\n🔧 Prerequisites:")
    print("1. opsight.py should be running (python opsight.py)")
    print("2. ddtool should be configured for Claude API access")
    print("3. ClaudeLocalAnalysis.py should be in the same directory")
    
    input("\nPress Enter to start the tests...")
    
    # Test successful cases
    test_claude_analysis_api()
    
    # Test error cases
    test_error_cases()
    
    print(f"\n{'='*60}")
    print("Testing completed!")
    print("Check opsight.log for detailed API request/response logs.") 