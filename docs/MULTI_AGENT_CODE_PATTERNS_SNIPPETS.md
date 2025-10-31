# Code Patterns & Snippets

## Essential Imports and Setup

### Standard Agent Imports
```python
# Core imports for agent development
from typing import Dict, Any, List, Optional, AsyncGenerator
from multi_agents.agents.base_agent import BaseAgent
from multi_agents.utils.views import print_agent_output
import asyncio
import aiohttp
import os
```

### LangGraph Workflow Imports
```python
# For workflow orchestration
from langgraph.graph import StateGraph, END
from typing import TypedDict
from multi_agents.memory.research import ResearchState
```

### Provider Imports
```python
# For provider development
from multi_agents.providers.base import BaseLLMProvider, BaseSearchProvider
from multi_agents.providers import ProviderFactory
import json
```

## Agent Patterns

### Complete Agent Template
```python
from typing import Dict, Any, Optional
from multi_agents.agents.base_agent import BaseAgent
from multi_agents.utils.views import print_agent_output

class TemplateAgent(BaseAgent):
    """Template for creating new agents"""
    
    def __init__(self, **kwargs):
        role = kwargs.get('role', 'Template Agent')
        goal = kwargs.get('goal', 'Perform template operations')
        backstory = kwargs.get('backstory', 'An expert agent specialized in template tasks')
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
        
        # Agent-specific configuration
        self.max_retries = kwargs.get('max_retries', 3)
        self.timeout = kwargs.get('timeout', 30)
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute the agent's main task"""
        if context is None:
            context = {}
        
        try:
            # Pre-execution setup
            self._log_execution_start(task, context)
            
            # Main processing
            result = await self._process_task(task, context)
            
            # Post-execution cleanup
            self._log_execution_success(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Error in {self.role}: {str(e)}"
            self._log_execution_error(error_msg)
            return await self._handle_error(e, task, context)
    
    async def _process_task(self, task: str, context: Dict[str, Any]) -> str:
        """Main task processing logic - override in subclasses"""
        # Extract relevant context
        previous_output = context.get('previous_output', '')
        additional_context = context.get('additional_context', {})
        
        # Build prompt
        prompt = self._build_prompt(task, previous_output, additional_context)
        
        # Generate response
        if self.llm:
            response = await self._generate_with_llm(prompt)
        else:
            response = await self._generate_without_llm(prompt)
        
        # Process and validate response
        processed_response = await self._post_process_response(response)
        
        return processed_response
    
    def _build_prompt(self, task: str, previous_output: str, additional_context: Dict[str, Any]) -> str:
        """Build the prompt for LLM generation"""
        prompt = f"""
        You are a {self.role}. {self.backstory}
        
        Your goal: {self.goal}
        
        Task: {task}
        
        Previous context: {previous_output}
        
        Additional context: {json.dumps(additional_context, indent=2)}
        
        Please provide your response:
        """
        return prompt.strip()
    
    async def _generate_with_llm(self, prompt: str) -> str:
        """Generate response using LLM"""
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            if self.verbose:
                print(f"⚠️ LLM generation failed: {e}")
            return await self._fallback_response(prompt)
    
    async def _generate_without_llm(self, prompt: str) -> str:
        """Generate response without LLM (fallback)"""
        return f"Template response for: {prompt[:100]}..."
    
    async def _post_process_response(self, response: str) -> str:
        """Post-process the generated response"""
        # Clean up response
        response = response.strip()
        
        # Validate response
        if not response:
            response = "No response generated"
        
        # Apply formatting
        response = self._apply_formatting(response)
        
        return response
    
    def _apply_formatting(self, content: str) -> str:
        """Apply consistent formatting to content"""
        # Remove excessive whitespace
        import re
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Ensure proper sentence ending
        if content and not content.endswith(('.', '!', '?')):
            content += '.'
        
        return content
    
    async def _handle_error(self, error: Exception, task: str, context: Dict[str, Any]) -> str:
        """Handle execution errors gracefully"""
        error_response = f"Unable to complete task '{task}' due to: {str(error)}"
        
        if self.verbose:
            print(f"❌ {self.role} Error: {error_response}")
        
        # Attempt retry if retries available
        retry_count = context.get('retry_count', 0)
        if retry_count < self.max_retries:
            context['retry_count'] = retry_count + 1
            await asyncio.sleep(1)  # Brief delay before retry
            return await self.execute(task, context)
        
        return error_response
    
    async def _fallback_response(self, prompt: str) -> str:
        """Provide fallback response when LLM fails"""
        return f"Fallback response from {self.role}"
    
    def _log_execution_start(self, task: str, context: Dict[str, Any]):
        """Log execution start"""
        if self.verbose:
            print(f"🚀 {self.role} starting: {task[:100]}...")
    
    def _log_execution_success(self, result: str):
        """Log successful execution"""
        if self.verbose:
            print_agent_output(f"{self.role} Output", result)
    
    def _log_execution_error(self, error_msg: str):
        """Log execution error"""
        if self.verbose:
            print(f"❌ {error_msg}")

# Usage example
async def example_usage():
    agent = TemplateAgent(verbose=True)
    result = await agent.execute("Analyze data", {"previous_output": "Some context"})
    print(result)
```

### Streaming Agent Pattern
```python
class StreamingAgent(BaseAgent):
    """Agent that supports streaming output"""
    
    async def execute_stream(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Execute with streaming output"""
        if context is None:
            context = {}
        
        yield f"🚀 {self.role} starting task...\n"
        
        try:
            # Stream the processing
            async for chunk in self._stream_process(task, context):
                yield chunk
            
            yield f"\n✅ {self.role} completed task\n"
            
        except Exception as e:
            yield f"\n❌ {self.role} failed: {str(e)}\n"
    
    async def _stream_process(self, task: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream the main processing"""
        prompt = self._build_prompt(task, context.get('previous_output', ''), {})
        
        if self.llm and hasattr(self.llm, 'astream'):
            async for chunk in self.llm.astream(prompt):
                yield chunk.content if hasattr(chunk, 'content') else str(chunk)
        else:
            # Simulate streaming for non-streaming LLMs
            result = await self._generate_with_llm(prompt)
            for i in range(0, len(result), 50):
                yield result[i:i+50]
                await asyncio.sleep(0.1)
```

## Provider Patterns

### LLM Provider Template
```python
from multi_agents.providers.base import BaseLLMProvider
from typing import List, Dict, Any, AsyncGenerator
import aiohttp
import json

class CustomLLMProvider(BaseLLMProvider):
    """Template for custom LLM providers"""
    
    def __init__(self, api_key: str, model: str = "default-model", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.example.com/v1')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        payload = {
            'model': self.model,
            'prompt': prompt,
            'max_tokens': kwargs.get('max_tokens', self.max_tokens),
            'temperature': kwargs.get('temperature', self.temperature),
            'stop': kwargs.get('stop', None)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/completions",
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['text'].strip()
                else:
                    error_data = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_data}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        payload = {
            'model': self.model,
            'prompt': prompt,
            'max_tokens': kwargs.get('max_tokens', self.max_tokens),
            'temperature': kwargs.get('temperature', self.temperature),
            'stream': True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/completions",
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                json_str = line_str[6:]
                                if json_str != '[DONE]':
                                    try:
                                        data = json.loads(json_str)
                                        if 'choices' in data and data['choices']:
                                            delta = data['choices'][0].get('delta', {})
                                            content = delta.get('content', '')
                                            if content:
                                                yield content
                                    except json.JSONDecodeError:
                                        continue
                else:
                    raise Exception(f"Streaming request failed: {response.status}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return ['default-model', 'advanced-model', 'fast-model']
    
    def validate_api_key(self) -> bool:
        """Validate API key"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return True  # Assume valid to avoid blocking
            else:
                return asyncio.run(self._test_api_key())
        except:
            return False
    
    async def _test_api_key(self) -> bool:
        """Test API key with simple request"""
        try:
            result = await self.generate("Hello", max_tokens=5)
            return len(result) > 0
        except:
            return False
    
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token"""
        return {
            "input": 0.000001,  # $0.000001 per input token
            "output": 0.000002  # $0.000002 per output token
        }
```

### Search Provider Template
```python
from multi_agents.providers.base import BaseSearchProvider
from typing import List, Dict, Any
import aiohttp

class CustomSearchProvider(BaseSearchProvider):
    """Template for custom search providers"""
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.searchprovider.com/v1')
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform web search"""
        params = {
            'q': query,
            'count': kwargs.get('count', self.max_results),
            'lang': kwargs.get('lang', 'en'),
            'safe': kwargs.get('safe', 'moderate')
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_search_results(data.get('results', []))
                else:
                    raise Exception(f"Search failed: {response.status}")
    
    async def search_news(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search news specifically"""
        params = {
            'q': query,
            'count': kwargs.get('count', self.max_results),
            'category': 'news',
            'freshness': kwargs.get('freshness', 'day')
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/news",
                headers=self.headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_news_results(data.get('articles', []))
                else:
                    raise Exception(f"News search failed: {response.status}")
    
    def _format_search_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Format search results to standard format"""
        formatted = []
        for result in results:
            formatted.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'snippet': result.get('description', result.get('snippet', '')),
                'published_date': result.get('date', ''),
                'source': 'custom_search'
            })
        return formatted
    
    def _format_news_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Format news results to standard format"""
        formatted = []
        for result in results:
            formatted.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'snippet': result.get('description', ''),
                'published_date': result.get('publishedAt', result.get('date', '')),
                'source': 'custom_news'
            })
        return formatted
```

## Workflow Patterns

### LangGraph Workflow Setup
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any

class CustomWorkflowState(TypedDict):
    """Define workflow state structure"""
    task: str
    agent_a_output: str
    agent_b_output: str
    agent_c_output: str
    final_result: str
    metadata: Dict[str, Any]

class WorkflowOrchestrator:
    """Template for workflow orchestration"""
    
    def __init__(self, **kwargs):
        self.verbose = kwargs.get('verbose', True)
        self.agents = self._initialize_agents(**kwargs)
        self.workflow = self._create_workflow()
    
    def _initialize_agents(self, **kwargs) -> Dict[str, Any]:
        """Initialize all agents"""
        return {
            'agent_a': AgentA(**kwargs),
            'agent_b': AgentB(**kwargs),
            'agent_c': AgentC(**kwargs)
        }
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(CustomWorkflowState)
        
        # Add nodes
        workflow.add_node("agent_a", self._agent_a_node)
        workflow.add_node("agent_b", self._agent_b_node)
        workflow.add_node("agent_c", self._agent_c_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Add edges
        workflow.set_entry_point("agent_a")
        workflow.add_edge("agent_a", "agent_b")
        workflow.add_conditional_edges(
            "agent_b",
            self._should_continue_to_c,
            {
                True: "agent_c",
                False: "finalize"
            }
        )
        workflow.add_edge("agent_c", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def _agent_a_node(self, state: CustomWorkflowState) -> Dict[str, Any]:
        """Execute Agent A"""
        if self.verbose:
            print("🚀 Executing Agent A...")
        
        result = await self.agents['agent_a'].execute(
            state['task'],
            {'metadata': state.get('metadata', {})}
        )
        
        return {'agent_a_output': result}
    
    async def _agent_b_node(self, state: CustomWorkflowState) -> Dict[str, Any]:
        """Execute Agent B"""
        if self.verbose:
            print("🚀 Executing Agent B...")
        
        context = {
            'previous_output': state.get('agent_a_output', ''),
            'metadata': state.get('metadata', {})
        }
        
        result = await self.agents['agent_b'].execute(state['task'], context)
        
        return {'agent_b_output': result}
    
    async def _agent_c_node(self, state: CustomWorkflowState) -> Dict[str, Any]:
        """Execute Agent C"""
        if self.verbose:
            print("🚀 Executing Agent C...")
        
        context = {
            'agent_a_output': state.get('agent_a_output', ''),
            'agent_b_output': state.get('agent_b_output', ''),
            'metadata': state.get('metadata', {})
        }
        
        result = await self.agents['agent_c'].execute(state['task'], context)
        
        return {'agent_c_output': result}
    
    async def _finalize_node(self, state: CustomWorkflowState) -> Dict[str, Any]:
        """Finalize the workflow"""
        if self.verbose:
            print("🏁 Finalizing workflow...")
        
        # Combine results
        final_result = self._combine_outputs(state)
        
        return {'final_result': final_result}
    
    def _should_continue_to_c(self, state: CustomWorkflowState) -> bool:
        """Decide whether to continue to Agent C"""
        # Example logic: continue if Agent B output is long enough
        agent_b_output = state.get('agent_b_output', '')
        return len(agent_b_output) > 100
    
    def _combine_outputs(self, state: CustomWorkflowState) -> str:
        """Combine all agent outputs"""
        outputs = []
        
        if state.get('agent_a_output'):
            outputs.append(f"## Agent A Output\n{state['agent_a_output']}")
        
        if state.get('agent_b_output'):
            outputs.append(f"## Agent B Output\n{state['agent_b_output']}")
        
        if state.get('agent_c_output'):
            outputs.append(f"## Agent C Output\n{state['agent_c_output']}")
        
        return "\n\n".join(outputs)
    
    async def run(self, task: str, metadata: Dict[str, Any] = None) -> str:
        """Run the complete workflow"""
        if metadata is None:
            metadata = {}
        
        initial_state = {
            'task': task,
            'metadata': metadata,
            'agent_a_output': '',
            'agent_b_output': '',
            'agent_c_output': '',
            'final_result': ''
        }
        
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state['final_result']

# Usage
async def run_workflow():
    orchestrator = WorkflowOrchestrator(verbose=True)
    result = await orchestrator.run("Analyze market trends")
    print(result)
```

## Utility Patterns

### Configuration Manager
```python
import os
import json
from typing import Dict, Any, Optional

class ConfigManager:
    """Manage configuration across the application"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "multi_agents/task.json"
        self._config = self._load_config()
        self._env_vars = self._load_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    def _load_env_vars(self) -> Dict[str, str]:
        """Load relevant environment variables"""
        env_vars = {}
        for key, value in os.environ.items():
            if key.endswith('_API_KEY') or key.startswith('PRIMARY_') or key.endswith('_PROVIDER'):
                env_vars[key] = value
        return env_vars
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback to environment"""
        # Check config file first
        if key in self._config:
            return self._config[key]
        
        # Check environment variables
        if key in self._env_vars:
            return self._env_vars[key]
        
        # Check with uppercase conversion
        if key.upper() in self._env_vars:
            return self._env_vars[key.upper()]
        
        return default
    
    def update(self, key: str, value: Any):
        """Update configuration value"""
        self._config[key] = value
    
    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get_provider_config(self, provider_type: str) -> Dict[str, Any]:
        """Get provider-specific configuration"""
        provider_config = {
            'primary_llm': self.get('PRIMARY_LLM_PROVIDER', 'google_gemini'),
            'primary_model': self.get('PRIMARY_LLM_MODEL', 'gemini-1.5-flash'),
            'primary_search': self.get('PRIMARY_SEARCH_PROVIDER', 'brave'),
            'llm_strategy': self.get('LLM_STRATEGY', 'primary_only'),
            'search_strategy': self.get('SEARCH_STRATEGY', 'primary_only')
        }
        
        return provider_config
    
    def validate_required_keys(self, required_keys: List[str]) -> Dict[str, bool]:
        """Validate that required configuration keys are present"""
        validation = {}
        for key in required_keys:
            validation[key] = self.get(key) is not None
        return validation

# Usage
config = ConfigManager()
api_key = config.get('BRAVE_API_KEY')
model = config.get('PRIMARY_LLM_MODEL', 'gemini-1.5-flash')
```

### Error Handler Decorator
```python
import functools
import traceback
from typing import Any, Callable, Optional

def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = False,
    error_message: Optional[str] = None
):
    """Decorator for consistent error handling"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    error_msg = error_message or f"Error in {func.__name__}: {str(e)}"
                    print(f"❌ {error_msg}")
                    if hasattr(args[0], 'verbose') and args[0].verbose:
                        traceback.print_exc()
                
                if reraise:
                    raise
                
                return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    error_msg = error_message or f"Error in {func.__name__}: {str(e)}"
                    print(f"❌ {error_msg}")
                    if hasattr(args[0], 'verbose') and args[0].verbose:
                        traceback.print_exc()
                
                if reraise:
                    raise
                
                return default_return
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# Usage
class ExampleAgent(BaseAgent):
    @handle_errors(default_return="Error occurred", log_errors=True)
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        # Agent logic that might fail
        result = await self._risky_operation(task)
        return result
```

### Retry Mechanism
```python
import asyncio
import random
from typing import Any, Callable, Optional

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
) -> Any:
    """Retry function with exponential backoff"""
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        
        except exceptions as e:
            if attempt == max_retries:
                raise e
            
            # Calculate delay
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            if jitter:
                delay += random.uniform(0, delay * 0.1)
            
            print(f"🔄 Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {str(e)}")
            await asyncio.sleep(delay)

# Usage
async def unreliable_api_call():
    # Simulated API call that might fail
    if random.random() < 0.7:
        raise Exception("API temporarily unavailable")
    return "Success"

result = await retry_with_backoff(
    unreliable_api_call,
    max_retries=3,
    base_delay=1.0
)
```

## Testing Patterns

### Agent Test Template
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from multi_agents.agents.template_agent import TemplateAgent

class TestTemplateAgent:
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        mock = AsyncMock()
        mock.ainvoke.return_value.content = "Test response from LLM"
        return mock
    
    @pytest.fixture
    def agent(self, mock_llm):
        """Create agent instance for testing"""
        return TemplateAgent(
            llm=mock_llm,
            verbose=False  # Disable verbose output during tests
        )
    
    @pytest.mark.asyncio
    async def test_execute_basic(self, agent):
        """Test basic agent execution"""
        task = "Test task"
        context = {"previous_output": "Test context"}
        
        result = await agent.execute(task, context)
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_llm(self, agent, mock_llm):
        """Test agent execution with LLM"""
        task = "Complex task requiring LLM"
        
        result = await agent.execute(task)
        
        # Verify LLM was called
        mock_llm.ainvoke.assert_called_once()
        
        # Verify result
        assert "Test response from LLM" in result
    
    @pytest.mark.asyncio
    async def test_execute_error_handling(self, agent, mock_llm):
        """Test agent error handling"""
        # Make LLM raise an exception
        mock_llm.ainvoke.side_effect = Exception("LLM error")
        
        result = await agent.execute("Test task")
        
        # Should return error message, not raise exception
        assert "Error in" in result or "Unable to complete" in result
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, agent, mock_llm):
        """Test retry mechanism"""
        # First call fails, second succeeds
        mock_llm.ainvoke.side_effect = [
            Exception("First failure"),
            MagicMock(content="Success on retry")
        ]
        
        result = await agent.execute("Test task", {"retry_count": 0})
        
        # Should have retried and succeeded
        assert "Success on retry" in result
        assert mock_llm.ainvoke.call_count == 2
    
    def test_prompt_building(self, agent):
        """Test prompt building logic"""
        task = "Test task"
        previous_output = "Previous context"
        additional_context = {"key": "value"}
        
        prompt = agent._build_prompt(task, previous_output, additional_context)
        
        assert task in prompt
        assert previous_output in prompt
        assert "key" in prompt
        assert "value" in prompt

# Run tests with: python -m pytest tests/test_template_agent.py -v
```

Remember: These patterns are battle-tested and follow the existing codebase structure. Always adapt them to your specific needs while maintaining consistency with the project architecture.