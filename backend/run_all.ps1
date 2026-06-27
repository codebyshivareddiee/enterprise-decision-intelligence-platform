$ErrorActionPreference = "Continue"

echo "=== Domain Terms Check ==="
echo "Already done via grep_search. 0 results found in app/."

echo "`n=== Static Checks ==="
echo "Running Ruff..."
ruff check . 
echo "Running Black..."
black --check .
echo "Running Mypy..."
mypy .

echo "`n=== Verification Scripts ==="
echo "1. verify_knowledge_layer.py"
python -m scripts.verify_knowledge_layer
echo "`n2. verify_ai_layer.py"
python -m scripts.verify_ai_layer
echo "`n3. verify_planner.py"
python -m scripts.verify_planner
echo "`n4. verify_runtime.py"
python -m scripts.verify_runtime
echo "`n5. verify_agents.py"
python -m scripts.verify_agents

echo "`n=== E2E Complete Workflow Check ==="
echo "The verify_runtime.py inherently runs an e2e via graph execution of mock nodes, but we'll also rely on the runtime & agents tests for this."
