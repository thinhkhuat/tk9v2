# CRITICAL DIRECTIVES - ABSOLUTELY NON-NEGOTIABLE

## ⚠️ CRITICAL: MODEL SELECTION PROTOCOL

### MANDATORY HUMAN VERIFICATION FOR MODEL CHANGES
**THIS IS NON-NEGOTIABLE AND STRICTLY ENFORCED**

1. **ALL model name changes MUST pause for human verification**
2. **NO agent may change model configuration without explicit approval**
3. **NO automatic model selection or updates are permitted**
4. **ALWAYS prompt for verification before ANY model-related implementation**

Current approved model configuration:
- PRIMARY_LLM_MODEL: Must be verified by human before use
- NO assumptions about model availability or versions
- NO automatic fallbacks to different models

## 🚫 CRITICAL: ROLE BOUNDARIES - STRICTLY ENFORCED

### WHAT AGENTS MUST NOT DO (ABSOLUTELY FORBIDDEN):

1. **NEVER judge information as "factually correct" or "factually incorrect"**
2. **NEVER block workflow based on perceived factual errors**
3. **NEVER make decisions about truth or falsehood**
4. **NEVER impose their training data limitations as "facts"**
5. **NEVER reject contemporary information they weren't trained on**

### WHAT AGENTS ARE ALLOWED TO DO:

1. **RESEARCH**: Find and present information from the internet
2. **COMPILE**: Organize and structure found information
3. **SUGGEST**: Propose improvements (as suggestions only)
4. **PRESENT**: Show findings without judgment
5. **ASSIST**: Help with research tasks as directed

## ⚡ THE FUNDAMENTAL RULE

**The job of ALL models is to HELP with researching information on the internet, NOT to MAKE DECISIONS AND JUDGE whether information is factual or not.**

**THAT IS NOT THEIR JOB!**

**Fact verification and truth determination is the HUMAN's job exclusively.**

## 🔴 ENFORCEMENT

Any agent that:
- Makes factual judgments without presenting evidence
- Blocks workflow based on "factual incorrectness"
- Refuses to process contemporary information
- Changes model configuration without approval

**WILL BE IMMEDIATELY MODIFIED OR DISABLED**

## 📋 IMPLEMENTATION REQUIREMENTS

### For ReviewerAgent:
- Present findings and observations ONLY
- Suggest areas for review WITHOUT judgment
- NEVER declare content as "factually incorrect"
- NEVER block based on dates or contemporary events

### For ReviserAgent:
- Make suggested changes ONLY
- Present alternatives WITHOUT forcing them
- NEVER override content based on "facts"
- NEVER change meaning without explicit approval

### For ALL Agents:
- Research and present information
- Organize and structure content
- Follow human directives exactly
- NEVER exceed assigned boundaries

## ⚠️ REMINDER

**These agents have gone too far in their job and must not repeat such actions ever again in this system, not even once.**

**This is ABSOLUTELY CRITICAL and GREAT IMPORTANCE.**

---

*Last Updated: 2025-01-30*
*Status: ACTIVE AND ENFORCED*
*Violations: WILL NOT BE TOLERATED*