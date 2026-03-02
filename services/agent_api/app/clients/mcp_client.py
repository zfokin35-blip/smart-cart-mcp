class MCPRetailClient:
    async def search_products(self, query: str) -> list[dict]:
        return [
            {"id": "vv-001", "title": "Молоко 3.2%", "price": 129.9},
            {"id": "vv-002", "title": "Хлеб цельнозерновой", "price": 79.0},
        ]
