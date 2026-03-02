import httpx


class CartApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def create_cart(self, user_id: str) -> int:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/carts", json={"user_external_id": user_id}
            )
            resp.raise_for_status()
            return resp.json()["cart_id"]

    async def add_item(self, cart_id: int, item: dict) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/carts/{cart_id}/items", json=item
            )
            resp.raise_for_status()
            return resp.json()

    async def get_latest_cart(self, user_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/carts/by-user/{user_id}/latest"
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def ensure_cart(self, user_id: str) -> int:
        latest = await self.get_latest_cart(user_id)
        if latest and "cart_id" in latest:
            return int(latest["cart_id"])
        return await self.create_cart(user_id)

    async def clear_cart(self, cart_id: int) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(f"{self.base_url}/api/v1/carts/{cart_id}/items")
            resp.raise_for_status()
            return resp.json()
