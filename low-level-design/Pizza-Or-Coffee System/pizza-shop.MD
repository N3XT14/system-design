Create a pizza with customizable toppings — implemented in Pizza with add_topping.
    - Add pizza to an order — implemented in Order.add_pizza.
    - Process payments (cash or card) — implemented with Order.process_payment.
    - Serve multiple orders at once — multiple Order can exist; each is independent.
    - Optionally apply promotions or discount codes — implemented with PromotionStrategy.
    - Customer Notifier

Factory Method: To create different pizza varieties.
Composite: Toppings can be added to pizza.
Strategy: Payment methods or promotions.
Singleton: The PizzaShop instance.
Observer (Optionally): To notify when the order is ready.
