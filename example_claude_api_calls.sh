#!/bin/bash

# Example API calls for the Claude code analysis endpoint in opsight.py
# Make sure opsight.py is running first: python opsight.py

echo "=== Claude Code Analysis API Examples ==="
echo

# Basic analysis of current directory
echo "1. Basic code analysis:"
echo "curl -X POST http://localhost:5000/analyze/code \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"directory\": \".\","
echo "    \"prompt\": \"What does this codebase do? Provide a summary of the main components.\","
echo "    \"max_files\": 10,"
echo "    \"extensions\": [\".py\"]"
echo "  }'"
echo

read -p "Press Enter to run this example..."
curl -X POST http://localhost:5000/analyze/code \
  -H 'Content-Type: application/json' \
  -d '{
    "directory": ".",
    "prompt": "What does this codebase do? Provide a summary of the main components.",
    "max_files": 10,
    "extensions": [".py"]
  }'

echo
echo
echo "2. Security analysis:"
echo "curl -X POST http://localhost:5000/analyze/code \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"directory\": \".\","
echo "    \"prompt\": \"Are there any security vulnerabilities in this code? Look for hardcoded credentials, SQL injection, or other issues.\","
echo "    \"max_files\": 5,"
echo "    \"extensions\": [\".py\", \".js\"],"
echo "    \"max_file_size\": 50"
echo "  }'"
echo

read -p "Press Enter to run this example..."
curl -X POST http://localhost:5000/analyze/code \
  -H 'Content-Type: application/json' \
  -d '{
    "directory": ".",
    "prompt": "Are there any security vulnerabilities in this code? Look for hardcoded credentials, SQL injection, or other issues.",
    "max_files": 5,
    "extensions": [".py", ".js"],
    "max_file_size": 50
  }'

echo
echo
echo "3. Architecture review:"
echo "curl -X POST http://localhost:5000/analyze/code \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"directory\": \".\","
echo "    \"prompt\": \"Describe the software architecture. What design patterns are used?\","
echo "    \"max_files\": 15"
echo "  }'"
echo

read -p "Press Enter to run this example..."
curl -X POST http://localhost:5000/analyze/code \
  -H 'Content-Type: application/json' \
  -d '{
    "directory": ".",
    "prompt": "Describe the software architecture. What design patterns are used?",
    "max_files": 15
  }'

echo
echo
echo "4. Analyze a specific directory:"
echo "curl -X POST http://localhost:5000/analyze/code \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"directory\": \"/tmp\","
echo "    \"prompt\": \"What files are in this system directory?\","
echo "    \"max_files\": 5"
echo "  }'"
echo

read -p "Press Enter to run this example..."
curl -X POST http://localhost:5000/analyze/code \
  -H 'Content-Type: application/json' \
  -d '{
    "directory": "/tmp",
    "prompt": "What files are in this system directory?",
    "max_files": 5
  }'

echo
echo
echo "5. Error example (missing directory):"
echo "curl -X POST http://localhost:5000/analyze/code \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"prompt\": \"Analyze this code\"}'"
echo

read -p "Press Enter to run this example..."
curl -X POST http://localhost:5000/analyze/code \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "Analyze this code"}'

echo
echo
echo "=== Examples completed! ==="
echo "Check opsight.log for detailed request/response logs." 