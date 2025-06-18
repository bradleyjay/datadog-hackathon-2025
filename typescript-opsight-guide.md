# Using Opsight API with Claude from TypeScript

## Quick Start

The opsight service provides a REST API endpoint to analyze code directories using Claude. Here's how to use it from TypeScript.

## Setup

```typescript
// Install axios for HTTP requests
// npm install axios

import axios from 'axios';

const OPSIGHT_BASE_URL = 'http://localhost:5000';
```

## Basic Code Analysis

```typescript
interface AnalysisRequest {
  directory: string;
  prompt: string;
  max_files?: number;
  max_file_size?: number; // KB
  max_lines?: number;
  extensions?: string[];
}

interface AnalysisResponse {
  success: boolean;
  directory: string;
  prompt: string;
  analysis_options: Record<string, any>;
  analysis: string; // Claude's response
}

async function analyzeCode(request: AnalysisRequest): Promise<string> {
  try {
    const response = await axios.post<AnalysisResponse>(
      `${OPSIGHT_BASE_URL}/analyze/code`,
      request,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 120000 // 2 minutes - Claude analysis can take time
      }
    );
    
    return response.data.analysis;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Analysis failed: ${error.response?.data?.error || error.message}`);
    }
    throw error;
  }
}
```

## Common Use Cases

### 1. General Code Review
```typescript
const analysis = await analyzeCode({
  directory: './src',
  prompt: 'What does this codebase do? Provide a summary of the main components.',
  max_files: 15,
  extensions: ['.ts', '.js', '.tsx']
});
```

### 2. Security Audit
```typescript
const securityReport = await analyzeCode({
  directory: './src',
  prompt: 'Are there any security vulnerabilities? Look for hardcoded secrets, SQL injection risks, or other issues.',
  max_files: 10,
  max_file_size: 50
});
```

### 3. Architecture Analysis
```typescript
const architectureReview = await analyzeCode({
  directory: './src',
  prompt: 'Describe the software architecture and design patterns used.',
  max_files: 20,
  extensions: ['.ts', '.tsx']
});
```

### 4. Bug Investigation
```typescript
const bugAnalysis = await analyzeCode({
  directory: './src/components',
  prompt: 'Look for potential bugs or code smells in these React components.',
  max_files: 8,
  extensions: ['.tsx', '.ts']
});
```

## Error Handling

```typescript
async function safeAnalyzeCode(request: AnalysisRequest): Promise<string | null> {
  try {
    return await analyzeCode(request);
  } catch (error) {
    console.error('Code analysis failed:', error);
    return null;
  }
}
```

## Complete Example

```typescript
import axios from 'axios';

class OpsightClient {
  constructor(private baseUrl = 'http://localhost:5000') {}

  async analyzeCode(
    directory: string,
    prompt: string,
    options: {
      maxFiles?: number;
      maxFileSize?: number;
      maxLines?: number;
      extensions?: string[];
    } = {}
  ): Promise<string> {
    const request = {
      directory,
      prompt,
      max_files: options.maxFiles || 20,
      max_file_size: options.maxFileSize || 100,
      max_lines: options.maxLines || 200,
      ...(options.extensions && { extensions: options.extensions })
    };

    const response = await axios.post(`${this.baseUrl}/analyze/code`, request, {
      timeout: 120000
    });

    return response.data.analysis;
  }
}

// Usage
const client = new OpsightClient();

async function main() {
  const analysis = await client.analyzeCode(
    './src',
    'Explain what this TypeScript code does and suggest improvements.',
    { 
      maxFiles: 10, 
      extensions: ['.ts', '.tsx'] 
    }
  );
  
  console.log('Claude Analysis:', analysis);
}
```

## Prerequisites

1. **Start opsight service**: `python opsight.py`
2. **Ensure ddtool is configured** for Claude API access
3. **Directory must exist** and be readable

## Parameters

| Parameter       | Required | Description                                       |
| --------------- | -------- | ------------------------------------------------- |
| `directory`     | ✅        | Path to analyze (absolute or relative)            |
| `prompt`        | ✅        | Question/instruction for Claude                   |
| `max_files`     | ❌        | Max files to include (default: 20)                |
| `max_file_size` | ❌        | Max file size in KB (default: 100)                |
| `max_lines`     | ❌        | Max lines per file (default: 200)                 |
| `extensions`    | ❌        | File extensions to include (e.g., ['.ts', '.js']) |

## Tips

- **Start small**: Use `max_files: 5-10` for initial testing
- **Filter by extension**: Specify relevant file types to avoid noise
- **Be specific**: Clear prompts get better Claude responses
- **Handle timeouts**: Claude analysis can take 30-120 seconds
- **Check logs**: See `opsight.log` for detailed request/response info 