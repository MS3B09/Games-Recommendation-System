import { useEffect, useRef, useState, type FormEvent } from 'react';
import { discoverGames, getFacets, searchGames, type DiscoverResponse, type Facets, type Filters, type Game } from './api/discovery';
import { ServiceError, type CatalogStatus } from './api/client';
import GameCard, { observedDate } from './GameCard';
import './discovery.css';

const defaults: Filters = { max_price_cents: null, price_operator: 'lte', free_only: false, platforms: [], platform_match: 'any',
  required_modes: [], preferred_terms: [], unwanted_terms: [], excluded_ids: [] };
const platformNames = { windows: 'Windows', mac: 'macOS', linux: 'Linux' } as const;
const modeNames = { 'single-player': 'Single-player', multiplayer: 'Multiplayer', 'online-co-op': 'Online co-op', 'local-co-op': 'Local co-op' } as const;
type ErrorState = { message: string; requestId?: string };
function errorState(error: unknown): ErrorState {
  return { message: error instanceof Error ? error.message : 'The service is unavailable. Please try again.', requestId: error instanceof ServiceError ? error.requestId : undefined };
}

export default function Discovery({ catalog }: { catalog: CatalogStatus }) {
  const [favorites, setFavorites] = useState<Game[]>([]);
  const [excluded, setExcluded] = useState<Game[]>([]);
  const [filters, setFilters] = useState<Filters>(defaults);
  const [budget, setBudget] = useState('');
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState<Game[]>([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchError, setSearchError] = useState<ErrorState | null>(null);
  const [facets, setFacets] = useState<Facets | null>(null);
  const [facetError, setFacetError] = useState(false);
  const [facetAttempt, setFacetAttempt] = useState(0);
  const [response, setResponse] = useState<DiscoverResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ErrorState | null>(null);
  const searchController = useRef<AbortController | null>(null);
  const discoveryController = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => { searchController.current?.abort(); discoveryController.current?.abort(); };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    getFacets(controller.signal).then((value) => { if (!controller.signal.aborted) { setFacets(value); setFacetError(false); } },
      () => { if (!controller.signal.aborted) setFacetError(true); });
    return () => controller.abort();
  }, [facetAttempt]);

  function invalidate() { discoveryController.current?.abort(); setResponse(null); setError(null); setBusy(false); }
  function update(patch: Partial<Filters>) { invalidate(); setFilters((current) => ({ ...current, ...patch })); }
  function toggle<K extends 'platforms' | 'required_modes' | 'preferred_terms' | 'unwanted_terms'>(key: K, term: Filters[K][number]) {
    const values: string[] = filters[key];
    update({ [key]: values.includes(term) ? values.filter((value) => value !== term) : [...values, term] });
  }
  async function find(event: FormEvent) {
    event.preventDefault();
    searchController.current?.abort();
    const controller = new AbortController(); searchController.current = controller;
    setSearchBusy(true); setHasSearched(true); setSearchError(null); setSearch([]);
    try { const page = await searchGames(query.trim(), controller.signal); if (!controller.signal.aborted) setSearch(page.items); }
    catch (reason) { if (!controller.signal.aborted) setSearchError(errorState(reason)); }
    finally { if (!controller.signal.aborted) setSearchBusy(false); }
  }
  async function discover(event: FormEvent) {
    event.preventDefault();
    invalidate();
    const controller = new AbortController(); discoveryController.current = controller;
    setBusy(true);
    try {
      const result = await discoverGames({ favorite_ids: favorites.map((game) => game.app_id), filters: { ...filters, excluded_ids: excluded.map((game) => game.app_id) }, limit: 10 }, controller.signal);
      if (!controller.signal.aborted) setResponse(result);
    } catch (reason) { if (!controller.signal.aborted) setError(errorState(reason)); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  function exclude(game: Game) {
    invalidate(); setExcluded((current) => current.some((item) => item.app_id === game.app_id) ? current : [...current, game]);
  }

  return <>
    <section className="discovery-intro"><h1>Find your next favorite.</h1>
      <p>Start with the games you love. Set your limits. Find something worth playing.</p>
      <p className="catalog-context">{catalog.game_count} games · US store / USD · {catalog.source_observed_at ? `Catalog observations from ${observedDate(catalog.source_observed_at)} (UTC)` : 'Observation dates unknown'}</p>
    </section>
    <div className="discovery-workspace">
      <aside className="criteria" aria-label="Discovery criteria">
        <section aria-labelledby="favorites-heading"><h2 id="favorites-heading">Your favorite games</h2>
          <p className="small muted">Pick titles to guide content similarity. Selections last until you leave or reload this page.</p>
          {favorites.length > 0 && <ul className="selected-games" aria-label="Selected favorites">{favorites.map((game) => <li key={game.app_id}><span>{game.title}</span><button className="quiet-button" onClick={() => { invalidate(); setFavorites((current) => current.filter((item) => item.app_id !== game.app_id)); }} aria-label={`Remove ${game.title} from favorites`}>Remove</button></li>)}</ul>}
          <form className="search-form" onSubmit={find}><label htmlFor="favorite-search">Search the catalog</label>
            <div className="search-row"><input id="favorite-search" type="search" maxLength={200} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try Hades or Portal" />
              <button type="submit" className="button">Search</button></div></form>
          <div className="search-status" role="status">{searchBusy ? 'Searching the catalog…' : searchError ? searchError.message : !hasSearched ? 'Search for a game you enjoyed, or search without a name to browse.' : search.length === 0 ? 'No titles found. Try a shorter name.' : 'Select a favorite from these catalog titles.'}</div>
          {!searchBusy && !searchError && <ul className="search-results">{search.map((game) => {
            const selected = favorites.some((item) => item.app_id === game.app_id);
            return <li key={game.app_id}><button type="button" className="pick-game" disabled={selected || favorites.length >= 50} onClick={() => { invalidate(); setFavorites((current) => [...current, game]); }}>
              <span>{game.title}</span><span className="pick-action">{selected ? 'Selected' : 'Add favorite'}</span></button></li>;
          })}</ul>}
          {favorites.length >= 50 && <p className="small">Favorite limit reached (50). Remove one to select another.</p>}
        </section>
        <form className="filter-form" onSubmit={discover}>
          <h2>Your requirements</h2>
          <div className="budget-fields"><label className="checkbox"><input type="checkbox" checked={filters.free_only} onChange={(event) => update({ free_only: event.target.checked, max_price_cents: event.target.checked || budget === '' ? null : Math.round(Number(budget) * 100) })} />Free-to-play only</label>
            <label htmlFor="budget">Maximum recorded price (USD)</label><input id="budget" type="number" min="0" max="10000" step="0.01" placeholder="No limit" disabled={filters.free_only} value={budget} onChange={(event) => {
              const value = event.target.value; setBudget(value); update({ max_price_cents: value === '' ? null : Math.round(Number(value) * 100) });
            }} /><p className="small muted">Maximum is inclusive. Recorded prices are snapshots, not live purchase quotes.</p></div>
          <fieldset><legend>Required platforms</legend><div className="checkbox-group">{Object.entries(platformNames).map(([key, label]) => <label className="checkbox" key={key}><input type="checkbox" checked={filters.platforms?.includes(key as 'windows' | 'mac' | 'linux')} onChange={() => toggle('platforms', key as 'windows' | 'mac' | 'linux')} />{label}</label>)}</div>
            <label htmlFor="platform-match" className="small">Platform matching</label><select id="platform-match" value={filters.platform_match} onChange={(event) => update({ platform_match: event.target.value as 'any' | 'all' })}><option value="any">Any selected platform</option><option value="all">All selected platforms</option></select></fieldset>
          <details className="more-filters"><summary>Play modes, genres & exclusions</summary>
            <fieldset><legend>Required play modes</legend>{Object.entries(modeNames).map(([key, label]) => <label className="checkbox" key={key}><input type="checkbox" checked={filters.required_modes?.includes(key as keyof typeof modeNames)} onChange={() => toggle('required_modes', key as keyof typeof modeNames)} />{label}</label>)}</fieldset>
            {facetError ? <p className="small">Genre choices could not load. <button type="button" className="quiet-button" onClick={() => setFacetAttempt((value) => value + 1)}>Retry genre choices</button></p> : !facets ? <p className="small">Loading genres…</p> : <>
              <fieldset><legend>Preferred genres (boost, not required)</legend><div className="term-options">{facets.genres.map((term) => <label className="checkbox" key={term}><input type="checkbox" checked={filters.preferred_terms?.includes(term)} onChange={() => toggle('preferred_terms', term)} />{term}</label>)}</div></fieldset>
              <fieldset><legend>Unwanted genres (exclude)</legend><div className="term-options">{facets.genres.map((term) => <label className="checkbox" key={term}><input type="checkbox" checked={filters.unwanted_terms?.includes(term)} onChange={() => toggle('unwanted_terms', term)} />{term}</label>)}</div></fieldset>
              <p className="small muted">This sample has genre evidence but no enriched tags. Missing tags cannot prove an experience is absent.</p></>}
            <p className="small">Exclude individual games using the result-card action. Required facts that are unknown do not pass your filters.</p>
            {excluded.length > 0 && <ul className="selected-games" aria-label="Excluded games">{excluded.map((game) => <li key={game.app_id}><span>{game.title}</span><button type="button" className="quiet-button" onClick={() => { invalidate(); setExcluded((current) => current.filter((item) => item.app_id !== game.app_id)); }}>Undo<span className="sr-only"> exclusion of {game.title}</span></button></li>)}</ul>}
          </details>
          <button className="button discover-button" type="submit" disabled={busy}>{busy ? 'Finding games…' : 'Discover games'}</button>
          <p className="small muted">No sign-in or AI key needed. Natural-language discovery is coming in a later milestone.</p>
        </form>
      </aside>
      <section className="results" aria-labelledby="results-heading" aria-busy={busy}>
        <div className="results-header"><h2 id="results-heading">Your shortlist</h2><span className="small muted">{response ? `${response.results.length} results` : 'Catalog-grounded discovery'}</span></div>
        <div role="status" aria-live="polite" className="results-status">{busy ? 'Finding games that meet your requirements. The free service may need a moment to wake up.' : error ? error.message : response ? response.results.length ? 'Your shortlist is ready. Open “Why this game?” to inspect the evidence.' : 'No games meet these requirements. Your filters have not been relaxed.' : 'Choose your favorites and requirements, then select Discover games.'}</div>
        {error?.requestId && <p className="small request-id">Request ID: {error.requestId}</p>}
        {response?.results.length === 0 && <ul className="empty-suggestions">{response.suggested_refinements.map((text) => <li key={text}>{text}</li>)}</ul>}
        {busy && <div className="result-placeholder" aria-hidden="true"><div /><div /></div>}
        {response && <div className="game-grid">{response.results.map((result, index) => <GameCard key={result.game.app_id} result={result} index={index} onExclude={exclude} />)}</div>}
        {!response && !busy && !error && <div className="discovery-empty"><h3>Built around your taste.</h3><p>Favorites guide the shortlist. Price, platform and play-mode requirements are checked against recorded Steam fields.</p><p className="small muted">An empty list stays empty until you change the requirements. No hidden filter relaxation.</p></div>}
      </section>
    </div>
  </>;
}
