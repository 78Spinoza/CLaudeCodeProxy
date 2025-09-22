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

## 🚨 CRITICAL NEW DISCOVERIES - TodoWrite Implementation Guide

### **What We Learned About TodoWrite**

Based on comprehensive research of Claude Code's actual behavior and system prompts, TodoWrite is **THE MOST CRITICAL TOOL** for replicating Claude Code's workflow. Here's what proxy implementations must understand:

### **1. Mandatory Proactive Behavior**
- TodoWrite is not just a "nice to have" tool - it's **mandated by Claude Code's system prompt**
- The system explicitly states: "Use these tools VERY frequently" and "If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable"
- **FIRST ACTION** for any non-trivial task: Create todo list before any file operations

### **2. Complete State Replacement Architecture**
- Each TodoWrite call **overwrites the entire todo list** - no incremental updates
- Session storage: `~/.claude/todos/[session-id]-agent-[agent-id].json`
- Todo structure includes `id`, `priority` fields that were missing from original docs

### **3. Real-Time Progress Psychology**
- Visual progress indicators create user confidence: ✅🔧❌
- Shows `activeForm` for in_progress tasks, `content` for others
- Progress stats: "3/5 completed, 1 in progress, 1 pending"
- Provides "window into Claude's thinking" - users can steer mid-task

### **4. Translation Requirements for Proxy Success**

**Critical Schema Updates Needed**:
```json
{
  "id": {
    "type": "string",
    "description": "Unique task identifier - REQUIRED for session tracking"
  },
  "priority": {
    "type": "string", 
    "enum": ["high", "medium", "low"],
    "description": "Task priority - affects display and ordering"
  }
}
```

**Behavioral Prompting Required**:
```
SYSTEM INSTRUCTION for Groq/xAI models:
"You have access to the manage_todos tool. Use this tool VERY frequently to ensure 
you are tracking your tasks and giving the user visibility into your progress. 
For any non-trivial task, you MUST use manage_todos to create a plan before 
taking any other actions. If you do not use this tool when planning, you may 
forget important tasks - and that is unacceptable."
```

**Display Handler Implementation**:
```python
def display_todo_progress(todos):
    total = len(todos)
    completed = len([t for t in todos if t['status'] == 'completed'])
    in_progress = len([t for t in todos if t['status'] == 'in_progress'])
    pending = len([t for t in todos if t['status'] == 'pending'])
    
    print(f"📋 Progress: {completed}/{total} completed, {in_progress} in progress, {pending} pending")
    
    for i, todo in enumerate(todos, 1):
        icon = {'completed': '✅', 'in_progress': '🔧', 'pending': '❌'}[todo['status']]
        text = todo.get('activeForm', todo['content']) if todo['status'] == 'in_progress' else todo['content']
        priority = f"[{todo.get('priority', 'medium')}]"
        print(f"  {i}. {icon} {text} {priority}")
```

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
    
    # CRITICAL: TodoWrite translation with new fields
    elif anthropic_tool == "TodoWrite" and openai_call["function"]["name"] == "manage_todos":
        return {
            "todos": openai_call["function"]["arguments"]["todos"]
            # Must preserve id, priority fields for session persistence
        }
```

**Error Handling**:
- Preserve Claude Code error messages
- Map error types between formats
- Maintain debugging capabilities

---

## 🎯 Complete Translation Mapping Table (UPDATED)

| Claude Code Tool | Custom Function | Key Parameter Changes & Critical Notes |
|------------------|-----------------|-------------------------------------|
| Read | read_file | Direct mapping: file_path, limit, offset |
| Write | write_file | Direct mapping: file_path, content |
| Edit | edit_file | Direct mapping: file_path, old_string, new_string, replace_all |
| MultiEdit | multi_edit_file | Edits array structure preserved |
| Bash | run_bash | Direct mapping: command, timeout, run_in_background |
| Grep | grep_search | Simplified: pattern, path, case_insensitive, context_lines |
| Glob | search_files | Direct mapping: pattern, path |
| WebFetch | web_fetch | Direct mapping: url, prompt |
| WebSearch | web_search | Simplified: query, domains array |
| **TodoWrite** ⭐ | **manage_todos** | **CRITICAL**: todos array with id, priority fields; complete list replacement; mandatory proactive usage |
| NotebookEdit | edit_notebook | cell_id → cell_index, edit_mode → operation |
| BashOutput | get_bash_output | bash_id, filter |
| KillShell | kill_bash_shell | shell_id |
| ExitPlanMode | exit_plan_mode | Direct mapping: plan |
| Task | delegate_task | subagent_type → agent_type |

---

## 🚨 PROXY IMPLEMENTATION CHECKLIST

### **For Successful Claude Code Replication**:

**✅ TodoWrite Integration (MANDATORY)**:
- [ ] Implement complete schema with id, priority fields
- [ ] Add proactive usage instructions to system prompt
- [ ] Implement visual progress display with icons
- [ ] Store todos per session for persistence
- [ ] Always replace entire todo list, never partial updates
- [ ] Trigger automatically for complex tasks

**✅ Schema Compliance**:
- [ ] All OpenAI tools include `"additionalProperties": false`
- [ ] All parameters properly typed with descriptions
- [ ] Required parameters specified correctly

**✅ Behavioral Matching**:
- [ ] Groq/xAI models instructed to use manage_todos frequently
- [ ] First response to complex tasks creates todo list
- [ ] Progress updates shown throughout task execution
- [ ] Tasks marked completed immediately upon finish

**✅ Translation Layer**:
- [ ] Bidirectional parameter mapping implemented
- [ ] Error handling preserves original messages
- [ ] Tool call IDs properly managed
- [ ] Response formatting maintains consistency

---

## Usage Guidelines

### Best Practices for Proxy Implementation

1. **Always Validate Schema**: Ensure `"additionalProperties": false` in all OpenAI tools
2. **Preserve Parameter Semantics**: Maintain exact meaning of parameters across formats
3. **Handle Optional Parameters**: Properly handle missing optional parameters
4. **Error Translation**: Map error messages appropriately between formats
5. **Response Consistency**: Maintain response structure expectations
6. **TodoWrite Priority**: Implement TodoWrite first - it's the foundation of Claude Code workflow

### Testing Strategy

1. **Schema Validation**: Test all tool schemas against OpenAI/GroqCloud requirements
2. **Parameter Mapping**: Verify all parameter translations work correctly
3. **Error Cases**: Test error handling and message preservation
4. **End-to-End**: Test complete workflows using translated tools
5. **Performance**: Measure translation overhead and optimize
6. **TodoWrite Behavior**: Verify proactive todo creation and progress tracking

### 🎯 Success Metrics

A successful proxy implementation should:
- Create todo lists for any complex user request
- Show visual progress throughout task execution
- Match Claude Code's structured, methodical approach
- Provide transparency into AI reasoning process
- Enable mid-task course correction by users

---

This comprehensive reference enables complete proxy implementation for any alternative AI provider, ensuring full access to Claude Code's development tool ecosystem through proper bidirectional translation. The TodoWrite tool is particularly critical - it's not just another tool, but the foundational workflow orchestrator that makes Claude Code uniquely effective for development tasks.