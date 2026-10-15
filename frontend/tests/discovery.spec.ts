import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const observed = '2026-10-14T12:00:00Z';
const source = { url: 'https://store.steampowered.com/api/appdetails?appids=10&cc=us', collected_at: observed, sha256: 'a'.repeat(64) };
const game = { app_id: 10, title: 'Fixture Adventure', description: 'A catalog description of exploration and combat.', store_url: 'https://store.steampowered.com/app/10/',
  artwork_url: null, eligibility: 'eligible', eligibility_reason: 'released_game_with_content_classification', early_access: true,
  platforms: { windows: true, mac: false, linux: null }, genres: ['action'], tags: [], modes: ['single-player'], free_to_play: false,
  price: { amount_cents: 1999, currency: 'USD', region: 'US', observed_at: observed, evidence_id: '10:price_cents' }, observed_at: observed,
  semantic_hash: 'a'.repeat(64), evidence: [{ id: '10:description', field: 'description', value: 'A catalog description of exploration and combat.', source },
    { id: '10:price_cents', field: 'price_cents', value: 1999, source }] };
const seed = { ...game, app_id: 1145360, title: 'Hades' };
const criteria = { max_price_cents: null, price_operator: 'lte', free_only: false, platforms: [], platform_match: 'any', required_modes: [], preferred_terms: [], unwanted_terms: [], excluded_ids: [] };
const result = { game, reasons: [{ text: 'Catalog description supports this candidate.', evidence_ids: ['10:description'] }], tradeoffs: ['Recorded prices may differ from the current Steam store.'] };
const response = { request_id: 'fixture-id', catalog_version: 'fixture-v1', ranking_version: 'seed-v1', effective_criteria: criteria, results: [result], degraded_reasons: [], suggested_refinements: [], timings_ms: { core: 12 } };

async function setup(page: Page) {
  await page.route('**/api/v1/catalog/status', (route) => route.fulfill({ json: { state: 'ready', catalog_version: 'fixture-v1', game_count: 2, region: 'US', currency: 'USD', source_observed_at: observed, semantic_query_matching: false, llm_enabled: false } }));
  await page.route('**/api/v1/games?*', (route) => route.fulfill({ json: { catalog_version: 'fixture-v1', items: [seed], total: 1, offset: 0 } }));
  await page.route('**/api/v1/facets', (route) => route.fulfill({ json: { catalog_version: 'fixture-v1', genres: ['action'], tags: [], modes: ['single-player'], platforms: ['windows'] } }));
}

test('favorite selection, exact filters, evidence and price freshness work together', async ({ page }) => {
  await setup(page);
  let body: Record<string, unknown> = {};
  await page.route('**/api/v1/discover', (route) => { body = route.request().postDataJSON(); return route.fulfill({ json: response }); });
  await page.goto('/');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await page.getByRole('button', { name: 'Hades Add favorite' }).click();
  await page.getByLabel('Maximum recorded price (USD)').fill('20');
  await page.getByLabel('Windows', { exact: true }).check();
  await page.getByText('Play modes, genres & exclusions', { exact: true }).click();
  await page.getByLabel('Single-player', { exact: true }).check();
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Fixture Adventure' })).toBeVisible();
  expect(body).toMatchObject({ favorite_ids: [1145360], filters: { max_price_cents: 2000, platforms: ['windows'], required_modes: ['single-player'] } });
  await expect(page.getByText(/US store · observed Oct 14, 2026/)).toBeVisible();
  await expect(page.getByText('Windows · Early Access', { exact: true })).toBeVisible();
  await page.getByText('Why this game?', { exact: true }).click();
  await expect(page.getByRole('link', { name: /Steam source for description/ })).toHaveAttribute('href', source.url);
  await page.getByRole('button', { name: 'Exclude Fixture Adventure', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Fixture Adventure' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  expect(body).toMatchObject({ filters: { excluded_ids: [10] } });
});

test('no matches is distinct from service failure and retry succeeds', async ({ page }) => {
  await setup(page);
  let requests = 0;
  await page.route('**/api/v1/discover', (route) => {
    requests++;
    return route.fulfill(requests === 1 ? { json: { ...response, results: [], suggested_refinements: ['Try another platform.'] } }
      : requests === 2 ? { status: 503, json: { code: 'database_unavailable', request_id: 'outage-id' } } : { json: response });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  await expect(page.getByText(/filters have not been relaxed/)).toBeVisible();
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  await expect(page.getByText('Request ID: outage-id')).toBeVisible();
  await expect(page.getByText(/filters have not been relaxed/)).toHaveCount(0);
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Fixture Adventure' })).toBeVisible();
});

test('editing criteria cancels an in-flight response and malformed claims are rejected', async ({ page }) => {
  await setup(page);
  let release: () => void = () => {};
  let started: () => void = () => {};
  const arrived = new Promise<void>((resolve) => { started = resolve; });
  const waiting = new Promise<void>((resolve) => { release = resolve; });
  await page.route('**/api/v1/discover', async (route) => { started(); await waiting; await route.fulfill({ json: response }); });
  await page.goto('/');
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  await arrived;
  await page.getByLabel('Windows', { exact: true }).check();
  release();
  await expect(page.getByRole('heading', { name: 'Fixture Adventure' })).toHaveCount(0);
  await page.unroute('**/api/v1/discover');
  await page.route('**/api/v1/discover', (route) => route.fulfill({ json: { ...response, results: [{ ...result, reasons: [{ text: 'Invented fact', evidence_ids: ['invented'] }] }] } }));
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  await expect(page.getByText(/response could not be verified/)).toBeVisible();
  await expect(page.getByText('Invented fact')).toHaveCount(0);
});

test('discovery is accessible on mobile, artwork fallback and direct details work', async ({ page }) => {
  await setup(page);
  await page.route('**/api/v1/discover', (route) => route.fulfill({ json: response }));
  await page.route('**/api/v1/games/10', (route) => route.fulfill({ json: game }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  await expect(page.getByText('Artwork unavailable', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole('link', { name: 'Fixture Adventure', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Fixture Adventure' })).toBeVisible();
  await page.reload();
  await page.getByText('Catalog evidence & provenance', { exact: true }).click();
  await expect(page.getByRole('link', { name: /Steam source for price_cents/ })).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
