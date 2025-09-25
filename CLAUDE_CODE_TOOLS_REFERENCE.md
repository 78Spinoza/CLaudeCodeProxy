# Claude Code Tools Complete Reference & Translation Guide

This document provides comprehensive documentation of all Claude Code tools with their exact specifications and bidirectional translation requirements for proxy implementations.

## Overview

Claude Code provides 15+ specialized tools that enable complete software development workflows. When using alternative AI providers (GroqCloud, xAI, etc.), these tools must be translated through a 4-step bidirectional API bridge system.

---

## Complete Tool Inventory

### Core File Operations
1. **Read** - Read files from filesystem with line limits and offsets
2. **Write** - Write new files or overwrite existing ones
3. **Edit** - Perform exact string replacements in files
4. **MultiEdit** - Make multiple edits to a single file atomically

### Search & Navigation
5. **Grep** - Powerful search using ripgrep with regex support
6. **Glob** - Fast file pattern matching with glob patterns

### System Integration
7. **Bash** - Execute shell commands with background support
8. **BashOutput** - Retrieve output from running background bash shells
9. **KillShell** - Terminate background bash shells

### Web & External Resources
10. **WebFetch** - Fetch and process web content with AI
11. **WebSearch** - Search the web for current information

### Specialized Tools
12. **NotebookEdit** - Edit Jupyter notebook cells
13. **TodoWrite** - Task management and progress tracking
14. **ExitPlanMode** - Exit planning mode workflow
15. **Task** - Launch specialized agents for complex operations

---

## Detailed Tool Specifications

### 1. Read Tool

**Purpose**: Read files from the local filesystem

**Anthropic Format (Claude Code)**:
```json
{
  "name": "Read",
  "description": "Reads a file from the local filesystem. You can access any file directly by using this tool.",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "The absolute path to the file to read"
      },
      "limit": {
        "type": "number",
        "description": "The number of lines to read. Only provide if the file is too large to read at once."
      },
      "offset": {
        "type": "number",
        "description": "The line number to start reading from. Only provide if the file is too large to read at once"
      }
    },
    "required": ["file_path"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Read a file from the local filesystem",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The absolute path to the file to read"
        },
        "limit": {
          "type": "number",
          "description": "Number of lines to read (optional)"
        },
        "offset": {
          "type": "number",
          "description": "Starting line number (optional)"
        }
      },
      "required": ["file_path"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Reads up to 2000 lines by default
- Supports line offset and limit for large files
- Returns content in `cat -n` format with line numbers
- Supports images, PDFs, and Jupyter notebooks
- Truncates lines longer than 2000 characters

---

### 2. Write Tool

**Purpose**: Write files to the local filesystem

**Anthropic Format (Claude Code)**:
```json
{
  "name": "Write",
  "description": "Writes a file to the local filesystem.",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "The absolute path to the file to write (must be absolute, not relative)"
      },
      "content": {
        "type": "string",
        "description": "The content to write to the file"
      }
    },
    "required": ["file_path", "content"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "write_file",
    "description": "Write a file to the local filesystem",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The absolute path to the file to write"
        },
        "content": {
          "type": "string",
          "description": "The content to write to the file"
        }
      },
      "required": ["file_path", "content"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Overwrites existing files
- Must read file first if editing existing file
- Always prefer editing existing files over creating new ones

---

### 3. Edit Tool

**Purpose**: Perform exact string replacements in files

**Anthropic Format (Claude Code)**:
```json
{
  "name": "Edit",
  "description": "Performs exact string replacements in files.",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "The absolute path to the file to modify"
      },
      "old_string": {
        "type": "string",
        "description": "The text to replace"
      },
      "new_string": {
        "type": "string",
        "description": "The text to replace it with (must be different from old_string)"
      },
      "replace_all": {
        "type": "boolean",
        "description": "Replace all occurences of old_string (default false)",
        "default": false
      }
    },
    "required": ["file_path", "old_string", "new_string"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "edit_file",
    "description": "Perform exact string replacements in files",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The absolute path to the file to modify"
        },
        "old_string": {
          "type": "string",
          "description": "The text to replace"
        },
        "new_string": {
          "type": "string",
          "description": "The replacement text"
        },
        "replace_all": {
          "type": "boolean",
          "description": "Replace all occurrences (default false)"
        }
      },
      "required": ["file_path", "old_string", "new_string"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Requires unique old_string match unless replace_all=true
- Preserves exact indentation and formatting
- Must read file before editing

---

### 4. MultiEdit Tool

**Purpose**: Make multiple edits to a single file in one atomic operation

**Anthropic Format (Claude Code)**:
```json
{
  "name": "MultiEdit",
  "description": "Performs exact string replacements in files.",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "The absolute path to the file to modify"
      },
      "edits": {
        "type": "array",
        "description": "Array of edit operations to perform sequentially on the file",
        "items": {
          "type": "object",
          "properties": {
            "old_string": {
              "type": "string",
              "description": "The text to replace"
            },
            "new_string": {
              "type": "string",
              "description": "The text to replace it with"
            },
            "replace_all": {
              "type": "boolean",
              "description": "Replace all occurences of old_string (default false)",
              "default": false
            }
          },
          "required": ["old_string", "new_string"]
        }
      }
    },
    "required": ["file_path", "edits"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "multi_edit_file",
    "description": "Make multiple edits to a single file atomically",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The absolute path to the file to modify"
        },
        "edits": {
          "type": "array",
          "description": "Array of edit operations",
          "items": {
            "type": "object",
            "properties": {
              "old_string": {"type": "string"},
              "new_string": {"type": "string"},
              "replace_all": {"type": "boolean", "default": false}
            },
            "required": ["old_string", "new_string"],
            "additionalProperties": false
          }
        }
      },
      "required": ["file_path", "edits"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Sequential edit application in order provided
- Atomic operation (all succeed or none applied)
- Built on top of Edit tool functionality

---

### 5. Bash Tool

**Purpose**: Execute shell commands in persistent session with optional timeout

**Anthropic Format (Claude Code)**:
```json
{
  "name": "Bash",
  "description": "Executes a given bash command in a persistent shell session with optional timeout",
  "input_schema": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "The command to execute"
      },
      "description": {
        "type": "string",
        "description": "Clear, concise description of what this command does in 5-10 words"
      },
      "timeout": {
        "type": "number",
        "description": "Optional timeout in milliseconds (max 600000)"
      },
      "run_in_background": {
        "type": "boolean",
        "description": "Set to true to run this command in the background"
      }
    },
    "required": ["command"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "run_bash",
    "description": "Execute shell commands with timeout and background support",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {
          "type": "string",
          "description": "The command to execute"
        },
        "description": {
          "type": "string",
          "description": "Brief description of what the command does"
        },
        "timeout": {
          "type": "number",
          "description": "Timeout in milliseconds (default 120000)"
        },
        "run_in_background": {
          "type": "boolean",
          "description": "Run command in background (default false)"
        }
      },
      "required": ["command"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Persistent shell session across calls
- Background execution support
- Timeout control (max 10 minutes)
- Proper handling of file paths with spaces (requires double quotes)

---

### 6. Grep Tool

**Purpose**: Powerful search tool built on ripgrep

**Anthropic Format (Claude Code)**:
```json
{
  "name": "Grep",
  "description": "A powerful search tool built on ripgrep",
  "input_schema": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "The regular expression pattern to search for in file contents"
      },
      "path": {
        "type": "string",
        "description": "File or directory to search in (rg PATH). Defaults to current working directory."
      },
      "glob": {
        "type": "string",
        "description": "Glob pattern to filter files (e.g. \"*.js\", \"*.{ts,tsx}\") - maps to rg --glob"
      },
      "type": {
        "type": "string",
        "description": "File type to search (rg --type). Common types: js, py, rust, go, java, etc."
      },
      "output_mode": {
        "type": "string",
        "enum": ["content", "files_with_matches", "count"],
        "description": "Output mode: \"content\" shows matching lines, \"files_with_matches\" shows file paths, \"count\" shows match counts"
      },
      "-i": {
        "type": "boolean",
        "description": "Case insensitive search (rg -i)"
      },
      "-n": {
        "type": "boolean",
        "description": "Show line numbers in output (rg -n). Requires output_mode: \"content\""
      },
      "-A": {
        "type": "number",
        "description": "Number of lines to show after each match (rg -A)"
      },
      "-B": {
        "type": "number",
        "description": "Number of lines to show before each match (rg -B)"
      },
      "-C": {
        "type": "number",
        "description": "Number of lines to show before and after each match (rg -C)"
      },
      "multiline": {
        "type": "boolean",
        "description": "Enable multiline mode where . matches newlines (rg -U --multiline-dotall)"
      },
      "head_limit": {
        "type": "number",
        "description": "Limit output to first N lines/entries"
      }
    },
    "required": ["pattern"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "grep_search",
    "description": "Search file contents using powerful regex patterns",
    "parameters": {
      "type": "object",
      "properties": {
        "pattern": {
          "type": "string",
          "description": "Regular expression pattern to search for"
        },
        "path": {
          "type": "string",
          "description": "File or directory to search (optional)"
        },
        "glob": {
          "type": "string",
          "description": "Glob pattern to filter files (optional)"
        },
        "case_insensitive": {
          "type": "boolean",
          "description": "Case insensitive search (default false)"
        },
        "show_line_numbers": {
          "type": "boolean",
          "description": "Show line numbers (default false)"
        },
        "context_lines": {
          "type": "number",
          "description": "Number of context lines around matches"
        }
      },
      "required": ["pattern"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Full regex syntax support
- Multiple output modes (content/files/count)
- File type and glob filtering
- Context lines around matches
- Multiline pattern matching

---

### 7. Glob Tool

**Purpose**: Fast file pattern matching

**Anthropic Format (Claude Code)**:
```json
{
  "name": "Glob",
  "description": "Fast file pattern matching tool that works with any codebase size",
  "input_schema": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "The glob pattern to match files against"
      },
      "path": {
        "type": "string",
        "description": "The directory to search in. If not specified, the current working directory will be used."
      }
    },
    "required": ["pattern"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "search_files",
    "description": "Find files using glob patterns",
    "parameters": {
      "type": "object",
      "properties": {
        "pattern": {
          "type": "string",
          "description": "Glob pattern to match files (e.g., '**/*.js', '*.py')"
        },
        "path": {
          "type": "string",
          "description": "Directory to search in (optional, defaults to current)"
        }
      },
      "required": ["pattern"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Works with any codebase size
- Supports patterns like "**/*.js" or "src/**/*.ts"
- Returns file paths sorted by modification time

---

### 8. WebFetch Tool

**Purpose**: Fetch content from URLs and process with AI

**Anthropic Format (Claude Code)**:
```json
{
  "name": "WebFetch",
  "description": "Fetches content from a specified URL and processes it using an AI model",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "format": "uri",
        "description": "The URL to fetch content from"
      },
      "prompt": {
        "type": "string",
        "description": "The prompt to run on the fetched content"
      }
    },
    "required": ["url", "prompt"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "web_fetch",
    "description": "Fetch and analyze web content",
    "parameters": {
      "type": "object",
      "properties": {
        "url": {
          "type": "string",
          "description": "URL to fetch content from"
        },
        "prompt": {
          "type": "string",
          "description": "Instructions for processing the content"
        }
      },
      "required": ["url", "prompt"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Converts HTML to markdown
- AI-powered content processing
- 15-minute cache for repeated requests
- Automatic HTTP to HTTPS upgrade

---

### 9. WebSearch Tool

**Purpose**: Search the web for current information

**Anthropic Format (Claude Code)**:
```json
{
  "name": "WebSearch",
  "description": "Allows Claude to search the web and use the results to inform responses",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "minLength": 2,
        "description": "The search query to use"
      },
      "allowed_domains": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Only include search results from these domains"
      },
      "blocked_domains": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Never include search results from these domains"
      }
    },
    "required": ["query"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "web_search",
    "description": "Search the web for current information",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Search query"
        },
        "domains": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Specific domains to search (optional)"
        }
      },
      "required": ["query"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Up-to-date information access
- Domain filtering support
- Current events and recent data
- US availability only

---

### 10. TodoWrite Tool

**Purpose**: Create and manage structured task lists

**Anthropic Format (Claude Code)**:
```json
{
  "name": "TodoWrite",
  "description": "Use this tool to create and manage a structured task list for your current coding session",
  "input_schema": {
    "type": "object",
    "properties": {
      "todos": {
        "type": "array",
        "description": "The updated todo list",
        "items": {
          "type": "object",
          "properties": {
            "content": {
              "type": "string",
              "minLength": 1,
              "description": "Task description (imperative form)"
            },
            "status": {
              "type": "string",
              "enum": ["pending", "in_progress", "completed"],
              "description": "Task status"
            },
            "activeForm": {
              "type": "string",
              "minLength": 1,
              "description": "Present continuous form of task"
            }
          },
          "required": ["content", "status", "activeForm"]
        }
      }
    },
    "required": ["todos"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "manage_todos",
    "description": "Create and manage task lists for project tracking",
    "parameters": {
      "type": "object",
      "properties": {
        "todos": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "content": {"type": "string"},
              "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"]
              },
              "activeForm": {"type": "string"}
            },
            "required": ["content", "status", "activeForm"],
            "additionalProperties": false
          }
        }
      },
      "required": ["todos"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Task state management (pending/in_progress/completed)
- Progress tracking across sessions
- Organizational support for complex tasks
- Real-time status updates

---

### 11. NotebookEdit Tool

**Purpose**: Edit Jupyter notebook cells

**Anthropic Format (Claude Code)**:
```json
{
  "name": "NotebookEdit",
  "description": "Completely replaces the contents of a specific cell in a Jupyter notebook (.ipynb file)",
  "input_schema": {
    "type": "object",
    "properties": {
      "notebook_path": {
        "type": "string",
        "description": "The absolute path to the Jupyter notebook file to edit"
      },
      "new_source": {
        "type": "string",
        "description": "The new source for the cell"
      },
      "cell_id": {
        "type": "string",
        "description": "The ID of the cell to edit"
      },
      "cell_type": {
        "type": "string",
        "enum": ["code", "markdown"],
        "description": "The type of the cell (code or markdown)"
      },
      "edit_mode": {
        "type": "string",
        "enum": ["replace", "insert", "delete"],
        "description": "The type of edit to make (replace, insert, delete)"
      }
    },
    "required": ["notebook_path", "new_source"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "edit_notebook",
    "description": "Edit Jupyter notebook cells",
    "parameters": {
      "type": "object",
      "properties": {
        "notebook_path": {
          "type": "string",
          "description": "Path to Jupyter notebook file"
        },
        "new_source": {
          "type": "string",
          "description": "New cell content"
        },
        "cell_index": {
          "type": "number",
          "description": "Cell index to edit (0-based)"
        },
        "cell_type": {
          "type": "string",
          "enum": ["code", "markdown"],
          "description": "Cell type"
        },
        "operation": {
          "type": "string",
          "enum": ["replace", "insert", "delete"],
          "description": "Edit operation"
        }
      },
      "required": ["notebook_path", "new_source"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Cell-level editing capabilities
- Support for code and markdown cells
- Insert, replace, and delete operations
- Works with .ipynb files

---

### 12. BashOutput Tool

**Purpose**: Retrieve output from running background bash shells

**Anthropic Format (Claude Code)**:
```json
{
  "name": "BashOutput",
  "description": "Retrieves output from a running or completed background bash shell",
  "input_schema": {
    "type": "object",
    "properties": {
      "bash_id": {
        "type": "string",
        "description": "The ID of the background shell to retrieve output from"
      },
      "filter": {
        "type": "string",
        "description": "Optional regular expression to filter the output lines"
      }
    },
    "required": ["bash_id"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "get_bash_output",
    "description": "Get output from background bash processes",
    "parameters": {
      "type": "object",
      "properties": {
        "bash_id": {
          "type": "string",
          "description": "Background shell ID"
        },
        "filter": {
          "type": "string",
          "description": "Regex filter for output lines (optional)"
        }
      },
      "required": ["bash_id"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Monitor long-running processes
- Regex filtering of output
- Returns only new output since last check

---

### 13. KillShell Tool

**Purpose**: Terminate running background bash shells

**Anthropic Format (Claude Code)**:
```json
{
  "name": "KillShell",
  "description": "Kills a running background bash shell by its ID",
  "input_schema": {
    "type": "object",
    "properties": {
      "shell_id": {
        "type": "string",
        "description": "The ID of the background shell to kill"
      }
    },
    "required": ["shell_id"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "kill_bash_shell",
    "description": "Terminate background bash processes",
    "parameters": {
      "type": "object",
      "properties": {
        "shell_id": {
          "type": "string",
          "description": "Shell ID to terminate"
        }
      },
      "required": ["shell_id"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Clean termination of background processes
- Success/failure status reporting
- Resource cleanup

---

### 14. ExitPlanMode Tool

**Purpose**: Exit planning mode after presenting implementation plan

**Anthropic Format (Claude Code)**:
```json
{
  "name": "ExitPlanMode",
  "description": "Use this tool when you are in plan mode and have finished presenting your plan and are ready to code",
  "input_schema": {
    "type": "object",
    "properties": {
      "plan": {
        "type": "string",
        "description": "The plan you came up with, that you want to run by the user for approval. Supports markdown."
      }
    },
    "required": ["plan"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "exit_plan_mode",
    "description": "Exit planning mode with implementation plan",
    "parameters": {
      "type": "object",
      "properties": {
        "plan": {
          "type": "string",
          "description": "Implementation plan (markdown supported)"
        }
      },
      "required": ["plan"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Used only for coding implementation tasks
- Supports markdown formatting
- Transitions from planning to execution

---

### 15. Task Tool (Agent Delegation)

**Purpose**: Launch specialized agents for complex operations

**Anthropic Format (Claude Code)**:
```json
{
  "name": "Task",
  "description": "Launch a new agent to handle complex, multi-step tasks autonomously",
  "input_schema": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "A short (3-5 word) description of the task"
      },
      "prompt": {
        "type": "string",
        "description": "The task for the agent to perform"
      },
      "subagent_type": {
        "type": "string",
        "description": "The type of specialized agent to use for this task"
      }
    },
    "required": ["description", "prompt", "subagent_type"]
  }
}
```

**OpenAI Format (GroqCloud/xAI)**:
```json
{
  "type": "function",
  "function": {
    "name": "delegate_task",
    "description": "Delegate complex tasks to specialized agents",
    "parameters": {
      "type": "object",
      "properties": {
        "description": {
          "type": "string",
          "description": "Brief task description"
        },
        "prompt": {
          "type": "string",
          "description": "Detailed task instructions"
        },
        "agent_type": {
          "type": "string",
          "description": "Type of specialized agent"
        }
      },
      "required": ["description", "prompt", "agent_type"],
      "additionalProperties": false
    }
  }
}
```

**Key Features**:
- Specialized agent types (general-purpose, statusline-setup, output-style-setup)
- Complex multi-step task handling
- Autonomous operation capabilities

---

## Bidirectional Translation Architecture

### 4-Step Translation Process

**Step 1: Custom Tool Definition**
- Define OpenAI-compatible tools for GroqCloud/xAI
- Must include `"additionalProperties": false`
- Map Claude Code functionality to custom function names

**Step 2: AI Model Tool Selection**
- Alternative AI models receive custom tools
- Models use tools naturally in OpenAI format
- Generate tool calls with proper function names and arguments

**Step 3: Translation to Claude Code API** ⭐
- **Critical**: Translate custom tool calls TO Claude Code's native format
- Execute through Claude Code's actual tool implementations
- Not reimplementation - true API bridge to Claude Code tools

**Step 4: Response Translation**
- Format results back to OpenAI function calling format
- Maintain proper tool_call_id mapping
- Preserve error handling and response structure

### Implementation Requirements

**Schema Compliance**:
- OpenAI format requires `"additionalProperties": false`
- All parameters must be properly typed
- Required parameters must be specified

**Parameter Mapping**:
```python
def translate_parameters(anthropic_tool, openai_call):
    # Example for Read tool
    if anthropic_tool == "Read" and openai_call["function"]["name"] == "read_file":
        return {
            "file_path": openai_call["function"]["arguments"]["file_path"],
            "limit": openai_call["function"]["arguments"].get("limit"),
            "offset": openai_call["function"]["arguments"].get("offset")
        }
```

**Error Handling**:
- Preserve Claude Code error messages
- Map error types between formats
- Maintain debugging capabilities

---

## Complete Translation Mapping Table

| Claude Code Tool | Custom Function | Key Parameter Changes |
|------------------|-----------------|---------------------|
| Read | read_file | Direct mapping: file_path, limit, offset |
| Write | write_file | Direct mapping: file_path, content |
| Edit | edit_file | Direct mapping: file_path, old_string, new_string, replace_all |
| MultiEdit | multi_edit_file | Edits array structure preserved |
| Bash | run_bash | Direct mapping: command, timeout, run_in_background |
| Grep | grep_search | Simplified: pattern, path, case_insensitive, context_lines |
| Glob | search_files | Direct mapping: pattern, path |
| WebFetch | web_fetch | Direct mapping: url, prompt |
| WebSearch | web_search | Simplified: query, domains array |
| TodoWrite | manage_todos | Direct mapping: todos array structure |
| NotebookEdit | edit_notebook | cell_id → cell_index, edit_mode → operation |
| BashOutput | get_bash_output | bash_id, filter |
| KillShell | kill_bash_shell | shell_id |
| ExitPlanMode | exit_plan_mode | Direct mapping: plan |
| Task | delegate_task | subagent_type → agent_type |

---

## Usage Guidelines

### Best Practices for Proxy Implementation

1. **Always Validate Schema**: Ensure `"additionalProperties": false` in all OpenAI tools
2. **Preserve Parameter Semantics**: Maintain exact meaning of parameters across formats
3. **Handle Optional Parameters**: Properly handle missing optional parameters
4. **Error Translation**: Map error messages appropriately between formats
5. **Response Consistency**: Maintain response structure expectations

### Testing Strategy

1. **Schema Validation**: Test all tool schemas against OpenAI/GroqCloud requirements
2. **Parameter Mapping**: Verify all parameter translations work correctly
3. **Error Cases**: Test error handling and message preservation
4. **End-to-End**: Test complete workflows using translated tools
5. **Performance**: Measure translation overhead and optimize

---

This comprehensive reference enables complete proxy implementation for any alternative AI provider, ensuring full access to Claude Code's development tool ecosystem through proper bidirectional translation.
