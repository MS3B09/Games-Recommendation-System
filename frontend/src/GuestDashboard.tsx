import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';
import { getAnalytics, type Analytics, type AnalyticsResponse, type Count } from './api/analytics';
import { ServiceError } from './api/client';
import { observed } from './GuestGameRow';

const number = (n: number) => n.toLocaleString('en-US');
const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function Values({ rows, caption }: { rows: Count[]; caption: string }) {
  return <details className="dashboard-values"><summary>View exact values</summary><table><caption>{caption}</caption>
    <thead><tr><th scope="col">Category</th><th scope="col">Games</th></tr></thead>
    <tbody>{rows.map(x => <tr key={x.label}><th scope="row">{x.label}</th><td>{number(x.count)}</td></tr>)}</tbody></table></details>;
}
function Chart({ title, note, rows, children, className = '' }: { title: string; note: ReactNode; rows: Count[]; children?: ReactNode; className?: string }) {
  const max = Math.max(1, ...rows.map(x => x.count));
  return <article className={`dashboard-chart ${className}`} aria-label={title}>
    <h3>{title}</h3><p className="dashboard-note">{note}</p>
    {children ?? (rows.length ? <ul className="dashboard-bars">{rows.map(x => <li key={x.label}>
      <div><span>{x.label}</span><strong>{number(x.count)}</strong></div>
      <span className="dashboard-track" aria-hidden="true"><span style={{ width: `${x.count / max * 100}%` }} /></span>
    </li>)}</ul> : <p>No recorded data for this chart.</p>)}
    <Values rows={rows} caption={title} />
  </article>;
}
function Coverage({ data, field }: { data: Analytics; field: string }) {
  const c = data.coverage[field]!;
  return <>{number(c.known)} known · {number(c.unknown)} unknown{c.invalid ? ` · ${number(c.invalid)} invalid` : ''}</>;
}
function DashboardData({ data: d }: { data: Analytics }) {
  const [year, setYear] = useState('all');
  const selected = d.release_years.filter(x => year === 'all' || String(x.year) === year);
  const released = months.map((label, i) => ({ label, count: selected.reduce((n, y) => n + y.months[i]!, 0) }));
  const maxMonth = Math.max(1, ...released.map(x => x.count));
  const wordMax = Math.max(1, ...d.words.map(x => x.count));
  return <>
    <dl className="dashboard-metrics" aria-label="Catalog overview">
      <div><dt>Total games</dt><dd><span>{number(d.total_games)}</span><p>Unique eligible games</p></dd></div>
      <div><dt>Avg. price</dt><dd><span>{d.avg_price_cents === null ? 'Unknown' : `$${(d.avg_price_cents / 100).toFixed(2)}`}</span><p>Original/list USD · <Coverage data={d} field="original_price" /></p></dd></div>
      <div><dt>Avg. discount</dt><dd><span>{d.avg_discount_percent === null ? 'Unknown' : `${d.avg_discount_percent.toFixed(2)}%`}</span><p><Coverage data={d} field="discount" /></p></dd></div>
      <div><dt>Total developers</dt><dd><span>{number(d.total_developers)}</span><p><Coverage data={d} field="developers" /> games</p></dd></div>
    </dl>
    {d.total_games === 0 ? <div className="dashboard-empty"><h2>No games in this snapshot.</h2><p>The charts will appear when an eligible catalog is published.</p></div> : <>
      <nav className="dashboard-sections" aria-label="Dashboard sections"><a href="#dashboard-prices">Prices &amp; value</a><a href="#dashboard-range">Releases &amp; genres</a><a href="#dashboard-people">Platforms &amp; people</a><a href="#dashboard-themes">Description themes</a></nav>
      <section className="dashboard-section" aria-labelledby="dashboard-prices"><h2 id="dashboard-prices">What does play cost?</h2><p>Recorded US store prices, not live offers. Price charts use original/list USD prices, not discounted checkout prices.</p>
        <Chart title="Free vs paid games" note="Free to play is an explicit source classification. A temporary $0 promotion does not make a paid game free to play." rows={d.free_paid} className="dashboard-free">
          <div className="dashboard-free-chart"><div className="dashboard-segments" aria-hidden="true">{d.free_paid.map((x, i) => <span key={x.label} className={`dashboard-segment-${i}`} style={{ flexGrow: x.count }} />)}</div>
            <ul>{d.free_paid.map((x, i) => <li key={x.label}><span className={`dashboard-key dashboard-segment-${i}`} aria-hidden="true" /><span>{x.label}</span><strong>{number(x.count)}</strong><span>{(x.count / d.total_games * 100).toFixed(1)}%</span></li>)}</ul></div>
        </Chart>
        <div className="dashboard-grid"><Chart title="Games by price range" note={<><Coverage data={d} field="original_price" /> · USD</>} rows={d.price_ranges} />
          <Chart title="Games by discount" note={<><Coverage data={d} field="discount" />. Valid discounts only; invalid values are excluded.</>} rows={d.discount_ranges} /></div>
      </section>
      <section className="dashboard-section" aria-labelledby="dashboard-range"><h2 id="dashboard-range">A catalog with range.</h2><p>Explore when games arrived and the genres they bring. Multi-genre games count once in each of their genres.</p>
        <div className="dashboard-grid dashboard-range-grid"><Chart title="Games released by month" note={<><Coverage data={d} field="release_month" /> month. Year-only dates are not assigned a month.</>} rows={released}>
          <div className="dashboard-year"><label htmlFor="release-year">Release year</label><select id="release-year" value={year} onChange={e => setYear(e.target.value)}><option value="all">All years</option>{d.release_years.map(y => <option key={y.year} value={y.year}>{y.year}</option>)}</select></div>
          {year !== 'all' && <p className="dashboard-note">{number(selected.reduce((n, y) => n + y.unknown_month, 0))} releases with an unknown month in {year}.</p>}
          <div className="dashboard-month-scroll" tabIndex={0} role="region" aria-label="Monthly release chart. Scroll horizontally for all months on narrow screens."><div className="dashboard-months" role="img" aria-label={`Monthly releases, ${year === 'all' ? 'all years' : year}. ${released.map(x => `${x.label}: ${x.count}`).join(', ')}`}>
            {released.map(x => <div key={x.label}><strong>{number(x.count)}</strong><span className="dashboard-month-track"><span style={{ height: `${x.count / maxMonth * 100}%` }} /></span><span>{x.label}</span></div>)}
          </div></div><p className="dashboard-chart-help">Scroll the chart for all months, or open the exact values below.</p>
        </Chart><Chart title="Top 15 game genres" note={<><Coverage data={d} field="genres" /> games. Full genre labels are retained.</>} rows={d.genres} className="dashboard-ranked" /></div>
      </section>
      <section className="dashboard-section" aria-labelledby="dashboard-people"><h2 id="dashboard-people">Platforms. Makers. Players.</h2><p>The support, studios and review sentiments recorded for this catalog.</p>
        <div className="dashboard-grid"><Chart title="Supported platforms" note="Linux(SteamOS) counts verified Linux support only. Independent SteamOS / Steam Deck compatibility has not been verified." rows={d.platforms}>
          <ul className="dashboard-platforms">{d.platforms.map(x => <li key={x.label}><div><strong>{x.label}</strong><strong>{number(x.count)}</strong></div><span className="dashboard-track" aria-hidden="true"><span style={{ width: `${x.count / d.total_games * 100}%` }} /></span><p>{number(x.unsupported)} unsupported · {number(x.unknown)} unknown</p></li>)}</ul>
        </Chart><Chart title="Review type distribution" note={<><Coverage data={d} field="reviews" /> summaries. Steam’s exact sentiment labels; all languages, all purchase types, off-topic activity filtered. No reviews and unknown are separate.</>} rows={d.reviews} /></div>
        <Chart title="Top 10 developers by game count" note="Each developer counts once per game. Co-developed games count for multiple developers. Names are normalized for spacing and case, never split at commas." rows={d.developers} className="dashboard-developers" />
      </section>
      <section className="dashboard-section" aria-labelledby="dashboard-themes"><h2 id="dashboard-themes">What’s in a description?</h2><p>Recurring words from the actual catalog descriptions. Larger words appear more often; these are themes, not verified gameplay attributes.</p>
        {d.words.length ? <div className="dashboard-word-cloud" aria-label="Description word cloud">{d.words.map(x => <span key={x.label} style={{ '--word-size': `${1 + Math.sqrt(x.count / wordMax) * 2.4}rem` } as CSSProperties} title={`${x.label}: ${number(x.count)} occurrences`}>{x.label}</span>)}</div> : <p>No description terms are available.</p>}
        <details className="dashboard-values"><summary>View word counts and method</summary><p>Top 60 terms by occurrence, then alphabetical ties. All descriptions are processed (up to the catalog’s 16,000-character limit per game); there is no combined-text truncation. Unicode normalization and case folding, 3–24-letter terms, English function-word and game/store boilerplate stopwords. No stemming. Layout follows deterministic frequency order.</p><p><Coverage data={d} field="description" /> descriptions.</p>
          <ol className="dashboard-word-counts">{d.words.map(x => <li key={x.label}><span>{x.label}</span><strong>{number(x.count)}</strong></li>)}</ol></details>
      </section>
    </>}
  </>;
}
export default function GuestDashboard() {
  const [snapshot, setSnapshot] = useState<AnalyticsResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void getAnalytics(controller.signal).then(result => { if (!controller.signal.aborted) setSnapshot(result); })
      .catch(err => { if (!controller.signal.aborted) setError(err instanceof ServiceError ? err.message : 'The dashboard could not be loaded. Please try again.'); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision]);
  function refresh() { setLoading(true); setError(''); setRevision(x => x + 1); }
  return <div className="dashboard">
    <section className="dashboard-intro" aria-labelledby="dashboard-title"><div><h1 id="dashboard-title" tabIndex={-1}>Inside the catalog.</h1><p>The games behind your next great find.</p></div>
      <div className="dashboard-snapshot"><p>US store · Recorded USD</p><button className="study-retry" type="button" disabled={loading} onClick={refresh}>{loading ? 'Loading snapshot…' : 'Refresh snapshot'}</button></div>
    </section>
    <div className="dashboard-body">
      {error && <div className="dashboard-error" role="alert"><h2>Dashboard unavailable.</h2><p>{error}</p>{snapshot && <p>The previous snapshot below is retained. It may no longer be the active catalog.</p>}<button className="study-retry" type="button" onClick={refresh} disabled={loading}>Retry dashboard</button><a href="/">Back to discovery</a></div>}
      {loading && <p role="status">{snapshot ? 'Checking the active catalog. The previous snapshot stays visible below.' : 'Loading catalog metrics and charts…'}</p>}
      {snapshot && <><div className="dashboard-provenance"><p>Observed {observed(snapshot.data.observed_from)}–{observed(snapshot.data.observed_until)} UTC</p><details><summary>About this snapshot</summary><p>This page shows the same versioned catalog used for recommendations, not every game on Steam. Refresh or reload to fetch the active version. Browsing these charts does not change your taste, saved games or chat.</p><p>Catalog <code>{snapshot.catalog_version}</code> · Created {observed(snapshot.catalog_created_at)} UTC</p></details></div><DashboardData key={snapshot.catalog_version} data={snapshot.data} /></>}
    </div>
  </div>;
}
