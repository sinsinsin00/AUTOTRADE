import os
import time
import pandas as pd
from dotenv import load_dotenv
import ccxt

# 핸들러 모듈 임포트
import ai_handler
import trading_handler

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 키 가져오기
binance_api_key = os.getenv('BINANCE_API_KEY')
binance_secret_key = os.getenv('BINANCE_SECRET_KEY')
claude_api_key = os.getenv('CLAUDE_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

# --- 바이낸스 연동 설정 ---
try:
    exchange = ccxt.binance({
        'apiKey': binance_api_key,
        'secret': binance_secret_key,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future', # 선물 거래소 사용 명시
            'adjustForTimeDifference': True, # 시간 동기화 문제 방지
        }
    })
    # 선물 시장 로드 (시장 정보 가져오기 위함)
    exchange.load_markets()
    print("바이낸스 선물 거래소 연결 및 시장 정보 로드 성공!")
    # 선물 계정 잔고 확인 (옵션)
    # balance = exchange.fetch_balance(params={'type': 'future'})
    # print(balance)
except Exception as e:
    print(f"바이낸스 연결 오류: {e}")
    exit()

# --- AI 클라이언트 설정 ---
# AI 핸들러 모듈의 초기화 함수 호출
ai_handler.initialize_ai_clients(claude_api_key, gemini_api_key)


# --- 메인 실행 루프 ---
if __name__ == "__main__":
    print("자동 매매 봇 시작...")
    # symbol = 'BTC/USDT:USDT' # 바이낸스 선물 USDT-M 심볼 형식 (ccxt가 내부적으로 처리 가능)
    ui_symbol = 'BTC/USDT'   # ccxt 함수들에 전달할 심볼 (대부분 :USDT 제외 형식 선호)
    timeframe = '15m'
    limit = 96
    amount_usdt = 100        # 투자 금액 (USDT) - 실제 운영시 신중히 설정
    leverage = 5             # 레버리지 배율 - 실제 운영시 신중히 설정
    stop_loss_pct = 0.5      # 손절 비율 (%)
    take_profit_pct = 0.5    # 익절 비율 (%)
    ai_provider = 'claude'   # 사용할 AI ('claude' 또는 'gemini')
    trade_interval_seconds = 60 * 5 # 5분마다 확인 (예시)

    while True:
        print("-" * 30)
        current_time = pd.Timestamp.now(tz='UTC') # 시간대 정보 포함
        print(f"현재 시간: {current_time}")

        try:
            # 1. 기존 포지션 확인
            can_enter_new_position = trading_handler.check_and_manage_position(exchange, ui_symbol)

            if can_enter_new_position:
                print("새로운 포지션 진입 시도...")
                # 포지션 진입 전 미체결 주문 정리 (안전 장치)
                trading_handler.cancel_open_orders(exchange, ui_symbol)

                # 2. 차트 데이터 가져오기
                ohlcv_data = trading_handler.fetch_ohlcv(exchange, ui_symbol, timeframe, limit)

                if ohlcv_data is not None and not ohlcv_data.empty:
                    # 3. AI 투자 판단 요청
                    ai_decision = ai_handler.get_ai_decision(ohlcv_data, ai_provider=ai_provider)

                    if ai_decision in ['long', 'short']:
                        # 4. 거래 수량 계산
                        current_price = trading_handler.get_current_price(exchange, ui_symbol)
                        if current_price:
                            quantity = trading_handler.calculate_quantity(current_price, amount_usdt, ui_symbol)

                            if quantity and quantity > 0:
                                # 5. 실제 거래 실행 (진입 및 SL/TP 설정)
                                success, entry_price = trading_handler.execute_trade(
                                    exchange, ui_symbol, ai_decision, quantity, leverage,
                                    stop_loss_pct, take_profit_pct
                                )
                                if success:
                                    print(f"거래 성공! 진입가: {entry_price}")
                                else:
                                    print("거래 실행 실패.")
                            else:
                                print("거래 수량 계산 실패 또는 0 이하.")
                        else:
                            print("현재 가격 조회 실패.")

                    elif ai_decision == 'hold':
                        print("AI 판단: 보류 (Hold)")
                    else: # error 또는 예상치 못한 응답
                        print(f"AI 판단 오류 또는 유효하지 않음: {ai_decision}")
                else:
                    print("차트 데이터 가져오기 실패")
            else:
                # 기존 포지션이 있으므로 다음 루프까지 대기
                print("기존 포지션 유지 중. 다음 사이클 대기...")

        except ccxt.RateLimitExceeded as e:
            print(f"API 속도 제한 초과: {e} - 잠시 후 재시도합니다.")
            time.sleep(60) # 잠시 대기
        except ccxt.NetworkError as e:
            print(f"네트워크 오류: {e} - 잠시 후 재시도합니다.")
            time.sleep(30) # 잠시 대기
        except ccxt.ExchangeNotAvailable as e:
            print(f"거래소 점검 중?: {e} - 잠시 후 재시도합니다.")
            time.sleep(120) # 잠시 대기
        except Exception as e:
            print(f"메인 루프 오류 발생: {e}")
            # 기타 예상치 못한 오류 발생 시 잠시 대기 후 재시도
            time.sleep(60)

        # 지정된 간격만큼 대기
        wait_time = trade_interval_seconds
        print(f"{wait_time}초 후 다음 사이클 시작...")
        time.sleep(wait_time) 