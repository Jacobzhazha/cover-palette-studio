#!/usr/bin/env node
// 将 cover_studio.py render 生成的 HTML 批量无损导出为标准像素 PNG
// 用法：node scripts/export_png.mjs <输出目录> [--chrome]
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const targetDir = path.resolve(process.argv[2] || './cover-out');
const manifestPath = path.join(targetDir, 'manifest.json');
const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));

// Resolve Playwright from the checkout or an explicitly supplied module.
const modulePath = process.env.PLAYWRIGHT_MODULE;
let chromium;
try {
  ({chromium} = await import(modulePath ? pathToFileURL(path.resolve(modulePath)).href : 'playwright'));
} catch (error) {
  if (error.code !== 'ERR_MODULE_NOT_FOUND') throw error;
  throw new Error('未找到 Playwright，请在仓库根目录运行 npm install --no-save playwright。', {cause: error});
}

const options = {headless: true};
if (process.argv.slice(3).includes('--chrome')) options.channel = 'chrome';
const browser = await chromium.launch(options);
try {
  for (const item of manifest) {
    const page = await browser.newPage({
      viewport: {width: item.width, height: item.height},
      deviceScaleFactor: 1
    });
    await page.goto(pathToFileURL(item.html).href, {waitUntil: 'load'});
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({path: item.png, type: 'png'});
    await page.close();
    console.log(`Exported ${path.basename(item.png)} (${item.width}x${item.height})`);
  }
} finally {
  await browser.close();
}
