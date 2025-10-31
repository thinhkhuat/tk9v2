"""
Google Gemini LLM Provider
Supports Gemini models through Google AI Studio API
"""

import asyncio
import json
import time
from typing import Dict, List, Any, AsyncGenerator
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..base import BaseLLMProvider, LLMResponse, LLMProviderError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configure Gemini
        api_key = config.get("api_key")
        if not api_key:
            raise LLMProviderError("Google API key is required", "gemini")
        
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model_name = config.get("model", "gemini-1.5-pro")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)
        
        # Create model instance
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        # Safety settings (less restrictive for research)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Pricing (approximate, in USD per 1K tokens)
        self.pricing = self._get_pricing()
    
    def _get_pricing(self) -> Dict[str, float]:
        """Get pricing information for different Gemini models"""
        # Approximate pricing as of 2024 (per 1K tokens)
        pricing_map = {
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-1.0-pro": {"input": 0.0005, "output": 0.0015},
        }
        return pricing_map.get(self.model_name, {"input": 0.001, "output": 0.003})
    
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        """Generate text using Gemini"""
        start_time = time.time()
        
        try:
            # Prepare the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt
            )
            
            # Check if response was blocked
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise LLMProviderError(
                    f"Content blocked: {response.prompt_feedback.block_reason}",
                    "gemini",
                    "content_blocked"
                )
            
            if not response.text:
                raise LLMProviderError("No text generated", "gemini", "empty_response")
            
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
                    "finish_reason": response.candidates[0].finish_reason if response.candidates else None
                }
            )
            
        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise
            raise LLMProviderError(f"Gemini API error: {str(e)}", "gemini")
    
    async def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming text using Gemini"""
        try:
            # Prepare the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            # Generate streaming response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise LLMProviderError(f"Gemini streaming error: {str(e)}", "gemini")
    
    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost for the API call"""
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(response)
        
        return (
            (input_tokens / 1000) * self.pricing["input"] +
            (output_tokens / 1000) * self.pricing["output"]
        )
    
    def validate_config(self) -> List[str]:
        """Validate Gemini provider configuration"""
        issues = []
        
        if not self.config.get("api_key"):
            issues.append("Google API key is required")
        
        if self.model_name not in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]:
            issues.append(f"Unsupported model: {self.model_name}")
        
        if not (0.0 <= self.temperature <= 2.0):
            issues.append("Temperature must be between 0.0 and 2.0")
        
        if not (1 <= self.max_tokens <= 32768):
            issues.append("Max tokens must be between 1 and 32768")
        
        return issues
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (approximate)"""
        # Rough estimation: 1 token ≈ 4 characters for most text
        return max(1, len(text) // 4)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        return {
            "provider": "gemini",
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "pricing": self.pricing,
            "capabilities": {
                "text_generation": True,
                "streaming": True,
                "system_prompts": True,
                "safety_filtering": True
            },
            "context_window": self._get_context_window()
        }
    
    def _get_context_window(self) -> int:
        """Get context window size for the model"""
        context_windows = {
            "gemini-1.5-pro": 2097152,  # 2M tokens
            "gemini-1.5-flash": 1048576,  # 1M tokens
            "gemini-1.0-pro": 32768,     # 32K tokens
        }
        return context_windows.get(self.model_name, 32768)
    
    async def test_connection(self) -> bool:
        """Test connection to Gemini API"""
        try:
            response = await self.generate("Hello", max_tokens=10)
            return bool(response.content)
        except:
            return False