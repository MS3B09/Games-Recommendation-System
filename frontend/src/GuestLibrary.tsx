import { useEffect, useRef, useState } from 'react';
import { resolveGames } from './api/discovery';
import { ServiceError } from './api/client';
import { type GuestSnapshot, type GuestStore } from './guest-store';
import { Artwork, label, observed, SaveButton } from './GuestGameRow';

export default function GuestLibrary({ store, state }: { store: GuestStore; state: GuestSnapshot }) {
  const request = useRef<AbortController | null>(null);
  const [message, setMessage] = useState('Saved titles stay visible here even when the catalog service is unavailable.');
  const [refreshing, setRefreshing] = useState(false);
  const [unknown, setUnknown] = useState<number[]>([]);
  useEffect(() => () => request.current?.abort(), []);
  async function refresh() {
    request.current?.abort();
    const controller = new AbortController(); request.current = controller;
    const ticket = store.ticket();
    setRefreshing(true);
    try {
      const result = await resolveGames(state.data.saved.map((game) => game.app_id), controller.signal);
      if (controller.signal.aborted || !store.current(ticket)) return;
      setUnknown(result.unknown_ids);
      setMessage(`Checked ${result.items.length} saved titles against the active catalog. Local snapshots are retained; check Steam for current purchase prices.`);
    } catch (error) { if (!controller.signal.aborted && store.current(ticket)) setMessage(error instanceof ServiceError ? error.message : 'The catalog could not be checked. Your local saved games remain available.'); }
    finally { if (!controller.signal.aborted && request.current === controller) setRefreshing(false); }
  }
  return <section className="study-library" aria-labelledby="saved-title">
    <div className="study-results-heading"><h1 id="saved-title">For another day.</h1><a href="/">Back to discovery</a></div>
    <p className="study-count">{state.data.saved.length} saved games · {state.persistent ? 'Saved on this device' : 'Temporary in this tab'}</p>
    <p>Saving a game keeps it on this list. It does not mark it Interested or change your recommendations.</p>
    <div className="study-library-tools"><button type="button" disabled={!state.data.saved.length || refreshing} onClick={refresh}>{refreshing ? 'Checking…' : 'Check catalog availability'}</button></div>
    <p className="study-local-status" role="status">{message}</p>
    {!state.data.saved.length && <div className="study-empty"><h2>Keep something good.</h2><p>Use Save game on a recommendation to keep its title, artwork and recorded price here.</p><a href="/">Find your next game</a></div>}
    {state.data.saved.map((game) => <article className="study-game study-saved-game" key={game.app_id} aria-labelledby={`saved-${game.app_id}`}>
      <a className="study-art" href={game.store_url} target="_blank" rel="noreferrer" aria-label={`View ${game.title} on Steam (opens in a new tab)`}><Artwork game={game} /></a>
      <div className="study-game-copy"><div className="study-game-heading"><h2 id={`saved-${game.app_id}`}>{game.title}</h2><p className="study-price">{game.price_cents === null ? 'Unknown' : `$${(game.price_cents / 100).toFixed(2)}`}<span>Cached recorded USD</span></p></div>
        <p className="study-metadata">{observed(game.observed_at)}{game.observed_at ? ' UTC' : ''} · {state.persistent ? 'Saved on this device' : 'Temporary in this tab'}</p>
        {unknown.includes(game.app_id) && <p>No longer available in the active catalog. Your saved title is retained.</p>}
        <div className="study-game-actions"><a href={game.store_url} target="_blank" rel="noreferrer">View on Steam<span className="study-sr"> (opens in a new tab)</span></a><SaveButton game={game} store={store} state={state} />
          <button type="button" onClick={() => store.toggleFavorite(game)}>{state.data.favorites.some((item) => item.app_id === game.app_id) ? 'Remove favorite' : 'Add favorite'}</button></div>
      </div>
    </article>)}
    <section className="study-library-section" aria-labelledby="feedback-title"><h2 id="feedback-title">Your feedback.</h2>
      <p>Not for me excludes that title and downweights similar content. Already played excludes only that title; it does not mean dislike.{state.data.feedback.some(item => item.kind === 'interested') ? ' Earlier Interested feedback is retained and can be removed here.' : ''}</p>
      {!state.data.feedback.length && <p>No recommendation feedback yet.</p>}
      <ul className="study-saved-list">{state.data.feedback.map((item) => <li key={item.app_id}><span>{item.title} · {label(item.kind)}</span><button type="button" aria-label={`Remove feedback for ${item.title}`} onClick={() => store.setFeedback({ ...cacheGamePlaceholder(item.app_id, item.title) }, null)}>Remove feedback</button></li>)}</ul>
    </section>
    <section className="study-library-section" aria-labelledby="history-title"><div className="study-results-heading"><h2 id="history-title">Recent discoveries.</h2>{state.data.history.length > 0 && <button type="button" onClick={() => store.removeHistory()}>Clear recent history</button>}</div>
      <p>Up to 20 recent summaries are kept here. No full conversations are stored.</p>
      {!state.data.history.length && <p>No recent discoveries yet.</p>}
      <ol className="study-saved-list">{state.data.history.map((item) => <li key={item.id}><span>{observed(item.timestamp)} UTC · {item.favorite_ids.length} favorites · {item.result_ids.length} results</span>
        <span>{item.preferences.free_only ? 'Free to play' : `${item.preferences.min_price_cents ? `From $${(item.preferences.min_price_cents / 100).toFixed(2)}` : 'Free'} – ${item.preferences.max_price_cents === null ? 'any price' : `$${(item.preferences.max_price_cents / 100).toFixed(2)}`} USD`} · {item.preferences.platforms.map(label).join(', ') || 'Any platform'}</span></li>)}</ol>
    </section>
  </section>;
}

const cacheGamePlaceholder = (app_id: number, title: string) => ({ app_id, title, store_url: `https://store.steampowered.com/app/${app_id}/`, artwork_url: null, price_cents: null, observed_at: null });
