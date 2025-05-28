const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();   // 새 탭 열기
  await page.goto('https://whatsdifferent.streamlit.app', { waitUntil: 'networkidle2' });   // 페이지 열기

  let clicked = false;

  // 버튼 찾기
  // 1번 버튼명 기반 data-testid="wakeup-button-viewer"
  const button = await page.$('button[data-testid="wakeup-button-viewer"]');
  if (button) {
    await button.click();
    clicked = true;
  } else {
    // 2번 텍스트 기반 fallback: ('Yes, get this app back up!')
    const buttons = await page.$$('button');
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text.trim() === 'Yes, get this app back up!') {
        await btn.click();
        clicked = true;
        break;
      }
    }
  }

  // 클릭 성공 시 60초 대기, 실패 시 1초 대기
  if (clicked) {
    await new Promise(resolve => setTimeout(resolve, 60000));
  } else {
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  await browser.close();   // 브라우저 종료

})();
