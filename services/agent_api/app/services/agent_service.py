class AgentService:
    def __init__(self, llm, mcp, cart):
        self.llm = llm
        self.mcp = mcp
        self.cart = cart

    async def process_message(self, user_id: str, text: str) -> dict:
        products = await self.mcp.search_products(text)
        action = await self.llm.extract_action(text, products)
        cart_id = await self.cart.create_cart(user_id)
        result = await self.cart.add_item(cart_id, action["arguments"])
        return {
            "reply": f"Добавил {action['arguments']['title']} в корзину. Итого: {result['total_amount']} ₽",
            "actions": [action],
        }
