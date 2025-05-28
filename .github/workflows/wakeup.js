// wakeup.js
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.goto('https://testforcal.streamlit.app', { waitUntil: 'networkidle2' });

  // "Yes, get this app back up!" 버튼 클릭
  try {
    const button = await page.$('button:contains("Yes, get this app back up!")');
    if (button) {
      await button.click();
      console.log('App wake-up button clicked.');
    } else {
      console.log('Wake-up button not found.');
    }
  } catch (err) {
    console.error('Error trying to click wake-up button:', err);
  }

  await browser.close();
})();
