import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const empty = { state: 'uninitialized', catalog_version: null, game_count: 0, region: 'US', currency: 'USD', source_observed_at: null, semantic_query_matching: false, llm_enabled: false };

test('direct nested route shows an unpublished catalog, not an outage', async ({ page }) => {
  await page.route('**/api/v1/catalog/status', (route) => route.fulfill({ json: empty }));
  await page.goto('/system');
  await expect(page.getByRole('heading', { name: 'The catalog is being prepared' })).toBeVisible();
  await expect(page.getByText('API connected', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: /API documentation/ })).toHaveAttribute('href', 'http://127.0.0.1:8000/docs');
  const violations = (await new AxeBuilder({ page }).analyze()).violations;
  expect(violations).toEqual([]);
});

test('database outage can recover through a manual retry', async ({ page }) => {
  let requests = 0;
  await page.route('**/api/v1/catalog/status', (route) => {
    requests++;
    return route.fulfill(requests === 1 ? { status: 503, json: { code: 'database_unavailable', message: 'internal detail', request_id: 'fixture-request', retryable: true } } : { json: empty });
  });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'The service is unavailable' })).toBeVisible();
  await expect(page.getByText('Request ID: fixture-request')).toBeVisible();
  await expect(page.getByText('internal detail')).toHaveCount(0);
  await page.getByRole('button', { name: 'Check connection again' }).click();
  await expect(page.getByText('API connected', { exact: true })).toBeVisible();
  expect(requests).toBe(2);
});

test('network failure is not a zero-game catalog', async ({ page }) => {
  await page.route('**/api/v1/catalog/status', (route) => route.abort());
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'The service is unavailable' })).toBeVisible();
  await expect(page.getByText('We couldn’t reach the service.', { exact: false })).toBeVisible();
  await expect(page.getByText('Unknown', { exact: true })).toHaveCount(2);
  await expect(page.getByText('Not recorded yet', { exact: true })).toHaveCount(0);
});

test('HTML gateway failure and malformed success are rejected', async ({ page }) => {
  await page.route('**/api/v1/catalog/status', (route) => route.fulfill({ status: 502, contentType: 'text/html', body: '<h1>Gateway</h1>' }));
  await page.goto('/');
  await expect(page.getByText(/unexpected response/)).toBeVisible();
  await page.unrouteAll();
  await page.route('**/api/v1/catalog/status', (route) => route.fulfill({ json: { ...empty, game_count: -1 } }));
  await page.getByRole('button', { name: 'Check connection again' }).click();
  await expect(page.getByText(/could not be verified/)).toBeVisible();
});

test('loading is accessible and bounded; no automatic background polling', async ({ page }) => {
  await page.clock.install();
  await page.route('**/api/v1/catalog/status', () => { /* Deliberately unanswered request. */ });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Checking…' })).toBeDisabled();
  await page.clock.fastForward(75_001);
  await expect(page.getByText(/took too long/)).toBeVisible();
});

test('mobile layout and keyboard navigation stay usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/api/v1/catalog/status', (route) => route.fulfill({ json: empty }));
  await page.goto('/system');
  await expect(page.getByText('API connected', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test('unknown route offers recovery without an API request', async ({ page }) => {
  await page.route('**/api/v1/catalog/status', () => { throw new Error('No status request on missing route'); });
  await page.goto('/missing');
  await expect(page.getByRole('heading', { name: 'This page isn’t here.' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Go home' })).toHaveAttribute('href', '/');
});
