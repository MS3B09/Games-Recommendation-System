import { useState } from 'react';
import type { components } from './api/schema';
import type { Game } from './api/discovery';

export function recordedPrice(game: Game): string {
  return game.price ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(game.price.amount_cents / 100) + ' USD' : 'Price unknown';
}
export function observedDate(value: string): string {
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(value));
}
export function Artwork({ game }: { game: Game }) {
  const [failed, setFailed] = useState(false);
  return game.artwork_url && !failed ? <img className="game-art" src={game.artwork_url} alt="" loading="lazy" width={460} height={215} onError={() => setFailed(true)} />
    : <div className="art-fallback">Artwork unavailable</div>;
}
export function GameFacts({ game }: { game: Game }) {
  return <div className="game-facts">
    <p className="price">{recordedPrice(game)} <span>{game.free_to_play ? 'Free-to-play' : 'Recorded price'}</span></p>
    <p className="small muted">{game.price ? `US store · observed ${observedDate(game.price.observed_at)} (UTC)` : 'No verified US/USD price observation.'}</p>
    <p className="small">{Object.entries(game.platforms).filter(([, supported]) => supported === true).map(([platform]) => platform === 'mac' ? 'macOS' : platform === 'windows' ? 'Windows' : 'Linux').join(' · ') || 'Platform support unknown'}{game.early_access ? ' · Early Access' : ''}</p>
  </div>;
}
export function EvidenceList({ game, ids }: { game: Game; ids?: string[] }) {
  const evidence = game.evidence.filter((item) => !ids || ids.includes(item.id));
  return <ul className="evidence-list">{evidence.map((item) => <li key={item.id}>
    <span>{item.field.replaceAll('_', ' ').replace('platform:', 'Platform: ')}: {Array.isArray(item.value) ? item.value.join(', ') : String(item.value)}</span>
    <a href={item.source.url} target="_blank" rel="noreferrer">Steam source<span className="sr-only"> for {item.field} (opens in a new tab)</span></a>
    <span className="muted">Collected {observedDate(item.source.collected_at)} (UTC)</span>
  </li>)}</ul>;
}

export default function GameCard({ result, index, onExclude }: {
  result: components['schemas']['Recommendation']; index: number; onExclude: (game: Game) => void;
}) {
  const { game } = result;
  return <article className="game-card" aria-labelledby={`game-${game.app_id}`}>
    <a href={`/games/${game.app_id}`} className="art-link" aria-label={`View ${game.title} details`}><Artwork game={game} /></a>
    <div className="game-card-copy">
      <div className="game-title"><span className="rank" aria-label={`Rank ${index + 1}`}>{index + 1}</span><h3 id={`game-${game.app_id}`}><a href={`/games/${game.app_id}`}>{game.title}</a></h3></div>
      <GameFacts game={game} />
      <p className="game-description">{game.description}</p>
      <details className="why-game"><summary>Why this game?</summary>
        <ul className="reasons">{result.reasons.map((reason, n) => <li key={n}>{reason.text}</li>)}</ul>
        <p className="small muted">Content similarity suggests candidates; it does not guarantee the same experience.</p>
        <h4>Source evidence</h4><EvidenceList game={game} ids={[...new Set(result.reasons.flatMap((reason) => reason.evidence_ids))]} />
        <h4>Keep in mind</h4><ul className="tradeoffs">{result.tradeoffs.map((text) => <li key={text}>{text}</li>)}</ul>
      </details>
      <div className="card-actions"><a className="text-link" href={game.store_url} target="_blank" rel="noreferrer">View on Steam<span className="sr-only"> (opens in a new tab)</span></a>
        <button className="quiet-button" type="button" onClick={() => onExclude(game)}>Exclude<span className="sr-only"> {game.title}</span></button></div>
    </div>
  </article>;
}
