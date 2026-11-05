import { expect, test } from '@playwright/test';

test('actual expanded app shares its catalog across discovery, analytics and chat services', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.route('https://**/*', route => route.abort());
  const apiFailures: string[] = [];
  page.on('requestfailed', request => {
    if (request.url().includes('/api/')) apiFailures.push(request.url());
  });
  const [facets, resolved] = await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/api/v1/facets')),
    page.waitForResponse(response => response.url().endsWith('/api/v1/games/resolve')),
    page.goto('/'),
  ]);
  expect(facets.status()).toBe(200);
  expect(resolved.status()).toBe(200);
  expect(await facets.headerValue('access-control-allow-origin')).toBe('http://127.0.0.1:4173');
  await expect(page.getByRole('button', { name: 'Find my next game', exact: true })).toBeEnabled();
  await expect(page.getByText(/couldn’t connect to the service/)).toHaveCount(0);
  const services = await page.evaluate(async base => {
    const post = (path: string, body: unknown) => fetch(base + path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
    const catalog = await (await fetch(base + '/api/v1/catalog/status')).json();
    const bytes = crypto.getRandomValues(new Uint8Array(32));
    const key = { conversation_id: crypto.randomUUID(),
      token: btoa(String.fromCharCode(...bytes)).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '') };
    let created: number, history: number, total: number, erased: boolean;
    try {
      created = (await post('/api/v2/assistant/conversations', { key, messages: [] })).status;
      const response = await post('/api/v2/assistant/history', key);
      history = response.status; total = (await response.json()).total;
    } finally {
      const response = await post('/api/v2/assistant/forget', key);
      erased = response.status === 200 && await response.json() === true;
    }
    const missing = await post('/api/v2/assistant/history', key);
    return { catalog, created, history, total, erased, historyAfterErasure: missing.status };
  }, new URL(facets.url()).origin);
  expect(services.catalog).toMatchObject({ game_count: 2000, semantic_query_matching: true, llm_enabled: true });
  expect(services).toMatchObject({ created: 200, history: 200, total: 0, erased: true, historyAfterErasure: 404 });
  const recommended = page.waitForResponse(response => response.url().endsWith('/api/v1/discover'));
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  const recommendations = await recommended;
  expect(recommendations.status()).toBe(200);
  expect((await recommendations.json()).catalog_version).toBe(services.catalog.catalog_version);
  const scale = await page.evaluate(() => ({
    rootFont: getComputedStyle(document.documentElement).fontSize,
    headingFont: getComputedStyle(document.querySelector('.study-opening h1')!).fontSize,
    rootZoom: getComputedStyle(document.documentElement).zoom,
    bodyTransform: getComputedStyle(document.body).transform,
  }));
  expect(scale).toEqual({ rootFont: '16px', headingFont: '96px', rootZoom: '1.25', bodyTransform: 'none' });
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(page.locator('.dashboard-metrics dd > span').first()).toHaveText('2,000');
  await expect(page.locator('.dashboard-chart')).toHaveCount(8);
  const analytics = await page.request.get(new URL(facets.url()).origin + '/api/v1/analytics');
  expect((await analytics.json()).catalog_version).toBe(services.catalog.catalog_version);
  await expect(page.getByRole('heading', { name: 'Dashboard unavailable.' })).toHaveCount(0);
  expect(apiFailures).toEqual([]);
});
