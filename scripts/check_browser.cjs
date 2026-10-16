const engines = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const { spawn } = require('node:child_process');
const { mkdir, writeFile } = require('node:fs/promises');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const url = process.env.CV_BASE_URL || 'http://127.0.0.1:4173/';
const engine = process.env.CV_BROWSER || 'chromium';
assert(['chromium','firefox','webkit'].includes(engine), 'Unsupported test browser');
const viewports = [
  {width:320,height:568}, {width:360,height:800}, {width:390,height:844},
  {width:430,height:932}, {width:600,height:900}, {width:767,height:900},
  {width:768,height:1024}, {width:844,height:390}, {width:1024,height:768},
  {width:1280,height:720}, {width:1440,height:900}, {width:1920,height:1080},
  {width:2560,height:1440}
];
const profile = require('../data/profile.json');
const sections = ['about', 'expertise', 'experience', 'education', 'contact'];
async function checkLayout(page, label) {
  const layout = await page.evaluate(() => {
    const problems=[];
    for (const el of document.querySelectorAll('main h1,main h2,main h3,main p,main li,main a,main dd,header a,header button')) {
      const box=el.getBoundingClientRect();const style=getComputedStyle(el);
      if(!box.width || !box.height || style.visibility==='hidden' || style.display==='none') continue;
      if(box.right > innerWidth+1 || box.left < -1) problems.push('offscreen: '+el.textContent.trim().slice(0,80));
      if(el.clientWidth && el.scrollWidth > el.clientWidth+1) problems.push('text overflow: '+el.textContent.trim().slice(0,80));
      if(['hidden','clip'].includes(style.overflowY) && el.clientHeight && el.scrollHeight>el.clientHeight+1) problems.push('vertical clipping: '+el.textContent.trim().slice(0,80));
    }
    return {width:innerWidth,scroll:document.documentElement.scrollWidth,problems};
  });
  assert(layout.scroll<=layout.width+1,`${label}: horizontal overflow (${layout.scroll})`);
  assert.deepEqual(layout.problems,[],`${label}: clipped or overflowing content`);
}
(async () => {
  const server=process.env.CV_BASE_URL ? null : spawn('python3',['-m','http.server','4173','--bind','127.0.0.1','--directory',path.join(root,'site')],{stdio:'ignore'});
  let browser;
  const report={browser:engine,viewports:[],fluidWidths:[]};
  try {
    let ready=false;
    for(let i=0;i<60;i++) {
      try {if((await fetch(url)).ok){ready=true;break;}}catch{}
      await new Promise(r=>setTimeout(r,250));
    }
    assert(ready,'Site failed to start');
    browser=await engines[engine].launch();
    await mkdir(path.join(root,'qa'),{recursive:true});
    for(const viewport of viewports) {
      const {width,height}=viewport;const label=`${engine} ${width}x${height}`;
      const context=await browser.newContext({viewport,deviceScaleFactor:width<768?2:1,hasTouch:width<768,isMobile:width<768&&engine!=='firefox',acceptDownloads:true,reducedMotion:'reduce'});
      const page=await context.newPage();page.setDefaultTimeout(15000);
      const errors=[];const failed=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('response',r=>{if(r.status()>=400) failed.push(`${r.status()} ${r.url()}`);});
      assert.equal((await page.goto(url)).status(),200);
      await page.evaluate(()=>document.fonts.ready);
      await page.getByRole('heading',{name:'Vadym Pyrozhenko',exact:true}).waitFor();
      assert.equal(await page.locator('.professional-title').innerText(),'Cloud Infrastructure & DevOps Professional');
      assert(!/Moldova|\bLocation\b|Senior DevOps|Infrastructure Operations \| Technical Leadership \| Cloud & Platform Engineering/i.test(await page.locator('body').innerText()),'Removed profile claims must stay absent');
      assert.equal(await page.locator('.experience-entry').count(),7);
      assert.equal(await page.locator('#projects').count(),0,'Selected work removed');
      assert(!/\bECTS\b/.test(await page.locator('body').innerText()));
      assert.equal(await page.locator('.career-card').count(),7);
      const logos=page.locator('.company-logo');
      assert.equal(await logos.count(),profile.roles.length);
      for(let i=0;i<profile.roles.length;i++) {
        const logo=logos.nth(i);await logo.scrollIntoViewIfNeeded();
        await page.waitForFunction(img=>img.complete && img.naturalWidth>0,await logo.elementHandle());
        await logo.evaluate(img=>img.decode());
        assert.equal(await logo.getAttribute('src'),profile.roles[i].logo);
        const dimensions=await logo.evaluate(img=>({natural:img.naturalWidth,fit:getComputedStyle(img).objectFit,width:img.getBoundingClientRect().width}));
        assert(dimensions.natural>0 && dimensions.width>0,'Employer logo loaded');
        assert.equal(dimensions.fit,'contain','Employer logo keeps its aspect ratio');
      }
      assert(await page.locator('.career-card').first().getAttribute('open') !== null);
      for (let index=0;index<profile.roles.length;index++) {
        const card=page.locator('.career-card').nth(index);
        if (index>0) await card.locator('summary').click();
        assert.equal(await card.locator('.responsibilities li').count(),profile.roles[index].responsibilities.length);
        assert.deepEqual(await card.locator('.responsibilities li').allTextContents(),profile.roles[index].responsibilities);
        await checkLayout(page,label+' expanded role '+index);
        if (index>0) await card.locator('summary').click();
      }
      assert(await page.locator('.career-card').nth(1).innerText().then(text=>text.includes('Hetzner Cloud')));

      assert.equal(await page.locator('.expertise-card').count(),profile.skills.length);
      assert.equal(await page.locator('.about-step').count(),profile.about.length,'Structured professional overview');
      assert.deepEqual(await page.locator('.about-step').evaluateAll(steps=>steps.map(step=>[...step.querySelectorAll('p')].map(p=>p.textContent).join('\n\n'))),profile.about,'Professional overview content preserved');
      assert.equal(await page.locator('.overview-fact').count(),4);
      assert.equal(await page.locator('.education-entry').count(),profile.education.length,'Every qualification visible');
      assert.deepEqual(await page.locator('.degree-field').allTextContents(),profile.education.map(degree=>degree.field));
      assert.deepEqual(await page.locator('.degree-institution').allTextContents(),profile.education.map(degree=>degree.institution));
      assert.deepEqual(await page.locator('.language-level').allTextContents(),profile.languages.map(language=>language.level));
      const portrait=await page.locator('.portrait-wrap img').evaluate(img=>{
        const box=img.getBoundingClientRect();return {width:box.width,height:box.height,natural:img.naturalWidth,fit:getComputedStyle(img).objectFit};
      });
      assert(Math.abs(portrait.width-portrait.height)<1,'Portrait remains square');
      assert(portrait.width<=portrait.natural+1,'Portrait CSS size does not exceed source resolution');
      assert.equal(portrait.fit,'cover');
      if([390,1440].includes(width)) {
        for(const section of ['about','experience','education'])await page.locator('#'+section).screenshot({scale:'css',path:path.join(root,'qa',`${engine}-${section}-${width}.png`),style:'.site-header,.skip-link{visibility:hidden!important}'});
      }

      assert.equal(await page.locator('.proficiency-card').count(),profile.skills.length);
      assert.deepEqual(await page.locator('.skill-name').allTextContents(),profile.skills.flatMap(skill=>skill.items.map(item=>item.name)),'Matrix preserves reference technologies');
      assert.deepEqual(await page.locator('.skill-level').allTextContents(),profile.skills.flatMap(skill=>skill.items.map(item=>item.level)),'Matrix preserves self-assessed reference levels');
      assert.equal(await page.locator('.legend-item').count(),4);
      assert.equal(await page.locator('.identity-card a[href="tel:'+profile.contact.tel+'"]').count(),1,'Primary phone in business card');
      assert.equal(await page.locator('.phone-contact .primary-phone').getAttribute('href'),'tel:'+profile.contact.tel);
      assert.equal(await page.locator('.phone-contact a').filter({hasText:'WhatsApp'}).getAttribute('href'),profile.contact.whatsapp);
      assert.equal(await page.locator('.phone-contact a').filter({hasText:'Viber'}).getAttribute('href'),profile.contact.viber);
      if([390,1440].includes(width))await page.locator('#expertise').screenshot({scale:'css',path:path.join(root,'qa',`${engine}-matrix-${width}.png`),style:'.site-header,.skip-link{visibility:hidden!important}'});

      assert(await page.evaluate(()=>[...document.images].every(img=>img.complete&&img.naturalWidth>0)),'Images load');
      assert(await page.evaluate(()=>document.fonts.check('16px Inter')),'Self-hosted font loads');
      await checkLayout(page,label);
      const cv=page.locator('.site-header a[download]');
      assert(await cv.isVisible(),'Header download accessible');
      assert((await cv.boundingBox()).height>=44,'Download touch target');
      if(width<768) {
        const toggle=page.locator('.menu-toggle');assert((await toggle.boundingBox()).height>=44);
        await toggle.click();assert.equal(await toggle.getAttribute('aria-expanded'),'true');
        assert(await page.locator('#mobile-navigation').isVisible());
        await checkLayout(page,label+' menu open');
        await page.keyboard.press('Escape');
        assert.equal(await toggle.getAttribute('aria-expanded'),'false');
        assert(await toggle.evaluate(el=>el===document.activeElement),'Escape restores focus');
        for(const id of sections) {
          await toggle.click();await page.locator(`#mobile-navigation a[href="#${id}"]`).click();
          await page.waitForFunction(hash=>location.hash===hash,'#'+id);
          assert.equal(await toggle.getAttribute('aria-expanded'),'false');
        }
      } else {
        for(const id of sections) {
          await page.locator(`.desktop-nav a[href="#${id}"]`).click();
          await page.waitForFunction(hash=>location.hash===hash,'#'+id);
        }
      }
      for(const id of ['about','experience','education','contact']) {
        await page.goto(url+'#'+id);
        await page.waitForFunction(section=>{
          const target=document.getElementById(section).getBoundingClientRect();
          const header=document.querySelector('.site-header').getBoundingClientRect();
          return target.top>=header.bottom-2 && target.top<innerHeight;
        },id);
        assert(await cv.isVisible(),'Download remains accessible when scrolled');
        await checkLayout(page,label+' #'+id);
      }
      const downloadEvent=page.waitForEvent('download');await cv.click();const download=await downloadEvent;
      assert.equal(download.suggestedFilename(),'Vadym_Pyrozhenko_CV.pdf');
      assert.equal(await download.failure(),null,'PDF download completes');
      const pdf=await context.request.get(new URL('Vadym_Pyrozhenko_CV.pdf',url).href);
      assert.equal(pdf.status(),200);assert((await pdf.body()).subarray(0,5).toString()==='%PDF-');
      const accessibility=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      assert.deepEqual(accessibility.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],label+' accessibility');
      await page.goto(url);await page.evaluate(()=>document.fonts.ready);
      await page.waitForTimeout(100);
      if(width>=768)assert.equal(await page.locator('.desktop-nav a[aria-current]').count(),0,'Profile navigation state');
      await page.screenshot({scale:'css',path:path.join(root,'qa',`${engine}-hero-${width}x${height}.png`)});
      if([320,390,768,1440,2560].includes(width))await page.screenshot({scale:'css',path:path.join(root,'qa',`${engine}-full-${width}.png`),fullPage:true});
      assert.deepEqual(errors,[],label+' JavaScript errors');assert.deepEqual(failed,[],label+' HTTP errors');
      report.viewports.push({width,height,layout:'passed',navigation:'passed',pdfDownload:'passed',accessibility:'passed',javascript:'passed'});
      await context.close();
    }
    // Sweep intermediate widths and both sides of every CSS breakpoint.
    // Resize an open mobile menu to desktop and back to verify responsive state.
    const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
    await page.goto(url);await page.evaluate(()=>document.fonts.ready);
    await page.locator('.menu-toggle').click();
    await page.screenshot({scale:'css',path:path.join(root,'qa',`${engine}-mobile-menu.png`)});
    await page.setViewportSize({width:1024,height:768});
    await page.waitForFunction(()=>document.querySelector('#mobile-navigation').hidden);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.locator('.menu-toggle').getAttribute('aria-expanded'),'false');
    const widths=[...new Set([320,360,375,390,430,600,638,639,640,641,699,700,701,766,767,768,769,899,900,901,979,980,981,1023,1024,1025,1159,1160,1161,1199,1200,1201,1279,1280,1281,1349,1350,1351,1440,1920,2560,...Array.from({length:71},(_,i)=>320+i*32)])].sort((a,b)=>a-b);
    for(const width of widths) {
      await page.setViewportSize({width,height:width<768?844:900});
      await checkLayout(page,`${engine} fluid width ${width}`);
      report.fluidWidths.push(width);
    }
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.locator('.portrait-orbit').evaluate(el=>getComputedStyle(el).animationName),'none');
    const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844},reducedMotion:'reduce'});
    const plain=await nojs.newPage();await plain.goto(url+'#experience');
    assert.equal(await plain.locator('.experience-entry').count(),7);assert(await plain.locator('#experience').isVisible());
    await plain.locator('.career-card').nth(1).locator('summary').focus();
    await plain.keyboard.press('Enter');
    assert(await plain.locator('.career-card').nth(1).locator('.responsibilities').isVisible(),'Native disclosure works without JavaScript');
    assert.equal(await page.locator('.arrival-scene').count(),0,'No arrival animation with reduced motion');
    const animated=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'no-preference'});
    const arrival=await animated.newPage();await arrival.goto(url);
    await arrival.getByRole('heading',{name:'Vadym Pyrozhenko',exact:true}).waitFor();
    await arrival.locator('.hero-actions a[href="#contact"]').click();
    await arrival.waitForFunction(()=>location.hash==='#contact');
    await arrival.waitForFunction(()=>!document.querySelector('.arrival-scene'));
    await arrival.goto(url+'#experience');
    assert.equal(await arrival.locator('.arrival-scene').count(),0,'Direct anchors skip arrival');
    await animated.close();report.arrivalAnimation='passed';
    await nojs.close();report.reducedMotion='passed';report.menuResize='passed';report.noJavaScriptContent='passed';
    await writeFile(path.join(root,'qa',`${engine}-report.json`),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report,null,2));
  } finally {
    if(browser)await browser.close();if(server)server.kill('SIGTERM');
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
