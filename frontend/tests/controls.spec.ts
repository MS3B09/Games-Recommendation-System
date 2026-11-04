import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mockCatalog } from './fixtures';
import { GUEST_KEY } from '../src/guest-store';

async function addChoice(page: Page, group: string, option: string) {
  const field = page.getByRole('group', { name: group, exact: true });
  await field.locator('summary').click();
  await field.getByRole('checkbox', { name: option, exact: true }).check();
  await field.locator('summary').press('Escape');
}

test('all three selectors retain multiple choices, send their hard constraints and persist after reload', async ({ page }) => {
  const requests = await mockCatalog(page);
  await page.goto('/');
  await addChoice(page, 'Required play modes', 'Multiplayer');
  await addChoice(page, 'Required platform', 'macOS');
  await addChoice(page, 'Required catalog genre', 'Action');
  await addChoice(page, 'Required catalog genre', 'Indie');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(1);
  expect(requests[0]?.filters).toMatchObject({ required_modes: ['single-player', 'multiplayer'], platforms: ['windows', 'mac'],
    platform_match: 'any', required_genres: ['action', 'indie'], preferred_terms: [], unwanted_terms: [] });
  await expect(page.getByRole('heading', { name: 'No games match these filters.' })).toBeVisible();
  await page.reload();
  for (const [group, options] of [['Required play modes', ['Single Player', 'Multiplayer']], ['Required platform', ['Windows', 'macOS']], ['Required catalog genre', ['Action', 'Indie']]] as const) {
    const field = page.getByRole('group', { name: group, exact: true });
    await field.locator('summary').click();
    for (const option of options) await expect(field.getByRole('checkbox', { name: option, exact: true })).toBeChecked();
    await field.locator('summary').press('Escape');
  }
  await expect(page.getByText('Play modes, preferences & exclusions', { exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Preferred genres or tags', { exact: true })).toHaveCount(0);
});

test('both price handles are draggable, keyboard-accessible, cannot cross, and zero means free only', async ({ page }) => {
  const requests = await mockCatalog(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/');
  const low = page.getByRole('slider', { name: 'Minimum recorded price', exact: true });
  const high = page.getByRole('slider', { name: 'Maximum recorded price', exact: true });
  await expect(high).toBeEnabled();
  const box = (await low.boundingBox())!;
  const width = box.width - 24;
  await page.mouse.move(box.x + 12, box.y + box.height / 2); await page.mouse.down();
  await page.mouse.move(box.x + 12 + width * .2, box.y + box.height / 2, { steps: 5 }); await page.mouse.up();
  expect(Number(await low.inputValue())).toBeGreaterThan(0);
  await page.mouse.move(box.x + 12 + width * .8, box.y + box.height / 2); await page.mouse.down();
  await page.mouse.move(box.x + 12 + width * .7, box.y + box.height / 2, { steps: 5 }); await page.mouse.up();
  expect(Number(await high.inputValue())).toBeLessThan(2000);
  const minimum = Number(await low.inputValue()); const maximum = Number(await high.inputValue());
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(1);
  expect(requests[0]?.filters).toMatchObject({ min_price_cents: minimum, max_price_cents: maximum, free_only: false });
  await page.reload();
  await expect(low).toHaveValue(String(minimum)); await expect(high).toHaveValue(String(maximum));
  await expect(high).toBeEnabled();
  await high.press('End'); await low.press('End'); await high.press('Home');
  await expect(high).toHaveValue('2500'); await expect(low).toHaveValue('2500');
  await low.press('Home'); await high.press('Home');
  await expect(low).toHaveValue('0'); await expect(high).toHaveValue('0');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(2);
  expect(requests[1]?.filters).toMatchObject({ min_price_cents: 0, max_price_cents: 0, free_only: true });
});

test('the complete row is aligned on desktop and menus/range remain accessible at narrow widths', async ({ page }) => {
  // Six serial axe scans need a larger total budget on the 8 GB CPU-only host.
  test.setTimeout(120_000);
  await mockCatalog(page);
  for (const width of [1777, 1440, 1000, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 }); await page.goto('/');
    await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeEnabled();
    const groups = page.locator('.study-limits > fieldset');
    await expect(groups).toHaveCount(4);
    if (width >= 1000) {
      const boxes = await groups.evaluateAll((elements) => elements.map((element) => { const rect = element.getBoundingClientRect(); return { x: rect.x, y: rect.y }; }));
      expect(new Set(boxes.map((box) => box.y)).size).toBe(1);
      expect(boxes.map((box) => box.x)).toEqual([...boxes.map((box) => box.x)].sort((a, b) => a - b));
    }
    const genres = page.getByRole('group', { name: 'Required catalog genre', exact: true });
    await genres.locator('summary').focus(); await page.keyboard.press('Enter');
    await expect(genres.getByRole('checkbox', { name: 'Action', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.keyboard.press('Escape');
    await expect(genres.locator('summary')).toBeFocused();
    await expect(genres.locator('details')).not.toHaveAttribute('open', '');
  }
});

test('legacy preferences clear hidden terms and preserve an unbounded budget when price metadata is unavailable', async ({ page }) => {
  const requests = await mockCatalog(page);
  await page.goto('/');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(1);
  await page.evaluate((key) => {
    const data = JSON.parse(localStorage.getItem(key)!);
    data.preferences.preferred_terms = ['rpg']; data.preferences.unwanted_terms = ['action'];
    data.preferences.max_price_cents = null;
    delete data.preferences.min_price_cents;
    localStorage.setItem(key, JSON.stringify(data));
  }, GUEST_KEY);
  await page.route('**/api/v1/facets', (route) => route.fulfill({ status: 503, json: { code: 'database_unavailable', request_id: 'price-fixture' } }));
  await page.reload();
  await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeDisabled();
  await expect(page.locator('.study-price-values')).toContainText('Any price');
  await expect(page.getByRole('button', { name: 'Retry catalog controls' })).toBeVisible();
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(2);
  expect(requests[1]?.filters).toMatchObject({ min_price_cents: 0, max_price_cents: null, free_only: false, preferred_terms: [], unwanted_terms: [] });
  expect(requests[1]?.preferences).toMatchObject({ min_price_cents: 0, max_price_cents: null, free_only: false, preferred_terms: [], unwanted_terms: [] });
  const savedMaximum = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)!).preferences.max_price_cents, GUEST_KEY);
  expect(savedMaximum).toBeNull();
});
