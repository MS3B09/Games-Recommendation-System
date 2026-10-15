import { useEffect, useState } from 'react';
import { getGame, type Game } from './api/discovery';
import { Artwork, EvidenceList, GameFacts } from './GameCard';
import './discovery.css';

export default function GameDetail({ id }: { id: number }) {
  const [game, setGame] = useState<Game | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    getGame(id, controller.signal).then((value) => { if (!controller.signal.aborted) setGame(value); },
      (reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'The catalog is unavailable.'); });
    return () => controller.abort();
  }, [id, attempt]);
  return <section className="game-detail"><a className="text-link" href="/">Back to discovery</a>
    {game ? <><h1>{game.title}</h1><Artwork game={game} /><GameFacts game={game} /><p>{game.description}</p>
      <p>{game.genres?.join(' · ')}</p><p>{game.modes?.join(' · ') || 'Play modes unknown'}</p>
      <p className="small muted">Recorded US/USD price; check Steam for current price and availability.</p>
      <a className="button" href={game.store_url} target="_blank" rel="noreferrer">View on Steam<span className="sr-only"> (opens in a new tab)</span></a>
      <details className="detail-evidence"><summary>Catalog evidence & provenance</summary><EvidenceList game={game} /></details></>
      : <><h1>Game details</h1><p role="status">{error || 'Loading recorded game details…'}</p>{error && <button className="button" onClick={() => { setError(null); setAttempt((value) => value + 1); }}>Try again</button>}</>}
  </section>;
}
