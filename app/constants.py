class OrderStatus:
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"


class PaymentStatus:
    SENDER_PAY = "SENDER_PAY"
    RECEIVER_PAY = "RECEIVER_PAY"
    PREPAID = "PREPAID"
    COD = "COD"


class ShippingStatus:
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"


class PaymentMethod:
    COD = "COD"
    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"
    PAYPAL = "PAYPAL"

    @classmethod
    def get_all(cls) -> list[dict[str, str]]:
        """Return all payment methods as list of dicts with id and name."""
        return [
            {"id": cls.COD, "name": "Cash on Delivery"},
            {"id": cls.BANK_TRANSFER, "name": "Bank Transfer"},
            {"id": cls.CREDIT_CARD, "name": "Credit Card"},
            {"id": cls.PAYPAL, "name": "PayPal"},
        ]
