const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const { spawn } = require('node:child_process');
const { mkdir, writeFile, readFile } = require('node:fs/promises');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const url = process.env.CV_BASE_URL || 'http://127.0.0.1:4173/';
const widths = [360, 390, 768, 1024, 1440];
const sections = ['about', 'expertise', 'experience', 'projects', 'education', 'contact'];
(async () => {
  const server = process.env.CV_BASE_URL ? null : spawn('python3', ['-m', 'http.server', '4173', '--bind', '127.0.0.1', '--directory', path.join(root, 'site')], { stdio: 'ignore' });
  let browser;
  const report = [];
  try {
    let ready = false;
    for (let i = 0; i < 60; i++) {
      try { if ((await fetch(url)).ok) { ready = true; break; } } catch {}
      await new Promise(resolve => setTimeout(resolve, 250));
    }
    assert(ready, 'Site failed to start');
    browser = await chromium.launch();
    await mkdir(path.join(root, 'qa'), { recursive: true });
    for (const width of widths) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
      const page = await context.newPage();
      const errors = [];
      const failed = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('response', response => { if (response.status() >= 400) failed.push(response.status() + ' ' + response.url()); });
      assert.equal((await page.goto(url)).status(), 200);
      await page.evaluate(() => document.fonts.ready);
      await page.getByRole('heading', { name: 'Vadym Pyrozhenko', exact: true }).waitFor();
      assert(await page.locator('.site-header a[download]').isVisible(), 'Header PDF download');
      assert(await page.locator('.professional-title').isVisible());
      assert.equal(await page.locator('.experience-entry').count(), 7);
      assert.equal(await page.locator('.expertise-card').count(), 7);
      await page.screenshot({path:path.join(root,'qa',`initial-${width}.png`),fullPage:true});
      const layout = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth, clipped: [...document.querySelectorAll('main h1,main h2,main h3,main p,main li,main a,main dd')].filter(el => {
        const box=el.getBoundingClientRect(); const style=getComputedStyle(el);
        return box.width > 0 && style.visibility !== 'hidden' && (box.right > innerWidth + 1 || box.left < -1);
      }).map(el=>el.textContent.slice(0,80)) }));
      assert(layout.scroll <= width + 1, `Horizontal overflow at ${width}: ${layout.scroll}`);
      assert.deepEqual(layout.clipped, [], `Offscreen text at ${width}`);
      if (width < 768) {
        const toggle=page.locator('.menu-toggle');
        await toggle.click();
        assert.equal(await toggle.getAttribute('aria-expanded'),'true');
        assert(await page.locator('#mobile-navigation').isVisible());
        await page.keyboard.press('Escape');
        assert.equal(await toggle.getAttribute('aria-expanded'),'false');
        assert(await toggle.evaluate(el=>el===document.activeElement));
        for (const id of sections) {
          await toggle.click();
          await page.locator(`#mobile-navigation a[href="#${id}"]`).click();
          await page.waitForFunction(hash => location.hash === hash, '#' + id);
          assert.equal(await toggle.getAttribute('aria-expanded'),'false');
        }
      } else {
        for (const id of sections) {
          await page.locator(`.desktop-nav a[href="#${id}"]`).click();
          await page.waitForFunction(hash => location.hash === hash, '#' + id);
        }
      }
      await page.goto(url+'#about');
      await page.locator('#about').waitFor();
      await page.waitForTimeout(400);
      const bounds = await page.locator('#about').boundingBox();
      const header = await page.locator('.site-header').boundingBox();
      assert(bounds.y >= header.height - 2, `Sticky header overlaps #about at ${width}`);
      const pdf = await context.request.get(new URL('Vadym_Pyrozhenko_CV.pdf', url).href);
      assert.equal(pdf.status(),200);
      assert((await pdf.body()).subarray(0,5).toString()==='%PDF-');
      const a11y=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      assert.deepEqual(a11y.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[], `Accessibility at ${width}`);
      await page.goto(url);
      await page.evaluate(() => document.fonts.ready);
      // Trigger presentation effects before recording the complete page.
      await page.evaluate(async () => { document.documentElement.style.scrollBehavior='auto'; for (let y=0;y<document.body.scrollHeight;y+=700) { scrollTo(0,y); await new Promise(r=>setTimeout(r,25)); } scrollTo(0,0); });
      await page.waitForTimeout(500);
      if (width >= 768) assert.equal(await page.locator('.desktop-nav a[aria-current]').count(), 0, 'Navigation state resets at the profile');
      await page.screenshot({path:path.join(root,'qa',`cv-${width}.png`),fullPage:true});
      await page.screenshot({path:path.join(root,'qa',`hero-${width}.png`)});
      assert.deepEqual(errors,[],`JavaScript errors at ${width}`);
      assert.deepEqual(failed,[],`HTTP errors at ${width}`);
      report.push({width,horizontalOverflow:false,navigation:'passed',pdf:'passed',accessibility:'passed',javascript:'passed'});
      await context.close();
    }
    const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
    await page.goto(url);
    assert.equal(await page.locator('.portrait-orbit').evaluate(el=>getComputedStyle(el).animationName),'none');
    await page.getByRole('button',{name:'Open navigation menu'}).click();
    await page.screenshot({path:path.join(root,'qa','mobile-menu.png')});
    // The complete CV must also remain readable when JavaScript is disabled.
    const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
    const plain=await nojs.newPage();await plain.goto(url+'#experience');
    assert.equal(await plain.locator('.experience-entry').count(),7);
    assert(await plain.locator('#experience').isVisible());
    await nojs.close();
    await writeFile(path.join(root,'qa','browser-report.json'),JSON.stringify({viewports:report,reducedMotion:'passed',noJavaScriptContent:'passed'},null,2));
    console.log(JSON.stringify(report,null,2));
  } finally {
    if(browser) await browser.close();
    if(server) server.kill('SIGTERM');
  }
})().catch(error=>{ console.error(error); process.exitCode=1; });
