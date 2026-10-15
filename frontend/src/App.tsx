import { useEffect, useRef, useState } from 'react';
import { apiOrigin, getCatalog, ServiceError, type CatalogStatus } from './api/client';
import Discovery from './Discovery';
import GameDetail from './GameDetail';

type Connection = { kind: 'loading' } | { kind: 'failed'; message: string; requestId?: string }
  | { kind: 'connected'; catalog: CatalogStatus };

export default function App() {
  const [connection, setConnection] = useState<Connection>({ kind: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const button = useRef<HTMLButtonElement>(null);
  const path = window.location.pathname;
  const gameMatch = /^\/games\/(\d+)\/?$/.exec(path);
  const validRoute = ['/', '/system', '/system/'].includes(path) || !!gameMatch;
  let docsUrl: string | undefined;
  try { docsUrl = `${apiOrigin()}/docs`; } catch { /* State region supplies configuration recovery. */ }

  useEffect(() => {
    if (!validRoute) return;
    const controller = new AbortController();
    let timedOut = false;
    const timer = window.setTimeout(() => { timedOut = true; controller.abort(); }, 75_000);
    getCatalog(controller.signal).then(
      (catalog) => { if (!controller.signal.aborted) setConnection({ kind: 'connected', catalog }); },
      (error: unknown) => {
        if (controller.signal.aborted && !timedOut) return;
        setConnection({ kind: 'failed', message: timedOut ? 'The service took too long to respond. Please try again.'
          : error instanceof Error ? error.message : 'The service is temporarily unavailable.',
          requestId: error instanceof ServiceError ? error.requestId : undefined });
      },
    ).finally(() => window.clearTimeout(timer));
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [attempt, validRoute]);

  const catalog = connection.kind === 'connected' ? connection.catalog : null;
  const heading = connection.kind === 'loading' ? 'Checking the connection…'
    : connection.kind === 'failed' ? 'The service is unavailable'
      : catalog?.state === 'uninitialized' ? 'The catalog is being prepared' : 'The catalog is connected';

  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header">
      <a className="wordmark" href="/" aria-label="Game Discovery home">Game Discovery<span aria-hidden="true">.</span></a>
      <nav aria-label="Main navigation"><a href="/" aria-current={path === '/' ? 'page' : undefined}>Discover</a><a href="/system" aria-current={path.startsWith('/system') ? 'page' : undefined}>Service status</a></nav>
    </header>
    <main id="main" tabIndex={-1}>
      {!validRoute ? <section className="intro"><h1>This page isn’t here.</h1><p>Return to the foundation page to check the service.</p><a className="button" href="/">Go home</a></section>
        : gameMatch ? <GameDetail id={Number(gameMatch[1])} />
        : path === '/' && catalog?.state === 'ready' ? <Discovery catalog={catalog} />
        : <>
          <section className="intro">
            <h1>A better way to find<br className="desktop-break" /> your next game.</h1>
            <p>Built around the games you love, the experience you want, and the constraints that matter to you.</p>
            <p className="build-note">Favorite-based discovery uses recorded catalog facts. Natural-language discovery is planned for a later milestone.</p>
          </section>
          <section className="connection" aria-labelledby="connection-title">
            <div className="connection-copy">
              <div role="status" aria-live="polite" aria-atomic="true">
                <h2 id="connection-title">{heading}</h2>
                <p className="connection-label"><span className={`state-dot ${connection.kind}`} aria-hidden="true" />
                  {connection.kind === 'connected' ? 'API connected' : connection.kind === 'failed' ? 'Connection interrupted' : 'Connecting to the API'}</p>
                <p>{connection.kind === 'failed' ? connection.message : connection.kind === 'loading'
                  ? 'The free demo may need up to a minute to wake up. This check runs once; it won’t poll in the background.'
                  : catalog?.state === 'uninitialized' ? 'The API and database are reachable. No catalog has been published yet, so there are no games to browse.'
                    : 'A catalog is published. Open Discover to browse favorite-based recommendations.'}</p>
                {connection.kind === 'failed' && connection.requestId && <p className="request-id">Request ID: {connection.requestId}</p>}
              </div>
              <div className="actions">
                <button ref={button} className="button" type="button" disabled={connection.kind === 'loading'} onClick={() => {
                  setConnection({ kind: 'loading' }); setAttempt((value) => value + 1);
                }}>{connection.kind === 'loading' ? 'Checking…' : 'Check connection again'}</button>
                {docsUrl && <a className="text-link" href={docsUrl} target="_blank" rel="noreferrer">API documentation<span className="sr-only"> (opens in a new tab)</span></a>}
              </div>
            </div>
            <dl className="catalog-facts">
              <div><dt>Catalog</dt><dd>{catalog ? catalog.state === 'ready' ? catalog.catalog_version : 'Not published' : 'Not available yet'}</dd></div>
              <div><dt>Games available</dt><dd>{catalog ? catalog.game_count.toLocaleString() : 'Unknown'}</dd></div>
              <div><dt>Source freshness</dt><dd>{catalog ? catalog.source_observed_at ? new Date(catalog.source_observed_at).toLocaleString() : 'Not recorded yet' : 'Unknown'}</dd></div>
            </dl>
          </section>
        </>}
    </main>
    <footer><p>Guest-first. No sign-in required.</p><p>First-release catalog scope: United States · USD</p></footer>
  </div>;
}
