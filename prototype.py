"""Repository convenience entrypoint; reusable implementation lives in the skill."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "skills/investment-hypothesis-verification/scripts/verify.py"
spec = importlib.util.spec_from_file_location("investment_verification", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if __name__ == "__main__":
    module.main()
