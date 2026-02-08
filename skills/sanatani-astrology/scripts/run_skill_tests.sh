#!/bin/bash
set -e

# Output file for golden results
OUTPUT_FILE="tests/skill_test_results.json"
echo "[" > "$OUTPUT_FILE"

run_test() {
    local NAME="$1"
    local PROMPT="$2"
    local EXPECTED_KEY="$3"
    
    echo "Running Test: $NAME"
    echo "Prompt: $PROMPT"
    
    # Run agent command and capture JSON output
    # Using --json to get structured response
    # Redirect stderr to stdout to capture fallback messages if any, though ideally separate
    RESPONSE=$(openclaw agent --agent main --message "$PROMPT" --json 2>&1)
    
    # Extract relevant data (simplified for now, just storing full response)
    # Ideally we'd parse this, but for golden generation we just save it.
    
    # Add to output array (handling comma correctly)
    if [ "$NAME" != "Panchang" ]; then
        echo "," >> "$OUTPUT_FILE"
    fi
    
    # Create a JSON object for this test result
    # We escape double quotes in response for embedding in JSON
    # This is a bit hacky in bash, but sufficient for test generation
    CLEAN_RESPONSE=$(echo "$RESPONSE" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
    
    cat <<EOF >> "$OUTPUT_FILE"
    {
        "test_name": "$NAME",
        "prompt": "$PROMPT",
        "expected_key": "$EXPECTED_KEY",
        "response": $CLEAN_RESPONSE
    }
EOF
}

# 1. Panchang Test
run_test "Panchang" \
    "Calculate Panchang for 2026-02-07 in Mumbai, India using sanatani-astrology. Return json." \
    "tithi"

# 2. Geocoding Test
run_test "Geocoding" \
    "What are the coordinates for Ayodhya? Use sanatani-astrology." \
    "latitude"

# 3. Chart Test
# Providing full details to ensure tool usage
run_test "Chart" \
    "Generate Vedic chart for User (1990-01-01 12:00 in Delhi). Use sanatani-astrology." \
    "planetary_positions"

# 4. Matchmaking Test
run_test "Matchmaking" \
    "Check compatibility between Person A (1990-01-01 12:00 Delhi) and Person B (1992-02-02 14:00 Mumbai). Use sanatani-astrology." \
    "total_points"

# 5. General/Skill Info
run_test "Skill_Info" \
    "How do I use the sanatani-astrology skill?" \
    "usage"

echo "]" >> "$OUTPUT_FILE"
echo "Tests completed. Results saved to $OUTPUT_FILE"
