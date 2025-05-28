const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  // 페이지 열기
  await page.goto('https://stexamplefork.streamlit.app', { waitUntil: 'networkidle2' });

  // 조금 기다렸다가 종료
  await new Promise(resolve => setTimeout(resolve, 60000));

  await browser.close();
})();
