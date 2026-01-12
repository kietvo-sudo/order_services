# 테스트 문서

이 디렉토리에는 `order_services` 애플리케이션의 단위 테스트가 포함되어 있습니다.

## 테스트 구조

```
tests/
├── __init__.py
├── conftest.py          # 공통 픽스처 및 설정
├── test_services.py     # app.services 모듈 테스트
└── test_crud.py         # app.crud 모듈 테스트
```

## 테스트 실행

### 기본 실행
```bash
pytest
```

### 상세 출력
```bash
pytest -v
```

### 특정 테스트 파일 실행
```bash
pytest tests/test_services.py
pytest tests/test_crud.py
```

### 특정 테스트 클래스 또는 함수 실행
```bash
pytest tests/test_services.py::TestParseAddress
pytest tests/test_crud.py::TestCreateOrder::test_create_order_success
```

### 커버리지 리포트 생성
```bash
pytest --cov=app --cov-report=html
```

## 테스트 커버리지

### test_services.py

#### `_parse_address` 함수 테스트
- ✅ 빈 문자열 처리
- ✅ None 값 처리
- ✅ 다양한 도시명 파싱 (Ho Chi Minh City, Hanoi, Da Nang, Can Tho, Hai Phong)
- ✅ 베트남어 도시명 파싱
- ✅ 약어 처리 (HCM)
- ✅ 알 수 없는 도시 기본값 처리
- ✅ 구(District) 번호 추출
- ✅ 대소문자 구분 없음

#### `send_order_to_shipment` 함수 테스트
- ✅ 성공적인 API 호출 (200, 201 상태 코드)
- ✅ API 오류 응답 처리
- ✅ 타임아웃 예외 처리
- ✅ 요청 오류 처리
- ✅ 예상치 못한 예외 처리
- ✅ JSON 파싱 오류 처리
- ✅ 수신자 정보 포함/미포함 케이스
- ✅ 무게 계산 로직
- ✅ 최소 무게 처리 (0kg → 1.0kg)
- ✅ COD 금액 설정
- ✅ 비COD 결제 처리
- ✅ 날짜/시간 필드 처리

### test_crud.py

#### `generate_order_code` 함수 테스트
- ✅ 주문 코드 형식 검증
- ✅ 고유성 보장
- ✅ 날짜 포함 확인

#### `generate_product_id` 함수 테스트
- ✅ UUID 형식 검증
- ✅ 고유성 보장

#### Product CRUD 테스트
- ✅ 제품 생성 성공
- ✅ 최소 필드로 제품 생성
- ✅ 데이터베이스 오류 처리
- ✅ 제품 조회 성공/실패
- ✅ 페이지네이션
- ✅ 제품 업데이트 (전체/부분)
- ✅ 제품 삭제

#### Order CRUD 테스트
- ✅ 주문 생성 성공
- ✅ 존재하지 않는 제품 처리
- ✅ 비활성 제품 처리
- ✅ 여러 아이템 포함 주문 생성
- ✅ 배송 API 실패 처리
- ✅ 배송 API 응답 파싱
- ✅ 주문 코드로 조회
- ✅ 페이지네이션
- ✅ 주문 상태 업데이트
- ✅ 주문 취소
- ✅ 이미 취소된 주문 처리
- ✅ 소계 계산 검증
- ✅ 기본값 설정 검증
- ✅ 주문 코드 충돌 처리

## 테스트 전략

### 1. 정상 케이스 (Happy Path)
모든 테스트는 먼저 정상적인 동작을 검증합니다.

### 2. 예외 처리
다음과 같은 예외 상황을 테스트합니다:
- 데이터베이스 오류
- 외부 API 오류
- 타임아웃
- 잘못된 입력 데이터
- 존재하지 않는 리소스

### 3. 경계값 및 엣지 케이스
- 빈 문자열/None 값
- 최소/최대 값
- 0 값 처리
- 중복 값 처리
- 특수 문자 처리

## 모킹 전략

### 외부 의존성 모킹
- **데이터베이스**: SQLite 인메모리 데이터베이스 사용 (`conftest.py`)
- **외부 API**: `unittest.mock.patch`를 사용하여 `httpx.Client` 모킹
- **시간**: 필요시 `datetime` 모킹

### 픽스처
`conftest.py`에서 다음 픽스처를 제공합니다:
- `db_session`: 테스트용 데이터베이스 세션
- `sample_product`: 샘플 제품 객체
- `sample_order`: 샘플 주문 객체
- `mock_httpx_client`: 모킹된 HTTP 클라이언트

## 테스트 작성 가이드라인

1. **명확한 테스트 이름**: 테스트 함수 이름은 무엇을 테스트하는지 명확히 표현해야 합니다.
2. **단일 책임**: 각 테스트는 하나의 동작만 검증해야 합니다.
3. **AAA 패턴**: Arrange-Act-Assert 패턴을 따릅니다.
4. **독립성**: 각 테스트는 다른 테스트에 의존하지 않아야 합니다.
5. **반복 가능성**: 테스트는 항상 같은 결과를 반환해야 합니다.

## 의존성

테스트 실행을 위해 다음 패키지가 필요합니다:
- `pytest`
- `pytest-mock` (선택사항, 모킹 편의성 향상)
- `pytest-cov` (선택사항, 커버리지 리포트)

설치:
```bash
pip install pytest pytest-mock pytest-cov
```

