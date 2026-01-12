"""
합성 테스트 데이터 생성기

프라이버시 보존 원칙:
- 실제 개인정보(이름, 전화번호, 이메일)를 사용하지 않음
- Faker 라이브러리를 사용하여 완전히 가짜 데이터 생성
- 프로덕션 데이터와 유사하지 않은 패턴 사용
- 테스트용으로만 사용 가능한 명확한 식별자 사용
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from faker import Faker

from app.schemas import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    Customer,
    OrderItemCreate,
    Pricing,
    Address,
    Shipper,
    Shipping,
    OrderCreate,
    OrderUpdate,
    OrderOut,
    OrderItemOut,
    ExternalStatusUpdate,
)

fake = Faker()
fake.seed_instance(42)  # 재현 가능한 데이터를 위한 시드 설정


class TestDataFactory:
    """합성 테스트 데이터 생성 팩토리 클래스"""

    @staticmethod
    def generate_product_id() -> str:
        """제품 ID 생성 (프로덕션과 구분되는 형식)"""
        return f"TEST-PROD-{fake.lexify(text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"

    @staticmethod
    def generate_order_code() -> str:
        """주문 코드 생성 (프로덕션과 구분되는 형식)"""
        timestamp = fake.numerify(text="########")
        suffix = fake.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        return f"TEST-ORD-{timestamp}-{suffix}"

    @staticmethod
    def generate_customer_name() -> str:
        """고객 이름 생성 (프로덕션과 구분되는 형식)"""
        return f"TestUser_{fake.lexify(text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"

    @staticmethod
    def generate_phone() -> str:
        """전화번호 생성 (프로덕션과 구분되는 형식)"""
        # 테스트용 명확한 패턴: 9로 시작하는 가짜 번호
        return f"9{fake.numerify(text='#########')}"

    @staticmethod
    def generate_email() -> str:
        """이메일 생성 (프로덕션과 구분되는 형식)"""
        username = fake.lexify(text='testuser_????', letters='abcdefghijklmnopqrstuvwxyz0123456789')
        return f"{username}@testdata.example"

    @staticmethod
    def generate_address() -> str:
        """주소 생성 (프로덕션과 구분되는 형식)"""
        city = fake.city()
        street = fake.street_address()
        return f"Test Address: {street}, {city}"

    @staticmethod
    def create_product(
        product_id: Optional[str] = None,
        name: Optional[str] = None,
        price: Optional[float] = None,
        stock: Optional[int] = None,
    ) -> ProductCreate:
        """제품 생성 스키마 생성"""
        return ProductCreate(
            name=name or f"Test Product {fake.word().capitalize()}",
            description=fake.text(max_nb_chars=200),
            price=price or round(fake.pyfloat(left_digits=3, right_digits=0, positive=True), 2),
            currency="VND",
            stock=stock if stock is not None else fake.pyint(min_value=0, max_value=1000),
            status=fake.random_element(elements=("ACTIVE", "INACTIVE")),
        )

    @staticmethod
    def create_product_out(
        product_id: Optional[str] = None,
        name: Optional[str] = None,
        price: Optional[float] = None,
    ) -> dict:
        """제품 출력 스키마용 딕셔너리 생성"""
        return {
            "id": product_id or TestDataFactory.generate_product_id(),
            "name": name or f"Test Product {fake.word().capitalize()}",
            "description": fake.text(max_nb_chars=200),
            "price": price or round(fake.pyfloat(left_digits=3, right_digits=0, positive=True), 2),
            "currency": "VND",
            "stock": fake.pyint(min_value=0, max_value=1000),
            "status": fake.random_element(elements=("ACTIVE", "INACTIVE")),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @staticmethod
    def create_product_update() -> ProductUpdate:
        """제품 업데이트 스키마 생성"""
        return ProductUpdate(
            name=f"Updated Product {fake.word().capitalize()}",
            description=fake.text(max_nb_chars=200),
            price=round(fake.pyfloat(left_digits=3, right_digits=0, positive=True), 2),
            stock=fake.pyint(min_value=0, max_value=1000),
            status=fake.random_element(elements=("ACTIVE", "INACTIVE")),
        )

    @staticmethod
    def create_customer() -> Customer:
        """고객 스키마 생성"""
        return Customer(
            name=TestDataFactory.generate_customer_name(),
            phone=TestDataFactory.generate_phone(),
            email=TestDataFactory.generate_email(),
        )

    @staticmethod
    def create_order_item(product_id: str, quantity: Optional[int] = None) -> OrderItemCreate:
        """주문 항목 생성 스키마 생성"""
        return OrderItemCreate(
            productId=product_id,
            quantity=quantity or fake.pyint(min_value=1, max_value=10),
        )

    @staticmethod
    def create_pricing(
        subtotal: Optional[float] = None,
        shipping_fee: Optional[float] = None,
        discount: Optional[float] = None,
    ) -> Pricing:
        """가격 정보 스키마 생성"""
        subtotal_val = subtotal or round(fake.pyfloat(left_digits=4, right_digits=0, positive=True), 2)
        shipping_fee_val = shipping_fee if shipping_fee is not None else round(
            fake.pyfloat(left_digits=2, right_digits=0, min_value=0, max_value=50000), 2
        )
        discount_val = discount if discount is not None else round(
            fake.pyfloat(left_digits=2, right_digits=0, min_value=0, max_value=subtotal_val * 0.3), 2
        )
        total_amount = subtotal_val + shipping_fee_val - discount_val

        return Pricing(
            subTotal=subtotal_val,
            shippingFee=shipping_fee_val,
            discount=discount_val,
            totalAmount=max(0, total_amount),  # 음수 방지
            currency="VND",
        )

    @staticmethod
    def create_address() -> Address:
        """주소 스키마 생성"""
        return Address(
            receiverName=TestDataFactory.generate_customer_name(),
            receiverPhone=TestDataFactory.generate_phone(),
            fullAddress=TestDataFactory.generate_address(),
        )

    @staticmethod
    def create_shipper() -> Shipper:
        """배송원 스키마 생성"""
        return Shipper(
            shipperId=f"TEST-SHIPPER-{fake.lexify(text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}",
            name=f"TestShipper_{fake.lexify(text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')}",
            phone=TestDataFactory.generate_phone(),
            vehicleType=fake.random_element(elements=("motorbike", "car", "truck")),
        )

    @staticmethod
    def create_shipping(
        status: Optional[str] = None,
        include_shipper: bool = False,
    ) -> Shipping:
        """배송 정보 스키마 생성"""
        shipping_statuses = [
            "NOT_CREATED",
            "CREATED",
            "PICKED",
            "DELIVERING",
            "DELIVERED",
            "FAILED",
            "CANCELLED",
        ]
        
        return Shipping(
            shippingOrderCode=f"TEST-SHIP-{fake.lexify(text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}",
            status=status or fake.random_element(elements=shipping_statuses),
            address=TestDataFactory.create_address(),
            shipper=TestDataFactory.create_shipper() if include_shipper else None,
            estimatedDeliveryTime=datetime.utcnow() + timedelta(days=fake.pyint(min_value=1, max_value=7)),
            deliveredAt=datetime.utcnow() - timedelta(days=fake.pyint(min_value=0, max_value=30)) if fake.boolean() else None,
            failedReason=fake.text(max_nb_chars=200) if fake.boolean(chance_of_getting_true=10) else None,
        )

    @staticmethod
    def create_order(
        customer: Optional[Customer] = None,
        items: Optional[List[OrderItemCreate]] = None,
        product_ids: Optional[List[str]] = None,
    ) -> OrderCreate:
        """주문 생성 스키마 생성"""
        if items is None:
            if product_ids is None:
                product_ids = [TestDataFactory.generate_product_id() for _ in range(fake.pyint(min_value=1, max_value=3))]
            items = [
                TestDataFactory.create_order_item(pid) for pid in product_ids
            ]

        return OrderCreate(
            customer=customer or TestDataFactory.create_customer(),
            items=items,
        )

    @staticmethod
    def create_order_update(order_status: Optional[str] = None) -> OrderUpdate:
        """주문 업데이트 스키마 생성"""
        order_statuses = ["DRAFT", "CONFIRMED", "CANCELLED", "COMPLETED"]
        return OrderUpdate(
            orderStatus=order_status or fake.random_element(elements=order_statuses),
        )

    @staticmethod
    def create_order_item_out(
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
        quantity: Optional[int] = None,
        unit_price: Optional[float] = None,
    ) -> dict:
        """주문 항목 출력 스키마용 딕셔너리 생성"""
        unit_price_val = unit_price or round(fake.pyfloat(left_digits=3, right_digits=0, positive=True), 2)
        quantity_val = quantity or fake.pyint(min_value=1, max_value=10)
        
        return {
            "id": fake.pyint(min_value=1, max_value=10000),
            "productId": product_id or TestDataFactory.generate_product_id(),
            "productName": product_name or f"Test Product {fake.word().capitalize()}",
            "quantity": quantity_val,
            "unitPrice": unit_price_val,
            "totalPrice": round(unit_price_val * quantity_val, 2),
        }

    @staticmethod
    def create_order_out(
        order_id: Optional[uuid.UUID] = None,
        order_code: Optional[str] = None,
        customer: Optional[Customer] = None,
        items: Optional[List[dict]] = None,
        pricing: Optional[Pricing] = None,
        shipping: Optional[Shipping] = None,
        order_status: Optional[str] = None,
        payment_method: Optional[str] = None,
        payment_status: Optional[str] = None,
    ) -> dict:
        """주문 출력 스키마용 딕셔너리 생성"""
        order_statuses = ["DRAFT", "CONFIRMED", "CANCELLED", "COMPLETED"]
        payment_statuses = ["PENDING", "PAID", "FAILED", "REFUNDED"]
        payment_methods = ["COD", "BANK_TRANSFER", "CREDIT_CARD", "PAYPAL"]

        if items is None:
            items = [
                TestDataFactory.create_order_item_out()
                for _ in range(fake.pyint(min_value=1, max_value=3))
            ]

        return {
            "id": order_id or uuid.uuid4(),
            "orderCode": order_code or TestDataFactory.generate_order_code(),
            "customer": (customer or TestDataFactory.create_customer()).model_dump(),
            "items": items,
            "pricing": (pricing or TestDataFactory.create_pricing()).model_dump(),
            "shipping": (shipping or TestDataFactory.create_shipping()).model_dump(),
            "orderStatus": order_status or fake.random_element(elements=order_statuses),
            "paymentMethod": payment_method or fake.random_element(elements=payment_methods),
            "paymentStatus": payment_status or fake.random_element(elements=payment_statuses),
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
        }

    @staticmethod
    def create_external_status_update() -> ExternalStatusUpdate:
        """외부 시스템 상태 업데이트 스키마 생성"""
        order_statuses = ["DRAFT", "CONFIRMED", "CANCELLED", "COMPLETED"]
        payment_statuses = ["PENDING", "PAID", "FAILED", "REFUNDED"]
        shipping_statuses = [
            "NOT_CREATED",
            "CREATED",
            "PICKED",
            "DELIVERING",
            "DELIVERED",
            "FAILED",
            "CANCELLED",
        ]

        return ExternalStatusUpdate(
            orderStatus=fake.random_element(elements=order_statuses) if fake.boolean() else None,
            paymentStatus=fake.random_element(elements=payment_statuses) if fake.boolean() else None,
            shippingStatus=fake.random_element(elements=shipping_statuses) if fake.boolean() else None,
            shippingOrderCode=f"TEST-SHIP-{fake.lexify(text='????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}" if fake.boolean() else None,
            shipper=TestDataFactory.create_shipper() if fake.boolean() else None,
            estimatedDeliveryTime=datetime.utcnow() + timedelta(days=fake.pyint(min_value=1, max_value=7)) if fake.boolean() else None,
            deliveredAt=datetime.utcnow() - timedelta(days=fake.pyint(min_value=0, max_value=30)) if fake.boolean() else None,
            failedReason=fake.text(max_nb_chars=200) if fake.boolean(chance_of_getting_true=10) else None,
        )


# 예제 데이터셋 생성 함수들
def generate_product_examples() -> List[dict]:
    """제품 예제 데이터셋 생성"""
    factory = TestDataFactory()
    return [
        factory.create_product_out() for _ in range(5)
    ]


def generate_order_examples() -> List[dict]:
    """주문 예제 데이터셋 생성"""
    factory = TestDataFactory()
    return [
        factory.create_order_out() for _ in range(5)
    ]


def generate_customer_examples() -> List[dict]:
    """고객 예제 데이터셋 생성"""
    factory = TestDataFactory()
    return [
        factory.create_customer().model_dump() for _ in range(5)
    ]


if __name__ == "__main__":
    # 예제 데이터 출력
    import json
    from datetime import datetime

    def json_serial(obj):
        """JSON 직렬화 헬퍼"""
        if isinstance(obj, (datetime, uuid.UUID)):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    factory = TestDataFactory()

    print("=" * 80)
    print("합성 테스트 데이터 예제")
    print("=" * 80)

    print("\n1. 제품 예제:")
    print(json.dumps(generate_product_examples(), indent=2, default=json_serial, ensure_ascii=False))

    print("\n2. 고객 예제:")
    print(json.dumps(generate_customer_examples(), indent=2, default=json_serial, ensure_ascii=False))

    print("\n3. 주문 생성 스키마 예제:")
    order_create = factory.create_order()
    print(json.dumps(order_create.model_dump(), indent=2, default=json_serial, ensure_ascii=False))

    print("\n4. 주문 출력 스키마 예제:")
    print(json.dumps(generate_order_examples(), indent=2, default=json_serial, ensure_ascii=False))

    print("\n5. 외부 상태 업데이트 예제:")
    status_update = factory.create_external_status_update()
    print(json.dumps(status_update.model_dump(), indent=2, default=json_serial, ensure_ascii=False))

