"""
Provider Failover Integration Module
Integrates enhanced failover system with existing multi-agent workflow
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from .enhanced_factory import initialize_enhanced_system, shutdown_enhanced_system, enhanced_config
from .enhanced_base import EnhancedProviderManager, FailoverEvent, ProviderHealth

logger = logging.getLogger(__name__)


class FailoverIntegration:
    """Integration layer for enhanced failover system with multi-agent workflow"""
    
    def __init__(self):
        self.provider_manager: Optional[EnhancedProviderManager] = None
        self.is_initialized = False
        self.fallback_mode = False
        
    async def initialize(self, enable_monitoring: bool = True) -> bool:
        """
        Initialize the enhanced failover system
        
        Args:
            enable_monitoring: Whether to enable health monitoring
            
        Returns:
            True if initialization successful, False if fallback mode
        """
        try:
            self.provider_manager = await initialize_enhanced_system(enable_monitoring)
            self.is_initialized = True
            self.fallback_mode = False
            
            # Add integration-specific callbacks
            self._setup_failover_callbacks()
            
            logger.info("Enhanced failover system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced failover system: {e}")
            logger.info("Falling back to basic provider system")
            self.fallback_mode = True
            return False
    
    def _setup_failover_callbacks(self):
        """Setup callbacks for failover events"""
        if not self.provider_manager:
            return
            
        def on_llm_failover(event: FailoverEvent):
            """Handle LLM failover events"""
            logger.info(
                f"LLM Provider failover: {event.from_provider} -> {event.to_provider} "
                f"({event.reason.value})"
            )
            
            # Update environment variables for gpt-researcher compatibility
            if enhanced_config:
                try:
                    enhanced_config.apply_to_environment()
                except Exception as e:
                    logger.error(f"Failed to update environment after LLM failover: {e}")
        
        def on_search_failover(event: FailoverEvent):
            """Handle search failover events"""
            logger.info(
                f"Search Provider failover: {event.from_provider} -> {event.to_provider} "
                f"({event.reason.value})"
            )
            
            # Update environment variables for gpt-researcher compatibility
            if enhanced_config:
                try:
                    enhanced_config.apply_to_environment()
                except Exception as e:
                    logger.error(f"Failed to update environment after search failover: {e}")
        
        # Register callbacks
        self.provider_manager.add_failover_callback(on_llm_failover)
        self.provider_manager.add_failover_callback(on_search_failover)
    
    async def get_llm_response(self, prompt: str, system_prompt: str = None, **kwargs):
        """
        Get LLM response with enhanced failover support
        
        Args:
            prompt: The prompt to generate response for
            system_prompt: Optional system prompt
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse object
        """
        if self.fallback_mode or not self.is_initialized or not self.provider_manager:
            # Fallback to gpt-researcher integration
            logger.debug("Using fallback mode for LLM generation")
            return await self._fallback_llm_generate(prompt, system_prompt, **kwargs)
        
        try:
            # Use enhanced provider manager
            return await self.provider_manager.llm_generate(
                prompt, 
                system_prompt=system_prompt, 
                fallback=True, 
                max_retries=3,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Enhanced LLM generation failed: {e}")
            logger.info("Falling back to basic LLM generation")
            
            # Fallback to basic system
            try:
                return await self._fallback_llm_generate(prompt, system_prompt, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback LLM generation also failed: {fallback_error}")
                raise e  # Raise original error
    
    async def get_search_results(self, query: str, search_type: str = "web", **kwargs):
        """
        Get search results with enhanced failover support
        
        Args:
            query: The search query
            search_type: Type of search (web, news)
            **kwargs: Additional search parameters
            
        Returns:
            SearchResponse object
        """
        if self.fallback_mode or not self.is_initialized or not self.provider_manager:
            # Fallback to gpt-researcher integration
            logger.debug("Using fallback mode for search")
            return await self._fallback_search_query(query, search_type, **kwargs)
        
        try:
            # Use enhanced provider manager
            return await self.provider_manager.search_query(
                query,
                search_type=search_type,
                fallback=True,
                max_retries=3,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            logger.info("Falling back to basic search")
            
            # Fallback to basic system
            try:
                return await self._fallback_search_query(query, search_type, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
                raise e  # Raise original error
    
    async def _fallback_llm_generate(self, prompt: str, system_prompt: str = None, **kwargs):
        """Fallback LLM generation using basic provider system"""
        from .factory import provider_manager
        
        return await provider_manager.llm_generate(
            prompt, 
            system_prompt=system_prompt,
            fallback=True,
            **kwargs
        )
    
    async def _fallback_search_query(self, query: str, search_type: str = "web", **kwargs):
        """Fallback search using basic provider system"""
        from .factory import provider_manager
        
        return await provider_manager.search_query(
            query,
            search_type=search_type, 
            fallback=True,
            **kwargs
        )
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the failover system"""
        if not self.is_initialized or not self.provider_manager:
            return {
                "status": "fallback_mode" if self.fallback_mode else "not_initialized",
                "provider_manager": None,
                "failover_enabled": False
            }
        
        try:
            status = await self.provider_manager.get_comprehensive_status()
            status["failover_integration"] = {
                "initialized": self.is_initialized,
                "fallback_mode": self.fallback_mode,
                "integration_version": "2.0"
            }
            return status
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_mode": self.fallback_mode
            }
    
    async def force_failover(self, provider_type: str, to_provider: str):
        """Force failover to a specific provider"""
        if not self.is_initialized or not self.provider_manager:
            raise RuntimeError("Enhanced failover system not initialized")
        
        await self.provider_manager.force_failover(provider_type, to_provider)
        logger.info(f"Forced failover {provider_type} -> {to_provider}")
    
    async def health_check_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all providers"""
        if not self.is_initialized or not self.provider_manager:
            return {"error": "Enhanced failover system not initialized"}
        
        results = {
            "llm_providers": {},
            "search_providers": {}
        }
        
        # Check LLM providers
        for name, provider in self.provider_manager.llm_providers.items():
            try:
                health_result = await provider.health_check()
                results["llm_providers"][name] = {
                    "status": health_result.status.value,
                    "response_time_ms": health_result.response_time_ms,
                    "error_message": health_result.error_message
                }
            except Exception as e:
                results["llm_providers"][name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Check search providers
        for name, provider in self.provider_manager.search_providers.items():
            try:
                health_result = await provider.health_check()
                results["search_providers"][name] = {
                    "status": health_result.status.value,
                    "response_time_ms": health_result.response_time_ms,
                    "error_message": health_result.error_message
                }
            except Exception as e:
                results["search_providers"][name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    async def get_failover_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failover history"""
        if not self.is_initialized or not self.provider_manager:
            return []
        
        history = []
        for event in self.provider_manager.failover_history[-limit:]:
            history.append({
                "timestamp": event.timestamp.isoformat(),
                "from_provider": event.from_provider,
                "to_provider": event.to_provider,
                "reason": event.reason.value,
                "error_message": event.error_message,
                "recovery_time_ms": event.recovery_time_ms
            })
        
        return history
    
    async def cleanup(self):
        """Cleanup failover integration resources"""
        if self.provider_manager:
            await self.provider_manager.cleanup()
        
        await shutdown_enhanced_system()
        self.is_initialized = False
        logger.info("Failover integration cleanup completed")


# Global failover integration instance
failover_integration = FailoverIntegration()


@asynccontextmanager
async def managed_failover_system(enable_monitoring: bool = True):
    """Context manager for failover system lifecycle"""
    try:
        success = await failover_integration.initialize(enable_monitoring)
        yield failover_integration, success
    finally:
        await failover_integration.cleanup()


async def get_failover_status() -> Dict[str, Any]:
    """Get current failover system status"""
    return await failover_integration.get_comprehensive_status()


async def test_all_providers() -> Dict[str, Any]:
    """Test all providers and return results"""
    return await failover_integration.health_check_all_providers()


# Convenience functions for backward compatibility
async def enhanced_llm_generate(prompt: str, system_prompt: str = None, **kwargs):
    """Generate LLM response with enhanced failover"""
    return await failover_integration.get_llm_response(prompt, system_prompt, **kwargs)


async def enhanced_search_query(query: str, search_type: str = "web", **kwargs):
    """Perform search with enhanced failover"""
    return await failover_integration.get_search_results(query, search_type, **kwargs)


# Integration with existing agent system
class AgentProviderMixin:
    """Mixin to add enhanced provider support to agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._use_enhanced_providers = True
    
    async def get_llm_response(self, prompt: str, system_prompt: str = None, **kwargs):
        """Get LLM response using enhanced system if available"""
        if self._use_enhanced_providers and failover_integration.is_initialized:
            return await failover_integration.get_llm_response(prompt, system_prompt, **kwargs)
        else:
            # Fallback to original method
            return await super().get_llm_response(prompt, system_prompt, **kwargs)
    
    async def search(self, query: str, search_type: str = "web", **kwargs):
        """Perform search using enhanced system if available"""
        if self._use_enhanced_providers and failover_integration.is_initialized:
            return await failover_integration.get_search_results(query, search_type, **kwargs)
        else:
            # Fallback to original method
            return await super().search(query, search_type, **kwargs)
    
    def disable_enhanced_providers(self):
        """Disable enhanced providers for this agent"""
        self._use_enhanced_providers = False
    
    def enable_enhanced_providers(self):
        """Enable enhanced providers for this agent"""
        self._use_enhanced_providers = True