"""
End-to-end tests for the complete research and translation workflow.
Tests the entire system integration from query to final translated output.
"""

import asyncio
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.append("/Users/thinhkhuat/DEV--local/multi-agent-deep-research/deep-research-mcp-og")

from multi_agents.agents.orchestrator import ChiefEditorAgent


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

        # Comprehensive test task
        self.task = {
            "query": "The impact of artificial intelligence on modern healthcare systems",
            "language": "vi",
            "max_sections": 3,
            "publish_formats": ["md", "pdf", "docx"],
            "model": "gemini-2.5-flash-preview-04-17-thinking",
            "guidelines": [
                "Focus on recent developments (2020-2024)",
                "Include both benefits and challenges",
                "Cite reliable sources",
            ],
            "tone": "analytical",
            "include_human_feedback": False,
            "follow_guidelines": True,
        }

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_workflow_with_translation(self):
        """Test the complete workflow from query to translated files"""

        # Mock all external dependencies to avoid real API calls
        with patch(
            "multi_agents.agents.researcher.ResearchAgent.run_initial_research"
        ) as mock_browser:
            with patch("multi_agents.agents.editor.EditorAgent.plan_research") as mock_planner:
                with patch(
                    "multi_agents.agents.editor.EditorAgent.run_parallel_research"
                ) as mock_researcher:
                    with patch("multi_agents.agents.writer.WriterAgent.run") as mock_writer:
                        with patch(
                            "multi_agents.agents.publisher.PublisherAgent.run"
                        ) as mock_publisher:
                            with patch(
                                "multi_agents.agents.translator.TranslatorAgent.run"
                            ) as mock_translator:

                                # Setup mock responses that simulate real workflow
                                await self._setup_workflow_mocks(
                                    mock_browser,
                                    mock_planner,
                                    mock_researcher,
                                    mock_writer,
                                    mock_publisher,
                                    mock_translator,
                                )

                                # Create orchestrator with file output
                                orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)

                                # Override output directory
                                orchestrator.output_dir = self.temp_dir

                                # Run complete workflow
                                result = await orchestrator.run_research_task("e2e_test")

                                # Verify final result structure
                                assert result is not None
                                assert "task" in result
                                assert "workflow_complete" in result
                                assert result["workflow_complete"] is True

                                # Verify translation was executed for Vietnamese
                                mock_translator.assert_called_once()

    @pytest.mark.asyncio
    async def test_english_workflow_no_translation(self):
        """Test workflow with English language (should skip translation)"""

        english_task = self.task.copy()
        english_task["language"] = "en"

        with patch(
            "multi_agents.agents.researcher.ResearchAgent.run_initial_research"
        ) as mock_browser:
            with patch("multi_agents.agents.editor.EditorAgent.plan_research") as mock_planner:
                with patch(
                    "multi_agents.agents.editor.EditorAgent.run_parallel_research"
                ) as mock_researcher:
                    with patch("multi_agents.agents.writer.WriterAgent.run") as mock_writer:
                        with patch(
                            "multi_agents.agents.publisher.PublisherAgent.run"
                        ) as mock_publisher:
                            with patch(
                                "multi_agents.agents.translator.TranslatorAgent.run"
                            ) as mock_translator:

                                await self._setup_workflow_mocks(
                                    mock_browser,
                                    mock_planner,
                                    mock_researcher,
                                    mock_writer,
                                    mock_publisher,
                                    mock_translator,
                                )

                                orchestrator = ChiefEditorAgent(
                                    task=english_task, write_to_files=True
                                )
                                orchestrator.output_dir = self.temp_dir

                                result = await orchestrator.run_research_task("english_test")

                                # Verify workflow completed without translation
                                assert result is not None
                                assert "task" in result

                                # Translation should not have been called for English
                                mock_translator.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test workflow error handling and recovery"""

        with patch(
            "multi_agents.agents.researcher.ResearchAgent.run_initial_research"
        ) as mock_browser:
            with patch("multi_agents.agents.editor.EditorAgent.plan_research") as mock_planner:
                with patch(
                    "multi_agents.agents.editor.EditorAgent.run_parallel_research"
                ) as mock_researcher:
                    with patch("multi_agents.agents.writer.WriterAgent.run") as mock_writer:
                        with patch(
                            "multi_agents.agents.publisher.PublisherAgent.run"
                        ) as mock_publisher:
                            with patch(
                                "multi_agents.agents.translator.TranslatorAgent.run"
                            ) as mock_translator:

                                # Setup mocks with one failure
                                await self._setup_workflow_mocks(
                                    mock_browser,
                                    mock_planner,
                                    mock_researcher,
                                    mock_writer,
                                    mock_publisher,
                                    mock_translator,
                                )

                                # Make translator fail
                                mock_translator.return_value = {
                                    "translation_result": {
                                        "status": "error",
                                        "message": "Translation service unavailable",
                                    },
                                    "workflow_complete": True,
                                }

                                orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)
                                orchestrator.output_dir = self.temp_dir

                                # Should still complete workflow even with translation error
                                result = await orchestrator.run_research_task("error_test")

                                assert result is not None
                                assert result["workflow_complete"] is True
                                assert result["translation_result"]["status"] == "error"

    async def _setup_workflow_mocks(
        self,
        mock_browser,
        mock_planner,
        mock_researcher,
        mock_writer,
        mock_publisher,
        mock_translator,
    ):
        """Setup comprehensive mocks for workflow agents"""

        # Mock browser agent (initial research)
        mock_browser.return_value = {
            "task": self.task,
            "initial_research": {
                "query": self.task["query"],
                "sources": [
                    {
                        "url": "https://example.com/ai-healthcare-1",
                        "title": "AI in Healthcare: Recent Advances",
                    },
                    {
                        "url": "https://example.com/ai-healthcare-2",
                        "title": "Healthcare AI Challenges",
                    },
                ],
                "summary": "Initial research on AI in healthcare reveals significant developments and challenges.",
            },
        }

        # Mock planner agent
        mock_planner.return_value = {
            "task": self.task,
            "initial_research": mock_browser.return_value["initial_research"],
            "research_plan": {
                "sections": [
                    {
                        "title": "Current AI Applications in Healthcare",
                        "query": "AI applications healthcare 2024",
                    },
                    {
                        "title": "Benefits and Improvements",
                        "query": "AI benefits healthcare efficiency",
                    },
                    {
                        "title": "Challenges and Limitations",
                        "query": "AI healthcare challenges limitations",
                    },
                ]
            },
            "human_feedback": None,
        }

        # Mock parallel researcher
        mock_researcher.return_value = {
            "task": self.task,
            "initial_research": mock_browser.return_value["initial_research"],
            "research_plan": mock_planner.return_value["research_plan"],
            "sections": [
                {
                    "title": "Current AI Applications in Healthcare",
                    "content": "AI is currently being used in diagnostics, treatment planning, and patient monitoring...",
                    "sources": ["source1", "source2"],
                },
                {
                    "title": "Benefits and Improvements",
                    "content": "AI has shown significant improvements in diagnostic accuracy and efficiency...",
                    "sources": ["source3", "source4"],
                },
                {
                    "title": "Challenges and Limitations",
                    "content": "Despite advances, AI faces challenges including data privacy and algorithmic bias...",
                    "sources": ["source5", "source6"],
                },
            ],
            "human_feedback": None,
        }

        # Mock writer agent
        mock_writer.return_value = {
            "task": self.task,
            "initial_research": mock_browser.return_value["initial_research"],
            "research_plan": mock_planner.return_value["research_plan"],
            "sections": mock_researcher.return_value["sections"],
            "draft": {
                "content": """# The Impact of Artificial Intelligence on Modern Healthcare Systems

## Introduction
Artificial intelligence is revolutionizing healthcare through advanced diagnostics and treatment optimization.

## Current AI Applications in Healthcare
AI is currently being used in diagnostics, treatment planning, and patient monitoring...

## Benefits and Improvements
AI has shown significant improvements in diagnostic accuracy and efficiency...

## Challenges and Limitations
Despite advances, AI faces challenges including data privacy and algorithmic bias...

## Conclusion
The integration of AI in healthcare presents both tremendous opportunities and significant challenges.""",
                "structure": [
                    "Introduction",
                    "Current AI Applications",
                    "Benefits and Improvements",
                    "Challenges and Limitations",
                    "Conclusion",
                ],
                "word_count": 850,
                "sources_cited": 6,
            },
        }

        # Mock publisher agent
        md_path = os.path.join(self.temp_dir, "ai_healthcare_report.md")
        pdf_path = os.path.join(self.temp_dir, "ai_healthcare_report.pdf")
        docx_path = os.path.join(self.temp_dir, "ai_healthcare_report.docx")

        # Create mock files
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(mock_writer.return_value["draft"]["content"])
        with open(pdf_path, "wb") as f:
            f.write(b"Mock PDF content")
        with open(docx_path, "wb") as f:
            f.write(b"Mock DOCX content")

        mock_publisher.return_value = {
            **mock_writer.return_value,
            "published_files": [md_path, pdf_path, docx_path],
            "publishing_status": "success",
        }

        # Mock translator agent
        mock_translator.return_value = {
            **mock_publisher.return_value,
            "translation_result": {
                "status": "success",
                "target_language": "vi",
                "language_name": "Vietnamese",
                "original_files": [md_path, pdf_path, docx_path],
                "translated_files": [
                    os.path.join(self.temp_dir, "ai_healthcare_report_vi.md"),
                    os.path.join(self.temp_dir, "ai_healthcare_report_vi.pdf"),
                    os.path.join(self.temp_dir, "ai_healthcare_report_vi.docx"),
                ],
            },
            "workflow_complete": True,
        }


class TestRealWorldScenarios:
    """Test realistic scenarios that might occur in production"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_large_content_translation(self):
        """Test translation of large content (realistic report size)"""

        # Create a large realistic report
        large_content = self._generate_large_report_content()

        translator = TranslatorAgent(output_dir=self.temp_dir)

        # Create mock markdown file
        md_path = os.path.join(self.temp_dir, "large_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(large_content)

        # Mock translation endpoint responses
        with patch.object(translator, "_translate_single_endpoint") as mock_endpoint:

            async def mock_translation_response(endpoint, payload):
                # Simulate realistic translation (slightly shorter than original)
                translated_content = f"# Báo Cáo Lớn\n\n{payload['transcript'][:1000]}... (đã dịch)"
                return {
                    "success": True,
                    "text": translated_content,
                    "length": len(translated_content),
                    "endpoint_name": endpoint["name"],
                }

            mock_endpoint.side_effect = mock_translation_response

            # Test translation
            result = await translator._translate_chunk_concurrent(
                large_content[:2000], "Vietnamese", "vi", {}  # Limit for test performance
            )

            assert result is not None
            assert "Báo Cáo Lớn" in result

    @pytest.mark.asyncio
    async def test_multiple_language_workflows(self):
        """Test workflows for different target languages"""

        languages_to_test = [
            ("vi", "Vietnamese"),
            ("fr", "French"),
            ("de", "German"),
            ("ja", "Japanese"),
            ("en", "English"),  # Should skip translation
        ]

        for lang_code, lang_name in languages_to_test:
            task = {
                "query": f"Test query for {lang_name}",
                "language": lang_code,
                "max_sections": 2,
                "publish_formats": ["md"],
            }

            orchestrator = ChiefEditorAgent(task=task)

            # Test translation decision
            research_state = {"task": task}
            should_translate = orchestrator._should_translate(research_state)

            if lang_code == "en":
                assert should_translate == "skip"
            else:
                assert should_translate == "translate"

    @pytest.mark.asyncio
    async def test_network_resilience(self):
        """Test system resilience to network issues during translation"""

        translator = TranslatorAgent()

        # Simulate various network conditions
        network_scenarios = [
            # All endpoints timeout
            lambda: asyncio.TimeoutError("Network timeout"),
            # Primary fails, backup succeeds
            lambda: {
                "success": True,
                "text": "Backup translation",
                "length": 100,
                "endpoint_name": "Backup",
            },
            # Intermittent failures
            lambda: {"success": True, "text": "Success after retry", "length": 100},
        ]

        for scenario in network_scenarios:
            with patch.object(translator, "_translate_single_endpoint") as mock_endpoint:
                if callable(scenario):
                    if "timeout" in str(scenario()):
                        mock_endpoint.side_effect = scenario()
                    else:
                        mock_endpoint.return_value = scenario()
                else:
                    mock_endpoint.return_value = scenario

                try:
                    result = await translator._translate_chunk_concurrent(
                        "Test content for network resilience", "Vietnamese", "vi", {}
                    )
                    # Should handle gracefully regardless of network issues
                    # Either succeed with backup or return None
                except Exception as e:
                    # Should not raise unhandled exceptions
                    pytest.fail(f"Unhandled exception during network failure: {e}")

    def test_file_system_edge_cases(self):
        """Test handling of file system edge cases"""

        translator = TranslatorAgent()

        # Test various file system scenarios
        test_cases = [
            # Non-existent directory
            ("/non/existent/path/file.md", "Should handle gracefully"),
            # Permission denied scenarios would need root/admin access to test properly
            # Files with special characters
            (os.path.join(self.temp_dir, "report_with_特殊字符.md"), "Should handle unicode"),
            # Very long file names (within OS limits)
            (os.path.join(self.temp_dir, "a" * 200 + ".md"), "Should handle long names"),
        ]

        for file_path, description in test_cases:
            if "non/existent" in file_path:
                # Test non-existent file handling
                format_files = translator._find_all_format_files(file_path)
                assert isinstance(format_files, dict)
            else:
                # Create test file and verify handling
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("Test content")

                format_files = translator._find_all_format_files(file_path)
                assert isinstance(format_files, dict)

    def _generate_large_report_content(self) -> str:
        """Generate a large realistic report for testing"""
        content = """# Comprehensive Analysis of Global Climate Change Impacts

## Executive Summary

This comprehensive analysis examines the multifaceted impacts of global climate change across various sectors including agriculture, healthcare, economic systems, and social structures. The report synthesizes findings from over 200 peer-reviewed studies published between 2020-2024.

## Introduction

Climate change represents one of the most pressing challenges of the 21st century. With global temperatures rising at unprecedented rates, the impacts are becoming increasingly visible across all aspects of human society and natural ecosystems.

### Background and Context

The scientific consensus on anthropogenic climate change has strengthened significantly over the past decade. Multiple lines of evidence point to human activities as the primary driver of current warming trends.

## Methodology

This analysis employed a systematic review approach, examining peer-reviewed literature from major scientific databases including PubMed, Web of Science, and Google Scholar. The search strategy focused on high-impact studies published in the last four years.

### Data Collection Procedures

A comprehensive search was conducted using specific keywords and Boolean operators to ensure thorough coverage of relevant literature. Studies were selected based on predefined inclusion and exclusion criteria.

## Climate Science Foundations

### Physical Climate System Changes

Global mean temperatures have increased by approximately 1.1°C since pre-industrial times, with the most rapid warming occurring in the past four decades. Arctic regions are experiencing warming at twice the global average rate.

### Atmospheric Composition Changes

Carbon dioxide concentrations have reached levels not seen in over 3 million years, currently exceeding 420 parts per million. Other greenhouse gases including methane and nitrous oxide are also increasing.

## Sectoral Impact Analysis

### Agricultural Systems

Climate change is significantly affecting global food security through altered precipitation patterns, increased frequency of extreme weather events, and shifting growing seasons.

#### Crop Yield Impacts

Studies indicate that major staple crops are experiencing yield declines in many regions. Wheat production has been particularly affected, with some regions seeing decreases of up to 15% compared to baseline projections.

#### Livestock and Dairy Production

Heat stress in livestock is reducing productivity and reproductive success rates. Dairy cattle are particularly vulnerable, with milk production declining in regions experiencing frequent heat waves.

### Water Resources

Changing precipitation patterns and increased evaporation rates are affecting freshwater availability across many regions. Some areas are experiencing more frequent and severe droughts, while others face increased flooding risks.

#### Groundwater Depletion

Increased demand for irrigation water combined with reduced recharge rates is leading to groundwater depletion in many agricultural regions.

#### Water Quality Issues

Rising temperatures are contributing to water quality deterioration through increased algal blooms and reduced oxygen levels in aquatic systems.

### Human Health Impacts

Climate change is affecting human health through multiple pathways including heat-related illness, vector-borne diseases, and food and water security issues.

#### Heat-Related Mortality

Extreme heat events are becoming more frequent and intense, leading to increased mortality rates, particularly among vulnerable populations including the elderly and those with pre-existing health conditions.

#### Vector-Borne Disease Expansion

Warmer temperatures and altered precipitation patterns are expanding the geographic range of disease vectors, potentially increasing the incidence of diseases such as malaria, dengue fever, and Lyme disease.

### Economic Implications

The economic costs of climate change are substantial and growing. Direct costs include damage from extreme weather events, while indirect costs include reduced productivity and increased adaptation expenses.

#### Infrastructure Damage

Extreme weather events are causing increasing damage to transportation, energy, and communication infrastructure. Coastal areas are particularly vulnerable to sea level rise and storm surge.

#### Insurance Industry Impacts

The insurance industry is experiencing significant losses from climate-related disasters, leading to increased premiums and reduced coverage availability in high-risk areas.

## Regional Analysis

### North America

North America is experiencing significant impacts from climate change, including increased wildfire activity, changing precipitation patterns, and more frequent extreme weather events.

### Europe

European regions are seeing earlier spring seasons, increased heat waves, and changing precipitation patterns that are affecting agriculture and water resources.

### Asia

Asia, home to the majority of the world's population, is experiencing diverse climate impacts including monsoon changes, glacier retreat, and increased typhoon intensity.

### Africa

African nations are particularly vulnerable to climate change impacts due to limited adaptive capacity and high dependence on climate-sensitive sectors such as agriculture.

### Small Island States

Small island developing states face existential threats from sea level rise and increased storm intensity, with some facing potential uninhabitability within decades.

## Adaptation and Mitigation Strategies

### Technology Solutions

Technological innovations are providing new options for both adaptation and mitigation, including renewable energy systems, climate-resilient crops, and advanced monitoring systems.

### Policy Approaches

Government policies at local, national, and international levels are crucial for effective climate action. Carbon pricing mechanisms and renewable energy incentives are among the tools being deployed.

### Community-Based Approaches

Local communities are developing innovative adaptation strategies based on traditional knowledge combined with modern scientific understanding.

## Future Projections

### Climate Model Scenarios

Current climate models project continued warming under all emission scenarios, with the magnitude depending on future greenhouse gas emissions and policy responses.

### Socioeconomic Implications

Future socioeconomic impacts will depend heavily on adaptation measures implemented today and the effectiveness of global mitigation efforts.

## Conclusions and Recommendations

The evidence clearly demonstrates that climate change is already having significant impacts across multiple sectors and regions. Urgent action is needed to both reduce emissions and adapt to unavoidable changes.

### Key Findings

1. Climate impacts are accelerating and becoming more severe
2. Vulnerable populations are disproportionately affected
3. Economic costs are substantial and growing
4. Immediate action is required to limit future risks

### Policy Recommendations

1. Implement ambitious emission reduction targets
2. Invest in adaptation infrastructure
3. Support vulnerable communities
4. Enhance international cooperation

## References and Sources

This analysis is based on comprehensive review of over 200 peer-reviewed studies and reports from leading scientific institutions and international organizations."""

        return content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
