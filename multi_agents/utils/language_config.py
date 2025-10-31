"""
Language Configuration Module
Handles system-wide language settings for the entire research process
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LanguageConfig:
    """Manages language configuration for the entire research process"""
    
    # Language code mappings
    LANGUAGE_CODES = {
        'en': 'English',
        'vi': 'Vietnamese', 
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'pt': 'Portuguese',
        'it': 'Italian',
        'ru': 'Russian',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'th': 'Thai'
    }
    
    # Country codes for search optimization
    LANGUAGE_TO_COUNTRY = {
        'en': 'US',
        'vi': 'VN',
        'es': 'ES', 
        'fr': 'FR',
        'de': 'DE',
        'zh': 'CN',
        'ja': 'JP',
        'ko': 'KR',
        'pt': 'BR',
        'it': 'IT',
        'ru': 'RU',
        'ar': 'SA',
        'hi': 'IN',
        'th': 'TH'
    }
    
    # Brave UI language codes
    BRAVE_UI_LANGS = {
        'en': 'en-US',
        'vi': 'vi-VN',
        'es': 'es-ES',
        'fr': 'fr-FR', 
        'de': 'de-DE',
        'zh': 'zh-CN',
        'ja': 'ja-JP',
        'ko': 'ko-KR',
        'pt': 'pt-BR',
        'it': 'it-IT',
        'ru': 'ru-RU',
        'ar': 'ar-SA',
        'hi': 'hi-IN',
        'th': 'th-TH'
    }
    
    @classmethod
    def get_research_language(cls) -> str:
        """Get the configured research language code"""
        return os.getenv('RESEARCH_LANGUAGE', 'en').lower()
    
    @classmethod
    def get_language_name(cls, lang_code: Optional[str] = None) -> str:
        """Get the full language name"""
        if lang_code is None:
            lang_code = cls.get_research_language()
        return cls.LANGUAGE_CODES.get(lang_code, 'English')
    
    @classmethod
    def get_search_country(cls, lang_code: Optional[str] = None) -> str:
        """Get the appropriate country code for search optimization"""
        if lang_code is None:
            lang_code = cls.get_research_language()
        return cls.LANGUAGE_TO_COUNTRY.get(lang_code, 'US')
    
    @classmethod
    def get_brave_ui_lang(cls, lang_code: Optional[str] = None) -> str:
        """Get the appropriate Brave UI language code"""
        if lang_code is None:
            lang_code = cls.get_research_language()
        return cls.BRAVE_UI_LANGS.get(lang_code, 'en-US')
    
    @classmethod
    def is_supported(cls, lang_code: str) -> bool:
        """Check if a language code is supported"""
        return lang_code.lower() in cls.LANGUAGE_CODES
    
    @classmethod
    def get_prompt_prefix(cls, lang_code: Optional[str] = None) -> str:
        """Get language-specific prompt prefix for LLM instructions"""
        if lang_code is None:
            lang_code = cls.get_research_language()
        
        language_name = cls.get_language_name(lang_code)
        
        if lang_code == 'en':
            return "You MUST respond and work entirely in English."
        elif lang_code == 'vi':
            return f"Bạn PHẢI trả lời và làm việc hoàn toàn bằng tiếng Việt. All content, research, analysis, and output must be in Vietnamese language."
        elif lang_code == 'es':
            return f"Debes responder y trabajar completamente en español. Todo el contenido, investigación, análisis y salida debe estar en idioma español."
        elif lang_code == 'fr':
            return f"Vous DEVEZ répondre et travailler entièrement en français. Tout le contenu, la recherche, l'analyse et la sortie doivent être en langue française."
        elif lang_code == 'de':
            return f"Sie MÜSSEN vollständig auf Deutsch antworten und arbeiten. Alle Inhalte, Recherchen, Analysen und Ausgaben müssen in deutscher Sprache sein."
        elif lang_code == 'zh':
            return f"您必须完全用中文回答和工作。所有内容、研究、分析和输出都必须使用中文。"
        elif lang_code == 'ja':
            return f"日本語で完全に回答し、作業してください。すべてのコンテンツ、研究、分析、出力は日本語である必要があります。"
        elif lang_code == 'ko':
            return f"한국어로 완전히 응답하고 작업해야 합니다. 모든 콘텐츠, 연구, 분석 및 출력은 한국어여야 합니다."
        else:
            return f"You MUST respond and work entirely in {language_name}. All content, research, analysis, and output must be in {language_name} language."
    
    @classmethod
    def get_search_terms_instruction(cls, lang_code: Optional[str] = None) -> str:
        """Get language-specific search terms instruction"""
        if lang_code is None:
            lang_code = cls.get_research_language()
        
        language_name = cls.get_language_name(lang_code)
        
        if lang_code == 'en':
            return "Generate search terms in English."
        elif lang_code == 'vi':
            return "Tạo các từ khóa tìm kiếm bằng tiếng Việt. Use Vietnamese keywords for web searches."
        elif lang_code == 'es':
            return "Genere términos de búsqueda en español. Use Spanish keywords for web searches."
        elif lang_code == 'fr':
            return "Générez des termes de recherche en français. Use French keywords for web searches."
        elif lang_code == 'de':
            return "Generieren Sie Suchbegriffe auf Deutsch. Use German keywords for web searches."
        elif lang_code == 'zh':
            return "生成中文搜索词。Use Chinese keywords for web searches."
        elif lang_code == 'ja':
            return "日本語で検索用語を生成してください。Use Japanese keywords for web searches."
        elif lang_code == 'ko':
            return "한국어로 검색어를 생성하세요. Use Korean keywords for web searches."
        else:
            return f"Generate search terms in {language_name}. Use {language_name} keywords for web searches."
    
    @classmethod
    def apply_to_environment(cls, lang_code: Optional[str] = None):
        """Apply language settings to environment variables - MODIFIED FOR RESEARCH QUALITY"""
        if lang_code is None:
            lang_code = cls.get_research_language()
        
        # REMOVED: Search language and country constraints that hurt research quality
        # Research agents should use English searches for best, most recent sources
        # Only set RESEARCH_LANGUAGE for the final translation step
        
        # Force English for search to get the best sources
        os.environ['SEARCH_LANGUAGE'] = 'en'
        os.environ['SEARCH_COUNTRY'] = 'US'
        os.environ['BRAVE_UI_LANG'] = 'en'
        
        # Set target language for final translation only
        os.environ['RESEARCH_LANGUAGE'] = lang_code
    
    @classmethod
    def get_guidelines_instruction(cls, lang_code: Optional[str] = None) -> str:
        """Get language-specific guidelines instruction for final output"""
        if lang_code is None:
            lang_code = cls.get_research_language()
        
        language_name = cls.get_language_name(lang_code)
        
        if lang_code == 'en':
            return "The final report MUST be written in English"
        elif lang_code == 'vi':
            return "Báo cáo cuối cùng PHẢI được viết bằng tiếng Việt"
        elif lang_code == 'es':
            return "El informe final DEBE estar escrito en español"
        elif lang_code == 'fr':
            return "Le rapport final DOIT être rédigé en français"
        elif lang_code == 'de':
            return "Der Abschlussbericht MUSS auf Deutsch verfasst werden"
        elif lang_code == 'zh':
            return "最终报告必须用中文撰写"
        elif lang_code == 'ja':
            return "最終レポートは日本語で書かれなければなりません"
        elif lang_code == 'ko':
            return "최종 보고서는 한국어로 작성되어야 합니다"
        else:
            return f"The final report MUST be written in {language_name}"
    
    @classmethod
    def get_status_message(cls) -> str:
        """Get current language configuration status message"""
        lang_code = cls.get_research_language()
        language_name = cls.get_language_name(lang_code)
        country = cls.get_search_country(lang_code)
        
        return f"Research Language: {language_name} ({lang_code.upper()}) | Search Region: {country}"

# Initialize language configuration
language_config = LanguageConfig()