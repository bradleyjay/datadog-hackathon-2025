#!/usr/bin/env python3
"""
Example usage of the ClaudeLocalAnalysis class.
Shows how to use the script programmatically with any directory path.
"""

from ClaudeLocalAnalysis import ClaudeLocalAnalysis
import os

def main():
    # Example 1: Initialize with current directory (default behavior)
    print("=== Example 1: Default initialization (current directory) ===")
    analyzer = ClaudeLocalAnalysis()
    result = analyzer.find_file("test_log_query.py")
    print(result[:200] + "...\n")
    
    # Example 2: Initialize with a specific base directory
    print("=== Example 2: Initialize with specific base directory ===")
    home_dir = os.path.expanduser("~")
    analyzer_with_base = ClaudeLocalAnalysis(base_directory=home_dir)
    result = analyzer_with_base.ask_question("What directories are in the home folder?")
    print(result[:200] + "...\n")
    
    # Example 3: Analyze any directory by absolute path
    print("=== Example 3: Analyze any directory by absolute path ===")
    analyzer = ClaudeLocalAnalysis()
    
    # Analyze a system directory (like /usr/local if it exists)
    system_dirs = ["/usr/local", "/opt", "/etc"]
    for sys_dir in system_dirs:
        if os.path.exists(sys_dir):
            result = analyzer.analyze_any_directory(
                sys_dir,
                f"What kind of files and directories are in {sys_dir}? Give a brief overview.",
                max_tokens=1000,
                analysis_options={
                    'max_files': 5,
                    'max_size_kb': 10,
                    'max_lines_per_file': 50
                }
            )
            print(f"Analysis of {sys_dir}:")
            print(result[:300] + "...\n")
            break
    
    # Example 4: Analyze a relative directory
    print("=== Example 4: Analyze relative directory ===")
    analyzer = ClaudeLocalAnalysis()
    result = analyzer.analyze_any_directory(
        ".",  # Current directory
        "What Python files are here and what do they do?",
        analysis_options={
            'extensions': ['.py'],
            'max_files': 5
        }
    )
    print(result[:400] + "...\n")
    
    # Example 5: Change base directory dynamically
    print("=== Example 5: Dynamic base directory changes ===")
    analyzer = ClaudeLocalAnalysis()
    
    # Change to a different base directory
    temp_dir = "/tmp" if os.path.exists("/tmp") else os.path.expanduser("~")
    analyzer.set_base_directory(temp_dir)
    
    result = analyzer.ask_question("What files are in this directory?")
    print(f"Files in {temp_dir}:")
    print(result[:200] + "...\n")
    
    # Example 6: Analyze different project directories
    print("=== Example 6: Multi-project analysis ===")
    analyzer = ClaudeLocalAnalysis()
    
    # Common project directories to check
    potential_projects = [
        "~/Desktop",
        "~/Documents",
        "~/Downloads",
        os.getcwd()
    ]
    
    for proj_path in potential_projects:
        expanded_path = os.path.expanduser(proj_path)
        if os.path.exists(expanded_path) and os.path.isdir(expanded_path):
            result = analyzer.analyze_any_directory(
                expanded_path,
                "Briefly describe what's in this directory. Are there any code projects?",
                analysis_options={
                    'max_files': 3,
                    'max_size_kb': 20,
                    'extensions': ['.py', '.js', '.ts', '.java', '.cpp', '.c']
                }
            )
            print(f"Analysis of {expanded_path}:")
            print(result[:250] + "...\n")
            break
    
    # Example 7: Security analysis of any directory
    print("=== Example 7: Security analysis ===")
    analyzer = ClaudeLocalAnalysis()
    result = analyzer.analyze_any_directory(
        ".",
        "Look for potential security issues in the code files. Check for hardcoded credentials, insecure practices, etc.",
        analysis_options={
            'extensions': ['.py', '.js', '.ts', '.json', '.yaml', '.yml'],
            'max_files': 10
        }
    )
    print("Security Analysis:")
    print(result[:400] + "...\n")
    
    # Example 8: Specific file analysis with target directory
    print("=== Example 8: File search in specific directory ===")
    analyzer = ClaudeLocalAnalysis()
    
    # Search for config files in home directory
    home_dir = os.path.expanduser("~")
    result = analyzer.find_file("config", target_directory=home_dir)
    print(f"Config files in {home_dir}:")
    print(result[:200] + "...\n")

if __name__ == "__main__":
    main() 