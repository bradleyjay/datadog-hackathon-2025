# Claude Local Analysis & Code Analyzer

A powerful Python script that uses Claude AI to analyze local directories and find files by reading actual file contents. This tool can provide deep insights into any repository or directory structure on your system.

## Features

### 🔍 File Finding
- Find specific files in any repository or directory
- Get file locations with context
- Search across different directory paths

### 📁 Universal Directory Analysis
- **Analyze ANY directory path** - absolute or relative
- Read and analyze actual file contents from any location
- Support for multiple file types and programming languages
- Intelligent filtering and size limits
- Deep code analysis and investigation

### 🔧 Advanced Path Handling
- **Flexible base directory** - Set any directory as your working base
- **Dynamic directory switching** - Change analysis context on the fly
- **Absolute and relative paths** - Works with ~/home, /usr/local, ./src, etc.
- **Smart path resolution** - Automatically resolves complex path relationships

### 🎯 Multi-Project Support
- Analyze multiple projects from a single script
- Compare codebases across different directories
- Generate insights across your entire development ecosystem

## Installation

1. Install Python dependencies:
```bash
pip install requests
```

2. Make the script executable:
```bash
chmod +x claude_file_finder.py
```

3. Ensure `ddtool` is installed and configured for authentication.

## Usage

### Basic File Finding (Any Directory)
```bash
# Find a file in current directory
./claude_file_finder.py --file "config.py"

# Find a file in a specific directory
./claude_file_finder.py --file "package.json" --target-dir ~/my-project

# Find files with a different base directory
./claude_file_finder.py --file "README.md" --base-dir /usr/local/src
```

### Universal Directory Analysis
```bash
# Analyze current directory
./claude_file_finder.py --analyze-dir .

# Analyze any absolute path
./claude_file_finder.py --analyze-dir /home/user/projects/my-app

# Analyze relative to home directory
./claude_file_finder.py --analyze-dir ~/Documents/code-projects

# Analyze with custom base directory
./claude_file_finder.py --analyze-dir src --base-dir ~/my-project

# Analyze system directories
./claude_file_finder.py --analyze-dir /etc --question "What configuration files are here?"
```

### Advanced Multi-Directory Analysis
```bash
# Compare two codebases
./claude_file_finder.py --analyze-dir ~/project-v1 --question "What's the architecture of this codebase?"
./claude_file_finder.py --analyze-dir ~/project-v2 --question "How does this architecture compare to the previous version?"

# Security audit across multiple projects
./claude_file_finder.py --analyze-dir ~/work-projects --extensions .py .js --question "Scan for security vulnerabilities"

# Technology stack analysis
./claude_file_finder.py --analyze-dir /usr/local/src --question "What programming languages and frameworks are used here?"
```

## Command Line Options

### Basic Options
- `--file, -f`: File to search for
- `--question, -q`: Custom question to ask Claude
- `--analyze-dir, -d`: Directory to analyze (any path - absolute or relative)

### Directory Control Options ⭐ NEW
- `--target-dir, -t`: Target directory for file searches and questions
- `--base-dir, -b`: Base directory for all operations (default: current directory)

### Analysis Options
- `--extensions`: File extensions to include (e.g., `.py .js .ts`)
- `--max-files`: Maximum files to analyze (default: 20)
- `--max-file-size`: Maximum file size in KB (default: 100)
- `--max-lines`: Maximum lines per file (default: 200)

### API Options
- `--datacenter`: Datacenter to use (default: us1.staging.dog)
- `--org-id`: Organization ID (default: 2)
- `--model`: Model to use (default: anthropic/claude-3-5-haiku-latest)
- `--max-tokens`: Maximum tokens in response (default: 2000)

### Performance Options
- `--no-file-tree`: Skip including file tree in request
- `--verbose, -v`: Verbose output with path information

## Programmatic Usage

```python
from claude_file_finder import ClaudeLocalAnalysis
import os

# Initialize with any base directory
analyzer = ClaudeLocalAnalysis(base_directory="~/my-projects")

# Analyze any directory by path
result = analyzer.analyze_any_directory(
    "/home/user/code/my-app",
    "What does this application do?"
)

# Change base directory dynamically
analyzer.set_base_directory("/usr/local/src")

# Find files in specific directories
result = analyzer.find_file("config.json", target_directory="~/my-app/src")

# Ask questions about different directories
result = analyzer.ask_question(
    "What's the security posture of this code?",
    target_directory="/path/to/sensitive-app"
)
```

## Path Examples

### Absolute Paths
```bash
# Unix/Linux/Mac paths
./claude_file_finder.py --analyze-dir /home/username/projects
./claude_file_finder.py --analyze-dir /usr/local/src
./claude_file_finder.py --analyze-dir /opt/applications

# Home directory expansion
./claude_file_finder.py --analyze-dir ~/Documents/code
./claude_file_finder.py --analyze-dir ~/.config
```

### Relative Paths
```bash
# Relative to current directory
./claude_file_finder.py --analyze-dir ./src
./claude_file_finder.py --analyze-dir ../other-project
./claude_file_finder.py --analyze-dir ../../shared-libraries

# Relative to base directory
./claude_file_finder.py --base-dir ~/projects --analyze-dir project-a/src
```

## Use Cases

### 🏢 Enterprise Code Analysis
- Audit multiple microservices across different repositories
- Analyze legacy codebases in various directories
- Security assessment of distributed applications

### 🔍 DevOps & Infrastructure
- Analyze configuration files across `/etc`, `/opt`, `/usr/local`
- Review Dockerfile and deployment scripts in multiple projects
- Infrastructure as Code analysis across directories

### 🎓 Learning & Education
- Study open source projects in `/usr/local/src`
- Compare different implementations of similar projects
- Understand coding patterns across various codebases

### 🛡️ Security Auditing
- Scan multiple applications for vulnerabilities
- Review configuration files across system directories
- Analyze third-party code in vendor directories

### 📊 Project Management
- Generate reports across multiple project directories
- Compare code quality between different teams/projects
- Track technology adoption across your organization

## Advanced Examples

### Multi-Project Security Audit
```bash
# Audit all Python projects in a directory tree
find ~/projects -name "*.py" -path "*/src/*" | head -10 | while read file; do
    dir=$(dirname "$file")
    ./claude_file_finder.py --analyze-dir "$dir" --extensions .py --question "Security audit: identify potential vulnerabilities"
done
```

### Technology Stack Discovery
```bash
# Discover what technologies are used across different projects
for dir in ~/projects/*/; do
    echo "Analyzing $dir"
    ./claude_file_finder.py --analyze-dir "$dir" --question "What programming languages, frameworks, and technologies are used here?"
done
```

### Configuration Analysis
```bash
# Analyze system configuration
./claude_file_finder.py --analyze-dir /etc --extensions .conf .cfg .json .yaml --question "What are the main system configurations?"
```

## File Analysis Features

### Universal Path Support
- **Absolute paths**: `/home/user/project`, `/usr/local/src`
- **Relative paths**: `./src`, `../other-project`
- **Home expansion**: `~/Documents`, `~user/projects`
- **Environment variables**: `$HOME/projects` (when expanded by shell)

### Smart Path Resolution
- **Base directory context**: All relative paths resolved from configurable base
- **Fallback mechanisms**: Tries base directory, then current directory
- **Path validation**: Warns about non-existent paths with fallbacks
- **Cross-platform**: Works on Linux, macOS, and Windows

### Enhanced Directory Traversal
- **Recursive analysis**: Walks entire directory trees
- **Smart filtering**: Excludes `.git`, `node_modules`, `__pycache__`, etc.
- **Size management**: Handles large directory trees efficiently
- **Permission handling**: Graceful handling of restricted directories

## Performance Considerations

- **Large directory trees**: Use `--max-files` to limit scope
- **Network filesystems**: May be slower, adjust timeouts accordingly
- **System directories**: Some may require special permissions
- **Memory usage**: Large analyses use more tokens and memory

## Tips for Best Results

1. **Start small**: Test with `--max-files 5` on new directories
2. **Use specific paths**: More specific paths give better results
3. **Filter by extension**: Use `--extensions` for focused analysis
4. **Iterate progressively**: Start broad, then drill down
5. **Combine approaches**: Use both file finding and directory analysis

## Security Considerations

- **Sensitive directories**: Be careful with `/etc`, `/var`, private directories
- **File permissions**: Script respects filesystem permissions
- **Data privacy**: File contents are sent to Claude API
- **System impact**: Large directory scans can be resource-intensive

## Troubleshooting

### Path Issues
- Use `--verbose` to see resolved paths
- Check directory existence with `ls -la /path/to/dir`
- Verify permissions with `ls -ld /path/to/dir`

### Performance Issues
- Reduce `--max-files` for large directories
- Use `--extensions` to filter file types
- Avoid scanning binary-heavy directories

### Authentication Issues
- Ensure `ddtool` works from any directory
- Check API permissions for your organization
- Verify network connectivity to API endpoint

The enhanced Claude Local Analysis tool now works as a universal code analysis tool that can investigate any directory on your system, making it perfect for DevOps, security auditing, project management, and code exploration across your entire development ecosystem! 