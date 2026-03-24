import sys
import asyncio
sys.path.insert(0, r"c:\Users\muham\My Portfolio Projects\voice agent\backend")

from app.services.supabase_service import SupabaseService
from app.core.config import get_settings

async def main():
    settings = get_settings()
    supabase = SupabaseService(settings)
    
    # 1. Check current prices
    response = supabase.client.table("products").select("title, price").execute()
    for row in response.data:
        print(f"Product: {row['title']}, Price in DB: {row['price']}")
        
    # 2. Fix the socks!
    print("Fixing the anomalous prices in the DB...")
    supabase.client.table("products").update({"price": 11.00}).eq("title", "Nike Squad Crew Soccer Socks").execute()
    supabase.client.table("products").update({"price": 91.00}).eq("title", "Macron Official Referee Jersey").execute()
    supabase.client.table("products").update({"price": 16.00}).eq("title", "Puma TeamGoal 23 Gymsack").execute()
    
    print("Done. All anomalies squashed.")

if __name__ == "__main__":
    asyncio.run(main())
