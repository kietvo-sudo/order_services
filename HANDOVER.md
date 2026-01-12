# Order Services 인수인계 문서

## 1. 시스템 개요

### 1.1 프로젝트 목적
Order Services는 주문 및 상품 관리를 위한 RESTful API 마이크로서비스입니다. FastAPI와 PostgreSQL을 기반으로 구축되었으며, 주문 생성, 상태 추적, 상품 관리, 외부 배송 서비스 통합 기능을 제공합니다.

### 1.2 기술 스택
- **언어**: Python 3.11
- **프레임워크**: FastAPI (비동기 웹 프레임워크)
- **서버**: Uvicorn (ASGI 서버)
- **ORM**: SQLAlchemy (동기 방식)
- **데이터베이스**: PostgreSQL
- **검증**: Pydantic (요청/응답 스키마)
- **설정 관리**: pydantic-settings
- **HTTP 클라이언트**: httpx (외부 API 통신)

### 1.3 아키텍처 패턴
- **계층 분리**: Router → Service → Repository (CRUD) 패턴
- **Clean Architecture**: 비즈니스 로직은 라우터가 아닌 서비스/CRUD 레이어에 위치
- **의존성 주입**: FastAPI의 `Depends`를 통한 데이터베이스 세션 관리

### 1.4 주요 기능
- 주문 생성 및 관리 (생성, 조회, 수정, 취소)
- 상품 카탈로그 관리 (CRUD)
- 주문 상태 추적 (주문 상태, 결제 상태, 배송 상태)
- 외부 배송 서비스 API 통합
- 자동 주문 코드 생성 (`ORD-YYYYMMDD-HHMMSS-XXXX` 형식)
- 자동 상품 ID 생성 (UUID)

---

## 2. 핵심 워크플로우 및 실행 흐름

### 2.1 애플리케이션 시작 흐름

```
1. app/main.py 실행
   ├─ FastAPI 앱 초기화
   ├─ CORS 미들웨어 설정
   ├─ Router 등록 (orders, products)
   └─ @app.on_event("startup")
       └─ Base.metadata.create_all(bind=engine)  # 테이블 자동 생성
```

### 2.2 주문 생성 워크플로우 (중요)

```12:200:app/crud.py
def create_order(db: Session, payload: schemas.OrderCreate) -> Order:
    # 1. 주문 코드 자동 생성 및 중복 확인
    # 2. 상품 조회 및 검증 (존재 여부, ACTIVE 상태 확인)
    # 3. 주문 항목 생성 및 가격 계산
    # 4. 주문 객체 생성 (DB 저장 전)
    # 5. 외부 배송 API 호출 (send_order_to_shipment)
    # 6. 배송 API 성공 시에만 DB 저장
    # 7. 실패 시 HTTPException 발생 (502 Bad Gateway)
```

**중요**: 주문은 **배송 API 호출 성공 후에만** 데이터베이스에 저장됩니다. 배송 API 실패 시 주문은 생성되지 않습니다.

### 2.3 외부 배송 서비스 통합

```66:220:app/services.py
def send_order_to_shipment(order) -> Optional[dict]:
    # 1. 주소 파싱 (도시, 구/군, 동 추출)
    # 2. 패키지 정보 계산 (무게, 가치)
    # 3. 배송 API 형식으로 데이터 변환
    # 4. httpx를 통한 POST 요청 (타임아웃 30초)
    # 5. 성공 시 응답 데이터 반환, 실패 시 None 반환
```

**배송 API 엔드포인트**: `https://ratty-rowe-demo135-368bf5d2.koyeb.app/api/shipments`

### 2.4 데이터베이스 세션 관리

```11:16:app/database.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- FastAPI의 `Depends(get_db)`를 통해 각 요청마다 새로운 세션 생성
- 요청 종료 시 자동으로 세션 닫힘
- 트랜잭션은 명시적으로 `commit()` 또는 `rollback()` 호출

### 2.5 주문 상태 업데이트 흐름

```
외부 시스템 → POST /orders/by-code/{order_code}/status-update
   ├─ OrderUpdate 스키마로 변환
   ├─ None이 아닌 필드만 업데이트
   └─ DB 저장 및 응답
```

---

## 3. 먼저 이해해야 할 중요한 파일 및 모듈

### 3.1 필수 파일 (우선순위 순)

#### 1. `app/config.py` - 설정 관리
```5:106:app/config.py
class Settings(BaseSettings):
    # 애플리케이션 설정, CORS 설정, 데이터베이스 연결 설정
    # DATABASE_URL 또는 개별 DB 파라미터 지원
    # 환경 변수 자동 로드 (.env 파일)
```

**핵심 포인트**:
- `DATABASE_URL`이 설정되면 개별 파라미터 무시
- `DATABASE_URL`이 없으면 모든 개별 파라미터 필수
- CORS 설정은 문자열 또는 리스트 형식 지원

#### 2. `app/models.py` - 데이터 모델
```23:104:app/models.py
class Order(Base):
    # 주문 엔티티: 고객 정보, 가격, 배송 정보, 상태 추적
    # order_code는 UniqueConstraint로 보장

class Product(Base):
    # 상품 카탈로그: 가격, 재고, 상태

class OrderItem(Base):
    # 주문-상품 연결 테이블 (다대다 관계)
    # 주문 시점의 가격 스냅샷 저장 (audit trail)
```

**핵심 포인트**:
- `Order.order_code`는 고유 제약 조건
- `OrderItem.unit_price`는 주문 시점 가격 저장 (상품 가격 변경 영향 없음)
- `Order.shipper`는 JSONB 타입으로 유연한 구조 저장

#### 3. `app/schemas.py` - 요청/응답 스키마
```8:163:app/schemas.py
# Pydantic 모델로 요청/응답 검증
# OrderCreate, OrderUpdate, OrderOut 등
# ExternalStatusUpdate: 외부 시스템용 상태 업데이트 스키마
```

**핵심 포인트**:
- 요청 스키마는 camelCase (예: `orderCode`, `customerId`)
- DB 모델은 snake_case (예: `order_code`, `customer_id`)
- `OrderOut`은 중첩된 구조로 변환하여 반환

#### 4. `app/crud.py` - 데이터 접근 계층
```95:200:app/crud.py
def create_order(...):
    # 주문 생성 로직
    # 배송 API 호출 후 DB 저장

def get_order_by_code(...):
    # joinedload를 통한 eager loading (N+1 문제 방지)
```

**핵심 포인트**:
- 모든 주문 조회는 `joinedload`를 사용하여 N+1 문제 방지
- 주문 코드/상품 ID 중복 시 재생성 로직 포함
- 트랜잭션 실패 시 명시적 `rollback()` 호출

#### 5. `app/services.py` - 외부 서비스 통합
```66:220:app/services.py
def send_order_to_shipment(order) -> Optional[dict]:
    # 주소 파싱 및 배송 API 호출
```

**핵심 포인트**:
- 주소 파싱은 기본적인 휴리스틱 방식 (프로덕션에서는 지오코딩 API 권장)
- 타임아웃 30초 설정
- 실패 시 `None` 반환, 성공 시 응답 데이터 반환

#### 6. `app/routers/orders.py` - 주문 API 엔드포인트
```64:139:app/routers/orders.py
# POST /orders: 주문 생성
# GET /orders: 주문 목록 (페이지네이션)
# GET /orders/by-code/{order_code}: 주문 조회
# PATCH /orders/by-code/{order_code}: 주문 수정
# DELETE /orders/by-code/{order_code}: 주문 취소 (soft delete)
# POST /orders/by-code/status-update/{order_code}: 외부 상태 업데이트
```

**핵심 포인트**:
- `serialize_order()` 함수로 Order 모델을 OrderOut 스키마로 변환
- 주문 취소는 실제 삭제가 아닌 상태 변경 (`CANCELLED`)

#### 7. `app/main.py` - 애플리케이션 진입점
```9:33:app/main.py
app = FastAPI(...)
# CORS 설정
# Router 등록
# Startup 이벤트에서 테이블 생성
```

### 3.2 보조 파일

- `app/database.py`: 데이터베이스 연결 및 세션 팩토리
- `app/constants.py`: 상태 상수 정의 (현재 사용되지 않음)
- `app/routers/products.py`: 상품 API 엔드포인트
- `insert_products.py`: 샘플 상품 삽입 유틸리티
- `validate_documentation.py`: 문서 검증 스크립트

---

## 4. 알려진 가정 또는 제약사항

### 4.1 데이터베이스 관련
- **테이블 자동 생성**: 프로덕션에서는 Alembic 같은 마이그레이션 도구 사용 권장
- **동기 SQLAlchemy**: 비동기 SQLAlchemy가 아닌 동기 방식 사용 (성능 최적화 필요 시 고려)
- **트랜잭션 관리**: 명시적 `commit()`/`rollback()` 사용, 자동 커밋 없음

### 4.2 외부 서비스 통합
- **배송 API 의존성**: 주문 생성 시 배송 API가 실패하면 주문이 생성되지 않음
  - **리스크**: 배송 API 장애 시 주문 생성 불가
  - **개선 제안**: 재시도 로직 또는 비동기 큐 시스템 도입
- **배송 API URL 하드코딩**: `app/services.py`에 하드코딩됨
  - **개선 제안**: 환경 변수로 관리

### 4.3 주소 파싱
- **기본 휴리스틱**: 주소 파싱이 간단한 문자열 매칭 방식
  - **제한**: 정확한 도시/구/동 추출 보장 불가
  - **개선 제안**: 지오코딩 API 또는 주소 데이터베이스 활용

### 4.4 주문 코드 생성
- **타임스탬프 기반**: `ORD-YYYYMMDD-HHMMSS-XXXX` 형식
- **중복 가능성**: 동일 초에 여러 주문 생성 시 충돌 가능 (재생성 로직으로 처리)
- **UUID 기반 랜덤 접미사**: 4자리 숫자만 사용 (충돌 가능성 낮음)

### 4.5 가격 계산
- **서버 측 검증**: 클라이언트가 전송한 `pricing` 정보와 서버에서 계산한 `subtotal` 비교 없음
  - **현재**: 서버에서 계산한 `subtotal`만 사용
  - **주의**: 클라이언트의 `pricing.subTotal`은 무시됨

### 4.6 재고 관리
- **재고 차감 없음**: 주문 생성 시 `Product.stock`이 자동으로 차감되지 않음
  - **리스크**: 동시 주문 시 재고 부족 가능
  - **개선 제안**: 트랜잭션 내에서 재고 확인 및 차감 로직 추가

### 4.7 상태 관리
- **상태 값 검증 부족**: `orderStatus`, `paymentStatus`, `shippingStatus`에 대한 엄격한 검증 없음
  - **현재**: 문자열로 저장, 스키마에 설명만 있음
  - **개선 제안**: Enum 사용 또는 상태 전이 검증 로직 추가

### 4.8 에러 처리
- **일반적인 예외 처리**: `create_product`에서만 `try-except` 사용
- **배송 API 실패**: HTTPException으로 처리하지만 재시도 없음

---

## 5. 일반적인 함정 또는 주의가 필요한 영역

### 5.1 데이터베이스 세션 관리
⚠️ **주의**: 세션은 요청마다 생성되며, 요청 종료 시 자동으로 닫힙니다. 백그라운드 작업에서 세션을 재사용하면 안 됩니다.

```python
# ❌ 잘못된 사용
db = SessionLocal()
# 백그라운드 작업에서 사용...

# ✅ 올바른 사용
def background_task():
    db = SessionLocal()
    try:
        # 작업 수행
    finally:
        db.close()
```

### 5.2 N+1 쿼리 문제
✅ **현재 해결됨**: `get_orders`, `get_order_by_code`에서 `joinedload` 사용

```python
# ✅ 올바른 방식 (현재 코드)
db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product))
```

⚠️ **주의**: 새로운 조회 함수 추가 시 eager loading 고려 필요

### 5.3 배송 API 실패 처리
⚠️ **중요**: 배송 API 실패 시 주문이 생성되지 않습니다. 이는 비즈니스 요구사항이지만, 배송 API 장애 시 전체 주문 시스템이 중단될 수 있습니다.

**개선 방안**:
- 재시도 로직 추가 (exponential backoff)
- 비동기 큐 시스템 도입 (예: Celery, RabbitMQ)
- 배송 API 실패 시에도 주문 저장 후 나중에 재시도하는 옵션

### 5.4 주문 코드 중복 처리
⚠️ **주의**: `generate_order_code()`는 타임스탬프 기반이므로 동일 초에 여러 주문 생성 시 충돌 가능성이 있습니다. 현재는 재생성 로직으로 처리하지만, 고부하 상황에서는 성능 이슈가 발생할 수 있습니다.

**개선 방안**:
- UUID 기반 주문 코드 사용
- 분산 ID 생성기 사용 (예: Snowflake)

### 5.5 트랜잭션 롤백
⚠️ **주의**: `create_order`에서 배송 API 호출이 DB 트랜잭션 외부에서 발생합니다. 배송 API 성공 후 DB 저장 실패 시 데이터 불일치가 발생할 수 있습니다.

**현재 동작**:
1. 배송 API 호출 (성공)
2. DB 저장 (실패 시)
3. 배송 API에는 주문이 생성되었지만 DB에는 없음

**개선 방안**:
- 분산 트랜잭션 또는 보상 트랜잭션 패턴 사용
- 배송 API 롤백 엔드포인트 활용

### 5.6 주소 파싱 정확도
⚠️ **주의**: `_parse_address()` 함수는 기본적인 휴리스틱만 사용합니다. 복잡한 주소 형식이나 오타가 있는 경우 잘못된 도시 정보가 추출될 수 있습니다.

**예시**:
```python
# "123 Main St, District 1, Ho Chi Minh City" → 정확
# "123 Main St, HCM" → 정확 (약어 인식)
# "123 Main St" → "Ho Chi Minh City" (기본값, 부정확할 수 있음)
```

### 5.7 상품 가격 변경 영향
✅ **현재 해결됨**: `OrderItem.unit_price`에 주문 시점 가격을 저장하므로, 이후 상품 가격 변경이 과거 주문에 영향을 주지 않습니다.

### 5.8 재고 관리 부재
⚠️ **중요**: 주문 생성 시 재고가 자동으로 차감되지 않습니다. 동시 주문 시 재고 부족 상황이 발생할 수 있습니다.

**개선 방안**:
```python
# create_order 내부에 추가 필요
if product.stock < item.quantity:
    raise HTTPException(400, "Insufficient stock")
product.stock -= item.quantity
```

### 5.9 환경 변수 설정
⚠️ **주의**: `.env` 파일이 없거나 잘못된 설정 시 애플리케이션 시작 실패

**검증 로직**: `app/config.py`의 `validate_database_config()`에서 확인

### 5.10 로깅
⚠️ **주의**: 로깅 설정이 명시적으로 구성되지 않았습니다. 프로덕션에서는 구조화된 로깅(예: JSON 형식) 및 로그 레벨 관리가 필요합니다.

**현재**: `logging.getLogger(__name__)` 사용, 기본 설정에 의존

---

## 6. 추가 참고사항

### 6.1 개발 환경 설정
1. Python 3.11 설치
2. Conda 환경 생성: `conda env create -f environment.yml`
3. `.env` 파일 생성 (데이터베이스 연결 정보)
4. 애플리케이션 실행: `uvicorn app.main:app --reload`

### 6.2 API 문서
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 6.3 테스트
⚠️ **현재 테스트 코드 없음**: 프로덕션 배포 전 단위 테스트 및 통합 테스트 작성 권장

### 6.4 프로덕션 배포 체크리스트
- [ ] Alembic 마이그레이션 설정
- [ ] 환경 변수 관리 (Secrets Manager)
- [ ] 로깅 설정 (구조화된 로그, 로그 레벨)
- [ ] 모니터링 및 알림 설정
- [ ] 배송 API 재시도 로직
- [ ] 재고 관리 로직 추가
- [ ] 상태 검증 로직 강화
- [ ] 성능 테스트 (부하 테스트)
- [ ] 보안 검토 (인증/인가, 입력 검증)

---

## 7. 연락처 및 추가 리소스

- **프로젝트 README**: `/README.md`
- **코딩 규칙**: `.cursorrules`
- **환경 설정**: `environment.yml`

---

**문서 작성일**: 2024
**마지막 업데이트**: 코드베이스 분석 기준

