import { request, isRecommendation, type Recommendation } from './discovery';

export type Conversation = { conversation_id: string; token: string; revision: number };
export type AssistantTurn = Conversation & { turn_id: string; message: string };
export type AssistantReply = { request_id: string; message: string; games: Recommendation[]; notices: string[]; revision: number; total_turns: number };
export type ImportedMessage = { role: 'user' | 'assistant'; content: string; game_ids: number[] };
export type ArchiveEvent = { id: string; input: string; status: string; output?: AssistantReply | null };
export type ArchivePage = { revision: number; total: number; offset: number; next_offset: number | null; events: ArchiveEvent[] };
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const uuid = (v: unknown): v is string => typeof v === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
export function isConversation(v: unknown): v is Conversation {
  return object(v) && uuid(v.conversation_id) && typeof v.token === 'string' && /^[A-Za-z0-9_-]{43}$/.test(v.token)
    && Number.isInteger(v.revision) && Number(v.revision) >= 0;
}
export function isAssistantReply(v: unknown): v is AssistantReply {
  return object(v) && typeof v.request_id === 'string' && typeof v.message === 'string' && !!v.message.trim() && v.message.length <= 4000
    && Array.isArray(v.games) && v.games.length <= 4 && v.games.every(isRecommendation)
    && Array.isArray(v.notices) && v.notices.every(x => typeof x === 'string')
    && Number.isInteger(v.revision) && Number(v.revision) >= 0 && Number.isInteger(v.total_turns) && Number(v.total_turns) >= 0;
}
export function isArchivePage(v: unknown): v is ArchivePage {
  return object(v) && Number.isInteger(v.revision) && Number.isInteger(v.total) && Number.isInteger(v.offset)
    && (v.next_offset === null || Number.isInteger(v.next_offset)) && Array.isArray(v.events)
    && v.events.length <= 50 && v.events.every(e => object(e) && uuid(e.id) && typeof e.input === 'string'
      && typeof e.status === 'string' && (e.output == null || (object(e.output) && typeof e.output.message === 'string'
        && Array.isArray(e.output.games) && e.output.games.every(isRecommendation))));
}
export function freshConversation(): Conversation {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const token = btoa(String.fromCharCode(...bytes)).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '');
  return { conversation_id: crypto.randomUUID(), token, revision: 0 };
}
export const createConversation = async (key: Conversation, messages: ImportedMessage[], signal: AbortSignal): Promise<Conversation> => {
  const v = await request('/api/v2/assistant/conversations', isConversation, signal,
    { key: { conversation_id: key.conversation_id, token: key.token }, messages });
  return { conversation_id: v.conversation_id, token: v.token, revision: v.revision };
};
export const sendAssistant = (body: AssistantTurn, signal: AbortSignal) => request('/api/v2/assistant', isAssistantReply, signal, body);
export const readConversation = (key: Conversation, before: number, signal: AbortSignal) =>
  request('/api/v2/assistant/history', isArchivePage, signal, { conversation_id: key.conversation_id, token: key.token, before, limit: 10 });
export const forgetConversation = (key: Conversation, signal: AbortSignal) =>
  request('/api/v2/assistant/forget', (v): v is boolean => typeof v === 'boolean', signal, { conversation_id: key.conversation_id, token: key.token });
