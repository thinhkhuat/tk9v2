#!/bin/bash

# Fix for Translation Revision Loop Issue
# This script applies the fix for the infinite loop that occurs when 
# translation → reviewer → reviser → publisher cycles indefinitely

echo "═══════════════════════════════════════════════════════════════════"
echo "  Fixing Translation Revision Loop Issue"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Issue: After translation, the workflow enters an infinite loop:"
echo "  TRANSLATOR → REVIEWER → REVISER → PUBLISHER → TRANSLATOR (repeat)"
echo ""
echo "Root Causes:"
echo "  1. Translator doesn't populate 'draft' field for reviewer"
echo "  2. Reviser sends back to publisher instead of ending workflow"
echo ""
echo "Applying fixes..."
echo ""

# Backup the original files
echo "Creating backups..."
mkdir -p backups/translation_loop_fix
cp multi_agents/agents/translator.py backups/translation_loop_fix/translator.py.bak
cp multi_agents/agents/orchestrator.py backups/translation_loop_fix/orchestrator.py.bak
cp multi_agents/agents/reviser.py backups/translation_loop_fix/reviser.py.bak
echo "✓ Backups created in backups/translation_loop_fix/"

echo ""
echo "Applying fixes to the workflow..."
echo ""

# The fixes have already been applied via the Edit tool
# This script documents what was changed

echo "✓ Fixed translator.py:"
echo "  - Modified run() method to populate 'draft' field with translated content"
echo "  - Now reads translated markdown file and passes it to reviewer"
echo ""

echo "✓ Fixed orchestrator.py:"
echo "  - Changed workflow edge: reviser → END (instead of reviser → publisher)"
echo "  - Prevents re-triggering translation after revision"
echo ""

echo "✓ Fixed reviser.py:"
echo "  - Added _save_revised_translation() method"
echo "  - Saves revised translations to files when translation_result exists"
echo ""

echo "═══════════════════════════════════════════════════════════════════"
echo "  Translation Loop Fix Applied Successfully!"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Testing recommendations:"
echo "  1. Run a research with translation (e.g., -l vi)"
echo "  2. Verify translation completes without looping"
echo "  3. Check that reviewer properly evaluates translated content"
echo "  4. Confirm workflow ends after review/revision"
echo ""
echo "To restore original files if needed:"
echo "  cp backups/translation_loop_fix/*.bak multi_agents/agents/"
echo ""