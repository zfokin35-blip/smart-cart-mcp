class AgentService:
    def __init__(self, llm, mcp, cart):
        self.llm = llm
        self.mcp = mcp
        self.cart = cart

    async def process_message(self, user_id: str, text: str) -> dict:
        user_text = (text or "").strip()
        if not user_text:
            return {"reply": "Напиши, что добавить в корзину 🙂", "actions": []}

        # 1) Поиск товаров в ВкусВилл (MCP)
        products = await self.mcp.search_products(user_text)

        if not products:
            return {
                "reply": "Ничего не нашёл по запросу. Попробуй уточнить (например: «молоко 1л»).",
                "actions": [],
            }

        # 2) LLM выбирает товар из каталога (или fallback)
        action = await self.llm.extract_action(user_text, products)

        # 3) Корзина НЕ создается каждый раз: берём latest или создаём при отсутствии
        cart_id = await self.cart.ensure_cart(user_id)

        # 4) Добавляем товар
        result = await self.cart.add_item(cart_id, action["arguments"])

        return {
            "reply": f"Добавил: {action['arguments']['title']} x{action['arguments']['qty']}. Итого: {result['total_amount']} ₽",
            "actions": [action],
        }
