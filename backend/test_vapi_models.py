import sys
from pathlib import Path

backend_dir = r"c:\Users\muham\My Portfolio Projects\voice agent\backend"
sys.path.insert(0, backend_dir)

from app.models.schemas import VapiAction, VapiToolResponse
from app.api.routes.vapi_tools import _vapi_action, _to_vapi_result

row = {
    "product_id": "12345",
    "title": "Arsenal Jersey",
    "price": 90,
    "images": ["url1"]
}

result = _vapi_action("trace123", "open_product", row, "Opening Arsenal Jersey.")
vapi_dict = _to_vapi_result("tool_call_1", result)

print("VAPI DICT:", vapi_dict)
