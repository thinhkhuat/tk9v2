# CLI Interface - Component Context

## Purpose

The CLI Interface provides command-line access to TK9's deep research capabilities through two modes: interactive chat-style interface for iterative research and single-query mode for one-off research tasks. It serves as the primary user interface for local development and direct research execution without the web dashboard.

## Current Status: Production Ready

**Last Updated**: 2025-10-31
**Status**: ✅ Stable - Full-featured CLI with 1,400+ lines
**Entry Point**: `/main.py` → CLI modules

## Component-Specific Development Guidelines

### CLI Design Principles
- **User-Friendly**: Clear prompts, helpful error messages, progress indicators
- **Flexible**: Support both interactive and single-query modes
- **Configurable**: Command-line arguments for all major options
- **Integrated**: Direct access to multi-agent system
- **File Output**: Optional `--save-files` for persistent research outputs

### Argument Parsing Pattern
```python
parser = argparse.ArgumentParser(description="Deep Research MCP")
parser.add_argument("--research", "-r", help="Single query")
parser.add_argument("--tone", "-t", choices=["objective", "critical", ...])
parser.add_argument("--language", "-l", default="vi")
parser.add_argument("--save-files", action="store_true")
parser.add_argument("--verbose", "-v", action="store_true")
```

### Interactive Mode Pattern
```python
class InteractiveCLI:
    def run(self):
        while True:
            query = self.prompt_user()
            if query.startswith("/"):
                self.handle_command(query)
            else:
                await self.execute_research(query)
```

## Major Subsystem Organization

### 1. Main Entry Point (`/main.py` - 150 lines)
**Argument parsing and mode selection**

**Key Responsibilities**:
- Parse command-line arguments
- Route to interactive or single-query mode
- Display configuration on request
- Handle verbosity and output settings

**Usage Modes**:
```bash
# Interactive mode (default)
python main.py
python main.py --interactive

# Single-query mode
python main.py --research "AI trends in 2024"

# With options
python main.py -r "Climate change" -t critical -l vi --save-files

# Show configuration
python main.py --config
```

### 2. Interactive CLI (`cli/interactive.py` - 438 lines)
**Chat-style interactive research interface**

**Features**:
- REPL-style command loop
- Session history management
- Real-time progress updates
- Command system (slash commands)
- Graceful exit handling

**Interactive Commands**:
```
/help          - Show available commands
/config        - Display current configuration
/providers     - Show provider information
/history       - View research history
/clear         - Clear screen
/quit or /exit - Exit interactive mode
```

**Session Flow**:
```python
class InteractiveCLI:
    def __init__(self):
        self.history = []
        self.config = load_config()

    async def run(self):
        print(welcome_message())
        while True:
            query = await self.get_user_input()
            if query.startswith("/"):
                self.handle_command(query)
            else:
                await self.execute_research(query)
                self.history.append(query)
```

### 3. CLI Commands (`cli/commands.py` - 413 lines)
**Command execution and research orchestration**

**Responsibilities**:
- Execute research queries
- Display configuration information
- Show provider status
- Format and display results
- Handle errors gracefully

**Key Methods**:
```python
class CLICommands:
    @staticmethod
    async def execute_research(query: str, **options):
        """Execute single research query"""
        # Initialize multi-agent system
        task = create_research_task(query, options)
        orchestrator = ChiefEditorAgent(task, write_to_files=options.get('save_files'))
        result = orchestrator.run_research_task()
        return result

    @staticmethod
    def show_config():
        """Display current configuration"""
        config = load_current_config()
        display_formatted_config(config)

    @staticmethod
    def show_providers():
        """Display provider information"""
        providers = get_provider_status()
        display_provider_table(providers)
```

### 4. Provider Display (`cli/providers.py` - 303 lines)
**Provider configuration and status display**

**Features**:
- Format provider information
- Show API key status (masked)
- Display failover configuration
- Provider health indicators

**Display Format**:
```
╔═══════════════════════════════════════════════════════════╗
║             PROVIDER CONFIGURATION                         ║
╠═══════════════════════════════════════════════════════════╣
║ LLM Provider                                              ║
║   Primary:   google_gemini (gemini-2.5-flash-preview)    ║
║   Fallback:  openai (gpt-4)                              ║
║   Strategy:  fallback_on_error                           ║
║                                                           ║
║ Search Provider                                           ║
║   Primary:   brave                                        ║
║   Fallback:  tavily                                       ║
║   Strategy:  fallback_on_error                           ║
╚═══════════════════════════════════════════════════════════╝
```

### 5. CLI Utilities (`cli/utils.py` - 256 lines)
**Helper functions for CLI operations**

**Utilities**:
- Input validation and sanitization
- Output formatting (tables, boxes, colors)
- Progress indicators and spinners
- File path helpers
- Error message formatting

**Common Patterns**:
```python
def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format data as ASCII table"""
    pass

def show_progress(message: str) -> ProgressSpinner:
    """Display progress spinner"""
    pass

def format_error(error: Exception) -> str:
    """Format error for user-friendly display"""
    pass
```

## Architectural Patterns

### 1. Command Pattern
**Slash commands in interactive mode**

```python
COMMANDS = {
    "/help": show_help,
    "/config": show_config,
    "/providers": show_providers,
    "/history": show_history,
    "/quit": exit_cli
}

def handle_command(command: str):
    if command in COMMANDS:
        COMMANDS[command]()
    else:
        print(f"Unknown command: {command}")
```

### 2. Builder Pattern
**Research task construction**

```python
def create_research_task(query: str, **options) -> Dict[str, Any]:
    return {
        "query": query,
        "tone": options.get("tone", "objective"),
        "language": options.get("language", "vi"),
        "max_sections": options.get("max_sections", 5),
        "guidelines": options.get("guidelines", []),
        "publish_formats": ["md", "pdf", "docx"]
    }
```

### 3. Facade Pattern
**Simplified interface to complex multi-agent system**

CLI provides simple interface hiding complexity of:
- Multi-agent orchestration
- Provider management
- State management
- File output

### 4. Observer Pattern
**Progress updates during research**

```python
async def execute_research_with_progress(query: str):
    progress = ProgressIndicator()

    # Subscribe to research events
    def on_progress(phase: str, message: str):
        progress.update(phase, message)

    result = await run_research(query, on_progress=on_progress)
    progress.complete()
    return result
```

## Integration Points

### Upstream Dependencies
- **Multi-Agent System** (`/multi_agents/`) - Core research execution
- **Configuration** (`/multi_agents/config/`) - Settings and providers
- **Main Entry** (`/main.py`) - Application entry point

### Downstream Dependencies
- **Standard Input/Output** - Terminal I/O
- **File System** - Optional output to `./outputs/`
- **Environment Variables** - Configuration via `.env`

### Usage Patterns

**Single-Query Mode**:
```bash
python main.py -r "Research topic" [options]
```

**Interactive Mode**:
```bash
python main.py
> Enter your research question
> /help
> /config
> /quit
```

**With Web Dashboard**:
```bash
# Web dashboard internally uses similar patterns
cd web_dashboard
./start_dashboard.sh

# Dashboard calls multi_agents system directly
# CLI provides alternative interface
```

### Environment Variables
```bash
# Inherited from multi_agents configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_SEARCH_PROVIDER=brave
RESEARCH_LANGUAGE=vi

# CLI-specific (optional)
CLI_VERBOSITY=INFO
CLI_DEFAULT_TONE=objective
CLI_AUTO_SAVE=false
```

## Development Patterns

### Adding New Command
1. **Define Command Function**: Add to `cli/commands.py`
   ```python
   @staticmethod
   def new_command():
       """New command description"""
       # Implementation
       pass
   ```

2. **Register Command**: Add to interactive mode
   ```python
   # In interactive.py
   COMMANDS["/newcommand"] = CLICommands.new_command
   ```

3. **Add Help Text**: Update `/help` command
4. **Test**: Run in interactive mode and verify

### Adding New Argument
1. **Add to Parser**: Update `main.py`
   ```python
   parser.add_argument(
       "--new-option",
       help="Description",
       default="default_value"
   )
   ```

2. **Pass to Research**: Update task creation
   ```python
   task = {
       "query": query,
       "new_option": args.new_option,
       # ...
   }
   ```

3. **Document**: Update help text and examples

### Improving User Experience
```python
# Rich formatting
from rich.console import Console
from rich.table import Table

console = Console()

def display_results(results):
    table = Table(title="Research Results")
    table.add_column("Section")
    table.add_column("Content")

    for section in results:
        table.add_row(section["title"], section["summary"])

    console.print(table)
```

## Performance Considerations

### Startup Time
- **Current**: < 1 second for argument parsing
- **Interactive Mode**: Additional ~1 second for initialization
- **First Research**: ~2 seconds to initialize multi-agent system

### Memory Usage
- **CLI Overhead**: ~10 MB
- **Multi-Agent System**: ~150 MB (loaded on first research)
- **Total**: ~160 MB for research execution

### Response Times
- **Interactive Commands**: < 100ms
- **Configuration Display**: < 50ms
- **Research Execution**: 5-30 minutes (depends on query complexity)

## Common Issues and Solutions

### Issue: Command Not Found
**Symptom**: `python: command not found` or `python3: command not found`
**Solution**: Use full Python path: `python3.12 main.py`

### Issue: Module Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'cli'`
**Solution**: Run from project root: `cd tk9_source_deploy && python main.py`

### Issue: Interactive Mode Not Starting
**Symptom**: CLI exits immediately
**Solution**: Ensure no conflicting arguments, check terminal compatibility

### Issue: Output Files Not Created
**Symptom**: Research completes but no files in `./outputs/`
**Solution**: Use `--save-files` flag: `python main.py -r "query" --save-files`

### Issue: API Key Errors
**Symptom**: `RuntimeError: Missing API key`
**Solution**:
```bash
# Check configuration
python main.py --config

# Set API keys in .env
echo "GOOGLE_API_KEY=your_key" >> .env
```

## Cross-References

### Related Documentation
- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - Research execution backend
- **[Web Dashboard](/web_dashboard/CONTEXT.md)** - Alternative web-based interface
- **[Configuration](/multi_agents/config/CONTEXT.md)** - Provider and settings configuration
- **[CLI Capabilities](/docs/CLI_MCP_CAPABILITIES.md)** - Detailed CLI features
- **[CLI Quick Reference](/docs/CLI_QUICK_REFERENCE.md)** - Command reference

### Key Files
- `main.py:1-150` - Entry point and argument parsing
- `cli/interactive.py:1-438` - Interactive REPL implementation
- `cli/commands.py:1-413` - Command execution logic
- `cli/providers.py:1-303` - Provider display formatting
- `cli/utils.py:1-256` - CLI helper utilities

### External Dependencies
- **argparse** - Command-line argument parsing
- **asyncio** - Async research execution
- **sys/os** - System and file operations
- **rich** (optional) - Enhanced terminal formatting

---

*This component context provides architectural guidance for the CLI Interface. For usage examples, see `/docs/CLI_QUICK_REFERENCE.md`. For detailed command documentation, run `python main.py --help`.*
