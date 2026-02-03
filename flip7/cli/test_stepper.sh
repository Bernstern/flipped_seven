#!/bin/bash
# Quick test of the round stepper
# This simulates pressing Enter 20 times to step through several turns

echo "Testing round stepper with RandomBot vs ConservativeBot..."
echo ""

# Generate 20 newlines and pipe to the stepper
yes "" | head -20 | uv run python step_round.py --seed 42
