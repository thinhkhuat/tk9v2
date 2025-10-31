"""
Enhanced Google Gemini LLM Provider
Includes robust health monitoring, error handling, and failover support
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, AsyncGenerator

# Suppress ALTS warnings before importing Google libraries
import sys
import os
# Add parent directory to path to import suppress_alts_warnings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from suppress_alts_warnings import safe_import_google_genai

genai = safe_import_google_genai()
if genai:
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
else:
    raise ImportError("Failed to import google.generativeai")

from ..enhanced_base import EnhancedBaseLLMProvider, LLMResponse, LLMProviderError, ProviderHealth

logger = logging.getLogger(__name__)


class EnhancedGeminiProvider(EnhancedBaseLLMProvider):
    """Enhanced Google Gemini LLM provider with robust error handling and monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configure Gemini
        api_key = config.get("api_key")
        if not api_key:
            raise LLMProviderError("Google API key is required", "gemini")
        
        genai.configure(api_key=api_key)
        
        # Initialize model configuration
        self.model_name = config.get("model", "gemini-1.5-pro")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)
        
        # Create model instance with enhanced error handling
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        # Safety settings (configurable for research use)
        safety_level = config.get("safety_level", "medium")
        safety_mapping = {
            "low": HarmBlockThreshold.BLOCK_ONLY_HIGH,
            "medium": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            "high": HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
        }
        
        safety_threshold = safety_mapping.get(safety_level, HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: safety_threshold,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: safety_threshold,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: safety_threshold,
            HarmCategory.HARM_CATEGORY_HARASSMENT: safety_threshold,
        }
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Enhanced configuration
        self.request_timeout = config.get("request_timeout", 30)
        self.max_retries_per_request = config.get("max_retries_per_request", 2)
        self.backoff_factor = config.get("backoff_factor", 1.5)
        
        # Pricing information (approximate, in USD per 1K tokens)
        self.pricing = self._get_pricing()
        
        # Rate limiting
        self.requests_per_minute = config.get("requests_per_minute", 60)
        self.request_history = []
        
        logger.info(f"Enhanced Gemini provider initialized: {self.model_name}")
    
    def _get_pricing(self) -> Dict[str, float]:
        """Get pricing information for different Gemini models"""
        # Approximate pricing as of 2024 (per 1K tokens)
        pricing_map = {
            "gemini-2.5-flash-preview-04-17-thinking": {"input": 0.000075, "output": 0.0003},
            "gemini-2.5-flash-preview-05-20": {"input": 0.000075, "output": 0.0003},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-1.0-pro": {"input": 0.0005, "output": 0.0015},
        }
        return pricing_map.get(self.model_name, {"input": 0.001, "output": 0.003})
    
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        """Generate text using Gemini with enhanced error handling and retry logic"""
        # Check rate limiting
        await self._check_rate_limit()
        
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        # Override config with kwargs
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        
        # Update generation config if needed
        if max_tokens != self.max_tokens or temperature != self.temperature:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=self.model._safety_settings
            )
        else:
            model = self.model
        
        last_error = None
        for attempt in range(self.max_retries_per_request):
            start_time = time.time()
            
            try:
                # Generate response with timeout
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, full_prompt),
                    timeout=self.request_timeout
                )
                
                # Check if response was blocked
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    error_msg = f"Content blocked: {response.prompt_feedback.block_reason}"
                    logger.warning(f"Gemini content blocked: {error_msg}")
                    raise LLMProviderError(error_msg, "gemini", "content_blocked")
                
                if not response.text:
                    error_msg = "No text generated from Gemini"
                    logger.warning(error_msg)
                    raise LLMProviderError(error_msg, "gemini", "empty_response")
                
                # Calculate metrics
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Estimate token usage
                input_tokens = self._estimate_tokens(full_prompt)
                output_tokens = self._estimate_tokens(response.text)
                total_tokens = input_tokens + output_tokens
                
                # Calculate cost
                cost = (
                    (input_tokens / 1000) * self.pricing["input"] +
                    (output_tokens / 1000) * self.pricing["output"]
                )
                
                # Record successful request
                self.request_history.append(time.time())
                
                return LLMResponse(
                    content=response.text,
                    model=self.model_name,
                    provider="gemini",
                    tokens_used=total_tokens,
                    cost=cost,
                    latency_ms=latency_ms,
                    metadata={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "safety_ratings": response.candidates[0].safety_ratings if response.candidates else [],
                        "finish_reason": response.candidates[0].finish_reason if response.candidates else None,
                        "attempt": attempt + 1,
                        "request_id": f"gemini_{int(time.time())}_{attempt}"
                    }
                )
                
            except asyncio.TimeoutError:
                last_error = LLMProviderError(
                    f"Request timeout after {self.request_timeout}s", "gemini", "timeout"
                )
                logger.warning(f"Gemini timeout on attempt {attempt + 1}")
                
            except Exception as e:
                if isinstance(e, LLMProviderError):
                    last_error = e
                else:
                    last_error = LLMProviderError(f"Gemini API error: {str(e)}", "gemini", "api_error")
                
                logger.warning(f"Gemini error on attempt {attempt + 1}: {e}")
            
            # Apply backoff if not the last attempt
            if attempt < self.max_retries_per_request - 1:
                backoff_time = self.backoff_factor ** attempt
                logger.debug(f"Backing off for {backoff_time}s before retry")
                await asyncio.sleep(backoff_time)
        
        # All retries exhausted
        logger.error(f"Gemini generation failed after {self.max_retries_per_request} attempts")
        raise last_error
    
    async def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming text using Gemini with enhanced error handling"""
        # Check rate limiting
        await self._check_rate_limit()
        
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        try:
            # Generate streaming response with timeout
            response_stream = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content, 
                    full_prompt, 
                    stream=True
                ),
                timeout=self.request_timeout
            )
            
            # Record request
            self.request_history.append(time.time())
            
            # Stream chunks
            chunk_count = 0
            async for chunk in self._async_stream_wrapper(response_stream):
                if chunk.text:
                    chunk_count += 1
                    yield chunk.text
            
            if chunk_count == 0:
                logger.warning("Gemini streaming returned no chunks")
                
        except asyncio.TimeoutError:
            error_msg = f"Streaming timeout after {self.request_timeout}s"
            logger.error(error_msg)
            raise LLMProviderError(error_msg, "gemini", "timeout")
            
        except Exception as e:
            error_msg = f"Gemini streaming error: {str(e)}"
            logger.error(error_msg)
            raise LLMProviderError(error_msg, "gemini", "streaming_error")
    
    async def _async_stream_wrapper(self, stream):
        """Async wrapper for Gemini's synchronous streaming"""
        def _iterate_stream():
            for chunk in stream:
                yield chunk
        
        loop = asyncio.get_event_loop()
        stream_iter = _iterate_stream()
        
        while True:
            try:
                chunk = await loop.run_in_executor(None, next, stream_iter)
                yield chunk
            except StopIteration:
                break
    
    async def _check_rate_limit(self):
        """Enhanced rate limiting with better handling"""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_history = [
            req_time for req_time in self.request_history 
            if now - req_time < 60
        ]
        
        # Check if we're at the limit
        if len(self.request_history) >= self.requests_per_minute:
            # Calculate wait time more precisely
            oldest_request = min(self.request_history)
            wait_time = 60 - (now - oldest_request)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                # Refresh the history after waiting
                now = time.time()
                self.request_history = [
                    req_time for req_time in self.request_history 
                    if now - req_time < 60
                ]
    
    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost for the API call"""
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(response)
        
        return (
            (input_tokens / 1000) * self.pricing["input"] +
            (output_tokens / 1000) * self.pricing["output"]
        )
    
    def validate_config(self) -> List[str]:
        """Enhanced validation of Gemini provider configuration"""
        issues = []
        
        # Basic validation
        if not self.config.get("api_key"):
            issues.append("Google API key is required")
        
        # Model validation
        supported_models = list(self.pricing.keys())
        if self.model_name not in supported_models:
            issues.append(f"Model '{self.model_name}' not in supported list: {supported_models}")
        
        # Parameter validation
        if not (0.0 <= self.temperature <= 2.0):
            issues.append("Temperature must be between 0.0 and 2.0")
        
        if not (1 <= self.max_tokens <= 100000):
            issues.append("Max tokens must be between 1 and 100000")
        
        # Enhanced validation
        if not (5 <= self.request_timeout <= 300):
            issues.append("Request timeout must be between 5 and 300 seconds")
        
        if not (1 <= self.max_retries_per_request <= 5):
            issues.append("Max retries per request must be between 1 and 5")
        
        if not (1.0 <= self.backoff_factor <= 3.0):
            issues.append("Backoff factor must be between 1.0 and 3.0")
        
        if not (1 <= self.requests_per_minute <= 600):
            issues.append("Requests per minute must be between 1 and 600")
        
        return issues
    
    def _estimate_tokens(self, text: str) -> int:
        """Enhanced token estimation"""
        if not text:
            return 0
        
        # More accurate estimation based on Gemini tokenization
        # Roughly 1 token per 4 characters for English, adjust for other languages
        base_tokens = len(text) // 4
        
        # Account for special characters and formatting
        special_char_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
        format_tokens = special_char_count // 10
        
        return max(1, base_tokens + format_tokens)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        base_info = super().get_model_info()
        
        # Add Gemini-specific information
        gemini_info = {
            "context_window": self._get_context_window(),
            "pricing": self.pricing,
            "capabilities": {
                "text_generation": True,
                "streaming": True,
                "system_prompts": True,
                "safety_filtering": True,
                "multimodal": "1.5" in self.model_name  # Gemini 1.5 models support multimodal
            },
            "rate_limits": {
                "requests_per_minute": self.requests_per_minute,
                "current_usage": len(self.request_history)
            },
            "performance": {
                "request_timeout": self.request_timeout,
                "max_retries": self.max_retries_per_request,
                "backoff_factor": self.backoff_factor
            }
        }
        
        base_info.update(gemini_info)
        return base_info
    
    def _get_context_window(self) -> int:
        """Get context window size for the model"""
        context_windows = {
            "gemini-2.5-flash-preview-04-17-thinking": 1048576,  # 1M tokens
            "gemini-2.5-flash-preview-05-20": 1048576,  # 1M tokens
            "gemini-1.5-pro": 2097152,  # 2M tokens
            "gemini-1.5-flash": 1048576,  # 1M tokens
            "gemini-1.0-pro": 32768,     # 32K tokens
        }
        return context_windows.get(self.model_name, 32768)
    
    async def test_connection(self) -> bool:
        """Enhanced connection test"""
        try:
            response = await self.generate("Test connection", max_tokens=10)
            return response.success
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False