export type Recovery = 'retry' | 'edit' | 'new_chat' | 'refresh' | 'discover' | 'remove_favorite' | 'back' | 'none';
type ErrorOptions = { code?: string; recovery?: Recovery; retryAt?: string; field?: string };
export class ServiceError extends Error {
  readonly code: string;
  readonly recovery: Recovery;
  readonly retryAt?: string;
  readonly field?: string;
  constructor(message: string, readonly requestId?: string, options: ErrorOptions = {}) {
    super(message);
    this.code = options.code ?? 'unexpected_error';
    this.recovery = options.recovery ?? 'retry';
    this.retryAt = options.retryAt;
    this.field = options.field;
  }
}

const copy: Record<string, [string, Recovery]> = {
  chat_session_missing: ['This chat could not be opened. Start a new chat to continue.', 'new_chat'],
  chat_session_conflict: ['This chat changed while you were writing. Refresh to load its latest messages.', 'refresh'],
  chat_archive_full: ['Chat storage is full. Your existing messages have been kept. Start a new chat or clear a chat you no longer need.', 'new_chat'],
  chat_tool_limit: ["The assistant couldn't finish checking that information within this turn. Please narrow the question.", 'edit'],
  chat_daily_calls: ["Today's free chat allowance has been used up. You can still find games using Your taste.", 'discover'],
  chat_daily_units: ["Today's free chat allowance has been used up. You can still find games using Your taste.", 'discover'],
  chat_rate_limited: ['Please wait a moment before sending another message.', 'retry'],
  chat_limited: ['Please wait a moment before sending another message.', 'retry'],
  chat_provider_limited: ['The AI service is receiving too many requests. Please try again later.', 'retry'],
  chat_busy: ['The assistant is finishing another reply. Please try again in a moment.', 'retry'],
  chat_timeout: ['The assistant took too long to reply. Please try your message again.', 'retry'],
  chat_provider_unavailable: ["The assistant can't reach its AI service right now. Please try again later, or find games using Your taste.", 'retry'],
  chat_accounting_unavailable: ["We couldn't check whether chat is available right now. Please try again later, or find games using Your taste.", 'retry'],
  chat_invalid_answer: ["We couldn't give you a reliable answer to that question. Try asking it another way.", 'edit'],
  chat_message_too_long: ['That message is too long. Please keep it under 2,000 characters.', 'edit'],
  chat_message_too_detailed: ['That message has more detail than the assistant can handle at once. Please shorten it and try again.', 'edit'],
  chat_context_limit: ['This conversation has become too long for the assistant to continue. Start a new chat with your main preferences.', 'new_chat'],
  chat_evidence_unavailable: ["The assistant couldn't prepare reliable game details for this request. Try finding games using Your taste.", 'discover'],
  chat_unconfigured: ["Chat isn't available on this version of the app. You can still find games using Your taste.", 'discover'],
  chat_service_configuration: ["Chat can't connect to its AI service because of a setup issue. You can still find games using Your taste.", 'discover'],
  chat_incompatible: ["Chat needs an update before this conversation can continue. Refresh the page. If it still doesn't work, please try again later.", 'refresh'],
  chat_interrupted: ['Your last reply was interrupted. Reopen the chat to check its saved history, or retry your message.', 'retry'],
  chat_unavailable: ['The assistant could not finish your reply. Please try again later.', 'retry'],
  network_error: ["We couldn't connect to the service. Check your internet connection and try again.", 'retry'],
  request_timeout: ['The service took too long to respond. Please try again.', 'retry'],
  database_busy: ['The game catalog is handling other requests. Please try again in a moment.', 'retry'],
  database_unavailable: ["We can't load the game catalog right now. Please try again shortly.", 'retry'],
  database_unconfigured: ['Game search is unavailable because of a service setup issue. Please try again later.', 'none'],
  database_configuration_invalid: ['Game search is unavailable because of a service setup issue. Please try again later.', 'none'],
  database_role_misconfigured: ['Game search is unavailable because of a service setup issue. Please try again later.', 'none'],
  catalog_not_initialized: ["The game catalog isn't ready yet. Please come back later.", 'none'],
  catalog_integrity_error: ["We couldn't load these game details correctly. Please try again later.", 'back'],
  analytics_unavailable: ['The dashboard is not available for this catalog version yet. You can still discover and save games.', 'retry'],
  analytics_integrity_error: ["We couldn't verify this catalog’s dashboard. Please try again later. Your saved games are unchanged.", 'retry'],
  unknown_favorite: ['A selected favorite is no longer available in our catalog. Remove unavailable favorites to continue.', 'remove_favorite'],
  game_not_found: ['This game is no longer available in our catalog. Choose another game to view its details.', 'back'],
  invalid_price_range: ["Choose a maximum price that's at least your minimum price.", 'edit'],
  invalid_input: ['Some details in your request need attention. Check your message or filters and try again.', 'edit'],
  service_configuration: ['This app cannot connect to its service because of a setup issue. Please try again later.', 'none'],
  invalid_response: ["We couldn't load the reply correctly. Refresh the page and try again.", 'refresh'],
  unexpected_error: ['The service hit an unexpected problem while handling your request. Please try again later.', 'retry'],
};

export function serviceError(code: string, options: ErrorOptions & { requestId?: string } = {}): ServiceError {
  const [message, recovery] = copy[code] ?? copy.unexpected_error!;
  return new ServiceError(message, options.requestId, { ...options, code, recovery });
}
const timedCodes = new Set(['chat_daily_calls', 'chat_daily_units', 'chat_rate_limited', 'chat_limited', 'chat_provider_limited']);
export function parseServiceError(value: unknown): ServiceError {
  const record = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  const code = typeof record.code === 'string' && Object.hasOwn(copy, record.code) ? record.code : 'unexpected_error';
  const timestamp = typeof record.retry_at === 'string' ? Date.parse(record.retry_at) : NaN;
  const retryAt = timedCodes.has(code) && Number.isFinite(timestamp) && timestamp <= Date.now() + 7 * 86400000
    ? new Date(timestamp).toISOString() : undefined;
  return serviceError(code, { retryAt, requestId: typeof record.request_id === 'string' ? record.request_id : undefined,
    field: ['message', 'price', 'request'].includes(String(record.field)) ? String(record.field) : undefined });
}
export const retryWait = (error: ServiceError | null | undefined, now: number) => error?.retryAt
  ? Math.max(0, Math.ceil((Date.parse(error.retryAt) - now) / 1000)) : 0;
export function errorText(error: ServiceError, now: number): string {
  if (!error.retryAt) return error.message;
  if (retryWait(error, now) === 0) return 'The waiting period has ended. You can try your request again now.';
  if (['chat_rate_limited', 'chat_limited', 'chat_provider_limited'].includes(error.code)) return error.message;
  const when = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' }).format(new Date(error.retryAt));
  return error.code.startsWith('chat_daily_')
    ? `Today's free chat allowance has been used up. Chat will be available again at ${when}. You can still find games using Your taste.`
    : `${error.message} You can try again after ${when}.`;
}

const AVAILABILITY_KEY = 'game-discovery:assistant-availability';
export function rememberAvailability(error: ServiceError): void {
  if (!error.retryAt || !timedCodes.has(error.code)) return;
  try { sessionStorage.setItem(AVAILABILITY_KEY, JSON.stringify({ code: error.code, retry_at: error.retryAt })); } catch { /* The current tab still keeps its in-memory error. */ }
}
export function readAvailability(): ServiceError | null {
  try {
    const raw = sessionStorage.getItem(AVAILABILITY_KEY);
    if (!raw || raw.length > 1000) return null;
    const error = parseServiceError(JSON.parse(raw));
    return error.retryAt && retryWait(error, Date.now()) > 0 ? error : null;
  } catch { return null; }
}
export function clearAvailability(): void {
  try { sessionStorage.removeItem(AVAILABILITY_KEY); } catch { /* Expired metadata is ignored on reload. */ }
}
