"""Run tests fresh — no cache interference."""
import sys
sys.path.insert(0, "/data/LLM-Apps/advanced-ai-agents/saferide")

# Force fresh reload
if "saferide" in sys.modules:
    del sys.modules["saferide"]

from saferide.models import VehicleCheck, Recall

# Test 1: Can we create with source?
v = VehicleCheck(vin="TEST", make="Toyota", model="Camry", year=2024, source="live")
print(f"Test 1 PASS: VehicleCheck with source=live: status={v.status}, source={v.source}")

# Test 2: Can we create without recalls?
v2 = VehicleCheck(vin=None, make="Honda", model="Civic", year=2023, status="clear", message="OK", source="live")
print(f"Test 2 PASS: VehicleCheck clear: source={v2.source}")

# Test 3: Recall with source
r = Recall(nhtsa_id="X", component="Test", summary="Test", consequence="", remedy="", safety_risk="low", report_date="", source="simulated")
print(f"Test 3 PASS: Recall with source: source={r.source}")

print("All basic model tests PASSED")