import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { ASSISTANT_KEY, boundChat, decodeAssistant, emptyAssistant, readAssistant, writeAssistant } from '../src/assistant-session';
import { SERVER_ASSISTANT_KEY } from '../src/server-assistant-session';
import { GUEST_KEY } from '../src/guest-store';
import { discovery, mockAssistant, mockCatalog } from './fixtures';

async function chatCatalog(page: Page) {
  const main = await mockCatalog(page);
  const { requests: chat } = await mockAssistant(page, (body, previous) => {
    const excluded = [body.message, ...previous.map(e => e.input)].some(text => /played|don't like/i.test(text)) ? [107100] : [];
    const result = discovery({ filters: { max_price_cents: 2000, excluded_ids: excluded } });
    const games = /hello/i.test(body.message) ? [] : result.results.slice(0, 2);
    return { message: games.length ? "Here are a couple of catalog options. Tell me if you'd like a different direction." : 'Hello! What would you like to play?', games, notices: ['Recorded USD, not live prices.'] };
  });
  return { main, chat };
}
async function say(page: Page, text: string) {
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill(text);
  await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await expect(page.locator('.assistant-thinking')).toHaveCount(0);
}

test('floating invitation can be dismissed and starter prompts prepare a draft without calling AI', async ({ page }) => {
  const { chat } = await chatCatalog(page);
  await page.goto('/');
  await expect(page.getByRole('complementary', { name: 'Game assistant invitation' })).toBeVisible();
  await page.getByRole('button', { name: 'Dismiss assistant greeting', exact: true }).click();
  await expect(page.getByRole('complementary', { name: 'Game assistant invitation' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Ask the assistant', exact: true })).toBeFocused();
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await page.getByRole('button', { name: 'A story to get lost in', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toHaveValue('I want a game with a memorable story. Help me find one.');
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toBeFocused();
  expect(chat).toHaveLength(0);
  await expect(page.getByRole('dialog')).not.toContainText('A separate conversation.');
  await expect(page.getByRole('dialog')).not.toContainText('Up to 20 recent messages');
  await page.getByRole('button', { name: 'Close game assistant', exact: true }).click();
  await expect(page.getByRole('complementary', { name: 'Game assistant invitation' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toHaveValue('I want a game with a memorable story. Help me find one.');
});

test('no-game chat replies omit catalog notices, including after reload, while game replies retain them', async ({ page }) => {
  await chatCatalog(page); await page.goto('/');
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await say(page, 'Hello');
  await expect(page.locator('.assistant-message-assistant')).toHaveCount(1);
  await expect(page.locator('.assistant-notices')).toHaveCount(0);
  await page.reload();
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(page.getByRole('log')).toContainText('Hello! What would you like to play?');
  await expect(page.locator('.assistant-notices')).toHaveCount(0);
  await say(page, 'Story and combat');
  await expect(page.locator('.assistant-game')).toHaveCount(2);
  await expect(page.locator('.assistant-notices')).toHaveText('Recorded USD, not live prices.');
});

test('chat and main discovery have separate inputs and chat never changes the main shortlist or controls', async ({ page }) => {
  const { main, chat } = await chatCatalog(page);
  await page.goto('/');
  await expect(page.getByRole('textbox', { name: 'What are you looking for?' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.locator('.study-game h3')).toHaveText(['Bastion', 'Transistor', 'Portal 2', 'Hollow Knight']);
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toBeFocused();
  await say(page, 'Linux co-op under $40');
  await expect(page.locator('.assistant-game')).toHaveCount(2);
  expect(Object.keys(chat[0]!).sort()).toEqual(['conversation_id', 'message', 'revision', 'token', 'turn_id']);
  expect(chat[0]).not.toHaveProperty('state');
  expect(chat[0]).not.toHaveProperty('messages');
  expect(main).toHaveLength(1);
  expect(main[0]).not.toHaveProperty('query');
  expect(main[0]).not.toHaveProperty('conversation');
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key)!).preferences.max_price_cents, GUEST_KEY)).toBe(2000);
  await expect(page.locator('.study-game h3')).toHaveText(['Bastion', 'Transistor', 'Portal 2', 'Hollow Knight']);
});

test('chat card details expand locally with only Save and Steam, sharing bookmarks but no feedback', async ({ page }) => {
  await chatCatalog(page); await page.goto('/');
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await say(page, 'Story and combat');
  const card = page.locator('.assistant-game').first();
  await expect(card.getByRole('button', { name: 'Save Bastion', exact: true })).toBeHidden();
  await card.locator('summary').first().click();
  await expect(card.locator('.game-facts')).toContainText('Genre');
  await expect(card.locator('.game-facts')).toContainText('Play style');
  await expect(card.locator('.game-facts')).toContainText('Platforms');
  await expect(card.locator('.game-price-note')).toContainText('Price recorded');
  await expect(card).not.toContainText('Catalog sources');
  await card.getByRole('button', { name: 'Save Bastion', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Saved games (1)' })).toBeVisible();
  await expect(card.getByRole('link', { name: /View on Steam/ })).toHaveAttribute('href', 'https://store.steampowered.com/app/107100/');
  await expect(card.getByRole('button', { name: 'Not For Me' })).toHaveCount(0);
  await expect(card.getByRole('button', { name: 'Already Played' })).toHaveCount(0);
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key)!).feedback, GUEST_KEY)).toEqual([]);
});

test('chat-local rejection carries forward and conversation survives close and reload; New chat clears only chat', async ({ page }) => {
  const { chat } = await chatCatalog(page); await page.goto('/');
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await page.getByRole('button', { name: 'Save Portal 2', exact: true }).click();
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await say(page, 'Story and combat'); await expect(page.locator('.assistant-game')).toHaveCount(2);
  await say(page, 'I already played Bastion'); await expect(page.locator('.assistant-message-assistant')).toHaveCount(2);
  await say(page, 'More like those'); await expect(page.locator('.assistant-message-assistant')).toHaveCount(3);
  expect(chat[2]?.conversation_id).toBe(chat[0]?.conversation_id);
  expect(chat[2]?.revision).toBe(2);
  await expect(page.locator('.assistant-message-assistant').last()).not.toContainText('Bastion');
  await page.getByRole('button', { name: 'Close game assistant', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Ask the assistant', exact: true })).toBeFocused();
  await page.reload(); await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(page.getByRole('log')).toContainText('I already played Bastion');
  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  await page.getByRole('button', { name: 'Start new chat', exact: true }).click();
  await expect(page.getByRole('log')).not.toContainText('I already played Bastion');
  expect(await page.evaluate(key => sessionStorage.getItem(key), ASSISTANT_KEY)).toBeNull();
  await expect(page.getByRole('link', { name: 'Saved games (1)' })).toBeVisible();
});

test('chat unavailable errors preserve the failed message and retry does not duplicate it', async ({ page }) => {
  await chatCatalog(page); await page.goto('/');
  await page.route('**/api/v2/assistant', route => route.fulfill({ status: 503, json: { code: 'chat_provider_unavailable', request_id: 'test' } }));
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await say(page, 'Hello'); await expect(page.getByRole('alert')).toContainText("can't reach its AI service");
  await page.getByRole('button', { name: 'Retry message' }).click();
  await expect(page.locator('.assistant-message-user')).toHaveCount(1);
  await page.getByRole('button', { name: 'Close game assistant', exact: true }).click();
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.locator('.study-game')).toHaveCount(4);
});

test('New chat and Clear my saved data reject late chat responses', async ({ page }) => {
  await chatCatalog(page); await page.goto('/');
  let finish: () => void = () => {};
  const held = new Promise<void>(resolve => { finish = resolve; });
  await page.route('**/api/v2/assistant', async route => { await held; await route.fulfill({ status: 503, json: { code: 'chat_unavailable', message: 'Late reply', request_id: 'test' } }).catch(() => {}); });
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill('Hello');
  await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  await page.getByRole('button', { name: 'Start new chat', exact: true }).click();
  finish(); await expect(page.getByRole('log')).not.toContainText('Hello');
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill('Draft');
  await page.getByRole('button', { name: 'Close game assistant', exact: true }).click();
  await page.getByText('Your device data', { exact: true }).click();
  await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
  expect(await page.evaluate(key => sessionStorage.getItem(key), SERVER_ASSISTANT_KEY)).toBeNull();
});

test('corrupt chat storage is protected until an explicit New chat', async ({ page }) => {
  await chatCatalog(page); await page.goto('/');
  await page.evaluate(key => sessionStorage.setItem(key, '{broken'), ASSISTANT_KEY);
  await page.reload(); await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(page.getByRole('dialog').getByRole('status')).toContainText('saved copy hasn’t been changed');
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill('Temporary draft');
  expect(await page.evaluate(key => sessionStorage.getItem(key), ASSISTANT_KEY)).toBe('{broken');
  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  await page.getByRole('button', { name: 'Start new chat', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toHaveValue('');
  expect(await page.evaluate(key => sessionStorage.getItem(key), ASSISTANT_KEY)).toBeNull();
});

test('assistant is keyboard accessible and fits desktop and mobile with catalog cards expanded', async ({ page }) => {
  test.setTimeout(120000);
  await chatCatalog(page); const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
    await say(page, 'Story and combat');
    await page.locator('.assistant-game').last().locator('summary').first().click();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    const box = await page.getByRole('dialog').boundingBox();
    expect(box!.x).toBeGreaterThanOrEqual(0); expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    await expect(page.getByRole('dialog')).toHaveAttribute('aria-modal', width === 390 ? 'true' : 'false');
    expect(await page.locator('main').evaluate(element => element.hasAttribute('inert'))).toBe(width === 390);
    if (width === 390) {
      await page.getByRole('button', { name: 'New chat', exact: true }).focus();
      await page.keyboard.press('Shift+Tab');
      await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(page.getByRole('button', { name: 'New chat', exact: true })).toBeFocused();
    }
    await page.getByRole('textbox', { name: 'Message the assistant' }).press('Escape');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(await page.locator('main').evaluate(element => element.hasAttribute('inert'))).toBe(false);
    await expect(page.getByRole('button', { name: 'Ask the assistant', exact: true })).toBeFocused();
  }
  expect(errors).toEqual([]);
});

test('assistant session bounds messages, cards and malformed data without importing main defaults', () => {
  const values = new Map<string, string>();
  const port = { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => { values.set(key, value); }, removeItem: (key: string) => { values.delete(key); } };
  const value = emptyAssistant();
  value.messages = boundChat(Array.from({ length: 30 }, () => ({ role: 'user', content: 'x'.repeat(2000), games: [], notices: [] })));
  expect(value.messages).toHaveLength(6);
  expect(value.state.criteria.max_price_cents).toBeNull();
  expect(writeAssistant(value, port)).toBe(true);
  expect(decodeAssistant(JSON.stringify({ ...value, favorites: [1145360] }))).not.toHaveProperty('favorites');
  expect(() => decodeAssistant(JSON.stringify({ ...value, state: { ...value.state, favorites: [1145360] } }))).toThrow();
  values.set(ASSISTANT_KEY, '{broken');
  expect(readAssistant(port).writable).toBe(false);
  expect(values.get(ASSISTANT_KEY)).toBe('{broken');
  expect(readAssistant(null).notice).toContain('reloading may lose');
});
