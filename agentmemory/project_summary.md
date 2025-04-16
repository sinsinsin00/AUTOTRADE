# 프로젝트 요약: AI 기반 비트코인 선물 자동매매 봇

## 1. 프로젝트 목표

- AI (Claude, Gemini)를 활용하여 비트코인(BTC/USDT) 선물 거래를 자동화하는 파이썬 기반 봇 개발.
- 바이낸스 선물 거래소 API를 연동하여 실제 거래 실행.
- 안정적인 운영을 위한 모듈화된 코드 구조 설계 및 위험 관리 (스탑로스/테이크프로핏) 기능 구현.

## 2. 기술 스택 및 환경

- **언어:** Python 3
- **주요 라이브러리:**
    - `ccxt`: 거래소 API 연동 (바이낸스)
    - `pandas`: 데이터 처리
    - `python-dotenv`: 환경 변수 관리 (API 키)
    - `anthropic`: Claude API
    - `google-generativeai`: Gemini API
- **거래소:** Binance Futures (USDT-M)
- **AI 모델:** Claude (anthropic), Gemini (google-generativeai)
- **코드 에디터:** VS Code (사용자 선택)
- **API 키 관리:** `.env` 파일을 통해 관리

## 3. 프로젝트 구조

- **`tradebitcoin/`**: 메인 프로젝트 폴더
    - **`main.py`**: 메인 실행 파일. 전체 워크플로우 제어, 환경 설정, 핸들러 모듈 호출.
    - **`ai_handler.py`**: AI 관련 로직 (Claude/Gemini API 호출, 프롬프트 생성, 응답 처리).
    - **`trading_handler.py`**: 거래 관련 로직 (바이낸스 API 연동, 데이터 조회, 주문 실행, 포지션 관리).
    - **`.env`**: API 키 등 민감 정보 저장 (버전 관리에서 제외 필요).
    - **`requirements.txt`**: 필요한 파이썬 라이브러리 목록.
- **`agentmemory/`**: 프로젝트 진행 상황 및 요약 문서 저장 폴더
    - **`project_summary.md`**: 현재 문서.

## 4. 현재 진행 상황

- 기본적인 프로젝트 폴더 및 파일 구조 생성 완료.
- `requirements.txt` 파일에 필요한 라이브러리 명시 완료.
- `.env` 파일을 통한 API 키 관리 설정 완료.
- `ccxt`를 이용한 바이낸스 선물 거래소 연동 기본 설정 완료 (`main.py`).
- AI 클라이언트 (Claude, Gemini) 초기화 로직 추가 (`ai_handler.py`, `main.py`).
- 주요 기능 함수들의 기본 골격 및 모듈 분리 완료:
    - `trading_handler.fetch_ohlcv`: 차트 데이터 조회
    - `trading_handler.get_current_price`: 현재가 조회
    - `trading_handler.calculate_quantity`: 주문 수량 계산 (기본)
    - `ai_handler.get_ai_decision`: AI 투자 판단 요청 (기본 프롬프트 및 API 호출 구조 포함)
    - `trading_handler.execute_trade`: 주문 실행 및 SL/TP 설정 (기본 구조)
    - `trading_handler.check_and_manage_position`: 포지션 확인
    - `trading_handler.cancel_open_orders`: 미체결 주문 취소
- `main.py`에서 주기적으로 위 함수들을 호출하여 자동매매 로직을 실행하는 메인 루프 구현 완료. 기본적인 오류 처리 포함.

## 5. 다음 단계 (TODO)

- **`ai_handler.py`**:
    - `get_ai_decision` 함수 내 실제 Claude 및 Gemini API 호출 로직 상세 구현 및 테스트.
    - 프롬프트 엔지니어링: 더 정교한 데이터 분석 및 판단을 위한 프롬프트 개선.
    - AI 모델 응답의 안정성 및 유효성 검증 강화.
    - 데이터 입력 길이 제한 및 처리 방식 개선 (토큰 수 고려).
- **`trading_handler.py`**:
    - `calculate_quantity`: `exchange.load_markets()` 정보(`market['limits']`, `market['precision']`)를 활용하여 정확한 최소 주문 수량, 금액, 소수점 처리 구현.
    - `execute_trade`: `exchange.load_markets()` 정보(`market['precision']`)를 활용하여 SL/TP 가격 계산 시 정확한 소수점 처리 구현. `reduceOnly` 파라미터 지원 여부 및 효과 재확인.
    - `cancel_open_orders`: `exchange.cancel_all_orders(symbol)`의 정확한 동작 방식 확인 (선물 특정 심볼만 취소하는지) 또는 `fetch_open_orders` 후 개별 취소 방식으로 변경 고려.
    - 오류 처리 강화: API 호출 실패, 잔고 부족 등 다양한 예외 상황에 대한 상세 처리 추가.
- **`main.py`**:
    - 로깅(Logging) 기능 추가: 파일 또는 데이터베이스에 거래 내역, AI 판단, 오류 등을 기록하여 추적 및 분석 용이성 확보.
    - 설정 값 관리 개선: `amount_usdt`, `leverage` 등 주요 파라미터를 설정 파일(예: JSON, YAML) 또는 환경 변수로 분리하는 방안 고려.
- **테스트 및 안정화:**
    - 실제 소액 또는 테스트넷 환경에서 봇 실행 및 안정성 검증.
    - 다양한 시장 상황에서의 동작 테스트. 