// Legacy decoder regressions plus their server-memory UI replacements. The
// pre-revision classifier-wire browser suite is retained in the prechange zip.
import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { ASSISTANT_KEY, boundChat, emptyAssistant, readAssistant, writeAssistant } from '../src/assistant-session';
import { decodeChatState, neutralChatCriteria } from '../src/chat-state';
import { SERVER_ASSISTANT_KEY, decodeServerAssistant, emptyAssistant as emptyServer, readAssistant as readServer, writeAssistant as writeServer } from '../src/server-assistant-session';
import { freshConversation, type AssistantTurn } from '../src/api/assistant';
import { mockAssistant, mockCatalog, discovery } from './fixtures';

const legacy = () => ({ version: 1, draft: 'Keep this draft', state: { criteria: { ...neutralChatCriteria(), max_price_cents: 2000, excluded_ids: [620] },
  query: 'old story', excluded_ids: [107100], shown_ids: [237930] },
  messages: [{ role: 'assistant', content: 'An earlier catalog option.', games: discovery().results.slice(0, 1), notices: ['Recorded USD.'] }] });
function storage(raw: string | null = null) {
  const values = new Map<string, string>(raw === null ? [] : [[ASSISTANT_KEY, raw]]);
  return { values, port: { getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => { values.set(key, value); }, removeItem: (key: string) => { values.delete(key); } } };
}
async function open(page: Page) { await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click(); }
async function say(page: Page, text: string) {
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill(text);
  await page.getByRole('button', { name: 'Send message', exact: true }).click();
  await expect(page.locator('.assistant-thinking')).toHaveCount(0);
}

test('legacy decoder retains transcript/cards/draft and quarantines every requirement', () => {
  const { values, port } = storage(JSON.stringify(legacy()));
  const loaded = readAssistant(port);
  expect(loaded.writable).toBe(true);
  expect(loaded.value.version).toBe(2);
  expect(loaded.value.draft).toBe('Keep this draft');
  expect(loaded.value.messages).toEqual(legacy().messages);
  expect(loaded.value.state.criteria).toEqual(neutralChatCriteria());
  expect(loaded.value.state.legacy_criteria?.max_price_cents).toBe(2000);
  expect(loaded.value.state.legacy_excluded_ids).toEqual([107100, 620]);
  expect(JSON.parse(values.get(ASSISTANT_KEY)!).version).toBe(2);
});
test('legacy future, corrupt, oversized and invalid-provenance storage remain protected', () => {
  for (const raw of ['{broken', 'x'.repeat(500001), JSON.stringify({ ...emptyAssistant(), version: 3 }),
    JSON.stringify({ ...emptyAssistant(), state: { version: 2, criteria: { max_price_cents: 2000 } } })]) {
    const { values, port } = storage(raw);
    expect(readAssistant(port).writable).toBe(false); expect(values.get(ASSISTANT_KEY)).toBe(raw);
  }
});
test('legacy v2 neutral state validates origins, uniqueness and main-data isolation', () => {
  expect(decodeChatState({ version: 2 })).toEqual(emptyAssistant().state);
  for (const state of [{ version: 2, user_turn: 1, provenance: { platforms: { user_turn: 2 } } },
    { version: 2, shown_ids: [620, 620] }, { version: 2, query: 'combat' },
    { version: 2, criteria: { excluded_ids: [620] } }, { version: 2, favorites: [620] }]) expect(() => decodeChatState(state)).toThrow();
});
test('blocked legacy migration writes preserve original and continue quarantined', () => {
  const loaded = readAssistant({ getItem: () => JSON.stringify(legacy()), setItem: () => { throw Error('blocked'); }, removeItem: () => {} });
  expect(loaded.writable).toBe(false); expect(loaded.value.messages).toEqual(legacy().messages);
  expect(loaded.notice).toContain('older copy could not be replaced');
});
test('legacy cache bounds still retain sourced state for old clients', () => {
  const value = emptyAssistant();
  value.state = decodeChatState({ version: 2, user_turn: 40, criteria: { required_modes: ['multiplayer'] }, provenance: { required_modes: { user_turn: 1 } } });
  value.messages = boundChat(Array.from({ length: 30 }, (_, i) => ({ role: 'assistant', content: `Later ${i}`, games: discovery().results, notices: [] })));
  const { port } = storage(); expect(writeAssistant(value, port)).toBe(true);
  expect(readAssistant(port).value.state.provenance.required_modes?.user_turn).toBe(1);
  expect(readAssistant(port).value.messages.reduce((n, m) => n + m.games.length, 0)).toBe(12);
});
test('server cache is not the archive and retains stable capability/pending identity', () => {
  const { port } = storage(); const value = emptyServer(); value.remote = freshConversation(); value.remoteReady = true;
  value.messages = Array.from({ length: 60 }, (_, i) => ({ role: 'user', content: `Message ${i}`, games: [], notices: [] })); value.totalTurns = 60;
  expect(writeServer(value, port)).toBe(true);
  const restored = readServer(port).value;
  expect(restored.messages).toHaveLength(20); expect(restored.historyBefore).toBe(40); expect(restored.remote).toEqual(value.remote);
  restored.messages.push({ role: 'user', content: 'Pending', games: [], notices: [] });
  restored.messages = restored.messages.slice(-20);
  restored.pending = { ...restored.remote!, turn_id: crypto.randomUUID(), message: 'Pending' };
  expect(decodeServerAssistant(JSON.stringify(restored)).pending).toEqual(restored.pending);
  expect(() => decodeServerAssistant(JSON.stringify({ ...restored, pending: { ...restored.pending, token: 'z'.repeat(43) } }))).toThrow();
  expect(() => decodeServerAssistant(JSON.stringify({ ...restored, remote: { ...restored.remote, favorite_ids: [1145360] } }))).toThrow();
});
test('corrupt/future server envelopes and pending mismatches are protected', () => {
  const { values, port } = storage();
  for (const raw of ['{broken', JSON.stringify({ ...emptyServer(), version: 9 }), JSON.stringify({ ...emptyServer(), remote: { token: 'secret' } })]) {
    values.set(SERVER_ASSISTANT_KEY, raw);
    expect(readServer(port).writable).toBe(false); expect(values.get(SERVER_ASSISTANT_KEY)).toBe(raw);
  }
});

test('browser imports retained legacy messages/cards without main criteria or hidden state', async ({ page }) => {
  await mockCatalog(page); const { requests } = await mockAssistant(page);
  const creates: unknown[] = [];
  await page.route('**/api/v2/assistant/conversations', route => { creates.push(route.request().postDataJSON()); return route.fallback(); });
  await page.goto('/'); await page.evaluate(({ key, value }) => sessionStorage.setItem(key, value), { key: ASSISTANT_KEY, value: JSON.stringify(legacy()) });
  await page.reload(); await open(page);
  await expect(page.getByRole('log')).toContainText('An earlier catalog option.');
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toHaveValue('Keep this draft');
  await say(page, 'What would you suggest?');
  expect(requests[0]).not.toHaveProperty('state'); expect(requests[0]).not.toHaveProperty('favorite_ids');
  expect(creates[0]).toMatchObject({ messages: [{ role: 'assistant', content: 'An earlier catalog option.', game_ids: [107100] }] });
  expect(JSON.stringify(creates[0])).not.toContain('max_price_cents');
  await page.reload(); await open(page); await expect(page.getByRole('log')).toContainText('An earlier catalog option.');
});

test('pending retry survives reload with exact turn and capability, without automatic inference', async ({ page }) => {
  await mockCatalog(page);
  const requests: AssistantTurn[] = [];
  await page.route('**/api/v2/assistant', route => {
    const body = route.request().postDataJSON() as AssistantTurn; requests.push(body);
    return requests.length === 1 ? route.fulfill({ status: 503, json: { code: 'chat_provider_unavailable' } })
      : route.fulfill({ json: { request_id: 'recovered', message: 'Recovered reply.', games: [], notices: [], revision: 1, total_turns: 1 } });
  });
  await page.goto('/'); await open(page); await say(page, 'Please remember this request');
  await expect(page.getByRole('alert')).toBeVisible(); await page.reload(); await open(page);
  await expect(page.getByRole('log')).toContainText('Please remember this request'); expect(requests).toHaveLength(1);
  await page.getByRole('button', { name: 'Retry message', exact: true }).click();
  await expect(page.getByRole('log')).toContainText('Recovered reply.'); expect(requests[1]).toEqual(requests[0]);
  await expect(page.locator('.assistant-message-user')).toHaveCount(1);
});

test('long server history is restored and earlier pages remain accessible beyond browser cache', async ({ page }) => {
  await mockCatalog(page); const { conversations } = await mockAssistant(page);
  await page.goto('/'); await open(page); await say(page, 'Initial request');
  const row = [...conversations.values()][0]!;
  row.events = Array.from({ length: 35 }, (_, i) => ({ id: crypto.randomUUID(), input: `Original turn ${i}`, status: 'done',
    output: { request_id: `r${i}`, message: `Answer ${i}`, games: [], notices: [], revision: i+1, total_turns: i+1 } })); row.revision = 35;
  await page.reload(); await open(page); await expect(page.getByRole('log')).toContainText('Original turn 34');
  await expect(page.getByRole('log')).not.toContainText('Original turn 0');
  for (let i = 0; i < 3; i++) await page.getByRole('button', { name: 'Load earlier messages', exact: true }).click();
  await expect(page.getByRole('log')).toContainText('Original turn 0');
  expect(row.events).toHaveLength(35);
});

test('new chat erases the previous server record and sends an independent revision-zero turn', async ({ page }) => {
  await mockCatalog(page); const { requests, conversations } = await mockAssistant(page);
  await page.goto('/'); await open(page); await say(page, 'Remember my old preference');
  const old = requests[0]!.conversation_id;
  await page.getByRole('button', { name: 'New chat', exact: true }).click(); await page.getByRole('button', { name: 'Start new chat', exact: true }).click();
  await expect(page.locator('.assistant-message')).toHaveCount(0); expect(conversations.has(old)).toBe(false);
  await say(page, 'Hello in a fresh chat'); expect(requests[1]!.conversation_id).not.toBe(old); expect(requests[1]!.revision).toBe(0);
});

test('clear data waits for successful server erasure and retains access if the network fails', async ({ page }) => {
  await mockCatalog(page); await page.goto('/'); await open(page); await say(page, 'Keep my chat until erasure succeeds');
  await page.getByRole('button', { name: 'Close game assistant' }).click(); await page.getByText('Your device data', { exact: true }).click();
  await page.route('**/api/v2/assistant/forget', route => route.abort());
  await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('couldn’t erase the server chat');
  expect(await page.evaluate(key => sessionStorage.getItem(key), SERVER_ASSISTANT_KEY)).not.toBeNull();
  await page.unroute('**/api/v2/assistant/forget');
  await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
  await expect.poll(() => page.evaluate(key => sessionStorage.getItem(key), SERVER_ASSISTANT_KEY)).toBeNull();
});

test('history restoration preserves a draft typed before closing the panel', async ({ page }) => {
  await mockCatalog(page); await page.goto('/'); await open(page); await say(page, 'Initial request');
  await page.getByRole('button', { name: 'Close game assistant' }).click();
  let release: () => void = () => {};
  const held = new Promise<void>(resolve => { release = resolve; });
  let started: () => void = () => {};
  const requested = new Promise<void>(resolve => { started = resolve; });
  await page.route('**/api/v2/assistant/history', async route => { started(); await held; await route.fallback(); });
  await open(page); await requested;
  await page.getByRole('textbox', { name: 'Message the assistant' }).fill('Keep this new draft after history loads');
  await page.getByRole('button', { name: 'Close game assistant' }).click();
  const response = page.waitForResponse(r => r.url().endsWith('/api/v2/assistant/history'));
  release(); await response;
  await expect.poll(() => page.evaluate(key => JSON.parse(sessionStorage.getItem(key)!).draft, SERVER_ASSISTANT_KEY))
    .toBe('Keep this new draft after history loads');
  await page.reload(); await open(page);
  await expect(page.getByRole('textbox', { name: 'Message the assistant' })).toHaveValue('Keep this new draft after history loads');
});

test('failed history restoration retries without sending a model request and clears its error', async ({ page }) => {
  await mockCatalog(page); const { requests } = await mockAssistant(page);
  await page.goto('/'); await open(page); await say(page, 'An original message');
  await page.getByRole('button', { name: 'Close game assistant' }).click();
  let fail = true;
  await page.route('**/api/v2/assistant/history', route => fail
    ? route.fulfill({ status: 503, json: { code: 'database_unavailable' } }) : route.fallback());
  await open(page); await expect(page.getByRole('button', { name: 'Retry chat history', exact: true })).toBeVisible();
  fail = false;
  await page.getByRole('button', { name: 'Retry chat history', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByRole('log')).toContainText('An original message');
  expect(requests).toHaveLength(1);
});

test('assistant Markdown renders safely and survives reload without altering user text or cards', async ({ page }) => {
  const markdown = '# A few ideas\n\n## Why they fit\n\n* **Goals & assists:** A clear example.\n* *A second point* with `inline code`.\n\n1. Choose a style.\n2. Open the game card.\n\n> We can narrow it down together.\n\n'
    + '[Steam](https://store.steampowered.com/) [Unsafe](javascript:alert(1))\n\n'
    + '![Remote image](https://example.invalid/track.png)\n\n<script>window.markdownExecuted = true</script>\n\n<img src=x onerror="window.markdownExecuted=true">\n\n'
    + '```text\n' + 'long-code-without-spaces'.repeat(20) + '\n```';
  await mockCatalog(page);
  const { requests } = await mockAssistant(page, () => ({ message: markdown, games: discovery().results.slice(0, 1) }));
  const pageErrors: string[] = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto('/'); await open(page); await say(page, '**User input stays literal**');
  const prose = page.locator('.assistant-markdown');
  await expect(prose.getByRole('heading', { name: 'A few ideas', level: 3 })).toBeVisible();
  await expect(prose.getByRole('heading', { name: 'Why they fit', level: 3 })).toBeVisible();
  await expect(prose.locator('ul > li')).toHaveCount(2);
  await expect(prose.locator('ol > li')).toHaveCount(2);
  await expect(prose.locator('strong')).toHaveText('Goals & assists:');
  await expect(prose.locator('em')).toHaveText('A second point');
  await expect(prose.locator('blockquote')).toContainText('narrow it down');
  await expect(prose.getByRole('link', { name: /Steam/ })).toHaveAttribute('rel', 'noopener noreferrer');
  await expect(prose.getByRole('link', { name: 'Unsafe' })).toHaveCount(0);
  await expect(prose.locator('script, img, iframe')).toHaveCount(0);
  expect(await page.evaluate(() => Object.hasOwn(window, 'markdownExecuted'))).toBe(false);
  await expect(page.locator('.assistant-message-user .assistant-prose')).toHaveText('**User input stays literal**');
  await expect(page.locator('.assistant-message-user strong')).toHaveCount(0);
  await expect(page.locator('.assistant-game')).toHaveCount(1);
  const code = prose.getByRole('region', { name: 'Code block' });
  for (const [width, height] of [[1440, 1000], [390, 844], [320, 640]] as const) {
    await page.setViewportSize({ width, height });
    expect(await page.locator('.assistant-log').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
    expect(await code.evaluate(el => el.scrollWidth > el.clientWidth)).toBe(true);
    await code.focus(); await page.keyboard.press('ArrowRight');
    await expect.poll(() => code.evaluate(el => el.scrollLeft)).toBeGreaterThan(0);
    expect((await new AxeBuilder({ page }).include('#game-assistant').analyze()).violations).toEqual([]);
    await page.locator('.assistant-log').evaluate(el => { el.scrollTop = 0; });
    await page.locator('.assistant-panel').screenshot({ path: test.info().outputPath(`markdown-${width}.png`) });
  }
  await page.reload(); await open(page);
  await expect(prose.locator('strong')).toHaveText('Goals & assists:');
  expect(requests).toHaveLength(1);
  expect(pageErrors).toEqual([]);
});
