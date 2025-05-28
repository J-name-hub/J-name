const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  // 페이지 열기
  await page.goto('https://stexamplefork.streamlit.app', { waitUntil: 'networkidle2' });

  // 버튼 텍스트로 버튼 찾기
  const buttonSelector = 'button'; // 일단 button 태그로 지정

  // 모든 버튼 중에서 텍스트가 정확히 일치하는 버튼 클릭
  const buttons = await page.$$(buttonSelector);
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.trim() === 'Yes, get this app back up!') {
      await btn.click();
      console.log('✅ 버튼 클릭 완료!');
      break;
    }
  }

  // 조금 기다렸다가 종료 (필요 시)
  await page.waitForTimeout(60000);

  await browser.close();
})();
