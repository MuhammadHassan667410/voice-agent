import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));

  await page.goto('http://127.0.0.1:8081/vapi.html');
  await new Promise(r => setTimeout(r, 2000));

  const vapi = await page.evaluate(() => {
    return {
      type: typeof window.Vapi,
      keys: window.Vapi ? Object.keys(window.Vapi) : null,
      isConstructor: typeof window.Vapi === 'function',
      defaultExport: window.Vapi && window.Vapi.default ? typeof window.Vapi.default : null
    };
  });
  console.log('EVAL result:', vapi);

  await browser.close();
})();
