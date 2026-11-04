import { isRecommendation, type ChatRequest, type ChatState, type Recommendation } from './api/discovery';
import { decodeChatState, migrateChatState, neutralChatState } from './chat-state';

export const ASSISTANT_KEY = 'game-discovery:assistant';
export type ChatMessage = { role: 'user' | 'assistant'; content: string; games: Recommendation[]; notices: string[] };
export type AssistantSession = { version: 2; messages: ChatMessage[]; state: ChatState; draft: string; pending: ChatRequest | null };
type Port = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
export const emptyAssistant = (): AssistantSession => ({ version: 2, messages: [], draft: '', pending: null, state: neutralChatState() });
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.length <= 10 && value.every(item => typeof item === 'string' && item.length <= 2000);
export function boundChat(messages: ChatMessage[]): ChatMessage[] {
  const recent = messages.slice(-20);
  while (recent.reduce((total, item) => total + item.content.length, 0) > 12000) recent.shift();
  let cards = 0;
  return recent.slice().reverse().map(item => { cards += item.games.length; return { ...item, games: cards <= 12 ? item.games : [] }; }).reverse();
}
export function decodeAssistant(raw: string): AssistantSession {
  if (raw.length > 500000) throw new Error('Assistant storage is too large');
  const value: unknown = JSON.parse(raw);
  if (!object(value) || ![1, 2].includes(Number(value.version)) || (value.version !== 1 && value.version !== 2)
    || typeof value.draft !== 'string' || value.draft.length > 2000
    || !Array.isArray(value.messages) || value.messages.length > 20
    || !value.messages.every(item => object(item) && ['user', 'assistant'].includes(String(item.role))
      && typeof item.content === 'string' && !!item.content.trim() && item.content.length <= 2000
      && Array.isArray(item.games) && item.games.length <= 4 && item.games.every(isRecommendation) && strings(item.notices))
    || value.messages.reduce((total, item) => total + item.content.length, 0) > 12000
    || value.messages.reduce((total, item) => total + item.games.length, 0) > 12) throw new Error('Invalid assistant storage');
  const state = value.version === 1 ? migrateChatState(value.state) : decodeChatState(value.state);
  let pending: ChatRequest | null = null;
  if (value.version === 2 && value.pending !== undefined && value.pending !== null) {
    const request = value.pending;
    if (!object(request) || Object.keys(request).some(key => !['message', 'messages', 'state'].includes(key))
      || typeof request.message !== 'string' || !request.message.trim() || request.message.length > 2000
      || !Array.isArray(request.messages) || request.messages.length > 20
      || !request.messages.every(item => object(item) && Object.keys(item).every(key => ['role', 'content'].includes(key))
        && ['user', 'assistant'].includes(String(item.role)) && typeof item.content === 'string' && !!item.content.trim() && item.content.length <= 2000)
      || request.messages.reduce((total, item) => total + item.content.length, 0) > 12000
      || value.messages.at(-1)?.role !== 'user' || value.messages.at(-1)?.content !== request.message) throw new Error('Invalid pending chat turn');
    const before = decodeChatState(request.state);
    if (JSON.stringify(before) !== JSON.stringify(state)) throw new Error('Pending chat state differs from the retained state');
    pending = { message: request.message, messages: request.messages.map(({ role, content }: { role: 'user' | 'assistant'; content: string }) => ({ role, content })), state: before };
  }
  return { version: 2, draft: value.draft, state, pending,
    messages: value.messages.map(({ role, content, games, notices }: ChatMessage) => ({ role, content, games, notices })) };
}
export function assistantPort(): Port | null { try { return window.sessionStorage; } catch { return null; } }
export function readAssistant(port = assistantPort()) {
  if (!port) return { value: emptyAssistant(), writable: false, notice: 'Your browser couldn’t save this chat. You can keep chatting, but reloading may lose the conversation.' };
  try {
    const raw = port.getItem(ASSISTANT_KEY);
    const value = raw === null ? emptyAssistant() : decodeAssistant(raw);
    if (raw !== null && JSON.parse(raw).version === 1) {
      const notice = 'Your saved chat was updated. Earlier requirements need confirmation: restate them with Start over, or use New chat.';
      try { const upgraded = JSON.stringify(value); decodeAssistant(upgraded); port.setItem(ASSISTANT_KEY, upgraded); }
      catch { return { value, writable: false, notice: `${notice} The older copy could not be replaced; this chat is temporary in memory.` }; }
      return { value, writable: true, notice };
    }
    return { value, writable: true, notice: '' };
  } catch { return { value: emptyAssistant(), writable: false, notice: 'We couldn’t open your saved chat. The saved copy hasn’t been changed. You can keep chatting temporarily or use New chat to start again.' }; }
}
export function writeAssistant(value: AssistantSession, port = assistantPort()): boolean {
  try { if (!port) return false; port.setItem(ASSISTANT_KEY, JSON.stringify(decodeAssistant(JSON.stringify(value)))); return true; } catch { return false; }
}
export function clearAssistant(port = assistantPort()): boolean {
  try { if (!port) return false; port.removeItem(ASSISTANT_KEY); return true; } catch { return false; }
}
