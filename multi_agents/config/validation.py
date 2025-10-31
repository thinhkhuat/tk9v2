"""
Configuration Validation System for Deep Research MCP
Comprehensive validation of provider configurations, API keys, and task settings
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    level: ValidationLevel
    component: str
    message: str
    suggestion: Optional[str] = None
    code: Optional[str] = None
    
    def __str__(self):
        prefix = {
            ValidationLevel.ERROR: "❌ ERROR",
            ValidationLevel.WARNING: "⚠️  WARNING", 
            ValidationLevel.INFO: "ℹ️  INFO"
        }
        result = f"{prefix[self.level]} [{self.component}]: {self.message}"
        if self.suggestion:
            result += f"\n   💡 Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """Results of a validation check"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    
    def add_error(self, component: str, message: str, suggestion: str = None, code: str = None):
        """Add an error-level validation issue"""
        issue = ValidationIssue(ValidationLevel.ERROR, component, message, suggestion, code)
        self.issues.append(issue)
        self.is_valid = False
        
    def add_warning(self, component: str, message: str, suggestion: str = None, code: str = None):
        """Add a warning-level validation issue"""
        issue = ValidationIssue(ValidationLevel.WARNING, component, message, suggestion, code)
        self.warnings.append(issue)
        
    def add_info(self, component: str, message: str, suggestion: str = None, code: str = None):
        """Add an info-level validation issue"""
        issue = ValidationIssue(ValidationLevel.INFO, component, message, suggestion, code)
        self.info.append(issue)
    
    def get_all_issues(self) -> List[ValidationIssue]:
        """Get all issues across all levels"""
        return self.issues + self.warnings + self.info
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.issues) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0


class ConfigurationValidator:
    """Comprehensive configuration validator for the Deep Research MCP system"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv(override=True)
        
        # Define supported providers and models
        self.supported_llm_providers = {
            "openai": {
                "api_key_env": "OPENAI_API_KEY",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini"],
                "required_env": ["OPENAI_API_KEY"]
            },
            "google_gemini": {
                "api_key_env": "GOOGLE_API_KEY", 
                "models": ["gemini-2.5-flash-preview-04-17-thinking", "gemini-2.5-flash-preview-05-20", "gemini-1.5-pro", "gemini-1.5-flash"],
                "required_env": ["GOOGLE_API_KEY"]
            },
            "anthropic": {
                "api_key_env": "ANTHROPIC_API_KEY",
                "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "required_env": ["ANTHROPIC_API_KEY"]
            },
            "azure_openai": {
                "api_key_env": "AZURE_OPENAI_API_KEY", 
                "models": ["gpt-4", "gpt-35-turbo"],
                "required_env": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
            }
        }
        
        self.supported_search_providers = {
            "tavily": {
                "api_key_env": "TAVILY_API_KEY",
                "required_env": ["TAVILY_API_KEY"]
            },
            "brave": {
                "api_key_env": "BRAVE_API_KEY",
                "required_env": ["BRAVE_API_KEY"]
            },
            "google": {
                "api_key_env": "GOOGLE_API_KEY",
                "required_env": ["GOOGLE_API_KEY", "GOOGLE_CSE_ID"]
            },
            "serpapi": {
                "api_key_env": "SERPAPI_API_KEY",
                "required_env": ["SERPAPI_API_KEY"]
            },
            "duckduckgo": {
                "api_key_env": None,
                "required_env": []  # No API key required
            }
        }
        
        self.supported_languages = {
            "en": "English",
            "vi": "Vietnamese", 
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ar": "Arabic"
        }
        
        self.required_core_settings = [
            "PRIMARY_LLM_PROVIDER",
            "PRIMARY_SEARCH_PROVIDER"
        ]
    
    def validate_environment_file(self, env_path: str = ".env") -> ValidationResult:
        """Validate the .env file exists and is readable"""
        result = ValidationResult(is_valid=True)
        
        # Check if .env file exists
        if not Path(env_path).exists():
            result.add_warning(
                "Environment", 
                f"Environment file '{env_path}' not found",
                "Create a .env file based on .env.example"
            )
        else:
            try:
                # Try to read the file
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check file is not empty
                if not content.strip():
                    result.add_warning(
                        "Environment",
                        f"Environment file '{env_path}' is empty",
                        "Add configuration variables to your .env file"
                    )
                else:
                    result.add_info(
                        "Environment", 
                        f"Environment file '{env_path}' found and readable"
                    )
                    
            except Exception as e:
                result.add_error(
                    "Environment",
                    f"Cannot read environment file '{env_path}': {str(e)}",
                    "Check file permissions and encoding"
                )
        
        return result
    
    def validate_core_settings(self) -> ValidationResult:
        """Validate core required configuration settings"""
        result = ValidationResult(is_valid=True)
        
        for setting in self.required_core_settings:
            value = os.getenv(setting)
            if not value:
                result.add_error(
                    "Core Config",
                    f"Required setting '{setting}' is not configured",
                    f"Set {setting} in your .env file"
                )
            elif value in [f"your_{setting.lower()}_here", "not_configured"]:
                result.add_error(
                    "Core Config",
                    f"Setting '{setting}' contains placeholder value",
                    f"Replace placeholder with actual value in .env file"
                )
            else:
                result.add_info("Core Config", f"'{setting}' is configured")
        
        return result
    
    def validate_llm_provider(self, provider_key: str = "PRIMARY_LLM_PROVIDER") -> ValidationResult:
        """Validate LLM provider configuration"""
        result = ValidationResult(is_valid=True)
        
        provider = os.getenv(provider_key)
        if not provider:
            result.add_error(
                "LLM Provider",
                f"LLM provider '{provider_key}' not configured",
                "Set PRIMARY_LLM_PROVIDER in .env file"
            )
            return result
        
        # Check if provider is supported
        if provider not in self.supported_llm_providers:
            result.add_error(
                "LLM Provider",
                f"Unsupported LLM provider: {provider}",
                f"Use one of: {', '.join(self.supported_llm_providers.keys())}"
            )
            return result
        
        provider_config = self.supported_llm_providers[provider]
        
        # Validate API key
        api_key_env = provider_config["api_key_env"]
        if api_key_env:
            api_key = os.getenv(api_key_env)
            if not api_key:
                result.add_error(
                    "LLM Provider",
                    f"API key '{api_key_env}' not configured for {provider}",
                    f"Set {api_key_env} in your .env file"
                )
            elif api_key.startswith("your_") or api_key == "not_configured":
                result.add_error(
                    "LLM Provider", 
                    f"API key '{api_key_env}' contains placeholder value",
                    "Replace with actual API key"
                )
            else:
                # Basic API key format validation
                if provider == "openai" and not api_key.startswith("sk-"):
                    result.add_warning(
                        "LLM Provider",
                        "OpenAI API key should start with 'sk-'",
                        "Verify your API key format"
                    )
                result.add_info("LLM Provider", f"API key for {provider} is configured")
        
        # Validate required environment variables
        for env_var in provider_config.get("required_env", []):
            if not os.getenv(env_var):
                result.add_error(
                    "LLM Provider",
                    f"Required environment variable '{env_var}' not set for {provider}",
                    f"Set {env_var} in your .env file"
                )
        
        # Validate model
        model_key = provider_key.replace("PROVIDER", "MODEL")
        model = os.getenv(model_key)
        if model and model not in provider_config["models"]:
            result.add_warning(
                "LLM Provider",
                f"Model '{model}' not in recommended list for {provider}",
                f"Consider using: {', '.join(provider_config['models'][:3])}"
            )
        elif model:
            result.add_info("LLM Provider", f"Model '{model}' is supported")
        
        return result
    
    def validate_search_provider(self, provider_key: str = "PRIMARY_SEARCH_PROVIDER") -> ValidationResult:
        """Validate search provider configuration"""
        result = ValidationResult(is_valid=True)
        
        provider = os.getenv(provider_key)
        if not provider:
            result.add_error(
                "Search Provider",
                f"Search provider '{provider_key}' not configured",
                "Set PRIMARY_SEARCH_PROVIDER in .env file"
            )
            return result
        
        # Check if provider is supported
        if provider not in self.supported_search_providers:
            result.add_error(
                "Search Provider",
                f"Unsupported search provider: {provider}",
                f"Use one of: {', '.join(self.supported_search_providers.keys())}"
            )
            return result
        
        provider_config = self.supported_search_providers[provider]
        
        # Validate API key (if required)
        api_key_env = provider_config["api_key_env"]
        if api_key_env:
            api_key = os.getenv(api_key_env)
            if not api_key:
                result.add_error(
                    "Search Provider",
                    f"API key '{api_key_env}' not configured for {provider}",
                    f"Set {api_key_env} in your .env file"
                )
            elif api_key.startswith("your_") or api_key == "not_configured":
                result.add_error(
                    "Search Provider",
                    f"API key '{api_key_env}' contains placeholder value", 
                    "Replace with actual API key"
                )
            else:
                result.add_info("Search Provider", f"API key for {provider} is configured")
        else:
            result.add_info("Search Provider", f"{provider} does not require API key")
        
        # Validate required environment variables
        for env_var in provider_config.get("required_env", []):
            if not os.getenv(env_var):
                result.add_error(
                    "Search Provider",
                    f"Required environment variable '{env_var}' not set for {provider}",
                    f"Set {env_var} in your .env file"
                )
        
        return result
    
    def validate_task_json(self, task_path: str = "multi_agents/task.json") -> ValidationResult:
        """Validate task.json configuration file"""
        result = ValidationResult(is_valid=True)
        
        # Check if file exists
        if not Path(task_path).exists():
            result.add_error(
                "Task Config",
                f"Task configuration file '{task_path}' not found",
                "Ensure task.json exists in the multi_agents directory"
            )
            return result
        
        try:
            # Load and parse JSON
            with open(task_path, 'r', encoding='utf-8') as f:
                task_config = json.load(f)
            
            # Validate required fields
            required_fields = ["query", "max_sections", "publish_formats", "model"]
            for field in required_fields:
                if field not in task_config:
                    result.add_error(
                        "Task Config",
                        f"Required field '{field}' missing from task.json",
                        f"Add '{field}' to task.json configuration"
                    )
            
            # Validate field values
            if "max_sections" in task_config:
                max_sections = task_config["max_sections"]
                if not isinstance(max_sections, int) or max_sections < 1:
                    result.add_error(
                        "Task Config",
                        "max_sections must be a positive integer",
                        "Set max_sections to a value >= 1"
                    )
                elif max_sections > 20:
                    result.add_warning(
                        "Task Config", 
                        f"max_sections ({max_sections}) is quite high",
                        "Consider using fewer sections for faster processing"
                    )
            
            # Validate publish formats
            if "publish_formats" in task_config:
                formats = task_config["publish_formats"]
                if not isinstance(formats, dict):
                    result.add_error(
                        "Task Config",
                        "publish_formats must be an object/dictionary",
                        "Set publish_formats as {\"markdown\": true, \"pdf\": true, \"docx\": true}"
                    )
                else:
                    supported_formats = ["markdown", "pdf", "docx"]
                    for fmt in formats:
                        if fmt not in supported_formats:
                            result.add_warning(
                                "Task Config",
                                f"Unknown publish format: {fmt}",
                                f"Supported formats: {', '.join(supported_formats)}"
                            )
            
            # Validate language setting
            if "language" in task_config:
                language = task_config["language"]
                if language not in self.supported_languages:
                    result.add_warning(
                        "Task Config", 
                        f"Language '{language}' may not be fully supported",
                        f"Recommended languages: {', '.join(list(self.supported_languages.keys())[:6])}"
                    )
                else:
                    result.add_info("Task Config", f"Language '{language}' ({self.supported_languages[language]}) is supported")
            
            result.add_info("Task Config", "task.json is valid and readable")
            
        except json.JSONDecodeError as e:
            result.add_error(
                "Task Config",
                f"Invalid JSON syntax in task.json: {str(e)}",
                "Fix JSON syntax errors in task.json"
            )
        except Exception as e:
            result.add_error(
                "Task Config",
                f"Error reading task.json: {str(e)}",
                "Check file permissions and format"
            )
        
        return result
    
    def validate_language_settings(self) -> ValidationResult:
        """Validate language configuration"""
        result = ValidationResult(is_valid=True)
        
        research_language = os.getenv("RESEARCH_LANGUAGE", "en")
        
        if research_language not in self.supported_languages:
            result.add_warning(
                "Language Config",
                f"Research language '{research_language}' may not be fully supported",
                f"Consider using: {', '.join(list(self.supported_languages.keys())[:6])}"
            )
        else:
            lang_name = self.supported_languages[research_language]
            result.add_info("Language Config", f"Research language set to {lang_name} ({research_language})")
        
        # Check for inconsistent language settings
        task_path = Path("multi_agents/task.json")
        if task_path.exists():
            try:
                with open(task_path, 'r', encoding='utf-8') as f:
                    task_config = json.load(f)
                
                task_language = task_config.get("language", "en")
                if task_language != research_language:
                    result.add_warning(
                        "Language Config",
                        f"Language mismatch: RESEARCH_LANGUAGE={research_language}, task.json language={task_language}",
                        "Ensure language settings are consistent across configuration files"
                    )
            except:
                pass  # Already handled in task validation
        
        return result
    
    def validate_directory_structure(self) -> ValidationResult:
        """Validate required directories exist and are writable"""
        result = ValidationResult(is_valid=True)
        
        # Check output directory
        output_dir = Path("outputs")
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                result.add_info("Directory", "Created outputs directory")
            except Exception as e:
                result.add_error(
                    "Directory",
                    f"Cannot create outputs directory: {str(e)}",
                    "Check write permissions for current directory"
                )
        elif not os.access(output_dir, os.W_OK):
            result.add_error(
                "Directory",
                "outputs directory is not writable",
                "Check directory permissions"
            )
        else:
            result.add_info("Directory", "outputs directory exists and is writable")
        
        # Check other critical directories
        critical_dirs = [
            "multi_agents",
            "multi_agents/agents", 
            "multi_agents/config",
            "multi_agents/providers"
        ]
        
        for dir_path in critical_dirs:
            if not Path(dir_path).exists():
                result.add_error(
                    "Directory",
                    f"Critical directory '{dir_path}' missing",
                    "Ensure all required project directories are present"
                )
        
        return result
    
    def validate_provider_strategies(self) -> ValidationResult:
        """Validate provider strategy settings"""
        result = ValidationResult(is_valid=True)
        
        valid_strategies = ["primary_only", "fallback_on_error", "load_balance"]
        
        llm_strategy = os.getenv("LLM_STRATEGY", "primary_only")
        search_strategy = os.getenv("SEARCH_STRATEGY", "primary_only")
        
        if llm_strategy not in valid_strategies:
            result.add_error(
                "Strategy Config",
                f"Invalid LLM_STRATEGY: {llm_strategy}",
                f"Use one of: {', '.join(valid_strategies)}"
            )
        
        if search_strategy not in valid_strategies:
            result.add_error(
                "Strategy Config",
                f"Invalid SEARCH_STRATEGY: {search_strategy}",
                f"Use one of: {', '.join(valid_strategies)}"
            )
        
        # Check fallback providers if strategy requires them
        if llm_strategy in ["fallback_on_error", "load_balance"]:
            if not os.getenv("FALLBACK_LLM_PROVIDER"):
                result.add_warning(
                    "Strategy Config",
                    f"LLM strategy '{llm_strategy}' specified but no fallback provider configured",
                    "Set FALLBACK_LLM_PROVIDER or change strategy to 'primary_only'"
                )
        
        if search_strategy in ["fallback_on_error", "load_balance"]:
            if not os.getenv("FALLBACK_SEARCH_PROVIDER"):
                result.add_warning(
                    "Strategy Config",
                    f"Search strategy '{search_strategy}' specified but no fallback provider configured",
                    "Set FALLBACK_SEARCH_PROVIDER or change strategy to 'primary_only'"
                )
        
        return result
    
    def validate_numeric_settings(self) -> ValidationResult:
        """Validate numeric configuration values"""
        result = ValidationResult(is_valid=True)
        
        numeric_settings = {
            "LLM_TEMPERATURE": (0.0, 2.0, "Temperature should be between 0.0 and 2.0"),
            "LLM_MAX_TOKENS": (1, 200000, "Max tokens should be between 1 and 200000"),
            "SEARCH_MAX_RESULTS": (1, 100, "Search max results should be between 1 and 100"),
            "PROVIDER_TIMEOUT": (1, 300, "Provider timeout should be between 1 and 300 seconds"),
            "PROVIDER_MAX_RETRIES": (0, 10, "Max retries should be between 0 and 10")
        }
        
        for setting, (min_val, max_val, message) in numeric_settings.items():
            value_str = os.getenv(setting)
            if value_str:
                try:
                    if setting in ["LLM_TEMPERATURE"]:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                    
                    if not (min_val <= value <= max_val):
                        result.add_warning(
                            "Numeric Config",
                            f"{setting}={value} is outside recommended range",
                            message
                        )
                    else:
                        result.add_info("Numeric Config", f"{setting} is configured correctly")
                        
                except ValueError:
                    result.add_error(
                        "Numeric Config",
                        f"{setting} has invalid numeric value: {value_str}",
                        "Provide a valid numeric value"
                    )
        
        return result
    
    def run_comprehensive_validation(self, 
                                   check_env_file: bool = True,
                                   check_task_json: bool = True,
                                   check_directories: bool = True) -> ValidationResult:
        """Run all validation checks and return comprehensive results"""
        overall_result = ValidationResult(is_valid=True)
        
        # Run all validation checks
        validation_checks = [
            ("Core Settings", self.validate_core_settings),
            ("LLM Provider", self.validate_llm_provider),
            ("Search Provider", self.validate_search_provider),
            ("Language Settings", self.validate_language_settings),
            ("Provider Strategies", self.validate_provider_strategies),
            ("Numeric Settings", self.validate_numeric_settings)
        ]
        
        if check_env_file:
            validation_checks.insert(0, ("Environment File", self.validate_environment_file))
        
        if check_task_json:
            validation_checks.append(("Task Configuration", self.validate_task_json))
        
        if check_directories:
            validation_checks.append(("Directory Structure", self.validate_directory_structure))
        
        # Run all checks and consolidate results
        for check_name, check_func in validation_checks:
            try:
                result = check_func()
                
                # Merge results
                overall_result.issues.extend(result.issues)
                overall_result.warnings.extend(result.warnings) 
                overall_result.info.extend(result.info)
                
                # Overall validity is false if any check fails
                if not result.is_valid:
                    overall_result.is_valid = False
                    
            except Exception as e:
                overall_result.add_error(
                    check_name,
                    f"Validation check failed: {str(e)}",
                    "Check system configuration and try again"
                )
        
        return overall_result
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration status"""
        return {
            "providers": {
                "llm": {
                    "primary": os.getenv("PRIMARY_LLM_PROVIDER", "not_set"),
                    "model": os.getenv("PRIMARY_LLM_MODEL", "not_set"),
                    "fallback": os.getenv("FALLBACK_LLM_PROVIDER", "none")
                },
                "search": {
                    "primary": os.getenv("PRIMARY_SEARCH_PROVIDER", "not_set"),
                    "fallback": os.getenv("FALLBACK_SEARCH_PROVIDER", "none")
                }
            },
            "strategies": {
                "llm": os.getenv("LLM_STRATEGY", "primary_only"),
                "search": os.getenv("SEARCH_STRATEGY", "primary_only")
            },
            "language": {
                "research": os.getenv("RESEARCH_LANGUAGE", "en")
            },
            "directories": {
                "outputs_exists": Path("outputs").exists(),
                "task_json_exists": Path("multi_agents/task.json").exists()
            }
        }


# Global validator instance
config_validator = ConfigurationValidator()


def validate_startup_configuration(verbose: bool = True) -> bool:
    """
    Validate configuration at startup and return whether system is ready.
    
    Args:
        verbose: Whether to print detailed validation results
        
    Returns:
        True if configuration is valid for startup, False otherwise
    """
    result = config_validator.run_comprehensive_validation()
    
    if verbose:
        print("\n🔍 Configuration Validation Results")
        print("=" * 50)
        
        # Print errors
        if result.has_errors():
            print(f"\n❌ ERRORS ({len(result.issues)}):")
            for issue in result.issues:
                print(f"   {issue}")
        
        # Print warnings  
        if result.has_warnings():
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for issue in result.warnings:
                print(f"   {issue}")
        
        # Print info
        if result.info:
            print(f"\n✅ CONFIGURATION STATUS ({len(result.info)}):")
            for issue in result.info:
                print(f"   {issue}")
        
        print("\n" + "=" * 50)
        
        if result.is_valid:
            print("🟢 Configuration is VALID - System ready to start")
        else:
            print("🔴 Configuration has ERRORS - Fix issues before starting")
            print("\n💡 Quick fixes:")
            print("   1. Copy .env.example to .env and configure your API keys")
            print("   2. Set PRIMARY_LLM_PROVIDER and PRIMARY_SEARCH_PROVIDER")  
            print("   3. Ensure all required API keys are configured")
        
        print()
    
    return result.is_valid


def get_validation_summary() -> Dict[str, Any]:
    """Get a quick validation summary for external tools"""
    result = config_validator.run_comprehensive_validation()
    
    return {
        "valid": result.is_valid,
        "error_count": len(result.issues),
        "warning_count": len(result.warnings),
        "info_count": len(result.info),
        "errors": [{"component": issue.component, "message": issue.message} for issue in result.issues],
        "warnings": [{"component": issue.component, "message": issue.message} for issue in result.warnings],
        "configuration": config_validator.get_configuration_summary()
    }