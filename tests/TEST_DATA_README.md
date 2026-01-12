# 테스트 데이터 생성기 사용 가이드

## 개요

`test_data_factory.py`는 주문 서비스의 모든 데이터 모델에 대한 합성 테스트 데이터를 생성하는 팩토리 클래스입니다.

## 설치

테스트 데이터 생성기를 사용하려면 `Faker` 라이브러리가 필요합니다:

```bash
pip install faker
```

또는 conda 환경의 경우:

```bash
conda install -c conda-forge faker
```

## 빠른 시작

### 기본 사용법

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 제품 생성
product = factory.create_product()
print(product.model_dump())

# 고객 생성
customer = factory.create_customer()
print(customer.model_dump())

# 주문 생성
order = factory.create_order(customer=customer)
print(order.model_dump())
```

### 예제 데이터셋 생성

```python
from tests.test_data_factory import (
    generate_product_examples,
    generate_customer_examples,
    generate_order_examples
)

# 여러 제품 예제
products = generate_product_examples()

# 여러 고객 예제
customers = generate_customer_examples()

# 여러 주문 예제
orders = generate_order_examples()
```

## 사용 예제

### 1. 제품 테스트 데이터 생성

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 기본 제품 생성
product = factory.create_product()

# 특정 속성을 가진 제품 생성
custom_product = factory.create_product(
    name="Custom Test Product",
    price=50000.0,
    stock=100
)

# 제품 업데이트 스키마 생성
product_update = factory.create_product_update()
```

### 2. 고객 테스트 데이터 생성

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 기본 고객 생성
customer = factory.create_customer()

# 고객 정보는 자동으로 합성 데이터로 생성됨:
# - 이름: TestUser_XXXX 형식
# - 전화번호: 9로 시작하는 가짜 번호
# - 이메일: @testdata.example 도메인
```

### 3. 주문 테스트 데이터 생성

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 기본 주문 생성 (고객과 항목 자동 생성)
order = factory.create_order()

# 특정 제품 ID를 가진 주문 생성
product_ids = ["TEST-PROD-A1B2", "TEST-PROD-C3D4"]
order_with_products = factory.create_order(product_ids=product_ids)

# 특정 고객을 가진 주문 생성
customer = factory.create_customer()
order_with_customer = factory.create_order(customer=customer)
```

### 4. 배송 정보 생성

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 기본 배송 정보 생성
shipping = factory.create_shipping()

# 배송원 정보를 포함한 배송 정보 생성
shipping_with_shipper = factory.create_shipping(include_shipper=True)

# 특정 상태의 배송 정보 생성
delivered_shipping = factory.create_shipping(status="DELIVERED")
```

### 5. 주문 출력 스키마 생성 (API 응답 테스트용)

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 완전한 주문 출력 스키마 생성
order_out = factory.create_order_out()

# 특정 속성을 가진 주문 출력 생성
custom_order_out = factory.create_order_out(
    order_status="COMPLETED",
    payment_status="PAID",
    payment_method="BANK_TRANSFER"
)
```

### 6. 외부 시스템 상태 업데이트 생성

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 외부 시스템에서 보낼 상태 업데이트 생성
status_update = factory.create_external_status_update()
```

## pytest에서 사용하기

### conftest.py에 팩토리 추가

```python
import pytest
from tests.test_data_factory import TestDataFactory

@pytest.fixture
def data_factory():
    """테스트 데이터 팩토리 픽스처"""
    return TestDataFactory()

@pytest.fixture
def sample_product_data(data_factory):
    """샘플 제품 데이터"""
    return data_factory.create_product()

@pytest.fixture
def sample_order_data(data_factory):
    """샘플 주문 데이터"""
    return data_factory.create_order()
```

### 테스트에서 사용

```python
def test_create_order(data_factory, db_session):
    """주문 생성 테스트"""
    order_data = data_factory.create_order()
    
    # 주문 생성 로직 테스트
    # ...
```

## JSON 예제 데이터 사용

`test_data_examples.json` 파일에는 미리 생성된 예제 데이터가 포함되어 있습니다:

```python
import json

with open('tests/test_data_examples.json', 'r', encoding='utf-8') as f:
    examples = json.load(f)

products = examples['products']
customers = examples['customers']
orders = examples['orders']
```

## 프라이버시 보존

모든 테스트 데이터는 다음 원칙을 따릅니다:

1. **실제 개인정보 사용 금지**: 실제 고객 이름, 전화번호, 이메일 사용 안 함
2. **명확한 테스트 식별자**: 모든 ID에 `TEST-` 접두사 사용
3. **완전히 합성된 데이터**: Faker를 사용한 가짜 데이터
4. **프로덕션과 분리**: 프로덕션 데이터와 혼동 불가능한 형식

자세한 내용은 `PRIVACY_GUIDELINES.md`를 참조하세요.

## 데이터 타입 및 제약사항

### 제품 (Product)
- `name`: 문자열 (최대 255자)
- `price`: 양수 float
- `stock`: 0 이상의 정수
- `status`: "ACTIVE" 또는 "INACTIVE"

### 주문 (Order)
- `orderStatus`: "DRAFT", "CONFIRMED", "CANCELLED", "COMPLETED"
- `paymentStatus`: "PENDING", "PAID", "FAILED", "REFUNDED"
- `paymentMethod`: "COD", "BANK_TRANSFER", "CREDIT_CARD", "PAYPAL"

### 배송 (Shipping)
- `status`: "NOT_CREATED", "CREATED", "PICKED", "DELIVERING", "DELIVERED", "FAILED", "CANCELLED"
- `vehicleType`: "motorbike", "car", "truck"

## 문제 해결

### Faker 모듈을 찾을 수 없음

```bash
pip install faker
```

### 재현 가능한 데이터가 필요함

`TestDataFactory`는 기본적으로 `Faker.seed(42)`를 사용하여 재현 가능한 데이터를 생성합니다. 다른 시드를 사용하려면:

```python
from faker import Faker

fake = Faker()
fake.seed(123)  # 다른 시드 값 사용
```

## 추가 리소스

- [프라이버시 가이드라인](PRIVACY_GUIDELINES.md)
- [예제 JSON 데이터](test_data_examples.json)
- [Faker 문서](https://faker.readthedocs.io/)

