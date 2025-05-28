const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();   // 새 탭 열기
  await page.goto('https://curricurri.streamlit.app', { waitUntil: 'networkidle2' });   // 페이지 열기

/*
  const buttons = await page.$$('button');
  let clicked = false;

  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.trim() === 'Yes, get this app back up!') {
      await btn.click();   // 텍스트 포함 버튼 클릭 완료
      await new Promise(resolve => setTimeout(resolve, 60000));   // 페이지에 60초 머무르기
      clicked = true;
      break;
    }
  }
*/

  const buttonTestId = isOwner ? "wakeup-button-owner" : "wakeup-button-viewer";
  const button = await page.$(`button[data-testid="${buttonTestId}"]`);
  let clicked = false;

  if (button) {
    await button.click();
    await new Promise(resolve => setTimeout(resolve, 60000));   // 페이지에 60초 머무르기
    clicked = true;
  }

  if (!clicked) {
    await new Promise(resolve => setTimeout(resolve, 1000));   // 페이지에 1초 머무르기
  }

  await browser.close();   // 브라우저 종료

})();
