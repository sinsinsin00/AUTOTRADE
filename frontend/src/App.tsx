import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

// FastAPI 백엔드에서 오는 데이터 타입과 일치하는 인터페이스 정의
interface Position {
  symbol: string;
  side: string;
  amount: number;
  entryPrice: number;
}

interface BotStatus {
  isRunning: boolean;
  lastUpdate: string | null; // 날짜/시간은 문자열로 받을 수 있음
  currentPosition: Position | null;
  recentLog: string;
}

function App() {
  // 봇 상태를 저장할 상태 변수
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false); // 로딩 상태 추가

  // 컴포넌트 마운트 시 백엔드에서 데이터 가져오기
  useEffect(() => {
    const fetchStatus = async () => {
      setError(null); // 이전 에러 초기화
      // setLoading(true); // 로딩 시작 - 필요시 사용
      try {
        // FastAPI 서버 주소 (포트 8000)
        const response = await fetch('http://127.0.0.1:8000/status');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: BotStatus = await response.json();
        setBotStatus(data);
        console.log("Fetched bot status:", data); // 콘솔에 데이터 출력 (확인용)
      } catch (e: any) {
        console.error("Error fetching bot status:", e);
        setError(`백엔드 API 호출 실패: ${e.message}. FastAPI 서버가 실행 중인지 확인하세요.`);
        setBotStatus(null); // 에러 시 상태 초기화
      }
      // setLoading(false); // 로딩 종료
    };

    fetchStatus(); // 처음 한 번 호출

    // 주기적으로 상태 업데이트 (예: 5초마다) - 필요시 주석 해제
    // const intervalId = setInterval(fetchStatus, 5000);
    // return () => clearInterval(intervalId); // 컴포넌트 언마운트 시 인터벌 정리

  }, []); // 빈 배열: 컴포넌트 마운트 시 한 번만 실행

  // 봇 시작 핸들러
  const handleStart = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/start', { method: 'POST' });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: BotStatus = await response.json();
      setBotStatus(data);
      console.log("Bot start command successful:", data);
    } catch (e: any) {
      console.error("Error starting bot:", e);
      setError(`봇 시작 실패: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 봇 중지 핸들러
  const handleStop = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/stop', { method: 'POST' });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: BotStatus = await response.json();
      setBotStatus(data);
      console.log("Bot stop command successful:", data);
    } catch (e: any) {
      console.error("Error stopping bot:", e);
      setError(`봇 중지 실패: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* 상단 바 영역 */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo-container">
            <a href="https://vitejs.dev" target="_blank">
              <img src={viteLogo} className="logo" alt="Vite logo" />
            </a>
            <a href="https://react.dev" target="_blank">
              <img src={reactLogo} className="logo react" alt="React logo" />
            </a>
          </div>
          <h1>AutoTrade Bot Dashboard</h1>
        </div>
        <nav className="header-nav"> {/* 상단 메뉴 영역 */} 
          <button>메뉴 1</button>
          <button>메뉴 2</button>
          <button>메뉴 3</button>
        </nav>
      </header>

      {/* 메인 컨텐츠 영역 (사이드바 + 메인 화면) */} 
      <div className="app-body">
        {/* 좌측 사이드바 */} 
        <aside className="sidebar">
          <nav className="sidebar-nav"> {/* 사이드바 네비게이션 */} 
            <button>사이드 메뉴 A</button>
            <button>사이드 메뉴 B</button>
            <button>사이드 메뉴 C</button>
          </nav>
        </aside>

        {/* 메인 화면: Bot Status + Bot Control */} 
        <main className="main-content">
          {/* Bot Status 카드 */} 
          <div className="card">
            <h2>Bot Status</h2>
            {/* 로딩/에러 표시는 메인 영역으로 옮기거나 유지 */}
            {/* {loading && <p>처리 중...</p>} */} 
            {error && <p style={{ color: 'red' }}>오류: {error}</p>} 
            {botStatus ? (
              <div>
                <p>실행 상태: {botStatus.isRunning ? '실행 중' : '중지됨'}</p>
                <p>마지막 업데이트: {botStatus.lastUpdate ? new Date(botStatus.lastUpdate).toLocaleString() : 'N/A'}</p>
                <p>최근 로그: {botStatus.recentLog}</p>
                {botStatus.currentPosition ? (
                  <div>
                    <h3>현재 포지션:</h3>
                    <p>종목: {botStatus.currentPosition.symbol}</p>
                    <p>방향: {botStatus.currentPosition.side}</p>
                    <p>수량: {botStatus.currentPosition.amount}</p>
                    <p>진입 가격: {botStatus.currentPosition.entryPrice}</p>
                  </div>
                ) : (
                  <p>현재 포지션 없음</p>
                )}
              </div>
            ) : (
              !error && <p>상태 정보를 불러오는 중...</p> 
            )}
          </div>

          {/* Bot Control 카드 */} 
          <div className="card">
            <h2>Bot Control</h2>
            {loading && <p>처리 중...</p>} {/* 로딩 표시를 메인으로 이동 */} 
            <button onClick={handleStart} disabled={loading || botStatus?.isRunning}>
              Start Bot
            </button>
            <button onClick={handleStop} disabled={loading || !botStatus?.isRunning} style={{ marginLeft: '10px' }}>
              Stop Bot
            </button>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
