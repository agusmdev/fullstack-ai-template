#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations> [model]"
  echo "  model: sonnet or opus (default: opus)"
  exit 1
fi

MODEL="${2:-opus}"
if [ "$MODEL" != "sonnet" ] && [ "$MODEL" != "opus" ]; then
  echo "Error: model must be 'sonnet' or 'opus'"
  exit 1
fi

for ((i=1; i<=$1; i++)); do
  echo ""
  echo "========================================"
  echo "  ITERATION $i"
  echo "========================================"
  echo ""

  # Run ccv which handles all output formatting
  ANTHROPIC_AUTH_TOKEN=${ZAI_API_KEY} ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic API_TIMEOUT_MS=3000000 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 ccv --model "$MODEL" --dangerously-skip-permissions -p \
    "use the swarm-orchestration skill and then Use bd (beads) to find and work on a task:
1. Run 'bd ready' to find an available task
2. If no tasks available, output <no-tasks/> and stop
3. Claim the task with 'bd update <id> --status in_progress'
4. Implement the task according to its acceptance criteria
5. Make a git commit with your changes
6. Close the task with 'bd close <id>'
ONLY WORK ON A SINGLE TASK."
done

echo ""
echo "========================================"
echo "  All $1 iterations completed"
echo "========================================"
