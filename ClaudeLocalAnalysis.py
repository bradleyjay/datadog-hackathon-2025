#!/usr/bin/env python3
"""
Claude Local Analysis Script
Makes requests to Claude API to analyze local directories and find files.
"""

import requests
import json
import subprocess
import sys
import argparse
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class ClaudeLocalAnalysis:
    def __init__(self, datacenter: str = "us1.staging.dog", org_id: str = "2", base_directory: str = None):
        self.base_url = f"https://ai-gateway.{datacenter}/v1/chat/completions"
        self.datacenter = datacenter
        self.org_id = org_id
        self.base_directory = self._resolve_base_directory(base_directory)
        
    def _resolve_base_directory(self, base_directory: str = None) -> str:
        """Resolve and validate the base directory."""
        if base_directory is None:
            return os.getcwd()
        
        # Convert to absolute path
        abs_path = os.path.abspath(os.path.expanduser(base_directory))
        
        if not os.path.exists(abs_path):
            print(f"Warning: Directory {abs_path} does not exist. Using current directory.")
            return os.getcwd()
        
        if not os.path.isdir(abs_path):
            print(f"Warning: {abs_path} is not a directory. Using current directory.")
            return os.getcwd()
        
        return abs_path
    
    def set_base_directory(self, directory: str):
        """Change the base directory for analysis."""
        self.base_directory = self._resolve_base_directory(directory)
        print(f"Base directory set to: {self.base_directory}")
        
    def get_auth_token(self) -> str:
        """Get authentication token using ddtool command."""
        try:
            cmd = [
                "ddtool", "auth", "token", "rapid-ai-platform", 
                "--datacenter", self.datacenter, "--http-header"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error getting auth token: {e}")
            print(f"Make sure ddtool is installed and configured")
            sys.exit(1)
        except FileNotFoundError:
            print("ddtool command not found. Please install ddtool first.")
            sys.exit(1)
    
    def get_file_tree(self, directory: str = None, max_depth: int = 3) -> str:
        """Get the file tree structure of the repository."""
        target_dir = directory or self.base_directory
        
        try:
            # First try git ls-files if it's a git repo
            result = subprocess.run(
                ["git", "ls-files"], 
                cwd=target_dir, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                if files and files[0]:  # Make sure we got actual files
                    return f"Git-tracked files in {target_dir}:\n" + '\n'.join(sorted(files))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to find command
        try:
            cmd = ["find", ".", "-type", "f", "-not", "-path", "./.*", "-not", "-path", "*/node_modules/*", "-not", "-path", "*/__pycache__/*"]
            if max_depth:
                cmd.extend(["-maxdepth", str(max_depth)])
            
            result = subprocess.run(
                cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                files = [f.lstrip('./') for f in result.stdout.strip().split('\n') if f.strip()]
                return f"Files in {target_dir}:\n" + '\n'.join(sorted(files))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Last resort - basic ls
        try:
            result = subprocess.run(
                ["ls", "-la"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return f"Directory listing of {target_dir}:\n" + result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return f"Unable to retrieve file tree information for {target_dir}."
    
    def should_include_file(self, file_path: str, extensions: List[str] = None, 
                           max_size_kb: int = 100) -> bool:
        """Check if a file should be included in analysis."""
        # Skip binary and large files
        skip_extensions = {'.pyc', '.pyo', '.exe', '.bin', '.jpg', '.jpeg', '.png', 
                          '.gif', '.pdf', '.zip', '.tar', '.gz', '.so', '.dylib', '.dll'}
        
        file_ext = Path(file_path).suffix.lower()
        
        # Skip known binary files
        if file_ext in skip_extensions:
            return False
        
        # Check if file extension is in allowed list (if provided)
        if extensions and file_ext not in extensions:
            return False
        
        # Check file size
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_size_kb * 1024:
                return False
        except OSError:
            return False
        
        return True
    
    def read_file_safely(self, file_path: str, max_lines: int = 200) -> str:
        """Read file contents safely, handling encoding issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > max_lines:
                    content = ''.join(lines[:max_lines])
                    content += f"\n... [File truncated after {max_lines} lines] ..."
                else:
                    content = ''.join(lines)
                return content
        except UnicodeDecodeError:
            try:
                # Try with latin-1 encoding for files with special characters
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                    if len(lines) > max_lines:
                        content = ''.join(lines[:max_lines])
                        content += f"\n... [File truncated after {max_lines} lines] ..."
                    else:
                        content = ''.join(lines)
                    return content
            except Exception:
                return f"[Error: Could not read file {file_path} - binary or encoding issues]"
        except Exception as e:
            return f"[Error reading {file_path}: {str(e)}]"
    
    def resolve_directory_path(self, directory: str) -> str:
        """Resolve directory path relative to base directory or as absolute path."""
        if os.path.isabs(directory):
            return directory
        
        # Try relative to base directory first
        relative_to_base = os.path.join(self.base_directory, directory)
        if os.path.exists(relative_to_base):
            return relative_to_base
        
        # Try relative to current working directory
        relative_to_cwd = os.path.abspath(directory)
        if os.path.exists(relative_to_cwd):
            return relative_to_cwd
        
        # Return the relative to base path even if it doesn't exist (will be handled by analyze_directory)
        return relative_to_base
    
    def analyze_directory(self, directory: str = None, extensions: List[str] = None, 
                         max_files: int = 20, max_size_kb: int = 100,
                         max_lines_per_file: int = 200) -> str:
        """Analyze all files in a directory and return their contents."""
        target_dir = directory if directory else self.base_directory
        
        # Resolve the directory path
        if directory and not os.path.isabs(directory):
            target_dir = self.resolve_directory_path(directory)
        
        if not os.path.isdir(target_dir):
            return f"Directory {target_dir} does not exist."
        
        files_analyzed = []
        total_files = 0
        
        # Get all files in directory
        for root, dirs, files in os.walk(target_dir):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in {'__pycache__', 'node_modules', '.git', 'venv', 'env'}]
            
            for file in files:
                if total_files >= max_files:
                    break
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, target_dir)
                
                if self.should_include_file(file_path, extensions, max_size_kb):
                    content = self.read_file_safely(file_path, max_lines_per_file)
                    files_analyzed.append({
                        'path': relative_path,
                        'content': content
                    })
                    total_files += 1
            
            if total_files >= max_files:
                break
        
        if not files_analyzed:
            return f"No suitable files found in {target_dir} for analysis."
        
        # Format the analysis
        analysis = f"Directory Analysis: {target_dir}\n"
        analysis += f"Files analyzed: {len(files_analyzed)}\n"
        analysis += "=" * 80 + "\n\n"
        
        for file_info in files_analyzed:
            analysis += f"FILE: {file_info['path']}\n"
            analysis += "-" * 40 + "\n"
            analysis += file_info['content'] + "\n"
            analysis += "=" * 80 + "\n\n"
        
        return analysis
    
    def make_request(self, message: str, model: str = "anthropic/claude-3-5-haiku-latest", 
                    max_tokens: int = 1000, stream: bool = False, 
                    target_directory: str = None,
                    include_file_tree: bool = True, include_directory_analysis: str = None,
                    analysis_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Claude API."""
        
        # Get authentication token
        auth_header = self.get_auth_token()
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'source': 'aip-dev',
            'org-id': self.org_id,
        }
        
        # Parse and add the auth header
        if ':' in auth_header:
            header_name, header_value = auth_header.split(':', 1)
            headers[header_name.strip()] = header_value.strip()
        else:
            print(f"Warning: Unexpected auth header format: {auth_header}")
            headers['Authorization'] = auth_header
        
        # Determine the working directory for the request
        working_dir = target_directory or self.base_directory
        
        # Build enhanced message
        enhanced_message = message
        context_parts = []
        
        # Add file tree if requested
        if include_file_tree:
            print(f"Getting file tree information for {working_dir}...")
            file_tree = self.get_file_tree(working_dir)
            context_parts.append(f"Repository Structure:\n{file_tree}")
        
        # Add directory analysis if requested
        if include_directory_analysis:
            analysis_dir = include_directory_analysis
            if not os.path.isabs(analysis_dir):
                analysis_dir = self.resolve_directory_path(analysis_dir)
            
            print(f"Analyzing directory: {analysis_dir}")
            analysis_opts = analysis_options or {}
            dir_analysis = self.analyze_directory(
                analysis_dir,
                extensions=analysis_opts.get('extensions'),
                max_files=analysis_opts.get('max_files', 20),
                max_size_kb=analysis_opts.get('max_size_kb', 100),
                max_lines_per_file=analysis_opts.get('max_lines_per_file', 200)
            )
            context_parts.append(dir_analysis)
        
        # Combine all context
        if context_parts:
            context = "\n\n".join(context_parts)
            enhanced_message = f"""{context}

User question: {message}"""
        
        # Prepare request body
        data = {
            "model": model,
            "cwd": working_dir,
            "messages": [
                {"role": "user", "content": enhanced_message}
            ],
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        # Make the request
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                verify=False  # -k flag equivalent
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            sys.exit(1)
    
    def find_file(self, filename: str, target_directory: str = None, **kwargs) -> str:
        """Find a specific file by asking Claude."""
        message = f"Where is the file '{filename}' located? Please provide the exact path."
        kwargs['target_directory'] = target_directory or self.base_directory
        response = self.make_request(message, **kwargs)
        
        if 'choices' in response and response['choices']:
            return response['choices'][0]['message']['content']
        else:
            return "No response received from Claude"
    
    def ask_question(self, question: str, target_directory: str = None, **kwargs) -> str:
        """Ask Claude any question about the codebase."""
        kwargs['target_directory'] = target_directory or self.base_directory
        response = self.make_request(question, **kwargs)
        
        if 'choices' in response and response['choices']:
            return response['choices'][0]['message']['content']
        else:
            return "No response received from Claude"
    
    def investigate_directory(self, directory: str = None, question: str = None, **kwargs) -> str:
        """Investigate a directory by analyzing its file contents."""
        target_dir = directory or self.base_directory
        
        if not question:
            question = f"Analyze the code in this directory. What does this code do? What are the main components, functions, and how do they work together?"
        
        # Set up directory analysis
        kwargs['include_directory_analysis'] = target_dir
        kwargs['target_directory'] = target_dir
        
        response = self.make_request(question, **kwargs)
        
        if 'choices' in response and response['choices']:
            return response['choices'][0]['message']['content']
        else:
            return "No response received from Claude"
    
    def analyze_any_directory(self, directory_path: str, question: str = None, **kwargs) -> str:
        """Analyze any directory by its absolute or relative path."""
        abs_path = os.path.abspath(os.path.expanduser(directory_path))
        
        if not os.path.exists(abs_path):
            return f"Error: Directory {abs_path} does not exist."
        
        if not os.path.isdir(abs_path):
            return f"Error: {abs_path} is not a directory."
        
        if not question:
            question = f"Analyze the code in the directory {abs_path}. What does this code do? What are the main components and how do they work together?"
        
        # Temporarily set this as the working directory for analysis
        original_base = self.base_directory
        self.base_directory = abs_path
        
        try:
            result = self.investigate_directory(abs_path, question, **kwargs)
            return result
        finally:
            # Restore original base directory
            self.base_directory = original_base


def main():
    parser = argparse.ArgumentParser(description='Analyze local directories and find files using Claude API')
    parser.add_argument('--file', '-f', help='File to search for')
    parser.add_argument('--question', '-q', help='Custom question to ask Claude')
    parser.add_argument('--analyze-dir', '-d', help='Directory to analyze (reads file contents)')
    parser.add_argument('--target-dir', '-t', help='Target directory for file searches and questions')
    parser.add_argument('--base-dir', '-b', help='Base directory for all operations (default: current directory)')
    parser.add_argument('--extensions', nargs='+', help='File extensions to include (e.g. .py .js .ts)')
    parser.add_argument('--max-files', type=int, default=20, help='Maximum files to analyze')
    parser.add_argument('--max-file-size', type=int, default=100, help='Maximum file size in KB')
    parser.add_argument('--max-lines', type=int, default=200, help='Maximum lines per file')
    parser.add_argument('--datacenter', default='us1.staging.dog', help='Datacenter to use')
    parser.add_argument('--org-id', default='2', help='Organization ID')
    parser.add_argument('--model', default='anthropic/claude-3-5-haiku-latest', help='Model to use')
    parser.add_argument('--max-tokens', type=int, default=2000, help='Maximum tokens in response')
    parser.add_argument('--no-file-tree', action='store_true', help='Skip including file tree in request')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.file and not args.question and not args.analyze_dir:
        print("Please provide either --file, --question, or --analyze-dir")
        parser.print_help()
        sys.exit(1)
    
    # Initialize the analyzer with base directory
    base_dir = args.base_dir or os.getcwd()
    analyzer = ClaudeLocalAnalysis(
        datacenter=args.datacenter, 
        org_id=args.org_id,
        base_directory=base_dir
    )
    
    if args.verbose:
        print(f"Base directory: {analyzer.base_directory}")
        if args.target_dir:
            print(f"Target directory: {args.target_dir}")
    
    # Prepare analysis options
    analysis_options = {
        'extensions': args.extensions,
        'max_files': args.max_files,
        'max_size_kb': args.max_file_size,
        'max_lines_per_file': args.max_lines
    }
    
    # Prepare kwargs for the request
    request_kwargs = {
        'model': args.model,
        'max_tokens': args.max_tokens,
        'target_directory': args.target_dir,
        'include_file_tree': not args.no_file_tree,
        'analysis_options': analysis_options
    }
    
    try:
        if args.analyze_dir:
            print(f"Analyzing directory: {args.analyze_dir}")
            question = args.question or "Analyze this code directory. What does the code do? What are the main components and how do they work together?"
            result = analyzer.analyze_any_directory(args.analyze_dir, question, **request_kwargs)
        elif args.file:
            print(f"Searching for file: {args.file}")
            result = analyzer.find_file(args.file, args.target_dir, **request_kwargs)
        else:
            print(f"Asking question: {args.question}")
            result = analyzer.ask_question(args.question, args.target_dir, **request_kwargs)
        
        print("\nClaude's Response:")
        print("-" * 50)
        print(result)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main() 