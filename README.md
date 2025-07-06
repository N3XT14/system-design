## Requirements

1. User should be able to add products to their wishlist.
2. User should be notified when price drops either to their specified price or due to a promotion.

# Core Classes

1. User
    - Stores the user's id, email, and their wishlist.

2. Product
    - Stores productId, current price, and promotions.

3. Wishlist
    - Stores (ProductId, DesiredDropPrice) per User.

4. PriceFetcher/Tracker
    - Allows adding a price drop event for a product by a user.
    - Notifies when drops happen (this might be a callback or notification service).

5. NotificationService
    - Mock service to notify users (SMS, Email, Push).