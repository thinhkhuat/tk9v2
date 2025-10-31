"""
Google Gemini LLM Provider with Lazy Import
Supports Gemini models through Google AI Studio API
Only imports google.generativeai when actually needed
"""

import asyncio
import json
import time
from typing import Dict, List, Any, AsyncGenerator, Optional

from ..base import BaseLLMProvider, LLMResponse, LLMProviderError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation with lazy imports"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Store config for lazy initialization
        self._config = config
        self._genai = None
        self._model = None
        self._initialized = False
        
        # Extract and validate API key early (doesn't require import)
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise LLMProviderError("Google API key is required", "gemini")
        
        self.model_name = config.get("model", "gemini-1.5-pro")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 8192)
    
    def _lazy_init(self):
        """Lazy initialization of Gemini - only imports when actually used"""
        if self._initialized:
            return
        
        try:
            # Import only when needed
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            self._genai = genai
            self._HarmCategory = HarmCategory
            self._HarmBlockThreshold = HarmBlockThreshold
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model with safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            self._initialized = True
            
        except ImportError as e:
            raise LLMProviderError(
                f"Google Gemini library not installed. Please install with: pip install google-generativeai",
                "gemini"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize Gemini: {str(e)}", "gemini") from e
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for Gemini API"""
        formatted = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Gemini uses "model" instead of "assistant"
            if role == "assistant":
                role = "model"
            elif role == "system":
                # Gemini doesn't have a system role, prepend to first user message
                if formatted and formatted[0]["role"] == "user":
                    formatted[0]["parts"] = [f"{content}\n\n{formatted[0]['parts'][0]}"]
                else:
                    formatted.append({"role": "user", "parts": [content]})
                continue
            
            formatted.append({"role": role, "parts": [content]})
        
        return formatted
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the Gemini model"""
        # Lazy initialization
        self._lazy_init()
        
        try:
            formatted_messages = self._format_messages(messages)
            
            # Extract the last message as the prompt
            if formatted_messages:
                prompt = formatted_messages[-1]["parts"][0]
                history = formatted_messages[:-1] if len(formatted_messages) > 1 else []
            else:
                raise ValueError("No messages provided")
            
            # Create chat session with history
            chat = self._model.start_chat(history=history)
            
            # Generate response
            response = await asyncio.to_thread(
                chat.send_message,
                prompt
            )
            
            return LLMResponse(
                content=response.text,
                model=self.model_name,
                tokens_used=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None,
                raw_response=response
            )
            
        except Exception as e:
            raise LLMProviderError(f"Gemini generation failed: {str(e)}", "gemini") from e
    
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream responses from Gemini"""
        # Lazy initialization
        self._lazy_init()
        
        try:
            formatted_messages = self._format_messages(messages)
            
            if formatted_messages:
                prompt = formatted_messages[-1]["parts"][0]
                history = formatted_messages[:-1] if len(formatted_messages) > 1 else []
            else:
                raise ValueError("No messages provided")
            
            # Create chat session
            chat = self._model.start_chat(history=history)
            
            # Stream response
            response = await asyncio.to_thread(
                chat.send_message,
                prompt,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise LLMProviderError(f"Gemini streaming failed: {str(e)}", "gemini") from e
    
    def validate_config(self) -> bool:
        """Validate the provider configuration"""
        return bool(self.api_key)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "provider": "google_gemini",
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "initialized": self._initialized
        }