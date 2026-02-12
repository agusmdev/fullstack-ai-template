#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations> [model]"
  echo "  model: opencode model (default: zai-coding-plan/glm-4.7)"
  exit 1
fi

MODEL="${2:-zai-coding-plan/glm-4.7}"

for ((i=1; i<=$1; i++)); do
  echo ""
  echo "========================================"
  echo "  ITERATION $i"
  echo "========================================"
  echo ""

  opencode -m "$MODEL" run "Analyze the codebase to find and fix bad practices or improvements:

1. LAUNCH MULTIPLE PARALLEL BACKGROUND AGENTS (explore, librarian) to thoroughly analyze the codebase:
   - Code patterns and structure (explore)
   - Best practices from official docs and examples (librarian)
   - Bad practices, code smells, anti-patterns
   - Security vulnerabilities
   - Performance issues
   - Testing gaps
   - Documentation inconsistencies
   - You can also check on ./inspiration-repo/backend/ for examples for some good ideas.

2. BE EXHAUSTIVE - don't stop at first result. Search deeply across the entire codebase.

3. After gathering comprehensive analysis, PRIORITIZE findings by:
   - Severity (critical > high > medium > low)
   - Impact (affects many files vs isolated)
   - Effort to fix

4. SELECT THE SINGLE HIGHEST PRIORITY issue and:
   - Implement the fix following best practices
   - Ensure all diagnostics pass
   - Run any relevant tests
   - Create a descriptive git commit

5. Output a summary of what was fixed.

ONLY WORK ON ONE ISSUE PER ITERATION. Focus on quality over quantity.
YOU absolutely MUST commit the changes to the codebase after each iteration."
done

echo ""
echo "========================================"
echo "  All $1 iterations completed"
echo "========================================"
