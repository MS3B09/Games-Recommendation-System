import { useEffect, useState } from 'react';
import { errorText, retryWait, type ServiceError } from './api/errors';

export function useRecoveryClock(retryAt?: string) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!retryAt) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [retryAt]);
  return now;
}

export default function ErrorNotice({ error, onRetry, onEdit, onNewChat, onDiscover, onRemoveFavorite, onBack, retryLabel = 'Try again', editLabel }: {
  error: ServiceError; onRetry?: () => void; onEdit?: () => void; onNewChat?: () => void;
  onDiscover?: () => void; onRemoveFavorite?: () => void; onBack?: () => void;
  retryLabel?: string; editLabel?: string;
}) {
  const now = useRecoveryClock(error.retryAt);
  const wait = retryWait(error, now);
  const recovery = error.retryAt && !wait ? 'retry' : error.recovery;
  return <div className="friendly-error">
    <p role="alert">{errorText(error, now)}</p>
    <div className="friendly-error-actions">
      {recovery === 'retry' && onRetry && <button className="study-retry" type="button" disabled={wait > 0} onClick={onRetry} aria-live="off">{wait ? `Try again in ${wait}s` : retryLabel}</button>}
      {recovery === 'edit' && onEdit && <button className="study-retry" type="button" onClick={onEdit}>{editLabel ?? `Edit ${error.field === 'price' ? 'limits' : 'message'}`}</button>}
      {recovery === 'new_chat' && onNewChat && <button type="button" onClick={onNewChat}>New chat</button>}
      {recovery === 'refresh' && <button type="button" onClick={() => window.location.reload()}>Refresh page</button>}
      {recovery === 'remove_favorite' && onRemoveFavorite && <button type="button" onClick={onRemoveFavorite}>Review favorites</button>}
      {recovery === 'back' && onBack && <button type="button" onClick={onBack}>Back to results</button>}
      {(recovery === 'discover' || onDiscover && ['chat_provider_unavailable', 'chat_accounting_unavailable', 'chat_provider_limited'].includes(error.code))
        && <a href={window.location.pathname === '/saved' ? '/#taste' : '#taste'} onClick={onDiscover}>Use Your taste</a>}
    </div>
  </div>;
}
