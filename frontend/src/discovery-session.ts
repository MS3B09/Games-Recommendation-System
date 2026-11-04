import type { DiscoverRequest, Filters } from './api/discovery';
import { defaultFilters, normalizeFilters, validFilters } from './guest-store';

export const SESSION_KEY = 'game-discovery:conversation';
export type Message = { role: 'user' | 'assistant'; content: string };
export type DiscoverySession = { version: 1; initialQuery: string; draft: string; messages: Message[]; criteria: Filters };
type Port = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
export const emptySession = (): DiscoverySession => ({ version: 1, initialQuery: '', draft: '', messages: [], criteria: defaultFilters() });
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);

export function boundMessages(messages: Message[]): Message[] {
  const bounded = messages.map((item) => ({ ...item, content: item.content.slice(0, 2000) })).slice(-20);
  while (bounded.reduce((sum, item) => sum + item.content.length, 0) > 12000) bounded.shift();
  return bounded;
}
export function decodeSession(raw: string): DiscoverySession {
  if (raw.length > 50000) throw new Error('Conversation storage is too large');
  const value: unknown = JSON.parse(raw);
  if (!object(value) || value.version !== 1 || typeof value.initialQuery !== 'string' || value.initialQuery.length > 2000
    || typeof value.draft !== 'string' || value.draft.length > 2000 || !validFilters(value.criteria)
    || !Array.isArray(value.messages) || value.messages.length > 20 || !value.messages.every((item) => object(item)
      && ['user', 'assistant'].includes(String(item.role)) && typeof item.content === 'string' && item.content.length > 0 && item.content.length <= 2000)) throw new Error('Invalid conversation');
  const messages = value.messages as Message[];
  if (messages.reduce((sum, item) => sum + item.content.length, 0) > 12000) throw new Error('Conversation context is too large');
  return { version: 1, initialQuery: value.initialQuery, draft: value.draft, criteria: normalizeFilters(value.criteria),
    messages: messages.map(({ role, content }) => ({ role, content })) };
}
export function sessionPort(): Port | null { try { return window.sessionStorage; } catch { return null; } }
export function readSession(port = sessionPort()): { value: DiscoverySession; writable: boolean; notice: string } {
  if (!port) return { value: emptySession(), writable: false, notice: 'Your request is temporary in memory. Session storage is unavailable; reload may lose it.' };
  try { const raw = port.getItem(SESSION_KEY); return { value: raw === null ? emptySession() : decodeSession(raw), writable: true, notice: '' }; }
  catch { return { value: emptySession(), writable: false, notice: 'Request storage could not be read. It has not been overwritten. Use Reset request storage, or continue temporarily.' }; }
}
export function writeSession(value: DiscoverySession, port = sessionPort()): boolean {
  try { if (!port) return false; port.setItem(SESSION_KEY, JSON.stringify(decodeSession(JSON.stringify(value)))); return true; } catch { return false; }
}
export function resetSession(port = sessionPort()): boolean { try { if (!port) return false; port.removeItem(SESSION_KEY); return true; } catch { return false; } }
export const conversationFor = (session: DiscoverySession): NonNullable<DiscoverRequest['conversation']> => ({ messages: boundMessages(session.messages), criteria: session.criteria });
