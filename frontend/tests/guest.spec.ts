import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { catalog, discovery, mockCatalog } from './fixtures';
import { GUEST_KEY } from '../src/guest-store';

test('desktop feedback sits beside Steam and Save, and details retain only concise essentials', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await mockCatalog(page);
  await page.route('**/api/v1/discover', route => {
    const response = discovery(route.request().postDataJSON());
    response.results[0]!.game.description = 'A source-recorded adventure with action and exploration. '.repeat(30);
    return route.fulfill({ json: response });
  });
  await page.goto('/');
  await expect(page.locator('.study-brand small')).toHaveText('Steam');
  await expect(page.locator('.study-brand .icon')).toHaveCount(1);
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href', '/favicon-32.png');
  const favicon = await page.request.get('/favicon-32.png');
  expect(favicon.ok()).toBe(true);
  expect(favicon.headers()['content-type']).toContain('image/png');
  const png = await favicon.body();
  expect(png.subarray(0, 8).toString('hex')).toBe('89504e470d0a1a0a');
  expect([png.readUInt32BE(16), png.readUInt32BE(20)]).toEqual([32, 32]);
  for (const route of ['/', '/current-original.html']) {
    expect(await (await page.request.get(route)).text()).toContain('href="/favicon-32.png"');
  }
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect(page.locator('.study-launch')).not.toContainText('Catalog-backed recommendations. No sign-in needed.');
    await expect(page.locator('.study-launch')).not.toContainText('Your taste is saved on this device.');
    await expect(page.getByRole('button', { name: 'Find my next game', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.locator('.study-launch').screenshot({ path: test.info().outputPath(`launch-${width}.png`) });
    await page.locator('.study-header').screenshot({ path: test.info().outputPath(`brand-${width}.png`) });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  const row = page.locator('.study-game').first();
  const steam = await row.getByRole('link', { name: 'View on Steam', exact: false }).last().boundingBox();
  const feedback = await row.getByRole('group', { name: 'Recommendation feedback for Bastion' }).boundingBox();
  const copy = await row.locator('.study-game-copy').boundingBox();
  expect(Math.abs(steam!.y + steam!.height / 2 - feedback!.y - feedback!.height / 2)).toBeLessThan(2);
  expect(Math.abs(copy!.x + copy!.width - feedback!.x - feedback!.width)).toBeLessThan(2);
  await row.getByText('Game details', { exact: true }).click();
  await expect(row.locator('.game-facts')).toContainText('Windows, macOS, Linux');
  await expect(row.locator('.game-price-note')).toContainText('Price recorded Oct 14, 2026.');
  expect((await row.locator('.game-description').textContent())!.length).toBeLessThan(300);
  await expect(row.locator('.study-evidence')).not.toContainText('Steam source:');
  await expect(row.locator('.study-evidence')).not.toContainText('Keep in mind');
  await expect(row.getByRole('button', { name: 'Save Bastion', exact: true })).toBeVisible();
});

test('favorites, preferences, saves, feedback and history survive reload and direct saved navigation', async ({ page }) => {
  const requests = await mockCatalog(page);
  await page.goto('/');
  await page.getByText('Change favorites', { exact: true }).click();
  await page.getByLabel('Search the catalog').fill('Transistor');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await page.getByRole('button', { name: 'Transistor Add favorite', exact: true }).click();
  await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeEnabled();
  await page.getByRole('slider', { name: 'Maximum recorded price', exact: true }).press('End');
  await page.getByText('Change favorites', { exact: true }).click();
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  expect(requests[0]?.feedback).toEqual([]); // Saving is not Interested.
  await page.getByRole('group', { name: 'Recommendation feedback for Portal 2' }).getByRole('button', { name: 'Not For Me', exact: true }).click();
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(2);
  expect(requests[1]?.feedback?.[0]?.kind).toBe('not-for-me');
  expect(requests[1]?.favorite_ids).toContain(237930);
  expect(requests[1]?.filters?.max_price_cents).toBe(2500);
  expect(requests[1]).not.toHaveProperty('saved');
  expect(requests[1]).not.toHaveProperty('history');
  await page.reload();
  await expect(page.getByRole('button', { name: 'Remove Transistor from favorites' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toHaveValue('2500');
  await page.getByRole('link', { name: 'Saved games (1)' }).click();
  await expect(page).toHaveURL(/\/saved$/);
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toBeVisible();
  await expect(page.getByText('Portal 2 · Not For Me', { exact: true })).toBeVisible();
  await expect(page.locator('.study-saved-list').last().locator('li')).toHaveCount(2);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toBeVisible();
  await page.route('**/api/v1/**', (route) => route.abort());
  await page.getByRole('button', { name: 'Check catalog availability' }).click();
  await expect(page.getByText(/couldn't connect to the service/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toBeVisible();
  await expect(page.getByText('Cached recorded USD', { exact: true })).toBeVisible();
});

test('played and negative feedback dismiss only their row without reordering or rerunning, persist and can be undone', async ({ page }) => {
  const requests = await mockCatalog(page);
  await page.goto('/current-original.html');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('group', { name: 'Recommendation feedback for Bastion' }).getByRole('button', { name: 'Already Played' }).click();
  await expect(page.locator('.study-game h3')).toHaveText(['Transistor', 'Portal 2', 'Hollow Knight']);
  expect(requests).toHaveLength(1);
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toHaveCount(0);
  await page.getByRole('group', { name: 'Recommendation feedback for Portal 2' }).getByRole('button', { name: 'Not For Me' }).click();
  await expect(page.locator('.study-game h3')).toHaveText(['Transistor', 'Hollow Knight']);
  expect(requests).toHaveLength(2);
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(3);
  expect(requests[2]?.feedback?.map((f) => f.kind)).toEqual(['already-played', 'not-for-me']);
  await expect(page.getByRole('heading', { name: 'Portal 2', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Interested', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Not this one/ })).toHaveCount(0);
  await page.reload();
  await page.getByRole('link', { name: 'Saved games (0)' }).click();
  await page.getByRole('button', { name: 'Remove feedback for Bastion' }).click();
  await expect(page.getByText('Bastion · Already Played', { exact: true })).toHaveCount(0);
});

test('hard controls explicitly clear stored defaults and no-match results never relax them', async ({ page }) => {
  const requests = await mockCatalog(page);
  await page.goto('/');
  await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeEnabled();
  await page.getByRole('slider', { name: 'Maximum recorded price', exact: true }).press('Home');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'No games match these filters.' })).toBeVisible();
  await expect(page.getByText(/Your filters have not been relaxed/)).toBeVisible();
  await page.getByRole('slider', { name: 'Maximum recorded price', exact: true }).press('End');
  const platforms = page.getByRole('group', { name: 'Required platform', exact: true });
  await platforms.locator('summary').click();
  await platforms.getByRole('button', { name: 'Clear required platform', exact: true }).click();
  await platforms.locator('summary').press('Escape');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect.poll(() => requests.length).toBe(2);
  expect(requests[1]?.filters).toMatchObject({ free_only: false, min_price_cents: 0, max_price_cents: 2500, platforms: [], required_genres: [] });
});

test('changing and restoring criteria during a request does not leave discovery disabled', async ({ page }) => {
  await mockCatalog(page); await page.goto('/');
  let finish: () => void = () => {};
  const held = new Promise<void>((resolve) => { finish = resolve; });
  let calls = 0;
  await page.route('**/api/v1/discover', async (route) => {
    if (++calls === 1) await held;
    await route.fulfill({ json: discovery(route.request().postDataJSON()) }).catch(() => {});
  });
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Finding games…', exact: true })).toBeDisabled();
  await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeEnabled();
  await page.getByRole('slider', { name: 'Maximum recorded price', exact: true }).press('Home');
  await page.getByRole('slider', { name: 'Maximum recorded price', exact: true }).press('End');
  await page.getByRole('slider', { name: 'Maximum recorded price', exact: true }).press('PageDown');
  await page.getByRole('slider', { name: 'Maximum recorded price', exact: true }).press('PageDown');
  await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toHaveValue('2000');
  await expect(page.getByRole('button', { name: 'Find my next game', exact: true })).toBeEnabled();
  finish();
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toBeVisible();
});

test('changing taste during a saved availability check still releases its checking state', async ({ page }) => {
  await mockCatalog(page); await page.goto('/');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  await page.goto('/saved');
  let finish: () => void = () => {};
  const held = new Promise<void>((resolve) => { finish = resolve; });
  await page.route('**/api/v1/games/resolve', async (route) => {
    await held;
    await route.fulfill({ json: { catalog_version: 'fixture-v1', items: [catalog[1]], unknown_ids: [] } });
  });
  await page.getByRole('button', { name: 'Check catalog availability', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Checking…', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Add favorite', exact: true }).click();
  finish();
  await expect(page.getByRole('button', { name: 'Check catalog availability', exact: true })).toBeEnabled();
});

test('clear cancels an in-flight recommendation and removes only this app’s local/session data', async ({ page }) => {
  await mockCatalog(page);
  await page.goto('/');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  await page.evaluate(() => { localStorage.setItem('unrelated', 'keep'); sessionStorage.setItem('unrelated', 'keep'); sessionStorage.setItem('game-discovery:conversation', 'old'); });
  let finish: () => void = () => {};
  const held = new Promise<void>((resolve) => { finish = resolve; });
  await page.route('**/api/v1/discover', async (route) => { await held; await route.fulfill({ json: discovery() }).catch(() => {}); });
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Finding games…', exact: true })).toBeDisabled();
  await page.getByText('Your device data', { exact: true }).click();
  await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
  finish();
  await expect(page.getByRole('link', { name: 'Saved games (0)' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toHaveCount(0);
  const stored = await page.evaluate((key) => ({ guest: localStorage.getItem(key), session: sessionStorage.getItem('game-discovery:conversation'), otherLocal: localStorage.getItem('unrelated'), otherSession: sessionStorage.getItem('unrelated') }), GUEST_KEY);
  expect(stored).toEqual({ guest: null, session: null, otherLocal: 'keep', otherSession: 'keep' });
});

test('same-browser tabs synchronize saves and clearing invalidates another tab’s pending work', async ({ context, page }) => {
  await mockCatalog(page); await page.goto('/');
  const other = await context.newPage(); await mockCatalog(other); await other.goto('/');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  await expect(other.getByRole('link', { name: 'Saved games (1)' })).toBeVisible();
  await other.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await other.getByRole('textbox', { name: 'Message the assistant' }).fill('Keep this chat only until data is cleared.');
  await other.getByRole('button', { name: 'Close game assistant', exact: true }).click();
  let finish: () => void = () => {};
  const held = new Promise<void>((resolve) => { finish = resolve; });
  await other.route('**/api/v1/discover', async (route) => { await held; await route.fulfill({ json: discovery() }).catch(() => {}); });
  await other.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(other.getByRole('button', { name: 'Finding games…', exact: true })).toBeDisabled();
  await page.getByText('Your device data', { exact: true }).click();
  await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
  finish();
  await expect(other.getByRole('link', { name: 'Saved games (0)' })).toBeVisible();
  await expect(other.getByText('Saved data was cleared in another tab.', { exact: true })).toBeVisible();
  await expect(other.getByRole('heading', { name: 'Bastion', exact: true })).toHaveCount(0);
  expect(await other.evaluate((key) => localStorage.getItem(key), GUEST_KEY)).toBeNull();
  expect(await other.evaluate(() => sessionStorage.getItem('game-discovery:assistant'))).toBeNull();
  await other.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(other.getByRole('textbox', { name: 'Message the assistant' })).toHaveValue('');
});

test('corrupt or future device data is not overwritten and the user can explicitly recover', async ({ page }) => {
  await mockCatalog(page);
  await page.addInitScript((key) => localStorage.setItem(key, '{"version":99}'), GUEST_KEY);
  await page.goto('/');
  await expect(page.getByText(/saved copy hasn’t been changed/)).toBeVisible();
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  expect(await page.evaluate((key) => localStorage.getItem(key), GUEST_KEY)).toBe('{"version":99}');
  await page.getByText('Your device data', { exact: true }).click();
  await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Saved games (0)' })).toBeVisible();
  expect(await page.evaluate((key) => localStorage.getItem(key), GUEST_KEY)).toBeNull();
});

test('blocked persistence is truthful and the catalog remains useful in memory', async ({ page }) => {
  await page.addInitScript(() => { Storage.prototype.setItem = () => { throw new DOMException('Blocked', 'QuotaExceededError'); }; });
  await mockCatalog(page); await page.goto('/');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Saved games (1)' })).toBeVisible();
  await expect(page.locator('footer').getByText(/Temporary in this tab/)).toBeVisible();
  await expect(page.getByText(/couldn’t save these changes/)).toBeVisible();
});

test('removed favorites and saved IDs are retained with an honest availability state', async ({ page }) => {
  await mockCatalog(page);
  await page.goto('/');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  await page.route('**/api/v1/games/resolve', (route) => route.fulfill({ json: { catalog_version: 'fixture-v2', items: [], unknown_ids: route.request().postDataJSON().app_ids } }));
  await page.reload();
  await expect(page.getByText(/no longer available in our catalog/)).toBeVisible();
  await page.goto('/saved');
  await page.getByRole('button', { name: 'Check catalog availability' }).click();
  await expect(page.getByText(/No longer available in the active catalog/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Bastion', exact: true })).toBeVisible();
});

test('desktop/mobile keyboard, picker, evidence and saved page remain accessible in Current', async ({ page }) => {
  await mockCatalog(page);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/');
    await page.keyboard.press('Tab');
    await expect(page.getByRole('link', { name: 'Skip to your taste', exact: true })).toBeFocused();
    await page.getByText('Change favorites', { exact: true }).click();
    await page.getByRole('button', { name: 'Search', exact: true }).click();
    await expect(page.locator('.study-pick-game')).toHaveCount(catalog.length);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.getByText('Change favorites', { exact: true }).click();
    await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
    const evidence = page.locator('.study-game summary').first();
    await evidence.focus(); await page.keyboard.press('Enter');
    await expect(page.locator('.study-game details').first()).toHaveAttribute('open', '');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.getByRole('button', { name: 'Save Bastion', exact: true }).click();
    await page.goto('/saved');
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.evaluate(() => localStorage.clear());
  }
});
