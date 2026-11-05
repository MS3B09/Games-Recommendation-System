import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';
import { mockCatalog } from './fixtures';
import { isAnalytics, type AnalyticsResponse } from '../src/api/analytics';
import { GUEST_KEY } from '../src/guest-store';

// Public, generated aggregate fixture from the independently checked 2000-game snapshot.
const snapshot = JSON.parse(readFileSync(new URL('./analytics-fixture.json', import.meta.url), 'utf8')) as AnalyticsResponse;
const clone = () => structuredClone(snapshot);

test('analytics parser rejects cross-version, malformed counts and missing fields', () => {
  expect(isAnalytics(snapshot)).toBe(true);
  for (const mutate of [
    (x: AnalyticsResponse) => { x.data.catalog_version = 'wrong'; },
    (x: AnalyticsResponse) => { x.data.platforms[0]!.unknown = -1; },
    (x: AnalyticsResponse) => { x.data.price_ranges[0]!.count += 1; },
    (x: AnalyticsResponse) => { x.data.avg_price_cents = null; },
  ]) { const x = clone(); mutate(x); expect(isAnalytics(x)).toBe(false); }
});

test('dashboard navigation, all thirteen items, year exploration, refresh and storage isolation', async ({ page }) => {
  await mockCatalog(page);
  let current = clone();
  await page.route('**/api/v1/analytics', route => route.fulfill({ json: current }));
  await page.goto('/');
  const before = await page.evaluate(key => localStorage.getItem(key), GUEST_KEY);
  await expect(page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link')).toHaveText(['Your taste', 'Discover', 'Dashboard', 'Saved games (0)']);
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toHaveAttribute('aria-current', 'page');
  await expect(page.locator('.dashboard-metrics dt')).toHaveCount(4);
  await expect(page.locator('.dashboard-metrics dd > span').first()).toHaveText('2,000');
  await expect(page.locator('.dashboard-chart')).toHaveCount(8);
  await expect(page.locator('.dashboard-word-cloud > span')).toHaveCount(60);
  await expect(page.locator('.dashboard-platforms').getByText('Linux(SteamOS)', { exact: true })).toBeVisible();
  await expect(page.getByText(/Independent SteamOS \/ Steam Deck compatibility/)).toBeVisible();
  await page.getByLabel('Release year', { exact: true }).selectOption('2006');
  const release = page.getByRole('article', { name: 'Games released by month' });
  await release.getByText('View exact values', { exact: true }).click();
  await expect(release.getByRole('row', { name: 'Nov 1', exact: true })).toBeVisible();
  await expect(release.locator('.dashboard-months strong')).toHaveText(snapshot.data.release_years.find(x => x.year === 2006)!.months.map(String));
  const refreshed = clone();
  refreshed.catalog_version = refreshed.data.catalog_version = 'refresh-fixture';
  refreshed.data.avg_price_cents = 2500;
  current = refreshed;
  await page.getByRole('button', { name: 'Refresh snapshot' }).click();
  await expect(page.locator('.dashboard-metrics dd > span').nth(1)).toHaveText('$25.00');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Inside the catalog.' })).toBeVisible();
  expect(await page.evaluate(key => localStorage.getItem(key), GUEST_KEY)).toBe(before);
  await page.getByRole('link', { name: 'Discover', exact: true }).click();
  await expect(page).toHaveURL(/\/#possibilities$/);
  await expect(page.getByRole('link', { name: 'Discover', exact: true })).toHaveAttribute('aria-current', 'location');
  await page.goto('/saved');
  await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toHaveAttribute('href', '/dashboard');
});

test('dashboard loading, manual retry, invalid reply and empty catalog are distinct', async ({ page }) => {
  await mockCatalog(page);
  let mode = 'loading';
  let release: (() => void) | undefined;
  const wait = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/analytics', async route => {
    if (mode === 'loading') { await wait; return route.fulfill({ status: 503, json: { code: 'analytics_unavailable' } }); }
    if (mode === 'invalid') return route.fulfill({ json: { ...clone(), catalog_version: 'wrong' } });
    return route.fulfill({ json: clone() });
  });
  await page.goto('/dashboard');
  await expect(page.locator('.dashboard-body').getByRole('status')).toContainText('Loading catalog metrics');
  release!();
  await expect(page.getByRole('alert')).toContainText('not available for this catalog version');
  mode = 'invalid';
  await page.getByRole('button', { name: 'Retry dashboard' }).click();
  await expect(page.getByRole('alert')).toContainText("couldn't load the reply correctly");
  mode = 'ready';
  await page.getByRole('button', { name: 'Retry dashboard' }).click();
  await expect(page.locator('.dashboard-metrics dd > span').first()).toHaveText('2,000');
  const empty = clone();
  Object.assign(empty.data, { total_games: 0, total_developers: 0, avg_price_cents: null, avg_discount_percent: null,
    release_years: [], genres: [], developers: [], reviews: [], words: [] });
  Object.values(empty.data.coverage).forEach(x => { x.known = x.unknown = x.invalid = 0; });
  for (const rows of [empty.data.free_paid, empty.data.price_ranges, empty.data.discount_ranges]) rows.forEach(x => { x.count = 0; });
  empty.data.platforms.forEach(x => { x.count = x.unknown = x.unsupported = 0; });
  expect(isAnalytics(empty)).toBe(true);
  await page.route('**/api/v1/analytics', route => route.fulfill({ json: empty }));
  await page.getByRole('button', { name: 'Refresh snapshot' }).click();
  await expect(page.getByRole('heading', { name: 'No games in this snapshot.' })).toBeVisible();
  await expect(page.locator('.dashboard-chart')).toHaveCount(0);
});

test('dashboard responsive charts, exact values, long labels and accessibility', async ({ page }) => {
  await mockCatalog(page);
  const current = clone();
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/v1/analytics', route => route.fulfill({ json: current }));
  await page.goto('/dashboard');
  await expect(page.locator('.dashboard-chart')).toHaveCount(8);
  for (const [width, height] of [[1440, 1000], [390, 844], [320, 640]]) {
    await page.setViewportSize({ width: width!, height: height! });
    await page.evaluate(() => document.fonts.ready);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const violations = (await new AxeBuilder({ page }).analyze()).violations;
    expect(violations).toEqual([]);
    if (process.env.DASHBOARD_CAPTURE_DIR) {
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/dashboard-${width}.png`, fullPage: true });
      await page.screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/dashboard-top-${width}.png` });
      if (width === 320) {
        const release = page.getByRole('article', { name: 'Games released by month' });
        await page.getByLabel('Release year', { exact: true }).selectOption('2006');
        await release.getByText('View exact values', { exact: true }).click();
        await release.screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/dashboard-release-values-320.png` });
        await page.getByLabel('Release year', { exact: true }).selectOption('all');
        await release.getByText('View exact values', { exact: true }).click();
        await page.locator('.dashboard-word-cloud').screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/dashboard-words-320.png` });
      }
    }
  }
  current.data.developers[0]!.label = '株式会社' + 'VeryLongUnbrokenDeveloperName'.repeat(9);
  await page.getByRole('button', { name: 'Refresh snapshot' }).click();
  await expect(page.locator('.dashboard-developers')).toContainText(current.data.developers[0]!.label);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.keyboard.press('Tab');
  expect(errors).toEqual([]);
});
