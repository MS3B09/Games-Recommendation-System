import type { components } from './schema';

export type CatalogStatus = components['schemas']['CatalogStatus'];
import { ServiceError, parseServiceError, serviceError } from './errors';
export { ServiceError } from './errors';

export function apiOrigin(): string {
  const value = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');
  if (!value) throw serviceError('service_configuration');
  let url: URL;
  try { url = new URL(value); }
  catch { throw serviceError('service_configuration'); }
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw serviceError('service_configuration');
  }
  if (url.protocol !== 'https:' && !(url.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(url.hostname))) {
    throw serviceError('service_configuration');
  }
  return url.origin;
}

function isCatalog(value: unknown): value is CatalogStatus {
  if (!value || typeof value !== 'object') return false;
  const v = value as Record<string, unknown>;
  return ['ready', 'uninitialized'].includes(String(v.state))
    && Number.isInteger(v.game_count) && Number(v.game_count) >= 0
    && (v.catalog_version === null || typeof v.catalog_version === 'string')
    && ((v.state === 'uninitialized' && v.catalog_version === null && v.game_count === 0)
      || (v.state === 'ready' && typeof v.catalog_version === 'string' && v.catalog_version.length > 0 && Number(v.game_count) > 0))
    && v.region === 'US' && v.currency === 'USD'
    && (v.source_observed_at === null || (typeof v.source_observed_at === 'string' && !Number.isNaN(Date.parse(v.source_observed_at))))
    && typeof v.semantic_query_matching === 'boolean' && typeof v.llm_enabled === 'boolean';
}

export async function getCatalog(signal: AbortSignal): Promise<CatalogStatus> {
  let response: Response;
  const timeout = AbortSignal.timeout(75_000);
  try {
    response = await fetch(`${apiOrigin()}/api/v1/catalog/status`, { signal: AbortSignal.any([signal, timeout]), credentials: 'omit' });
  } catch (error) {
    if (error instanceof ServiceError || signal.aborted) throw error;
    throw serviceError(timeout.aborted ? 'request_timeout' : 'network_error');
  }
  let body: unknown;
  try { body = await response.json(); }
  catch (error) {
    if (signal.aborted) throw error;
    throw serviceError(timeout.aborted ? 'request_timeout' : 'invalid_response');
  }
  if (!response.ok) {
    throw parseServiceError(body);
  }
  if (!isCatalog(body)) throw serviceError('invalid_response');
  return body;
}
