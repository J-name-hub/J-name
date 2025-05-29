const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();   // 새 탭 열기
  await page.goto('https://testforcal.streamlit.app', { waitUntil: 'networkidle2' });   // 페이지 열기

  await browser.close();   // 브라우저 종료

})();
