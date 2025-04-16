# trading_handler.py
import ccxt
import pandas as pd
import time
import math

def fetch_ohlcv(exchange, symbol='BTC/USDT:USDT', timeframe='15m', limit=96):
    """바이낸스에서 OHLCV 데이터 가져오기"""
    print(f"{symbol} {timeframe} 봉 데이터 가져오는 중...")
    try:
        # ccxt는 선물 심볼에서 ':USDT' 부분을 자동으로 처리할 수 있음 (확인 필요)
        # 만약 문제가 발생하면 symbol='BTC/USDT' 로 시도
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not ohlcv:
            print("데이터를 가져오지 못했습니다.")
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        print(f"데이터 가져오기 완료 (최근 {len(df)}개 봉)")
        # print(df.tail()) # 마지막 5개 데이터 출력 (확인용)
        return df
    except ccxt.NetworkError as e:
        print(f"네트워크 오류: {e}")
    except ccxt.ExchangeError as e:
        print(f"거래소 오류: {e}")
    except Exception as e:
        print(f"OHLCV 데이터 가져오기 중 예상치 못한 오류: {e}")
    return None

def get_current_price(exchange, symbol='BTC/USDT:USDT'):
    """현재가 가져오기"""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"현재가 가져오기 오류: {e}")
        return None

def calculate_quantity(current_price, amount_usdt, symbol='BTC/USDT:USDT'):
    """USDT 금액에 해당하는 비트코인 수량 계산 (최소 주문 단위 고려)"""
    if current_price is None or current_price <= 0:
        return None
    # TODO: 거래소에서 최소 주문 수량 및 소수점 자리수 정보 가져오기 (fetchMarkets 사용)
    # 임시로 소수점 3자리에서 반올림
    quantity = amount_usdt / current_price
    precision = 3 # 임시 정밀도
    step_size = 1 / math.pow(10, precision)
    rounded_quantity = math.floor(quantity / step_size) * step_size
    print(f"{amount_usdt} USDT는 약 {rounded_quantity:.{precision}f} BTC에 해당 (현재가: {current_price})")
    # TODO: 최소 주문 금액 확인 로직 추가 (예: 5 USDT 이상)
    if rounded_quantity * current_price < 5: # 바이낸스 최소 주문 금액 예시
        print("계산된 수량이 최소 주문 금액보다 작습니다.")
        return None
    return rounded_quantity


def execute_trade(exchange, symbol, decision, quantity, leverage=5, stop_loss_pct=0.5, take_profit_pct=0.5):
    """AI 판단에 따라 선물 거래 실행 및 SL/TP 설정"""
    print(f"{symbol} {decision} 주문 실행 중 (수량: {quantity}, 레버리지: {leverage}x)...")
    side = 'buy' if decision == 'long' else 'sell'
    order_type = 'market' # 시장가 주문

    try:
        # 0. 레버리지 설정 (매번 할 필요는 없을 수 있으나, 확인차원에서 실행)
        print(f"레버리지 {leverage}x 설정 시도...")
        exchange.set_leverage(leverage, symbol)
        print("레버리지 설정 완료.")

        # 1. 포지션 진입 주문 (시장가)
        print(f"{side.upper()} {order_type} 주문 실행...")
        order = exchange.create_order(symbol, order_type, side, quantity)
        print(f"주문 성공: {order['id']}")
        entry_price = order.get('average') or order.get('price') or get_current_price(exchange, symbol) # 진입 가격 확인
        if entry_price is None:
            print("진입 가격을 확인할 수 없어 SL/TP 설정 불가.")
            return False, None # 주문은 성공했을 수 있으나 가격 확인 실패

        print(f"진입 가격: {entry_price}")

        # 2. 스탑로스(SL) / 테이크프로핏(TP) 주문 설정
        print("스탑로스 / 테이크프로핏 주문 설정 중...")
        sl_price = 0
        tp_price = 0

        # 가격 계산 (소수점 처리 필요 - fetchMarkets 정보 활용)
        # TODO: 정확한 가격 계산을 위해 tick size 등 market 정보 활용
        price_precision = 2 # 예시: 가격 소수점 2자리

        if decision == 'long':
            sl_price = round(entry_price * (1 - stop_loss_pct / 100), price_precision)
            tp_price = round(entry_price * (1 + take_profit_pct / 100), price_precision)
            sl_side = 'sell'
            tp_side = 'sell'
        else: # short
            sl_price = round(entry_price * (1 + stop_loss_pct / 100), price_precision)
            tp_price = round(entry_price * (1 - take_profit_pct / 100), price_precision)
            sl_side = 'buy'
            tp_side = 'buy'

        print(f"SL 가격: {sl_price}, TP 가격: {tp_price}")

        # 스탑 마켓 주문 (손절)
        sl_params = {'stopPrice': sl_price, 'reduceOnly': True}
        sl_order = exchange.create_order(symbol, 'stop_market', sl_side, quantity, params=sl_params)
        print(f"스탑로스 주문 성공: {sl_order['id']}")

        # 테이크 프로핏 마켓 주문 (익절)
        tp_params = {'stopPrice': tp_price, 'reduceOnly': True}
        tp_order = exchange.create_order(symbol, 'take_profit_market', tp_side, quantity, params=tp_params)
        print(f"테이크프로핏 주문 성공: {tp_order['id']}")

        print("주문 및 SL/TP 설정 완료.")
        return True, entry_price # 성공 여부와 진입 가격 반환

    except ccxt.InsufficientFunds as e:
        print(f"오류: 잔액 부족 - {e}")
    except ccxt.ExchangeError as e:
        print(f"거래소 오류 발생: {e}")
    except Exception as e:
        print(f"주문 실행 중 예상치 못한 오류: {e}")

    return False, None # 실패 시


def check_and_manage_position(exchange, symbol):
    """현재 포지션 확인 및 관리 (포지션 없으면 True 반환)"""
    print(f"{symbol} 포지션 확인 중...")
    try:
        positions = exchange.fetch_positions([symbol])
        # fetch_positions는 리스트를 반환하므로, 특정 심볼에 대한 포지션 필터링
        position = next((p for p in positions if p['symbol'] == symbol and p.get('contracts', 0) != 0), None)

        if position:
            # 포지션 정보 출력 (옵션)
            contracts = position.get('contracts')
            entry_price = position.get('entryPrice')
            side = position.get('side')
            pnl = position.get('unrealizedPnl')
            print(f"현재 포지션: {side} / 수량: {contracts} / 진입가: {entry_price} / 미실현 손익: {pnl}")
            return False # 포지션 있음 (새 진입 불가)
        else:
            print("현재 열린 포지션 없음.")
            return True # 포지션 없음 (새 진입 가능)

    except Exception as e:
        print(f"포지션 확인 중 오류 발생: {e}")
        return False # 오류 발생 시 안전하게 새 진입 막기

def cancel_open_orders(exchange, symbol):
    """특정 심볼의 모든 미체결 주문 취소"""
    print(f"{symbol} 미체결 주문 확인 및 취소 중...")
    try:
        # 주의: cancel_all_orders 가 선물에서 모든 심볼을 취소할 수 있음. 특정 심볼만 지원하는지 확인 필요.
        # fetch_open_orders 로 가져와서 하나씩 취소하는 것이 더 안전할 수 있음.
        # 여기서는 우선 cancel_all_orders 사용 (ccxt 문서 확인 필요)
        result = exchange.cancel_all_orders(symbol)
        print("미체결 주문 정리 완료.")
        # print(result) # 취소 결과 출력 (옵션)
        return True
    except Exception as e:
        print(f"미체결 주문 취소 중 오류 발생: {e}")
        return False 