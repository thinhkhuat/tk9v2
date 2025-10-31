# Fact-Checking and Research Validation Reference

## Overview

The Deep Research MCP system implements multiple layers of fact-checking and validation to ensure research accuracy and reliability. This document outlines the validation mechanisms, fact-checking strategies, and quality assurance processes.

## Validation Layers

### 1. Source Validation
**Agent**: BrowserAgent  
**Process**: Initial source quality assessment

**Validation Criteria**:
- Domain authority and reputation
- Publication date and recency
- Author credentials
- Citation presence
- HTTPS security
- Content consistency

**Implementation**:
```python
def validate_source(url, content):
    checks = {
        "domain_reputation": check_domain_authority(url),
        "ssl_certificate": verify_https(url),
        "content_length": len(content) > MIN_CONTENT_LENGTH,
        "publication_date": extract_and_validate_date(content),
        "author_present": detect_author_information(content)
    }
    return all(checks.values())
```

### 2. Information Cross-Verification
**Agent**: ResearcherAgent  
**Process**: Multi-source fact verification

**Verification Strategy**:
- Minimum 2-3 sources per fact
- Cross-reference statistics and data
- Identify conflicting information
- Weight sources by credibility

**Conflict Resolution**:
```python
def resolve_conflicts(facts):
    # Group facts by similarity
    fact_clusters = cluster_similar_facts(facts)
    
    # Weight by source credibility
    for cluster in fact_clusters:
        weighted_facts = []
        for fact in cluster:
            weight = calculate_source_weight(fact.source)
            weighted_facts.append((fact, weight))
        
        # Select fact with highest credibility
        return max(weighted_facts, key=lambda x: x[1])[0]
```

### 3. Citation Verification
**Agent**: WriterAgent  
**Process**: Reference and citation validation

**Citation Checks**:
- URL accessibility
- Reference formatting
- Publication details
- DOI validation
- Archive.org fallback

### 4. Statistical Validation
**Agent**: ReviewerAgent  
**Process**: Data and statistics verification

**Validation Methods**:
- Range checking (reasonable bounds)
- Consistency checking
- Trend analysis
- Outlier detection

## Fact-Checking Strategies

### Multi-Provider Verification
```python
async def verify_fact_across_providers(fact, providers):
    results = []
    for provider in providers:
        verification = await provider.search_and_verify(fact)
        results.append(verification)
    
    # Consensus scoring
    consensus_score = calculate_consensus(results)
    return consensus_score > CONSENSUS_THRESHOLD
```

### Temporal Validation
```python
def validate_temporal_claims(claim):
    # Extract temporal references
    dates = extract_dates(claim)
    
    # Verify chronological consistency
    if not verify_chronology(dates):
        return False
    
    # Check against known timelines
    return verify_against_timeline(claim, dates)
```

### Numerical Validation
```python
def validate_statistics(stat):
    checks = {
        "range": is_within_reasonable_range(stat.value),
        "precision": check_precision_claims(stat),
        "source": verify_statistical_source(stat.source),
        "methodology": validate_methodology(stat)
    }
    return CheckResult(checks)
```

## Quality Scoring System

### Research Quality Metrics
```python
class QualityScorer:
    def calculate_quality_score(self, research_data):
        scores = {
            "source_diversity": self.score_source_diversity(research_data.sources),
            "citation_quality": self.score_citations(research_data.citations),
            "fact_verification": self.score_fact_verification(research_data.facts),
            "recency": self.score_information_recency(research_data.dates),
            "completeness": self.score_completeness(research_data.sections)
        }
        
        # Weighted average
        weights = {
            "source_diversity": 0.2,
            "citation_quality": 0.25,
            "fact_verification": 0.3,
            "recency": 0.15,
            "completeness": 0.1
        }
        
        return sum(scores[k] * weights[k] for k in scores)
```

### Confidence Levels
| Score Range | Confidence Level | Action |
|------------|------------------|--------|
| 0.9 - 1.0 | Very High | Proceed with publication |
| 0.75 - 0.89 | High | Minor review recommended |
| 0.6 - 0.74 | Medium | Additional verification needed |
| 0.4 - 0.59 | Low | Significant gaps, more research required |
| < 0.4 | Very Low | Restart research with better sources |

## Automated Fact-Checking Tools

### 1. Claim Detection
```python
class ClaimDetector:
    def detect_claims(self, text):
        claims = []
        
        # Statistical claims
        claims.extend(self.find_statistical_claims(text))
        
        # Factual assertions
        claims.extend(self.find_factual_assertions(text))
        
        # Causal claims
        claims.extend(self.find_causal_claims(text))
        
        return claims
```

### 2. Source Tracking
```python
class SourceTracker:
    def __init__(self):
        self.sources = {}
        self.citations = {}
    
    def track_source(self, fact, source):
        fact_id = generate_fact_id(fact)
        if fact_id not in self.sources:
            self.sources[fact_id] = []
        self.sources[fact_id].append(source)
    
    def get_source_count(self, fact):
        fact_id = generate_fact_id(fact)
        return len(self.sources.get(fact_id, []))
```

### 3. Bias Detection
```python
class BiasDetector:
    def detect_bias(self, text, sources):
        bias_indicators = {
            "source_political_lean": self.check_political_bias(sources),
            "language_sentiment": self.analyze_sentiment(text),
            "cherry_picking": self.detect_cherry_picking(text, sources),
            "false_balance": self.detect_false_balance(text)
        }
        return BiasReport(bias_indicators)
```

## Research Guidelines Enforcement

### Guideline Validation
```python
def validate_guidelines(research_data, guidelines):
    violations = []
    
    for guideline in guidelines:
        if "recent" in guideline.lower():
            if not check_recency(research_data):
                violations.append("Outdated sources used")
        
        if "peer-reviewed" in guideline.lower():
            if not check_peer_review(research_data.sources):
                violations.append("Non-peer-reviewed sources")
        
        if "primary sources" in guideline.lower():
            if not check_primary_sources(research_data.sources):
                violations.append("Over-reliance on secondary sources")
    
    return violations
```

## Error Detection and Correction

### Common Error Patterns
1. **Outdated Information**: Facts that have been superseded
2. **Misattributed Quotes**: Incorrect source attribution
3. **Statistical Errors**: Calculation or interpretation errors
4. **Logical Fallacies**: Reasoning errors
5. **Context Stripping**: Facts taken out of context

### Automated Correction
```python
class ErrorCorrector:
    def auto_correct(self, research_data):
        corrections = []
        
        # Update outdated facts
        for fact in research_data.facts:
            if self.is_outdated(fact):
                updated_fact = self.find_updated_version(fact)
                corrections.append((fact, updated_fact))
        
        # Fix statistical errors
        for stat in research_data.statistics:
            if error := self.detect_statistical_error(stat):
                corrected_stat = self.correct_statistic(stat, error)
                corrections.append((stat, corrected_stat))
        
        return corrections
```

## Manual Review Integration

### Human-in-the-Loop Validation
```python
class HumanReviewer:
    async def request_human_validation(self, content, concerns):
        review_request = {
            "content": content,
            "concerns": concerns,
            "specific_questions": self.generate_questions(concerns),
            "suggested_corrections": self.suggest_corrections(content)
        }
        
        human_feedback = await self.get_human_feedback(review_request)
        return self.process_feedback(human_feedback)
```

## Validation Reporting

### Validation Report Structure
```json
{
    "overall_confidence": 0.85,
    "fact_verification": {
        "verified_facts": 45,
        "unverified_facts": 5,
        "conflicting_facts": 2
    },
    "source_quality": {
        "high_quality": 15,
        "medium_quality": 8,
        "low_quality": 2
    },
    "citations": {
        "valid": 48,
        "broken": 2,
        "unverifiable": 1
    },
    "potential_issues": [
        {
            "type": "outdated_statistic",
            "location": "Section 2.3",
            "severity": "medium",
            "suggestion": "Update with 2024 data"
        }
    ]
}
```

## Best Practices

### For High-Quality Research
1. **Diversify Sources**: Use multiple independent sources
2. **Verify Statistics**: Cross-check all numerical claims
3. **Check Dates**: Ensure information is current
4. **Validate Experts**: Verify credentials of cited experts
5. **Document Uncertainty**: Note areas of disagreement

### For Fact-Checking
1. **Primary Sources First**: Prefer original sources
2. **Multiple Confirmation**: Require 2-3 sources minimum
3. **Context Preservation**: Maintain original context
4. **Transparency**: Document verification process
5. **Update Regularly**: Refresh facts periodically

## Configuration Options

### Fact-Checking Settings
```bash
# Environment variables
FACT_CHECK_ENABLED=true
MIN_SOURCES_PER_FACT=2
REQUIRE_PRIMARY_SOURCES=true
CONSENSUS_THRESHOLD=0.7
QUALITY_SCORE_MINIMUM=0.75

# task.json configuration
{
    "fact_checking": {
        "enabled": true,
        "strict_mode": false,
        "min_source_quality": "medium",
        "require_citations": true,
        "verify_statistics": true
    }
}
```

## Debugging Fact-Checking

### Validation Logs
```bash
# Enable detailed validation logging
export VALIDATION_DEBUG=true

# Check validation report
cat outputs/latest/validation_report.json

# View fact-checking details
grep "VALIDATION" workflow.log
```

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Low confidence scores | Poor source quality | Use better search providers |
| Conflicting facts | Source disagreement | Increase consensus threshold |
| Broken citations | URL changes | Enable archive.org fallback |
| Outdated information | Old sources | Set recency requirements |
| Bias detection triggers | Single viewpoint | Diversify source selection |

## Future Enhancements

### Planned Features
- Real-time fact-checking APIs integration
- Machine learning for claim detection
- Automated bias correction
- Blockchain-based fact verification
- Community-driven fact validation
- Knowledge graph integration
- Semantic similarity for fact matching