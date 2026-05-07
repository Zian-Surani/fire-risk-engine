# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: pw-temp.spec.js >> operations and simulation pages stay connected to backend
- Location: pw-temp.spec.js:3:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:3000/operations
Call log:
  - navigating to "http://127.0.0.1:3000/operations", waiting until "networkidle"

```

# Test source

```ts
  1  | ﻿const { test, expect } = require('@playwright/test');
  2  | 
  3  | test('operations and simulation pages stay connected to backend', async ({ page }) => {
  4  |   const consoleErrors = [];
  5  |   const pageErrors = [];
  6  |   page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  7  |   page.on('pageerror', err => pageErrors.push(String(err)));
  8  | 
> 9  |   await page.goto('http://127.0.0.1:3000/operations', { waitUntil: 'networkidle' });
     |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:3000/operations
  10 |   await expect(page.getByText('Operations Hub')).toBeVisible();
  11 |   await expect(page.getByText(/Backend unavailable/i)).toHaveCount(0);
  12 |   await page.getByRole('button', { name: 'OPTIMIZE DEPLOYMENT' }).click();
  13 |   await page.waitForTimeout(3000);
  14 |   await expect(page.getByText(/Backend unavailable/i)).toHaveCount(0);
  15 | 
  16 |   await page.goto('http://127.0.0.1:3000/simulation-ai', { waitUntil: 'networkidle' });
  17 |   await expect(page.getByText('Alpha-7 Simulation')).toBeVisible();
  18 |   await expect(page.getByText(/Simulation feed unavailable/i)).toHaveCount(0);
  19 |   await page.getByRole('button', { name: 'Initiate Sequence' }).click();
  20 |   await page.waitForTimeout(3000);
  21 |   await expect(page.getByText(/Simulation feed unavailable/i)).toHaveCount(0);
  22 | 
  23 |   expect(consoleErrors, `Console errors: ${consoleErrors.join('\n')}`).toEqual([]);
  24 |   expect(pageErrors, `Page errors: ${pageErrors.join('\n')}`).toEqual([]);
  25 | });
  26 | 
```