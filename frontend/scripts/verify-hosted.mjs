// Bounded, read-only hosted M1 checks. Failure states are browser-intercepted only.
/* global document, window */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const frontend = new URL(process.env.HOSTED_FRONTEND_URL || 'https://steam-discovery.netlify.app').origin;
const api = new URL(process.env.HOSTED_API_URL || 'https://steam-discovery-api.fastapicloud.dev').origin;
const endpoint = `${api}/api/v1/catalog/status`;
const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const evidence = { frontend, api, checks: [], browserErrors: [], responses: [] };
const ok = (name) => evidence.checks.push(name);
const canonical = (value) => Array.isArray(value) ? value.map(canonical)
  : value && typeof value === 'object'
    ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])])) : value;

try {
  for (const [path, status] of [['/health/live', 200], ['/api/v1/catalog/status', 200], ['/health/ready', 503]]) {
    const started = performance.now();
    const response = await context.request.get(`${api}${path}`, { headers: { Origin: frontend }, timeout: 90000 });
    const json = await response.json();
    assert.equal(response.status(), status, `${path} HTTP status`);
    assert.equal(response.headers()['access-control-allow-origin'], frontend, `${path} CORS`);
    assert.notEqual(response.headers()['access-control-allow-credentials'], 'true');
    if (path === '/health/live') assert.equal(json.status, 'alive');
    if (path === '/api/v1/catalog/status') {
      assert.equal(json.state, 'uninitialized'); assert.equal(json.game_count, 0);
      assert.equal(json.catalog_version, null); assert.equal(json.source_observed_at, null);
      assert.equal(json.region, 'US'); assert.equal(json.currency, 'USD');
      assert.equal(json.semantic_query_matching, false); assert.equal(json.llm_enabled, false);
    }
    if (path === '/health/ready') {
      assert.equal(json.code, 'catalog_not_initialized'); assert.equal(json.retryable, false);
      assert.equal(json.request_id, response.headers()['x-request-id']);
    }
    evidence.responses.push({ path, status: response.status(), observedRoundTripMs: Math.round(performance.now() - started) });
  }
  ok('health/catalog/expected-readiness and CORS on success/error');
  const options = await context.request.fetch(endpoint, {
    method: 'OPTIONS', headers: { Origin: frontend, 'Access-Control-Request-Method': 'GET' },
  });
  assert.equal(options.status(), 200);
  assert.equal(options.headers()['access-control-allow-origin'], frontend);
  const otherOrigin = await context.request.get(endpoint, { headers: { Origin: 'https://untrusted.example' } });
  assert.equal(otherOrigin.headers()['access-control-allow-origin'], undefined);
  ok('explicit-origin preflight and no CORS grant to unrelated origin');

  const openapi = await context.request.get(`${api}/openapi.json`);
  assert.equal(openapi.status(), 200);
  const actual = await openapi.json();
  const local = JSON.parse(await readFile(new URL('../../backend/openapi.json', import.meta.url), 'utf8'));
  assert.deepEqual(canonical(actual.paths), canonical(local.paths));
  assert.deepEqual(canonical(actual.components), canonical(local.components));
  const docs = await context.request.get(`${api}/docs`);
  assert.equal(docs.status(), 200); assert.match(await docs.text(), /swagger-ui/i);
  ok('hosted OpenAPI paths/models match tracked contract; docs HTML available');
  const docsPage = await context.newPage();
  await docsPage.goto(`${api}/docs`);
  await expect(docsPage.locator('.swagger-ui .info .title')).toContainText('Game Discovery API', { timeout: 30000 });
  await expect(docsPage.locator('.opblock-summary-path').filter({ hasText: '/api/v1/catalog/status' })).toBeVisible();
  await docsPage.close();
  ok('Swagger UI renders the application and catalog operation');

  const page = await context.newPage();
  page.on('pageerror', (error) => evidence.browserErrors.push(error.name));
  const assets = new Set();
  let realRequests = 0;
  page.on('response', (response) => {
    if (response.url() === endpoint) realRequests++;
    if (response.request().resourceType() === 'script' && response.url().startsWith(`${frontend}/assets/`)) assets.add(response.url());
  });
  for (const path of ['/', '/system']) {
    const response = await page.goto(`${frontend}${path}`);
    assert.equal(response.status(), 200);
    await expect(page.getByText('API connected', { exact: true })).toBeVisible({ timeout: 85000 });
    await expect(page.getByRole('heading', { name: 'The catalog is being prepared' })).toBeVisible();
    await expect(page.getByRole('link', { name: /API documentation/ })).toHaveAttribute('href', `${api}/docs`);
    await expect(page.getByText('Not recorded yet', { exact: true })).toBeVisible();
  }
  assert.equal(realRequests, 2, 'one request per page mount');
  await page.getByRole('button', { name: 'Check connection again' }).click();
  await expect(page.getByText('API connected', { exact: true })).toBeVisible({ timeout: 85000 });
  assert.equal(realRequests, 3);
  ok('live frontend mount, direct SPA navigation, real API origin/CORS and manual retry');
  assert.equal((await new AxeBuilder({ page }).analyze()).violations.length, 0);
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
  assert.equal((await new AxeBuilder({ page }).analyze()).violations.length, 0);
  await page.reload();
  await expect(page.getByText('API connected', { exact: true })).toBeVisible({ timeout: 85000 });
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  ok('desktop/mobile axe scans, 390px layout, reload and keyboard entry');

  for (const url of assets) {
    const response = await context.request.get(url);
    const text = await response.text();
    assert.equal(response.status(), 200);
    assert.ok(text.includes(api));
    assert.ok(!/postgres(?:ql)?:\/\/[^\s"']+:[^\s"']+@|gsk_[A-Za-z0-9]{24,}|sb_secret_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC )?PRIVATE KEY/.test(text), 'secret pattern in client asset');
  }
  assert.ok(assets.size > 0);
  ok('served application JS has configured public API origin and no tested secret patterns');

  await page.route(endpoint, (route) => route.abort());
  await page.getByRole('button', { name: 'Check connection again' }).click();
  await expect(page.getByRole('heading', { name: 'The service is unavailable' })).toBeVisible();
  await expect(page.getByText('Unknown', { exact: true })).toHaveCount(2);
  await expect(page.getByText('Not recorded yet', { exact: true })).toHaveCount(0);
  await page.unroute(endpoint);
  await page.getByRole('button', { name: 'Check connection again' }).click();
  await expect(page.getByText('API connected', { exact: true })).toBeVisible({ timeout: 85000 });
  ok('browser-only simulated outage stays distinct from empty data and recovers against real API');
  assert.deepEqual(evidence.browserErrors, []);
  console.log(JSON.stringify({ result: 'pass', ...evidence }, null, 2));
} finally { await context.close(); await browser.close(); }
