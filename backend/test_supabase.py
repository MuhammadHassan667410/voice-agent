import sys
import asyncio
from typing import Any
sys.path.insert(0, r"c:\Users\muham\My Portfolio Projects\voice agent\backend")

from app.services.supabase_service import SupabaseService
from app.core.config import get_settings

settings = get_settings()
supabase = SupabaseService(settings)

product_id = "gid://shopify/Product/9194007888090"
row = supabase.get_product_by_id(product_id)

print(f"Row for {product_id} is:", "FOUND" if row else "NOT FOUND")
if row:
    print(row.keys())
