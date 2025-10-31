# Validation Checklists

## Pre-Development Checklist

### Before Making Any Changes
- [ ] Read project CLAUDE.md and understand system architecture
- [ ] Check current working directory is `/Users/thinhkhuat/dev-local/multi-agent-deep-research/deep-research-mcp-og`
- [ ] Verify Python version is 3.13+ with `python --version`
- [ ] Confirm virtual environment is active
- [ ] Review recent git commits with `git log --oneline -5`
- [ ] Check git status to understand current changes

### Environment Verification
- [ ] `.env` file exists and contains required API keys
- [ ] `multi_agents/task.json` exists and is valid JSON
- [ ] `pyproject.toml` specifies Python 3.13+ requirement
- [ ] Required directories exist: `multi_agents/`, `multi_agents/agents/`, `multi_agents/providers/`
- [ ] No import errors when running `python -c "import multi_agents"`

### Understanding Current System
- [ ] Identify which agents already exist in `multi_agents/agents/`
- [ ] Understand the LangGraph workflow in `multi_agents/agents/orchestrator.py`
- [ ] Review provider system in `multi_agents/providers/` and `multi_agents/config/`
- [ ] Check BRAVE search integration in `multi_agents/simple_brave_retriever.py`
- [ ] Understand state management via `ResearchState` TypedDict

## Agent Development Checklist

### Before Creating New Agent
- [ ] Verify agent doesn't already exist
- [ ] Determine if existing agent can be modified instead
- [ ] Plan integration point in workflow
- [ ] Identify required inputs and outputs
- [ ] Check if new state fields are needed

### Agent Implementation
- [ ] Inherit from `BaseAgent` class
- [ ] Implement required `execute()` method with proper signature
- [ ] Include error handling with try/catch blocks
- [ ] Add logging and verbose output support
- [ ] Use `print_agent_output()` for consistent formatting
- [ ] Return string result (not dict or other types)

### Agent Integration
- [ ] Add import to `multi_agents/agents/__init__.py`
- [ ] Add agent to workflow in `orchestrator.py`
- [ ] Define state field in `ResearchState` TypedDict if needed
- [ ] Add workflow node function following naming pattern
- [ ] Connect with appropriate edges in workflow graph
- [ ] Test agent independently before integration

### Agent Testing
- [ ] Create unit test file in `tests/unit/`
- [ ] Test `execute()` method with and without LLM
- [ ] Test error handling scenarios
- [ ] Test with various input contexts
- [ ] Mock external dependencies appropriately
- [ ] Verify proper async/await usage

## Provider Development Checklist

### Before Creating New Provider
- [ ] Check if provider already exists in `multi_agents/providers/`
- [ ] Determine provider type: LLM or Search
- [ ] Research API documentation and authentication
- [ ] Plan model mappings and configurations
- [ ] Check rate limits and pricing considerations

### LLM Provider Implementation
- [ ] Inherit from `BaseLLMProvider`
- [ ] Implement `generate()` method with proper error handling
- [ ] Implement `generate_stream()` for streaming support
- [ ] Implement `get_available_models()` with actual model list
- [ ] Implement `validate_api_key()` for key verification
- [ ] Add cost information in `get_cost_per_token()`
- [ ] Use proper timeout and retry mechanisms

### Search Provider Implementation  
- [ ] Inherit from `BaseSearchProvider`
- [ ] Implement `search()` method returning standardized format
- [ ] Implement `search_news()` for news-specific searches
- [ ] Format results with required fields: title, url, snippet, published_date, source
- [ ] Handle pagination and result limits
- [ ] Add proper error handling for API failures

### Provider Registration
- [ ] Add provider to appropriate registry in `multi_agents/config/providers.py`
- [ ] Add model mappings if applicable
- [ ] Add API key mapping in `ProviderManager._get_api_key_for_provider()`
- [ ] Update `.env.example` with new environment variables
- [ ] Test provider independently before integration

## Workflow Modification Checklist

### Before Modifying Workflow
- [ ] Understand current workflow structure in `orchestrator.py`
- [ ] Map out existing nodes and edges
- [ ] Identify insertion point for new functionality
- [ ] Check if modification affects parallel execution
- [ ] Consider impact on state management

### Workflow Changes
- [ ] Update `ResearchState` TypedDict if new fields needed
- [ ] Add new node functions following async pattern
- [ ] Update workflow graph with new nodes/edges
- [ ] Handle conditional routing if applicable
- [ ] Maintain proper error propagation
- [ ] Test workflow execution order

### State Management
- [ ] New state fields have appropriate types
- [ ] State updates return proper dictionary format
- [ ] No state keys are overwritten unintentionally
- [ ] State passed correctly between nodes
- [ ] Cleanup of temporary state if needed

## Configuration Checklist

### Environment Configuration
- [ ] All required API keys are present in `.env`
- [ ] Provider configurations match available options
- [ ] Model names are correct and available
- [ ] BRAVE configuration includes `RETRIEVER=custom`
- [ ] No sensitive data committed to repository

### Task Configuration
- [ ] `multi_agents/task.json` is valid JSON
- [ ] All required fields are present
- [ ] Configuration values are within acceptable ranges
- [ ] Language codes are valid ISO codes
- [ ] Guidelines array is properly formatted

## Integration Testing Checklist

### System Integration
- [ ] All agents execute without errors
- [ ] Workflow completes end-to-end successfully
- [ ] File output generates correctly (if enabled)
- [ ] Translation workflow works (if configured)
- [ ] Provider switching works (if configured)

### API Integration
- [ ] BRAVE search returns results
- [ ] LLM providers generate responses
- [ ] Translation services respond correctly
- [ ] Rate limits are respected
- [ ] Error handling works for API failures

### Output Validation
- [ ] Generated reports have proper structure
- [ ] Markdown formatting is preserved
- [ ] File exports work for all formats (PDF, DOCX, MD)
- [ ] Translation preserves formatting
- [ ] Output directory structure is correct

## Error Handling Checklist

### Exception Handling
- [ ] All async functions have try/catch blocks
- [ ] Errors are logged with appropriate detail
- [ ] Graceful fallbacks are provided
- [ ] User-friendly error messages
- [ ] No bare `except:` clauses

### Resilience Features
- [ ] Retry mechanisms for transient failures
- [ ] Timeout handling for long-running operations
- [ ] Resource cleanup in finally blocks
- [ ] Circuit breaker patterns for external APIs
- [ ] Fallback providers configured if applicable

## Performance Checklist

### Resource Management
- [ ] Async context managers used for HTTP sessions
- [ ] No resource leaks in file operations
- [ ] Memory usage reasonable for large inputs
- [ ] Concurrent operation limits respected
- [ ] Proper cleanup of temporary files

### Optimization
- [ ] Parallel execution where appropriate
- [ ] Efficient data structures used
- [ ] Unnecessary API calls eliminated
- [ ] Caching implemented where beneficial
- [ ] Database queries optimized if applicable

## Security Checklist

### API Security
- [ ] API keys stored in environment variables only
- [ ] No hardcoded credentials in source code
- [ ] Proper authentication headers used
- [ ] SSL/TLS used for all API communications
- [ ] API rate limits respected

### Input Validation
- [ ] User inputs validated and sanitized
- [ ] File paths validated to prevent traversal
- [ ] No code injection vulnerabilities
- [ ] Proper error messages (no sensitive data leaked)
- [ ] Input length limits enforced

## Documentation Checklist

### Code Documentation
- [ ] Function docstrings explain purpose and parameters
- [ ] Complex logic has inline comments
- [ ] Type hints provided for function signatures
- [ ] Examples provided for complex functions
- [ ] Error conditions documented

### Configuration Documentation
- [ ] New environment variables documented in `.env.example`
- [ ] Configuration options explained
- [ ] Default values specified
- [ ] Required vs optional settings clarified
- [ ] Provider-specific requirements noted

## Deployment Checklist

### Pre-Deployment
- [ ] All tests pass locally
- [ ] Code follows project conventions
- [ ] No debug prints or temporary code left
- [ ] Dependencies properly specified in requirements
- [ ] Version numbers updated if applicable

### MCP Server Deployment
- [ ] MCP server starts without errors
- [ ] `deep_research` tool is exposed correctly
- [ ] Tool parameters are properly defined
- [ ] Tool returns expected response format
- [ ] No file writes in MCP mode (unless explicitly requested)

### CLI Deployment
- [ ] CLI interface works in interactive mode
- [ ] Single query mode functions correctly
- [ ] File saving works when enabled
- [ ] Help commands provide useful information
- [ ] Configuration display works properly

## Quality Assurance Checklist

### Code Quality
- [ ] Functions have single responsibility
- [ ] Code is readable and maintainable
- [ ] Consistent naming conventions used
- [ ] No code duplication
- [ ] Proper separation of concerns

### Testing Coverage
- [ ] Unit tests for new functions
- [ ] Integration tests for workflow changes
- [ ] Error path testing included
- [ ] Mock objects used appropriately
- [ ] Test data is realistic

### Review Checklist
- [ ] Code follows existing patterns
- [ ] No breaking changes to existing functionality
- [ ] Performance impact is acceptable
- [ ] Security implications considered
- [ ] Documentation is updated

## Final Validation

### Pre-Commit Checklist
- [ ] All checklists above completed
- [ ] Code compiles without warnings
- [ ] All tests pass
- [ ] No linting errors
- [ ] Git commit message is descriptive

### Verification Commands
```bash
# Run these commands before finalizing changes

# Check syntax
python -m py_compile multi_agents/main.py

# Run tests
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

# Check basic functionality
python main.py --config
python main.py --provider-info

# Test minimal functionality
python main.py --research "test query" --no-save-files

# Check imports
python -c "from multi_agents.main import run_research_task; print('✅ Import successful')"

# Verify MCP server
python mcp_server.py --help
```

### Success Criteria
- [ ] System starts without errors
- [ ] Basic research query completes successfully
- [ ] File outputs are generated correctly (when enabled)
- [ ] No regression in existing functionality
- [ ] Performance remains acceptable
- [ ] All error conditions handled gracefully

---

## Quick Reference: Common Validation Commands

```bash
# Environment check
python --version && echo $VIRTUAL_ENV && ls .env

# Module import check
python -c "import multi_agents; print('✅ Module imports')"

# Provider validation
python main.py --provider-info

# Quick functionality test
python main.py --research "test" --no-save-files

# Dependency check
pip list | grep -E "(langgraph|gpt-researcher|aiohttp)"

# File structure validation
ls multi_agents/agents/ && ls multi_agents/providers/
```

Remember: These checklists are designed to prevent common mistakes and ensure high-quality code. Use them as a guide, not a rigid process.