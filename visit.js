const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new', // 최신 모드로 headless
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.goto('https://yeongjongdonakreomap.streamlit.app', { waitUntil: 'networkidle2' });

  console.log('✅ Visited Streamlit app as a browser!');
  await browser.close();
})();
