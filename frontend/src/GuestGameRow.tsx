import { useState } from 'react';
import type { DiscoverResponse, Game } from './api/discovery';
import { cacheGame, type CachedGame, type GuestSnapshot, type GuestStore } from './guest-store';
import Icon from './Icon';

export function Artwork({ game }: { game: CachedGame | Game }) {
  const [failed, setFailed] = useState(false);
  return failed || !game.artwork_url ? <div className="study-art-fallback">Artwork unavailable</div>
    : <img src={game.artwork_url} alt="" width={460} height={215} loading="lazy" onError={() => setFailed(true)} />;
}
export const observed = (date: string | null | undefined) => date
  ? new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' }) : 'Unknown observation date';
export const label = (term: string) => term.split('-').map((word) => word ? word[0]!.toUpperCase() + word.slice(1) : '').join(' ');

export function GameEssentials({ game, showTraits = false }: { game: Game; showTraits?: boolean }) {
  const description = game.description.replace(/\s+/g, ' ').trim();
  const boundary = description.lastIndexOf(' ', 280);
  const excerpt = description.length > 280 ? `${description.slice(0, boundary > 200 ? boundary : 280)}…` : description;
  const platforms = Object.entries(game.platforms).filter(([, supported]) => supported === true)
    .map(([platform]) => platform === 'mac' ? 'macOS' : label(platform)).join(', ');
  return <div className="game-essentials">
    <p className="game-description">{excerpt || 'No description recorded.'}</p>
    <dl className="game-facts">
      {showTraits && <div className="game-facts-genres"><dt>Genre</dt><dd>{(game.genres ?? []).map(label).join(' · ') || 'Not recorded'}</dd></div>}
      {showTraits && <div><dt>Play style</dt><dd>{(game.modes ?? []).map(label).join(' · ') || 'Not recorded'}</dd></div>}
      <div><dt>Platforms</dt><dd>{platforms || 'Not recorded'}</dd></div>
    </dl>
    {showTraits && game.early_access && <p className="game-early-access">Early Access — features and content may change.</p>}
    <p className="game-price-note">{game.price?.observed_at ? `Price recorded ${observed(game.price.observed_at)}.` : game.price ? 'Price date not recorded.' : 'Price not recorded.'} Check Steam for current pricing.</p>
  </div>;
}

export function SaveButton({ game, store, state }: { game: CachedGame; store: GuestStore; state: GuestSnapshot }) {
  const saved = state.data.saved.some((item) => item.app_id === game.app_id);
  return <><button type="button" aria-pressed={saved} aria-label={`${saved ? 'Remove saved' : 'Save'} ${game.title}`} onClick={() => store.toggleSaved(game)}>{saved ? 'Saved' : 'Save game'}</button>
    {!state.persistent && <span className="study-local-only">Temporary in this tab — not saved in browser storage.</span>}</>;
}

export function GuestGameRow({ result, store, state }: { result: DiscoverResponse['results'][number]; store: GuestStore; state: GuestSnapshot }) {
  const { game } = result;
  const cached = cacheGame(game);
  const active = state.data.feedback.find((item) => item.app_id === game.app_id)?.kind;
  return <article className="study-game" aria-labelledby={`study-game-${game.app_id}`}>
    <a className="study-art" href={game.store_url} target="_blank" rel="noreferrer" aria-label={`View ${game.title} on Steam (opens in a new tab)`}><Artwork game={game} /></a>
    <div className="study-game-copy">
      <div className="study-game-heading"><h3 id={`study-game-${game.app_id}`}>{game.title}</h3><p className="study-price">{game.price ? `$${(game.price.amount_cents / 100).toFixed(2)}` : 'Unknown'}<span>Recorded USD</span></p></div>
      <p className="study-metadata"><span>{(game.genres ?? []).map(label).join(' / ') || 'Genres not recorded'}</span><span>{(game.modes ?? []).map(label).join(' · ') || 'Play modes not recorded'}{game.early_access ? ' · Early Access' : ''}</span></p>
      <p className="study-reason">{result.reasons[0]?.text}</p>
      <details className="study-evidence"><summary>Game details<Icon name="chevron" /></summary><GameEssentials game={game} /></details>
      <div className="study-game-actions"><a href={game.store_url} target="_blank" rel="noreferrer">View on Steam<span className="study-sr"> (opens in a new tab)</span></a>
        <SaveButton game={cached} store={store} state={state} />
        <div className="study-feedback" role="group" aria-label={`Recommendation feedback for ${game.title}`}>
          {(['not-for-me', 'already-played'] as const).map((kind) => <button type="button" key={kind} aria-pressed={active === kind}
            onClick={() => store.setFeedback(cached, active === kind ? null : kind)}>{label(kind)}</button>)}
        </div>
      </div>
    </div>
  </article>;
}
