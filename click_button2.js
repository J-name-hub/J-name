const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.goto('https://mymeal.streamlit.app', { waitUntil: 'domcontentloaded' });

  let clicked = false;

  // 1번: data-testid 기반 버튼 클릭 시도
  const button = await page.$('button[data-testid="wakeup-button-viewer"]');
  if (button) {
    await button.click();
    clicked = true;
  } else {
    // 2번: 텍스트 기반 버튼 찾기 (fallback)
    await page.waitForSelector('button', { timeout: 10000 }); // 버튼이 로드되길 최대 10초 대기
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
  await new Promise(resolve => setTimeout(resolve, clicked ? 60000 : 1000));

  await browser.close();
})();
