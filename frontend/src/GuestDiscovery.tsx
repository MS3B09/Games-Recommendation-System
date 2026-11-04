import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import Icon from './Icon';
import { discoverGames, getFacets, resolveGames, searchGames, type DiscoverResponse, type Facets, type Game } from './api/discovery';
import { ServiceError } from './api/client';
import { serviceError } from './api/errors';
import ErrorNotice from './ErrorNotice';
import { cacheGame, defaultFilters, rankingKey, type GuestSnapshot, type GuestStore } from './guest-store';
import { Artwork, GuestGameRow, label } from './GuestGameRow';
import { MultiChoice, PriceRange } from './DiscoveryControls';
import { CriteriaSummary } from './HybridSummary';

type RequestState<T> = { key: string; loading?: boolean; value?: T; error?: ServiceError };
const message = (error: unknown) => error instanceof ServiceError ? error : serviceError('unexpected_error');

export default function GuestDiscovery({ store, state }: { store: GuestStore; state: GuestSnapshot }) {
  const { data } = state;
  const preferences = data.preferences;
  // Feedback changes hide only their exact titles. Keep the submitted shortlist
  // and its ordering until another explicit discovery; favorites/limits still
  // invalidate it. The full ranking key remains the in-flight response guard.
  const criteria = JSON.stringify([data.favorites.map(game => game.app_id), preferences]);
  const requestCriteria = rankingKey(data);
  const favoriteIds = data.favorites.map((game) => game.app_id).join(',');
  const [resolved, setResolved] = useState<RequestState<{ items: Game[]; unknown_ids: number[] }>>({ key: '' });
  const [search, setSearch] = useState('');
  const [choices, setChoices] = useState<RequestState<Game[]>>({ key: '' });
  const [facets, setFacets] = useState<RequestState<Facets>>({ key: '' });
  const [findings, setFindings] = useState<RequestState<DiscoverResponse>>({ key: '' });
  const searchRequest = useRef<AbortController | null>(null);
  const discoveryRequest = useRef<{ key: string; ranking: string; controller: AbortController } | null>(null);
  const facetsRequest = useRef<AbortController | null>(null);
  const resolvedRequest = useRef<AbortController | null>(null);
  const facetsCache = useRef<Facets | null>(null);
  const findingsSection = useRef<HTMLElement>(null);
  function reviewFavorites() {
    const picker = document.querySelector<HTMLDetailsElement>('.study-picker');
    if (picker) picker.open = true;
    document.getElementById('study-search')?.focus();
  }
  function editLimits() {
    document.querySelector<HTMLInputElement>('[aria-label="Maximum recorded price"]')?.focus();
  }
  async function refreshFavorites() {
    resolvedRequest.current?.abort();
    const controller = new AbortController(); resolvedRequest.current = controller;
    const ticket = store.ticket();
    try {
      const value = await resolveGames(data.favorites.map(game => game.app_id), controller.signal);
      if (!controller.signal.aborted && store.current(ticket)) setResolved({ key: favoriteIds, value });
    } catch (error) {
      if (!controller.signal.aborted && store.current(ticket)) setResolved({ key: favoriteIds, error: message(error) });
    }
  }
  const loadFacets = useCallback(async () => {
    if (facetsCache.current || facetsRequest.current) return;
    const controller = new AbortController(); facetsRequest.current = controller;
    setFacets({ key: 'catalog', loading: true });
    try {
      const value = await getFacets(controller.signal);
      if (!controller.signal.aborted) { facetsCache.current = value; setFacets({ key: 'catalog', value }); }
    } catch (error) { if (!controller.signal.aborted) setFacets({ key: 'catalog', error: message(error) }); }
    finally { if (facetsRequest.current === controller) facetsRequest.current = null; }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const ready = favoriteIds ? resolveGames(favoriteIds.split(',').map(Number), controller.signal).then((result) => {
      if (!controller.signal.aborted) setResolved({ key: favoriteIds, value: result });
    }).catch((error: unknown) => { if (!controller.signal.aborted) setResolved({ key: favoriteIds, error: message(error) }); }) : Promise.resolve();
    // Sequence metadata after favorite resolution rather than competing for the
    // small API request allowance with two automatic requests at once.
    void ready.then(() => { if (!controller.signal.aborted) void loadFacets(); });
    return () => { controller.abort(); resolvedRequest.current?.abort(); };
  }, [favoriteIds, loadFacets]);
  useEffect(() => () => { if (discoveryRequest.current?.ranking === requestCriteria) discoveryRequest.current.controller.abort(); }, [requestCriteria]);
  useEffect(() => () => { searchRequest.current?.abort(); facetsRequest.current?.abort(); discoveryRequest.current?.controller.abort(); }, []);

  async function searchFavorites(query: string) {
    searchRequest.current?.abort();
    const controller = new AbortController(); searchRequest.current = controller;
    setChoices({ key: query, loading: true });
    try {
      const result = await searchGames(query, controller.signal);
      if (!controller.signal.aborted) setChoices({ key: query, value: result.items });
    } catch (error) { if (!controller.signal.aborted) setChoices({ key: query, error: message(error) }); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!store.setPreferences({ min_price_cents: priceMinimum, max_price_cents: unboundedPrice ? null : priceMaximum,
      free_only: !unboundedPrice && priceMaximum === 0, price_operator: preferences.price_operator, platform_match: 'any', preferred_terms: [], unwanted_terms: [] })) return;
    await runDiscovery();
  }
  async function runDiscovery() {
    const current = store.getSnapshot().data;
    const key = JSON.stringify([current.favorites.map(game => game.app_id), current.preferences]);
    const ticket = store.ticket();
    discoveryRequest.current?.controller.abort();
    const controller = new AbortController(); discoveryRequest.current = { key, ranking: rankingKey(current), controller };
    setFindings({ key, loading: true });
    findingsSection.current?.focus({ preventScroll: true }); findingsSection.current?.scrollIntoView({ behavior: 'instant', block: 'start' });
    try {
      const value = await discoverGames({ favorite_ids: current.favorites.map((game) => game.app_id), preferences: current.preferences,
        filters: current.preferences,
        feedback: current.feedback.map(({ app_id, kind, timestamp }) => ({ app_id, kind, timestamp })), limit: 10 }, controller.signal);
      if (!controller.signal.aborted && store.current(ticket)) {
        if (!store.addHistory(value, ticket)) return;
        discoveryRequest.current = null;
        setFindings({ key, value });
      }
    } catch (error) { if (!controller.signal.aborted && store.current(ticket)) setFindings({ key, error: message(error) }); }
    finally {
      if (discoveryRequest.current?.controller === controller) setFindings((current) => current.key === key && current.loading ? { ...current, loading: false } : current);
    }
  }
  const currentFindings = findings.key === criteria ? findings : null;
  const results = currentFindings?.value?.results;
  const dismissed = new Set(data.feedback.filter(item => item.kind !== 'interested').map(item => item.app_id));
  const visibleResults = results?.filter(item => !dismissed.has(item.game.app_id));
  const genres = [...new Set([...(facets.value?.genres ?? ['action', 'adventure', 'indie', 'rpg', 'simulation']), ...preferences.required_genres])];
  const priceMinimum = preferences.free_only ? 0 : preferences.min_price_cents ?? 0;
  const priceCeiling = Math.min(1000000, Math.max(100, Math.ceil(Math.max(facets.value?.max_price_cents ?? 0,
    preferences.max_price_cents ?? 0, priceMinimum) / 100) * 100));
  const priceMaximum = preferences.free_only ? 0 : preferences.max_price_cents ?? priceCeiling;
  // The disabled slider needs a finite layout scale, but that fallback must
  // never become a real budget when a saved unbounded price cannot be resolved.
  const unboundedPrice = !preferences.free_only && preferences.max_price_cents === null && facets.value?.max_price_cents == null;
  const validResolved = resolved.key === favoriteIds ? resolved.value : undefined;

  return <>
    <section className="study-composer" id="taste" aria-labelledby="study-title">
      <div className="study-opening"><h1 id="study-title">Find your next.</h1><p>Good taste. New territory.{' '}<br />Start with the games you love.</p></div>
      <div className="study-request">
        <div className="study-favorites-line"><span className="study-sentence">I’m into</span>
          {data.favorites.map((game) => <button type="button" className="study-favorite" key={game.app_id} aria-label={`Remove ${game.title} from favorites`} onClick={() => store.toggleFavorite(game)}>{game.title}<Icon name="close" /></button>)}
          {!data.favorites.length && <span className="study-fresh">a fresh start.</span>}
          <details className="study-picker"><summary>Change favorites</summary>
            <div className="study-picker-content">
              <p className="study-picker-guidance">Tap a cover to select or remove a favorite. Choose up to 50 favorites. {state.persistent ? 'Saved on this device.' : 'Temporary in this tab.'}</p>
              <form className="study-picker-search" onSubmit={(event) => { event.preventDefault(); void searchFavorites(search.trim()); }}>
                <label htmlFor="study-search">Search the catalog</label><div className="study-picker-search-row"><input id="study-search" type="search" maxLength={200} placeholder="Try Hades or Portal" value={search} onChange={(event) => setSearch(event.target.value)} />
                  <button className="study-picker-search-button" type="submit"><Icon name="search" /><span>Search</span></button></div>
              </form>
              <p className="study-picker-status" role="status">{choices.loading ? 'Searching the catalog…' : choices.error ? '' : (choices.value === undefined ? 'Search for a favorite, or submit an empty search to browse the catalog.' : choices.value.length ? `${data.favorites.length} selected · Select a favorite from these catalog titles.` : 'No titles found. Try a shorter name.')}</p>
              {choices.error && <ErrorNotice error={choices.error} onRetry={() => void searchFavorites(search.trim())} onEdit={() => document.getElementById('study-search')?.focus()} />}
              <ul className="study-picker-games" aria-label="Favorite game choices">{choices.value?.map((game) => {
                const selected = data.favorites.some((item) => item.app_id === game.app_id);
                return <li key={game.app_id}><button className="study-pick-game" type="button" aria-pressed={selected} disabled={!selected && data.favorites.length >= 50} onClick={() => store.toggleFavorite(cacheGame(game))}>
                  <span className="study-pick-art" aria-hidden="true"><Artwork game={game} /></span><span className="study-pick-title">{game.title}</span>
                  <span className="study-pick-action">{selected ? <><Icon name="check" />Selected</> : <><Icon name="plus" />Add<span className="study-sr"> favorite</span></>}</span>
                </button></li>;
              })}</ul>
            </div>
          </details>
        </div>
        {validResolved?.unknown_ids.length ? <div className="study-catalog-notice" role="status"><p>{data.favorites.filter((game) => validResolved.unknown_ids.includes(game.app_id)).map((game) => game.title).join(', ')} {validResolved.unknown_ids.length === 1 ? 'is' : 'are'} no longer available in our catalog. Remove unavailable favorites to continue.</p><button type="button" onClick={() => data.favorites.filter((game) => validResolved.unknown_ids.includes(game.app_id)).forEach((game) => store.toggleFavorite(game))}>Remove unavailable favorites</button></div> : null}
        {resolved.key === favoriteIds && resolved.error && <ErrorNotice error={resolved.error} onRetry={() => void refreshFavorites()} onRemoveFavorite={reviewFavorites} />}
        <form className="study-boundaries" id="study-form" onSubmit={submit}>
          <p className="study-range-intro">My limits</p>
          <div className="study-limits">
            <MultiChoice title="Required play modes" values={preferences.required_modes} limit={4}
              options={(['single-player', 'online-co-op', 'local-co-op', 'multiplayer'] as const).map((value) => ({ value, label: label(value) }))}
              onChange={(required_modes) => store.setPreferences({ required_modes })} />
            <MultiChoice title="Required platform" values={preferences.platforms} limit={3}
              options={(['windows', 'mac', 'linux'] as const).map((value) => ({ value, label: value === 'mac' ? 'macOS' : label(value) }))}
              onChange={(platforms) => store.setPreferences({ platforms, platform_match: 'any' })} />
            <MultiChoice title="Required catalog genre" values={preferences.required_genres}
              options={genres.map((value) => ({ value, label: value === 'rpg' ? 'RPG' : label(value) }))}
              onOpen={loadFacets} onChange={(required_genres) => store.setPreferences({ required_genres })} />
            <PriceRange minimum={priceMinimum} maximum={priceMaximum} ceiling={priceCeiling}
              unbounded={unboundedPrice}
              disabled={!facets.value || facets.value.max_price_cents == null}
              onChange={(minimum, maximum) => store.setPreferences({ min_price_cents: minimum, max_price_cents: maximum,
                free_only: maximum === 0, price_operator: 'lte' })} />
          </div>
          <p className="study-filter-hint">All selected modes and genres; any selected platform. Recorded USD prices, not live quotes.</p>
          {facets.error && <ErrorNotice error={facets.error} onRetry={() => void loadFacets()} retryLabel="Retry catalog controls" />}
          {facets.value?.max_price_cents === null && <p className="study-catalog-notice">The catalog has no known recorded prices for a price slider.</p>}
          {preferences.excluded_ids.length > 0 && <div className="study-exclusions"><span>{preferences.excluded_ids.length} explicitly excluded</span><button type="button" onClick={() => store.setPreferences({ excluded_ids: [] })}>Undo exclusions</button></div>}
        </form>
      </div>
      <div className="study-launch"><button type="submit" form="study-form" className="study-discover" disabled={currentFindings?.loading}>{currentFindings?.loading ? 'Finding games…' : 'Find my next game'}<Icon name="arrow" /></button></div>
    </section>
    <section className="study-results" id="possibilities" ref={findingsSection} tabIndex={-1} aria-labelledby="study-results-title" aria-busy={!!currentFindings?.loading}>
      <div className="study-results-heading"><h2 id="study-results-title">The possibilities.</h2><a href="#taste">Rework your request</a></div>
      <p className="study-count" role="status">{currentFindings?.loading ? 'Finding games. The free service may need a moment to wake up.' : currentFindings?.error ? '' : (results ? `${visibleResults?.length ?? 0} catalog-backed recommendations${visibleResults?.length !== results.length ? ' · Feedback saved. Find again for a fresh ranking.' : ''}` : findings.key ? 'Your taste changed. Find again to apply your current preferences and feedback.' : 'Start with your favorites, then find your next game.')}</p>
      {currentFindings?.error && <ErrorNotice error={currentFindings.error} onRetry={() => void runDiscovery()} retryLabel="Try discovery again" onEdit={editLimits} editLabel="Edit limits" onRemoveFavorite={reviewFavorites} onBack={() => findingsSection.current?.focus()} />}
      {currentFindings?.loading && <div className="study-loading" aria-hidden="true"><div /><div /></div>}
      {currentFindings?.value && <><p className="study-criteria-lead">Applied to this search · Hard criteria</p><CriteriaSummary criteria={preferences} /></>}
      {results?.length === 0 && <div className="study-empty"><h3>No games match these filters.</h3><p>Try increasing your budget or removing a filter. Your filters have not been relaxed.</p><button type="button" onClick={() => store.setPreferences(defaultFilters())}>Reset boundaries</button></div>}
      {!!results?.length && visibleResults?.length === 0 && <div className="study-empty"><h3>A fresh shortlist?</h3><p>You've dismissed these games. Find my next game will use your saved feedback for new recommendations.</p></div>}
      {visibleResults?.map((result) => <GuestGameRow key={result.game.app_id} result={result} store={store} state={state} />)}
      {currentFindings?.value && <p className="study-source-note">US store snapshots · See each game’s evidence for observation dates. Prices may have changed.</p>}
    </section>
  </>;
}
