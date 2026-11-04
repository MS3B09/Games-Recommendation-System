import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mockCatalog } from './fixtures';
test.use({ timezoneId: 'America/New_York', locale: 'en-US' });

async function open(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
}
async function say(page: Page, text = 'Help me find a game to play with friends.') {
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill(text);
  await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await expect(page.locator('.assistant-thinking')).toHaveCount(0);
}

for (const [code, text, action] of [
  ['chat_daily_calls', "free chat allowance", 'Use Your taste'],
  ['chat_daily_units', "free chat allowance", 'Use Your taste'],
  ['chat_provider_limited', 'receiving too many requests', 'Retry message'],
  ['chat_busy', 'finishing another reply', 'Retry message'],
  ['chat_timeout', 'took too long', 'Retry message'],
  ['chat_provider_unavailable', "can't reach its AI service", 'Retry message'],
  ['chat_accounting_unavailable', "couldn't check whether chat", 'Retry message'],
  ['chat_invalid_answer', 'reliable answer', 'Edit message'],
  ['chat_message_too_long', '2,000 characters', 'Edit message'],
  ['chat_message_too_detailed', 'shorten it', 'Edit message'],
  ['chat_context_limit', 'conversation has become too long', 'New chat'],
  ['chat_evidence_unavailable', 'reliable game details', 'Use Your taste'],
  ['chat_unconfigured', "isn't available on this version", 'Use Your taste'],
  ['chat_service_configuration', 'because of a setup issue', 'Use Your taste'],
  ['chat_incompatible', 'needs an update', 'Refresh page'],
]) {
  test(`friendly ${code} exposes the right recovery without raw diagnostics`, async ({ page }) => {
    await mockCatalog(page);
    await page.route('**/api/v2/assistant', route => route.fulfill({ status: 503,
      json: { code, message: 'PRIVATE_DRIVER_PAYLOAD', request_id: 'PRIVATE_REQUEST_ID' } }));
    await open(page); await say(page);
    await expect(page.getByRole('alert')).toContainText(text!);
    await expect(page.getByRole('dialog')).not.toContainText('PRIVATE_');
    const actions = page.locator('.friendly-error-actions');
    await expect(actions.getByRole(action === 'Use Your taste' ? 'link' : 'button', { name: action!, exact: true })).toBeVisible();
    if (['Edit message', 'Use Your taste', 'New chat', 'Refresh page'].includes(action!)) await expect(actions.getByRole('button', { name: 'Retry message', exact: true })).toHaveCount(0);
    await expect(page.locator('.assistant-message-user')).toHaveCount(1);
  });
}

test('daily allowance shows local reset and survives New chat and reload without another request', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-28T12:00:00Z') });
  await mockCatalog(page);
  let calls = 0;
  await page.route('**/api/v2/assistant', route => { calls++; return route.fulfill({ status: 429,
    json: { code: 'chat_daily_calls', retry_at: '2026-10-29T00:00:00Z' } }); });
  await open(page); await say(page);
  await expect(page.getByRole('alert')).toContainText('available again at');
  await expect(page.getByRole('alert')).toContainText('8:00 PM EDT');
  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  await expect(page.getByRole('log')).toContainText('Help me find');
  await page.getByRole('button', { name: 'Keep chatting', exact: true }).click();
  await expect(page.locator('.assistant-message-user')).toHaveCount(1);
  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  await page.getByRole('button', { name: 'Start new chat', exact: true }).click();
  await expect(page.locator('.assistant-message-user')).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill('Another question');
  await expect(page.getByRole('button', { name: /Send available in/ })).toBeDisabled();
  await page.reload(); await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('free chat allowance');
  await expect(page.getByRole('button', { name: /Send available in/ })).toBeDisabled();
  expect(calls).toBe(1);
  await page.clock.fastForward(13 * 3600000);
  await expect(page.getByRole('button', { name: 'Send message', exact: true })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Retry message', exact: true })).toHaveCount(0);
  expect(calls).toBe(1);
});

test('cooldown expires without automatic retry and explicit retry sends the identical request', async ({ page }) => {
  await page.clock.install();
  await mockCatalog(page);
  const requests: unknown[] = [];
  await page.route('**/api/v2/assistant', route => {
    const body = route.request().postDataJSON();
    requests.push(body);
    if (requests.length === 2) return route.fulfill({ json: { request_id: 'recovered', message: 'Here is the recovered reply.', games: [], notices: [],
      revision: body.revision + 1, total_turns: 1 } });
    return route.fulfill({ status: 429, json: { code: 'chat_rate_limited', retry_at: new Date(Date.now() + 2000).toISOString() } });
  });
  await open(page); await say(page);
  await expect(page.getByRole('button', { name: /Try again in/ })).toBeDisabled();
  await expect(page.getByRole('alert')).toHaveText('Please wait a moment before sending another message.');
  await expect(page.getByRole('alert')).not.toContainText('You can try again after');
  await page.clock.fastForward(5000);
  await expect(page.getByRole('button', { name: 'Retry message', exact: true })).toBeEnabled();
  expect(requests).toHaveLength(1);
  await page.getByRole('button', { name: 'Retry message', exact: true }).click();
  await expect(page.locator('.assistant-thinking')).toHaveCount(0);
  expect(requests).toHaveLength(2);
  expect(requests[1]).toEqual(requests[0]);
  await expect(page.locator('.assistant-message-user')).toHaveCount(1);
  await expect(page.getByRole('log')).toContainText('Here is the recovered reply.');
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('invalid answer can be edited without duplicating the failed message', async ({ page }) => {
  await mockCatalog(page);
  await page.route('**/api/v2/assistant', route => route.fulfill({ status: 502, json: { code: 'chat_invalid_answer' } }));
  await open(page); await say(page, 'A question to revise');
  await page.getByRole('button', { name: 'Edit message', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toHaveValue('A question to revise');
  await expect(page.locator('.assistant-message-user')).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toBeFocused();
});

test('network failure is actionable and preserves the pending message', async ({ page }) => {
  await mockCatalog(page);
  await page.route('**/api/v2/assistant', route => route.abort('failed'));
  await open(page); await say(page);
  await expect(page.getByRole('alert')).toContainText('Check your internet connection');
  await expect(page.getByRole('button', { name: 'Retry message', exact: true })).toBeVisible();
  await expect(page.locator('.assistant-message-user')).toHaveCount(1);
});

test('a browser request timeout ends loading and offers retry rather than a connection diagnosis', async ({ page }) => {
  await mockCatalog(page);
  let release: () => void = () => {};
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v2/assistant', async route => { await held; await route.abort().catch(() => {}); });
  await open(page);
  await page.evaluate(() => {
    Object.defineProperty(AbortSignal, 'timeout', { value: () => {
      const controller = new AbortController();
      setTimeout(() => controller.abort(new DOMException('Timed out', 'TimeoutError')), 100);
      return controller.signal;
    } });
  });
  try {
    await say(page);
    await expect(page.getByRole('alert')).toContainText('took too long to reply');
    await expect(page.getByRole('button', { name: 'Retry message', exact: true })).toBeVisible();
    await expect(page.locator('.assistant-message-user')).toHaveCount(1);
  } finally { release(); }
});

for (const width of [1440, 1000, 900, 390, 320]) {
  test(`catalog connection error stays readable and retries successfully at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: width > 900 ? 1000 : 844 });
    await mockCatalog(page);
    let failed = true;
    let calls = 0;
    await page.route('**/api/v1/facets', route => {
      calls++;
      return failed ? route.abort('connectionrefused') : route.fallback();
    });
    await page.goto('/');
    const notice = page.locator('.study-boundaries > .friendly-error');
    await expect(notice.getByRole('alert')).toContainText("couldn't connect");
    const controlsBox = await page.locator('.study-limits').boundingBox();
    const noticeBox = await notice.boundingBox();
    expect(Math.abs(noticeBox!.x - controlsBox!.x)).toBeLessThan(1);
    expect(Math.abs(noticeBox!.width - controlsBox!.width)).toBeLessThan(1);
    const retry = notice.getByRole('button', { name: 'Retry catalog controls', exact: true });
    expect((await retry.boundingBox())!.height).toBeLessThanOrEqual(50);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await notice.scrollIntoViewIfNeeded();
    await page.screenshot({ path: testInfo.outputPath(`catalog-connection-${width}.png`), fullPage: true });
    expect(calls).toBe(1);
    failed = false;
    await retry.click();
    await expect(notice).toHaveCount(0);
    await expect(page.getByRole('slider', { name: 'Maximum recorded price' })).toBeEnabled();
    await expect(page.getByRole('slider', { name: 'Maximum recorded price' })).toHaveValue('2000');
    expect(calls).toBe(2);
  });
}

for (const width of [1440, 390, 320]) {
  test(`friendly error states are accessible and fit ${width}px`, async ({ page }, testInfo) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : width === 320 ? 640 : 844 });
    await mockCatalog(page);
    const pageErrors: string[] = []; page.on('pageerror', error => pageErrors.push(error.message));
    for (const code of ['chat_daily_calls', 'chat_invalid_answer', 'chat_context_limit']) {
      await page.route('**/api/v2/assistant', route => route.fulfill({ status: 503, json: { code,
        ...(code === 'chat_daily_calls' ? { retry_at: new Date(Date.now() + 3600000).toISOString() } : {}) } }));
      await open(page); await say(page);
      await expect(page.getByRole('alert')).toBeVisible();
      const header = await page.locator('.assistant-header').boundingBox();
      const input = await page.getByRole('textbox', { name: 'Message the assistant' }).boundingBox();
      expect(header!.height).toBeLessThanOrEqual(64);
      expect(input!.height).toBeGreaterThanOrEqual(44);
      expect(input!.height).toBeLessThanOrEqual(48);
      expect(await page.locator('.assistant-status').evaluate(element => element.scrollHeight <= element.clientHeight)).toBe(true);
      expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
      await page.screenshot({ path: testInfo.outputPath(`${code}-${width}.png`), fullPage: true });
      await page.evaluate(() => { sessionStorage.removeItem('game-discovery:assistant'); sessionStorage.removeItem('game-discovery:assistant-v3'); sessionStorage.removeItem('game-discovery:assistant-availability'); });
    }
    expect(pageErrors).toEqual([]);
  });
}
