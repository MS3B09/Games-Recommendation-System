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

test('chart code loads only on the dashboard and readable data survives a chart-download failure without disclosures', async ({ page }) => {
  await mockCatalog(page);
  await page.route('**/api/v1/analytics', route => route.fulfill({ json: clone() }));
  let downloads = 0;
  await page.route('**/assets/plotly-basic*.js', route => { downloads++; return route.abort(); });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Find my next game', exact: true })).toBeVisible();
  expect(downloads).toBe(0);
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(page.getByText('Interactive chart unavailable. Values are shown below; reload to try again.', { exact: true })).toHaveCount(7);
  expect(downloads).toBeGreaterThan(0);
  const free = page.getByRole('article', { name: 'Free vs paid games', exact: true });
  await expect(free.getByRole('row', { name: 'Free to play 352', exact: true })).toBeVisible();
  await expect(page.getByText('View exact values', { exact: true })).toHaveCount(0);
  await expect(page.locator('.dashboard-share-values li')).toHaveCount(6);
  await expect(page.locator('.dashboard-lollipops li')).toHaveCount(10);
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
  await expect(page.locator('.dashboard-plot[data-ready="true"]')).toHaveCount(7);
  expect(await page.locator('.dashboard-interactive').evaluateAll(nodes => [...new Set(nodes.map(n => n.getAttribute('data-chart-kind')))].sort())).toEqual(['column', 'donut', 'line', 'lollipop', 'rank', 'stack', 'strip', 'summary-donut']);
  await expect(page.locator('.dashboard-body')).not.toContainText(/\b(?:un)?known\b/i);
  await expect(page.locator('.dashboard-provenance')).toHaveCount(0);
  await expect(page.locator('.dashboard-body summary')).toHaveText(['View word counts and method']);
  await expect(page.locator('.dashboard-body')).not.toContainText(/Recorded US store prices, not live offers|not discounted checkout prices|Names are normalized for spacing and case|these are themes, not verified gameplay attributes|All percentages use the/);
  await page.getByText('View word counts and method', { exact: true }).click();
  await expect(page.locator('.dashboard-word-counts li')).toHaveCount(60);
  await page.getByText('View word counts and method', { exact: true }).click();
  for (const article of await page.locator('.dashboard-chart').all()) await expect(article).not.toContainText(/unknown|user reviews/i);
  const price = page.getByRole('article', { name: 'Games by price range', exact: true });
  await expect(price.locator('.bartext')).toHaveText(['227', '317', '581', '422', '61']);
  await expect(page.locator('.dashboard-ranked .bartext')).toHaveText(snapshot.data.genres.map(r => r.count.toLocaleString('en-US')));
  await expect(page.locator('.dashboard-lollipops strong')).toHaveText(snapshot.data.developers.map(r => r.count.toLocaleString('en-US')));
  await expect(page.locator('.dashboard-share-values strong')).toHaveText(['1,381', '23', '78', '92', '24', '10']);
  const discounts = page.getByRole('article', { name: 'Games by discount', exact: true });
  const discountRows = snapshot.data.discount_ranges.filter(r => r.count > 0);
  const discountTotal = discountRows.reduce((n, r) => n + r.count, 0);
  for (const [i, row] of discountRows.entries()) {
    await discounts.locator('.barlayer .trace .point path').nth(i).hover({ force: true });
    await expect(discounts.getByRole('tooltip')).toContainText(row.label);
    await expect(discounts.getByRole('tooltip')).toContainText(`${row.count.toLocaleString('en-US')} games`);
    await expect(discounts.getByRole('tooltip')).toContainText(`${(row.count / discountTotal * 100).toFixed(1)}%`);
  }
  const reviews = page.getByRole('article', { name: 'Review type distribution', exact: true });
  await expect(reviews.locator('.dashboard-legend button')).toHaveCount(6);
  await expect(reviews.locator('.dashboard-legend p')).toHaveText('Toggle a category to compare.');
  await expect(reviews.locator('text.slicetext')).toHaveText(['54.7%', '17.2%', '12.3%', '12.2%', '2.6%', '0.9%']);
  await expect(page.locator('.dashboard-stack-key')).toHaveText('SupportedUnsupported');
  await expect(page.locator('[data-chart-kind="stack"] .bartext')).toHaveText(['2,000', '496', '331', '1,504', '1,669']);
  await expect(page.locator('[data-chart-kind="stack"] .xtick text')).toHaveText(['Windows', 'macOS', 'Linux']);
  await expect(page.getByText(/Independent SteamOS \/ Steam Deck compatibility/)).toBeVisible();
  await page.getByLabel('Release year', { exact: true }).selectOption('2006');
  const release = page.getByRole('article', { name: 'Games released by month' });
  await expect(release.getByRole('row', { name: 'Nov 1', exact: true })).toHaveCount(1);
  await expect(release.getByRole('row')).toHaveCount(3);
  await expect.poll(() => release.locator('.dashboard-plot').evaluate(node => (node as HTMLElement & { data: { y: number[] }[] }).data?.[0]?.y)).toEqual(snapshot.data.release_years.find(x => x.year === 2006)!.months);
  const free = page.getByRole('article', { name: 'Free vs paid games', exact: true });
  await expect(free.locator('text.slicetext')).toHaveText(['17.6%', '82.4%']);
  await expect(free.locator('.annotation-text')).toContainText('2,000');
  const category = free.getByRole('button', { name: /^Free / });
  await category.focus(); await page.keyboard.press('Space');
  await expect(category).toHaveAttribute('aria-pressed', 'false');
  await expect.poll(() => free.locator('.dashboard-plot').evaluate(node => (node as HTMLElement & { layout: { hiddenlabels: string[] } }).layout?.hiddenlabels)).toContain('Free to play');
  await category.click(); await expect(category).toHaveAttribute('aria-pressed', 'true');
  // Plotly's transparent drag layer receives pointer events above its SVG points.
  await release.locator('.scatterlayer .point').nth(10).hover({ force: true });
  await expect(release.locator('.hoverlayer')).toContainText('Nov');
  const drag = await release.locator('.nsewdrag').boundingBox();
  await page.mouse.move(drag!.x + drag!.width * .2, drag!.y + drag!.height * .2);
  await page.mouse.down();
  await page.mouse.move(drag!.x + drag!.width * .7, drag!.y + drag!.height * .8, { steps: 8 });
  await page.mouse.up();
  await expect.poll(() => release.locator('.dashboard-plot').evaluate(node => (node as HTMLElement & { layout: { xaxis: { range: number[] } } }).layout?.xaxis?.range?.[1])).toBeLessThan(11);
  await release.getByRole('button', { name: 'Reset view: Games released by month', exact: true }).click();
  await expect.poll(() => release.locator('.dashboard-plot').evaluate(node => (node as HTMLElement & { layout: { xaxis: { range: number[] } } }).layout?.xaxis?.range?.[1])).toBeGreaterThanOrEqual(11);
  const refreshed = clone();
  refreshed.catalog_version = refreshed.data.catalog_version = 'refresh-fixture';
  refreshed.data.avg_price_cents = 2500;
  refreshed.data.free_paid[2]!.count = 50;
  refreshed.data.free_paid[1]!.count -= 50;
  current = refreshed;
  await page.getByRole('button', { name: 'Refresh snapshot' }).click();
  await expect(page.locator('.dashboard-metrics dd > span').nth(1)).toHaveText('$25.00');
  await expect(free.locator('.annotation-text')).toContainText('1,950');
  await expect(free.locator('.dashboard-legend button')).toHaveCount(2);
  await expect(free.locator('text.slicetext')).toHaveText(['18.1%', '81.9%']);
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
  await expect(page.locator('.dashboard-metrics dd > span').nth(1)).toHaveText('—');
  await expect(page.locator('.dashboard-metrics dd > span').nth(1)).toHaveAttribute('aria-label', 'Not available');
  await expect(page.locator('.dashboard-metrics dd > span').nth(2)).toHaveText('—');
  await expect(page.locator('.dashboard-chart')).toHaveCount(0);
});

test('dashboard responsive labels, expanded genre plot, compact developers and accessibility', async ({ page }) => {
  await mockCatalog(page);
  const current = clone();
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/v1/analytics', route => route.fulfill({ json: current }));
  await page.goto('/dashboard');
  await expect(page.locator('.dashboard-chart')).toHaveCount(8);
  await expect(page.locator('.dashboard-plot[data-ready="true"]')).toHaveCount(7);
  await page.getByRole('button', { name: 'Dismiss assistant greeting', exact: true }).click();
  for (const [width, height] of [[1440, 1000], [390, 844], [320, 640]]) {
    await page.setViewportSize({ width: width!, height: height! });
    await page.evaluate(() => document.fonts.ready);
    await expect.poll(() => page.locator('.dashboard-plot').evaluateAll(nodes => nodes.every(node => Math.abs(node.querySelector('.main-svg')!.getBoundingClientRect().width - node.getBoundingClientRect().width) < 2))).toBe(true);
    expect(await page.locator('.dashboard-ranked .dashboard-plot').evaluate(node => (node as HTMLElement & { _fullLayout: { _size: { r: number } } })._fullLayout._size.r)).toBeLessThanOrEqual(54);
    if (width === 1440) expect((await page.locator('.dashboard-lollipops').boundingBox())!.height).toBeLessThan(480);
    for (const [title, labels] of [
      ['Supported platforms', ['Windows', 'macOS', 'Linux']],
      ['Games by price range', current.data.price_ranges.filter(r => r.count > 0).map(r => r.label)],
      ['Games released by month', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']],
    ] as const) {
      const chart = page.getByRole('article', { name: title, exact: true });
      await expect(chart.locator('.xtick text')).toHaveText([...labels]);
      expect(await chart.locator('.dashboard-plot').evaluate(node => {
        const p = node.getBoundingClientRect();
        return Array.from(node.querySelectorAll('.xtick text')).filter(label => {
          const r = label.getBoundingClientRect();
          return !r.width || getComputedStyle(label).visibility !== 'visible' || r.left < p.left - 1 || r.right > p.right + 1 || r.top < p.top - 1 || r.bottom > p.bottom + 1;
        }).map(label => label.textContent);
      })).toEqual([]);
      if (title === 'Games released by month') expect(await chart.locator('.xtick text').evaluateAll(nodes => {
        const boxes = nodes.map(n => n.getBoundingClientRect());
        return boxes.slice(1).every((r, i) => r.left >= boxes[i]!.right - .5);
      })).toBe(true);
    }
    expect(await page.locator('.dashboard-plot').evaluateAll(nodes => nodes.flatMap(node => {
      const plot = node.getBoundingClientRect();
      return Array.from(node.querySelectorAll('.slicetext, .bartext')).filter(label => {
        const r = label.getBoundingClientRect();
        return r.width > 0 && (r.left < plot.left - 1 || r.right > plot.right + 1 || r.top < plot.top - 1 || r.bottom > plot.bottom + 1);
      }).map(label => label.textContent);
    }))).toEqual([]);
    const discounts = page.getByRole('article', { name: 'Games by discount', exact: true });
    await discounts.locator('.dashboard-plot').scrollIntoViewIfNeeded();
    await discounts.locator('.barlayer .trace .point path').last().hover({ force: true });
    await expect(discounts.getByRole('tooltip')).toContainText('10 games · 0.6%');
    const tooltip = await discounts.getByRole('tooltip').boundingBox();
    const strip = await discounts.locator('.barlayer').boundingBox();
    expect(tooltip!.y + tooltip!.height).toBeLessThan(strip!.y);
    const plot = await discounts.locator('.dashboard-plot').boundingBox();
    expect(tooltip!.width).toBeLessThanOrEqual(200);
    expect(tooltip!.height).toBeLessThan(64);
    expect(tooltip!.x).toBeGreaterThanOrEqual(plot!.x - 1);
    expect(tooltip!.x + tooltip!.width).toBeLessThanOrEqual(plot!.x + plot!.width + 1);
    const entries = discounts.locator('.dashboard-share-values li');
    const first = await entries.nth(0).boundingBox();
    const second = await entries.nth(1).boundingBox();
    expect(first!.y - (plot!.y + plot!.height)).toBeCloseTo(second!.y - (first!.y + first!.height), 0);
    if (process.env.DASHBOARD_CAPTURE_DIR) await discounts.locator('.dashboard-plot').screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/discount-hover-${width}.png` });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const violations = (await new AxeBuilder({ page }).analyze()).violations;
    expect(violations).toEqual([]);
    if (process.env.DASHBOARD_CAPTURE_DIR) {
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/dashboard-${width}.png`, fullPage: true });
      await page.screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/dashboard-top-${width}.png` });
      for (const [slug, title] of [
        ['free', 'Free vs paid games'], ['price', 'Games by price range'], ['discount', 'Games by discount'],
        ['range', 'Games released by month'], ['genres', 'Top 15 game genres'], ['platforms', 'Supported platforms'],
        ['reviews', 'Review type distribution'], ['developers', 'Top 10 developers by game count'],
      ]) if (width === 1440 || ['free', 'price', 'discount', 'range', 'genres', 'platforms', 'reviews', 'developers'].includes(slug!)) {
        await page.getByRole('article', { name: title!, exact: true }).screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/${slug}-${width}.png` });
      }
      if (width === 320) {
        const release = page.getByRole('article', { name: 'Games released by month' });
        await page.getByLabel('Release year', { exact: true }).selectOption('2006');
        await release.screenshot({ path: `${process.env.DASHBOARD_CAPTURE_DIR}/dashboard-release-2006-320.png` });
        await page.getByLabel('Release year', { exact: true }).selectOption('all');
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
