
    const { chromium } = require('playwright');
    (async () => {
      const browser = await chromium.launch();
      const page = await browser.newPage();
      try {
        console.log("Navigating...");
        await page.goto('https://www.newera.bio/', { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(3000); 
        await page.screenshot({ path: 'C:/users/StevenDesk/clawd/workspace/deep-research-saas/backend/workspace/research_output/www.newera.bio__1772013773.png', fullPage: false }); 
        
        const content = await page.innerText('body');
        console.log("__CONTENT_START__");
        console.log(content);
        console.log("__CONTENT_END__");
      } catch (e) {
        console.error(e);
      } finally {
        await browser.close();
      }
    })();
    