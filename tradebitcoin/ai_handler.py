# ai_handler.py
import os
import anthropic
import google.generativeai as genai
import time # 임시 지연용

# API 키는 main.py에서 전달받거나 여기서 다시 로드할 수 있습니다.
# 여기서는 main에서 전달받는다고 가정하고 클라이언트 초기화 함수를 만듭니다.

claude_client = None
gemini_model = None

def initialize_ai_clients(claude_key, gemini_key):
    """AI 클라이언트를 초기화합니다."""
    global claude_client, gemini_model
    try:
        claude_client = anthropic.Anthropic(api_key=claude_key)
        print("Claude 클라이언트 초기화 성공.")
    except Exception as e:
        print(f"Claude 클라이언트 초기화 오류: {e}")

    try:
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel('gemini-pro') # 예시 모델, 필요시 변경
        print("Gemini 모델 초기화 성공.")
    except Exception as e:
        print(f"Gemini 모델 초기화 오류: {e}")

def get_ai_decision(data_df, ai_provider='claude'):
    """AI에게 데이터(DataFrame)를 제공하고 투자 판단 받기 (롱/숏)"""
    print(f"{ai_provider} 통해 투자 판단 요청 중...")

    # 데이터를 AI가 이해할 수 있는 형태로 변환 (예: JSON 문자열)
    # 데이터 양이 많을 경우 요약하거나 필요한 부분만 추출하는 것이 좋습니다.
    try:
        # DataFrame을 JSON 문자열로 변환 (레코드 방향)
        data_json = data_df.to_json(orient='records', date_format='iso')
        # 데이터가 너무 길 경우 일부만 사용하거나 요약 필요
        max_input_length = 10000 # 예시: 최대 입력 길이 제한 (토큰 수 고려 필요)
        if len(data_json) > max_input_length:
            print(f"데이터가 너무 길어 최근 {max_input_length}자만 사용합니다.")
            data_json = data_json[-max_input_length:]

        prompt = f"""
당신은 암호화폐 트레이딩 전문가입니다. 다음은 최근 비트코인(BTC/USDT) 15분봉 데이터입니다:
{data_json}

이 데이터를 분석하여 다음 포지션을 'long' 또는 'short' 중 하나로 결정해주세요.
다른 설명 없이 오직 'long' 또는 'short' 단어만 응답해주세요.
"""

        if ai_provider == 'claude' and claude_client:
            # TODO: Claude API 호출 구현
            message = claude_client.messages.create(
                model="claude-3-opus-20240229", # 또는 다른 Claude 모델
                max_tokens=10,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            decision = message.content[0].text.strip().lower()
            print(f"Claude 응답: {decision}")

        elif ai_provider == 'gemini' and gemini_model:
            # TODO: Gemini API 호출 구현
            response = gemini_model.generate_content(prompt)
            decision = response.text.strip().lower()
            print(f"Gemini 응답: {decision}")

        else:
            print(f"지원하지 않거나 초기화되지 않은 AI 제공자: {ai_provider}")
            return "error" # 또는 None

        # 응답 유효성 검사
        if decision in ['long', 'short']:
            print(f"AI 판단 결과: {decision}")
            return decision
        else:
            print(f"AI 응답이 유효하지 않음: {decision}")
            return "hold" # 유효하지 않으면 보류

    except Exception as e:
        print(f"{ai_provider} API 호출 중 오류 발생: {e}")
        return "error"

    # # 임시 반환값 (실제 API 호출 구현 전)
    # time.sleep(1)
    # temp_decision = "long"
    # print(f"AI 판단 결과 (임시): {temp_decision}")
    # return temp_decision 