# 경로: streamlit_keep_alive.js
const puppeteer = require('puppeteer');

// ========== 설정 상수 ==========
const STREAMLIT_URLS = [
  'https://calendarforpar.streamlit.app'
  // 추가 URL이 있으면 여기에 추가
  // 'https://another-app.streamlit.app'
];
const WAIT_TIME = 60000; // 60초 (버튼 클릭 후 앱이 완전히 깨어날 때까지 대기)
const WAKEUP_BUTTON_TEST_ID = 'wakeup-button-viewer'; // Streamlit wake-up 버튼의 data-testid
const WAKEUP_BUTTON_TEXT = 'Yes, get this app back up!'; // wake-up 버튼의 텍스트

/**
 * Streamlit 앱들을 깨우는 메인 함수
 * - 각 URL을 순차적으로 방문하여 wake-up 버튼 클릭
 * - 성공 시 WAIT_TIME만큼 대기하여 앱이 완전히 활성화되도록 함
 */
async function wakeUpStreamlitApp() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    for (const url of STREAMLIT_URLS) {
      console.log(`🚀 Visiting: ${url}`);
      
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'networkidle2' });

      const clicked = await clickWakeUpButton(page);
      
      if (clicked) {
        console.log(`✅ Wake-up button clicked successfully for: ${url}`);
        await new Promise(resolve => setTimeout(resolve, WAIT_TIME));
      } else {
        console.log(`❌ Wake-up button not found for: ${url}`);
      }
      
      await page.close();
    }
  } finally {
    await browser.close();
  }
}

/**
 * Streamlit의 wake-up 버튼을 찾아서 클릭하는 함수
 * 2가지 방법으로 버튼을 찾음:
 * 1. data-testid 속성으로 찾기 (우선순위 높음)
 * 2. 버튼 텍스트로 찾기 (fallback)
 */
async function clickWakeUpButton(page) {
  // 1차 시도: data-testid로 버튼 찾기
  const buttonByTestId = await page.$(`button[data-testid="${WAKEUP_BUTTON_TEST_ID}"]`);
  if (buttonByTestId) {
    await buttonByTestId.click();
    return true;
  }

  // 2차 시도: 텍스트로 버튼 찾기
  const allButtons = await page.$('button');
  for (const button of allButtons) {
    const text = await page.evaluate(el => el.textContent, button);
    if (text.trim() === WAKEUP_BUTTON_TEXT) {
      await button.click();
      return true;
    }
  }

  return false;
}

// ========== 스크립트 실행 ==========
// 메인 함수 실행 및 에러 처리
wakeUpStreamlitApp().catch(console.error);
