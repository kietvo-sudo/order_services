# 테스트 데이터 프라이버시 가이드라인

## 개요

이 문서는 `test_data_factory.py`에서 생성되는 합성 테스트 데이터의 프라이버시 보존 원칙과 구현 방법을 설명합니다.

## 프라이버시 보존 원칙

### 1. 실제 개인정보 사용 금지

**원칙**: 실제 고객의 이름, 전화번호, 이메일 주소를 절대 사용하지 않습니다.

**구현**:
- 모든 이름은 `TestUser_XXXX` 형식의 가짜 식별자 사용
- 전화번호는 `9`로 시작하는 명확히 가짜인 패턴 사용 (예: `9123456789`)
- 이메일은 `@testdata.example` 도메인 사용 (실제 존재하지 않는 도메인)

### 2. 프로덕션 데이터와의 명확한 구분

**원칙**: 테스트 데이터가 프로덕션 데이터와 혼동되지 않도록 명확한 식별자 사용.

**구현**:
- 제품 ID: `TEST-PROD-XXXX` 형식
- 주문 코드: `TEST-ORD-XXXXXXXX-XXXX` 형식
- 배송 코드: `TEST-SHIP-XXXX` 형식
- 배송원 ID: `TEST-SHIPPER-XXXX` 형식

### 3. 완전히 합성된 데이터

**원칙**: Faker 라이브러리를 사용하여 완전히 가짜이지만 현실적인 데이터 생성.

**구현**:
- Faker의 시드 값 설정 (`Faker.seed(42)`)으로 재현 가능한 데이터 생성
- 실제 데이터베이스나 프로덕션 시스템과 무관한 완전히 독립적인 데이터

### 4. 테스트 전용 명확한 표시

**원칙**: 모든 데이터에 테스트용임을 명확히 표시.

**구현**:
- 모든 식별자에 `TEST-` 접두사 사용
- 이메일 도메인에 `testdata.example` 사용
- 주소에 "Test Address:" 접두사 사용

## 데이터 타입별 프라이버시 보존 방법

### 고객 정보 (Customer)

```python
# ❌ 잘못된 예시 (실제 데이터 사용)
name = "Nguyen Van A"
phone = "0901234567"
email = "customer@realcompany.com"

# ✅ 올바른 예시 (합성 데이터)
name = "TestUser_ABCD"
phone = "9123456789"
email = "testuser_abcd@testdata.example"
```

**보존 방법**:
- 이름: `TestUser_` + 랜덤 문자열
- 전화번호: `9`로 시작하는 10자리 가짜 번호
- 이메일: `testuser_` + 랜덤 문자열 + `@testdata.example`

### 제품 정보 (Product)

```python
# ❌ 잘못된 예시 (실제 제품명 사용)
name = "iPhone 15 Pro Max"
id = "IPHONE-15-PRO-MAX"

# ✅ 올바른 예시 (합성 데이터)
name = "Test Product Widget"
id = "TEST-PROD-A1B2"
```

**보존 방법**:
- 제품명: `Test Product` + 일반적인 단어
- 제품 ID: `TEST-PROD-` + 랜덤 문자열

### 주문 정보 (Order)

```python
# ❌ 잘못된 예시 (실제 주문 코드 형식 사용)
order_code = "ORD-20240101-120000-1234"

# ✅ 올바른 예시 (합성 데이터)
order_code = "TEST-ORD-20240101-ABCD"
```

**보존 방법**:
- 주문 코드: `TEST-ORD-` + 타임스탬프 + 랜덤 문자열
- 모든 주문 관련 식별자에 `TEST-` 접두사

### 주소 정보 (Address)

```python
# ❌ 잘못된 예시 (실제 주소 사용)
address = "123 Nguyen Hue Street, Ho Chi Minh City"

# ✅ 올바른 예시 (합성 데이터)
address = "Test Address: 123 Fake Street, Test City"
```

**보존 방법**:
- 주소: `Test Address:` 접두사 + Faker로 생성된 가짜 주소
- 실제 도시명이나 거리명과 무관한 완전히 가짜 데이터

## 사용 가이드

### 1. 테스트 데이터 생성

```python
from tests.test_data_factory import TestDataFactory

factory = TestDataFactory()

# 제품 생성
product = factory.create_product()

# 고객 생성
customer = factory.create_customer()

# 주문 생성
order = factory.create_order(customer=customer)
```

### 2. 예제 데이터셋 사용

```python
from tests.test_data_factory import generate_product_examples, generate_order_examples

# 여러 제품 예제 생성
products = generate_product_examples()

# 여러 주문 예제 생성
orders = generate_order_examples()
```

### 3. JSON 파일 사용

`test_data_examples.json` 파일에는 미리 생성된 예제 데이터가 포함되어 있습니다. 이 파일은:
- 프로덕션 데이터와 완전히 분리됨
- 모든 식별자가 `TEST-` 접두사를 가짐
- 실제 개인정보를 포함하지 않음

## 컴플라이언스 확인

### ✅ 확인 사항

- [x] 실제 고객 이름 사용 안 함
- [x] 실제 전화번호 사용 안 함
- [x] 실제 이메일 주소 사용 안 함
- [x] 실제 제품명 사용 안 함
- [x] 프로덕션 데이터베이스와 연결 안 함
- [x] 모든 식별자에 테스트 표시 포함
- [x] 재현 가능한 데이터 생성 (시드 사용)

### ⚠️ 주의사항

1. **절대 프로덕션 데이터베이스에 저장하지 마세요**
   - 테스트 데이터는 테스트 환경에서만 사용

2. **실제 API 호출 시 주의**
   - 외부 시스템에 테스트 데이터를 전송하지 않도록 주의

3. **로그에 남지 않도록 주의**
   - 테스트 데이터가 프로덕션 로그에 기록되지 않도록 주의

## 의존성

테스트 데이터 생성기를 사용하려면 `Faker` 라이브러리가 필요합니다:

```bash
pip install faker
```

또는 conda 환경의 경우:

```bash
conda install -c conda-forge faker
```

## 추가 정보

- Faker 라이브러리 문서: https://faker.readthedocs.io/
- 데이터 프라이버시 모범 사례: https://owasp.org/www-project-web-security-testing-guide/

