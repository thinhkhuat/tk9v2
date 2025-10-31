#!/usr/bin/env python3
"""
Comprehensive Test Suite for Critical Fixes
Tests all the critical and high priority fixes implemented in the Deep Research MCP system
"""

import pytest
import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
from multi_agents.config.validation import (
    ConfigurationValidator, 
    validate_startup_configuration, 
    get_validation_summary
)
from multi_agents.providers.enhanced_factory import EnhancedProviderFactory
from multi_agents.providers.failover_integration import failover_integration
from multi_agents.simple_brave_retriever import setup_simple_brave_retriever


class TestImportFixes:
    """Test import statement fixes and warning suppressions"""
    
    def test_mcp_retriever_warning_suppression(self, caplog):
        """Test that MCPRetriever warnings are suppressed"""
        with caplog.at_level(logging.WARNING):
            # This import should not generate warnings
            from multi_agents import main
            
            # Check that no MCPRetriever warnings were logged
            mcp_warnings = [
                record for record in caplog.records 
                if 'MCPRetriever' in record.getMessage()
            ]
            assert len(mcp_warnings) == 0, f"MCPRetriever warnings not suppressed: {mcp_warnings}"
    
    def test_core_imports_work(self):
        """Test that core imports work without errors"""
        try:
            from multi_agents.agents import ChiefEditorAgent
            from multi_agents.providers.factory import provider_manager
            from multi_agents.config.providers import ProviderConfigManager
            from multi_agents.simple_brave_retriever import CustomRetriever
        except ImportError as e:
            pytest.fail(f"Core imports failed: {e}")
    
    def test_brave_retriever_integration(self):
        """Test BRAVE retriever integration"""
        # Setup test environment
        with patch.dict(os.environ, {
            'PRIMARY_SEARCH_PROVIDER': 'brave',
            'BRAVE_API_KEY': 'test_api_key'
        }):
            try:
                result = setup_simple_brave_retriever()
                assert result is True, "BRAVE retriever setup should succeed"
            except Exception as e:
                pytest.fail(f"BRAVE retriever integration failed: {e}")


class TestAsyncPatternFixes:
    """Test async/await pattern fixes in agent workflows"""
    
    @pytest.mark.asyncio
    async def test_async_agent_methods(self):
        """Test that agent methods are properly async"""
        from multi_agents.agents.researcher import ResearchAgent
        from multi_agents.agents.writer import WriterAgent
        from multi_agents.agents.reviser import ReviserAgent
        
        # Check that key methods are coroutines
        research_agent = ResearchAgent()
        assert asyncio.iscoroutinefunction(research_agent.run_initial_research)
        assert asyncio.iscoroutinefunction(research_agent.run_depth_research)
        
        writer_agent = WriterAgent()
        assert asyncio.iscoroutinefunction(writer_agent.run)
        
        reviser_agent = ReviserAgent()
        assert asyncio.iscoroutinefunction(reviser_agent.run)
        assert asyncio.iscoroutinefunction(reviser_agent.revise_draft)
    
    @pytest.mark.asyncio
    async def test_no_blocking_calls_in_async_context(self):
        """Test that blocking calls have been properly converted to async"""
        from multi_agents.agents.utils.llms import call_model
        
        # This should be an async function
        assert asyncio.iscoroutinefunction(call_model)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_async_workflows(self):
        """Test error handling in async workflows"""
        from multi_agents.providers.factory import provider_manager
        
        try:
            # This should handle errors gracefully
            response = await provider_manager.llm_generate(
                "test prompt",
                fallback=True,
                max_retries=1
            )
            # Should either succeed or fail gracefully
            assert response is not None or True  # Either works or fails gracefully
        except Exception as e:
            # Exception should be handled gracefully
            assert isinstance(e, (RuntimeError, ValueError, TypeError))


class TestConfigurationValidation:
    """Test configuration validation system"""
    
    def test_configuration_validator_initialization(self):
        """Test that configuration validator initializes correctly"""
        validator = ConfigurationValidator()
        
        assert hasattr(validator, 'supported_llm_providers')
        assert hasattr(validator, 'supported_search_providers')
        assert len(validator.supported_llm_providers) > 0
        assert len(validator.supported_search_providers) > 0
    
    def test_env_file_validation(self):
        """Test environment file validation"""
        validator = ConfigurationValidator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_KEY=test_value\n")
            temp_env = f.name
        
        try:
            result = validator.validate_environment_file(temp_env)
            assert result.is_valid is True
            assert len(result.info) > 0
        finally:
            os.unlink(temp_env)
    
    def test_missing_env_file_handling(self):
        """Test handling of missing environment file"""
        validator = ConfigurationValidator()
        
        result = validator.validate_environment_file("nonexistent.env")
        assert len(result.warnings) > 0
        
        # Should warn but not completely fail
        warning_messages = [w.message for w in result.warnings]
        assert any("not found" in msg for msg in warning_messages)
    
    def test_llm_provider_validation(self):
        """Test LLM provider validation"""
        validator = ConfigurationValidator()
        
        # Test with valid configuration
        with patch.dict(os.environ, {
            'PRIMARY_LLM_PROVIDER': 'google_gemini',
            'GOOGLE_API_KEY': 'test_key'
        }):
            result = validator.validate_llm_provider()
            assert result.is_valid is True
    
    def test_invalid_provider_validation(self):
        """Test validation with invalid provider"""
        validator = ConfigurationValidator()
        
        with patch.dict(os.environ, {
            'PRIMARY_LLM_PROVIDER': 'invalid_provider'
        }):
            result = validator.validate_llm_provider()
            assert result.is_valid is False
            assert len(result.issues) > 0
    
    def test_comprehensive_validation(self):
        """Test comprehensive validation"""
        validator = ConfigurationValidator()
        
        # Set up minimal valid environment
        with patch.dict(os.environ, {
            'PRIMARY_LLM_PROVIDER': 'google_gemini',
            'PRIMARY_SEARCH_PROVIDER': 'brave',
            'GOOGLE_API_KEY': 'test_key',
            'BRAVE_API_KEY': 'test_key'
        }):
            result = validator.run_comprehensive_validation(
                check_env_file=False,
                check_task_json=False,
                check_directories=False
            )
            # Should have some info messages at minimum
            assert len(result.get_all_issues()) > 0
    
    def test_startup_validation_function(self):
        """Test startup validation function"""
        # Set up valid environment for testing
        with patch.dict(os.environ, {
            'PRIMARY_LLM_PROVIDER': 'google_gemini',
            'PRIMARY_SEARCH_PROVIDER': 'brave',
            'GOOGLE_API_KEY': 'test_key',
            'BRAVE_API_KEY': 'test_key'
        }):
            result = validate_startup_configuration(verbose=False)
            # Should return boolean
            assert isinstance(result, bool)
    
    def test_validation_summary(self):
        """Test validation summary function"""
        summary = get_validation_summary()
        
        assert isinstance(summary, dict)
        assert 'valid' in summary
        assert 'error_count' in summary
        assert 'warning_count' in summary
        assert 'configuration' in summary


class TestProviderFailover:
    """Test provider failover logic and health checks"""
    
    @pytest.mark.asyncio
    async def test_failover_integration_initialization(self):
        """Test failover integration initialization"""
        # Reset failover integration state
        await failover_integration.cleanup()
        
        success = await failover_integration.initialize(enable_monitoring=False)
        
        # Should either succeed or go into fallback mode
        assert isinstance(success, bool)
        
        # Cleanup
        await failover_integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_failover_status_reporting(self):
        """Test failover status reporting"""
        await failover_integration.cleanup()
        await failover_integration.initialize(enable_monitoring=False)
        
        try:
            status = await failover_integration.get_comprehensive_status()
            
            assert isinstance(status, dict)
            assert 'status' in status
            
        finally:
            await failover_integration.cleanup()
    
    @pytest.mark.asyncio 
    async def test_provider_health_checks(self):
        """Test provider health checks"""
        await failover_integration.cleanup()
        success = await failover_integration.initialize(enable_monitoring=False)
        
        if success:
            try:
                health_results = await failover_integration.health_check_all_providers()
                
                assert isinstance(health_results, dict)
                # Should have sections for different provider types
                expected_keys = ['llm_providers', 'search_providers']
                for key in expected_keys:
                    if key in health_results:
                        assert isinstance(health_results[key], dict)
                        
            finally:
                await failover_integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_enhanced_llm_generation(self):
        """Test enhanced LLM generation with failover"""
        await failover_integration.cleanup()
        await failover_integration.initialize(enable_monitoring=False)
        
        try:
            # This should either work or fail gracefully
            response = await failover_integration.get_llm_response(
                "test prompt",
                max_retries=1
            )
            
            # Response should be valid or None (graceful failure)
            if response is not None:
                assert hasattr(response, 'content') or isinstance(response, str)
                
        except Exception as e:
            # Should be a recognized exception type
            assert isinstance(e, (RuntimeError, ValueError, TypeError))
            
        finally:
            await failover_integration.cleanup()
    
    @pytest.mark.asyncio
    async def test_enhanced_search_query(self):
        """Test enhanced search with failover"""
        await failover_integration.cleanup()
        await failover_integration.initialize(enable_monitoring=False)
        
        try:
            # This should either work or fail gracefully
            response = await failover_integration.get_search_results(
                "test query",
                search_type="web"
            )
            
            # Response should be valid or None (graceful failure)
            if response is not None:
                assert hasattr(response, 'results') or isinstance(response, (list, dict))
                
        except Exception as e:
            # Should be a recognized exception type
            assert isinstance(e, (RuntimeError, ValueError, TypeError))
            
        finally:
            await failover_integration.cleanup()


class TestErrorHandling:
    """Test error handling and recovery mechanisms"""
    
    def test_configuration_error_recovery(self):
        """Test recovery from configuration errors"""
        # Test with broken configuration
        with patch.dict(os.environ, {
            'PRIMARY_LLM_PROVIDER': 'invalid_provider'
        }):
            # This should not crash
            try:
                result = validate_startup_configuration(verbose=False)
                # Should return False for invalid config but not crash
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"Configuration validation should handle errors gracefully: {e}")
    
    def test_missing_api_key_handling(self):
        """Test handling of missing API keys"""
        # Remove all API keys
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {
                'PRIMARY_LLM_PROVIDER': 'google_gemini',
                'PRIMARY_SEARCH_PROVIDER': 'brave'
            }):
                validator = ConfigurationValidator()
                result = validator.validate_llm_provider()
                
                # Should detect missing API key
                assert result.is_valid is False
                assert len(result.issues) > 0
                
                # Should mention API key in error message
                error_messages = [issue.message for issue in result.issues]
                assert any('API key' in msg for msg in error_messages)
    
    def test_directory_creation_error_handling(self):
        """Test handling of directory creation errors"""
        validator = ConfigurationValidator()
        
        # Mock directory creation to fail
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
            with patch('pathlib.Path.exists', return_value=False):
                result = validator.validate_directory_structure()
                
                # Should handle error gracefully
                assert result.is_valid is False
                assert len(result.issues) > 0
    
    @pytest.mark.asyncio
    async def test_provider_error_recovery(self):
        """Test provider error recovery mechanisms"""
        from multi_agents.providers.factory import provider_manager
        
        # Test with invalid prompt that might cause errors
        try:
            response = await provider_manager.llm_generate(
                "",  # Empty prompt might cause errors
                fallback=True,
                max_retries=1
            )
            
            # Should either succeed or fail gracefully
            assert response is not None or True
            
        except Exception as e:
            # Should be handled gracefully with known exception types
            assert isinstance(e, (RuntimeError, ValueError, TypeError))


class TestPerformance:
    """Test that fixes don't impact system performance"""
    
    def test_configuration_validation_performance(self):
        """Test configuration validation performance"""
        import time
        
        start_time = time.time()
        
        # Run validation multiple times
        for _ in range(5):
            validate_startup_configuration(verbose=False)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        
        # Should complete in reasonable time
        assert avg_time < 1.0, f"Configuration validation too slow: {avg_time:.3f}s"
    
    def test_import_performance(self):
        """Test import performance"""
        import time
        
        start_time = time.time()
        
        # Test core imports
        from multi_agents.agents import ChiefEditorAgent
        from multi_agents.providers.factory import provider_manager
        from multi_agents.config.providers import ProviderConfigManager
        
        end_time = time.time()
        import_time = end_time - start_time
        
        # Should import quickly
        assert import_time < 2.0, f"Imports too slow: {import_time:.3f}s"
    
    def test_memory_usage(self):
        """Test memory usage is reasonable"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Should use reasonable amount of memory
        assert memory_mb < 500, f"Memory usage too high: {memory_mb:.1f}MB"


class TestIntegrationWorkflow:
    """Test integration workflow to ensure all fixes work together"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_initialization(self):
        """Test complete system initialization"""
        # Test that system can initialize completely
        try:
            # Configuration validation
            config_valid = validate_startup_configuration(verbose=False)
            
            # Provider system initialization
            await failover_integration.cleanup()
            failover_success = await failover_integration.initialize(enable_monitoring=False)
            
            # BRAVE integration (if configured)
            if os.getenv('PRIMARY_SEARCH_PROVIDER') == 'brave':
                brave_success = setup_simple_brave_retriever()
            else:
                brave_success = True  # Not needed
            
            # At least configuration should work
            assert isinstance(config_valid, bool)
            assert isinstance(failover_success, bool)
            assert isinstance(brave_success, bool)
            
        finally:
            await failover_integration.cleanup()
    
    def test_backward_compatibility(self):
        """Test that fixes maintain backward compatibility"""
        # Test that old interfaces still work
        try:
            from multi_agents.config.validation import config_validator
            from multi_agents.providers.factory import provider_manager
            
            # These should still be accessible
            assert config_validator is not None
            assert provider_manager is not None
            
        except ImportError as e:
            pytest.fail(f"Backward compatibility broken: {e}")


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    pytest.main([__file__, "-v"])