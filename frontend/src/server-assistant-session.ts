import { isRecommendation } from './api/discovery';
import { forgetConversation, isConversation, type AssistantTurn, type Conversation, type ArchiveEvent } from './api/assistant';
import { readAssistant as readLegacy, clearAssistant as clearLegacy, type ChatMessage } from './assistant-session';

export { assistantPort } from './assistant-session';
export const SERVER_ASSISTANT_KEY = 'game-discovery:assistant-v3';
type Port = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
export type AssistantSession = { version: 3; messages: ChatMessage[]; draft: string; pending: AssistantTurn | null;
  remote: Conversation | null; historyBefore: number; totalTurns: number };
export type ServerAssistantSession = AssistantSession & { remoteReady: boolean };
export const emptyAssistant = (): ServerAssistantSession => ({ version: 3, messages: [], draft: '', pending: null, remote: null, remoteReady: false, historyBefore: 0, totalTurns: 0 });
const port = (): Port | null => { try { return window.sessionStorage; } catch { return null; } };
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
// This is only a reload cache. The server archive is the source of conversation memory.
export function boundChat(messages: ChatMessage[]): ChatMessage[] {
  const cache = messages.slice(-20);
  while (cache.reduce((n, m) => n + m.content.length, 0) > 16000) cache.shift();
  let cards = 0;
  return cache.slice().reverse().map(m => { cards += m.games.length; return { ...m, games: cards <= 12 ? m.games : [] }; }).reverse();
}
export function decodeServerAssistant(raw: string): ServerAssistantSession {
  if (raw.length > 500000) throw Error('Oversized cache');
  const v: unknown = JSON.parse(raw);
  if (!object(v) || Object.keys(v).some(k => !['version', 'messages', 'draft', 'pending', 'remote', 'remoteReady', 'historyBefore', 'totalTurns'].includes(k))
    || v.version !== 3 || typeof v.draft !== 'string' || v.draft.length > 2000
    || !Array.isArray(v.messages) || v.messages.length > 20 || !v.messages.every(m => object(m)
      && ['user', 'assistant'].includes(String(m.role)) && typeof m.content === 'string' && m.content.length <= 4000
      && Array.isArray(m.games) && m.games.length <= 4 && m.games.every(isRecommendation)
      && Array.isArray(m.notices) && m.notices.every((n: unknown) => typeof n === 'string'))
    || typeof v.remoteReady !== 'boolean' || !(v.remote === null || isConversation(v.remote)) || !Number.isInteger(v.historyBefore) || Number(v.historyBefore) < 0
    || !Number.isInteger(v.totalTurns) || Number(v.totalTurns) < 0) throw Error('Invalid server chat cache');
  if (v.remote && Object.keys(v.remote).some(k => !['conversation_id', 'token', 'revision'].includes(k))) throw Error('Unknown conversation fields');
  if (v.pending !== null && (!isConversation(v.pending) || !object(v.pending) || !('turn_id' in v.pending) || !('message' in v.pending) || typeof v.pending.turn_id !== 'string'
    || Object.keys(v.pending).some(k => !['conversation_id', 'token', 'revision', 'turn_id', 'message'].includes(k))
    || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v.pending.turn_id) || typeof v.pending.message !== 'string' || !v.pending.message.trim()
    || v.pending.message.length > 2000 || !v.remote || v.pending.conversation_id !== v.remote.conversation_id
    || v.pending.token !== v.remote.token || v.pending.revision !== v.remote.revision
    || v.messages.at(-1)?.role !== 'user' || v.messages.at(-1)?.content !== v.pending.message)) throw Error('Invalid pending turn');
  return v as unknown as ServerAssistantSession;
}
export function readAssistant(storage = port()) {
  if (!storage) return { value: emptyAssistant(), writable: false, notice: 'Browser storage is unavailable. Keep this tab open to retain access to your server chat.' };
  try {
    const raw = storage.getItem(SERVER_ASSISTANT_KEY);
    if (raw !== null) return { value: decodeServerAssistant(raw), writable: true, notice: '' };
    const legacy = readLegacy(storage);
    return { value: { ...emptyAssistant(), messages: legacy.value.messages, draft: legacy.value.draft },
      writable: legacy.writable, notice: legacy.value.messages.length ? 'Your retained tab messages will be imported when you next send. Earlier messages outside that old cache are unavailable.' : legacy.notice };
  } catch { return { value: emptyAssistant(), writable: false, notice: 'This chat cache could not be opened. Its saved copy has been protected. Start a new chat to continue.' }; }
}
export function writeAssistant(value: ServerAssistantSession, storage = port()): boolean {
  try {
    if (!storage) return false;
    const messages = boundChat(value.messages);
    const stored = { ...value, messages, historyBefore: Math.max(value.historyBefore, value.totalTurns - messages.filter(m => m.role === 'user').length) };
    const raw = JSON.stringify(stored); decodeServerAssistant(raw); storage.setItem(SERVER_ASSISTANT_KEY, raw); return true;
  } catch { return false; }
}
export function clearAssistant(storage = port()): boolean {
  try { if (!storage) return false; storage.removeItem(SERVER_ASSISTANT_KEY); clearLegacy(storage); return true; } catch { return false; }
}
export async function eraseServerAssistant() {
  const saved = readAssistant();
  if (saved.value.remote) await forgetConversation(saved.value.remote, new AbortController().signal);
}
export function archiveMessages(events: ArchiveEvent[]): ChatMessage[] {
  return events.flatMap(e => [
    ...(e.input ? [{ role: 'user' as const, content: e.input, games: [], notices: [] }] : []),
    ...(e.output ? [{ role: 'assistant' as const, content: e.output.message, games: e.output.games, notices: e.output.notices ?? [] }] : []),
  ]);
}
