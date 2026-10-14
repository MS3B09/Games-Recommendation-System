import type { components } from './schema';

export type CatalogStatus = components['schemas']['CatalogStatus'];
type ApiError = components['schemas']['ApiError'];

export class ServiceError extends Error {
  constructor(message: string, readonly requestId?: string) { super(message); }
}

export function apiOrigin(): string {
  const value = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');
  if (!value) throw new ServiceError('The API address has not been configured for this deployment.');
  let url: URL;
  try { url = new URL(value); }
  catch { throw new ServiceError('The API address needs attention.'); }
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new ServiceError('The API address needs attention.');
  }
  if (url.protocol !== 'https:' && !(url.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(url.hostname))) {
    throw new ServiceError('The API address must use HTTPS.');
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
  try {
    response = await fetch(`${apiOrigin()}/api/v1/catalog/status`, { signal, credentials: 'omit' });
  } catch (error) {
    if (error instanceof ServiceError || signal.aborted) throw error;
    throw new ServiceError('We couldn’t reach the service. It may be waking up or temporarily unavailable.');
  }
  let body: unknown;
  try { body = await response.json(); }
  catch { throw new ServiceError('The service returned an unexpected response. Please try again shortly.'); }
  if (!response.ok) {
    const error = body as Partial<ApiError> | null;
    const configurationError = error && ['database_unconfigured', 'database_configuration_invalid', 'database_role_misconfigured'].includes(error.code ?? '');
    throw new ServiceError(
      configurationError ? 'The service needs configuration. The project owner needs to check the backend settings.'
        : 'The catalog service is temporarily unavailable. Please try again shortly.',
      error && typeof error.request_id === 'string' ? error.request_id : undefined,
    );
  }
  if (!isCatalog(body)) throw new ServiceError('The catalog response could not be verified. Please try again shortly.');
  return body;
}
