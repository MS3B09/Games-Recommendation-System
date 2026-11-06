import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';
import { getAnalytics, type Analytics, type AnalyticsResponse, type Count } from './api/analytics';
import { ServiceError } from './api/client';
import { observed } from './GuestGameRow';
import DashboardPlot, { type DashboardPlotKind } from './DashboardPlot';
import Icon from './Icon';

const number = (n: number) => n.toLocaleString('en-US');
const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function Values({ rows, caption }: { rows: Count[]; caption: string }) {
  return <details className="dashboard-values"><summary>View exact values</summary><table><caption>{caption}</caption>
    <thead><tr><th scope="col">Category</th><th scope="col">Games</th></tr></thead>
    <tbody>{rows.map(x => <tr key={x.label}><th scope="row">{x.label}</th><td>{number(x.count)}</td></tr>)}</tbody></table></details>;
}
function Chart({ title, note, rows, children, className = '', kind = 'rank' }: { title: string; note: ReactNode; rows: (Count & { unsupported?: number })[]; children?: ReactNode; className?: string; kind?: DashboardPlotKind }) {
  const shown = rows.filter(x => (x.count > 0 || (kind === 'stack' && (x.unsupported ?? 0) > 0)) && x.label.trim().toLowerCase() !== 'unknown');
  return <article className={`dashboard-chart ${className}`} aria-label={title}>
    <h3>{title}</h3><p className="dashboard-note">{note}</p>
    {children}
    {/* Keep all twelve month positions in the trend, without listing zero-value statistics. */}
    <DashboardPlot title={title} rows={kind === 'line' ? rows : shown} kind={kind} />
    <Values rows={shown.filter(x => x.count > 0)} caption={title} />
  </article>;
}
function Coverage({ data, field, compact = false }: { data: Analytics; field: string; compact?: boolean }) {
  const c = data.coverage[field]!;
  return <>{number(c.known)} known{!compact && <> · {number(c.unknown)} unknown{c.invalid ? ` · ${number(c.invalid)} invalid` : ''}</>}</>;
}
function DashboardData({ data: d }: { data: Analytics }) {
  const [year, setYear] = useState('all');
  const selected = d.release_years.filter(x => year === 'all' || String(x.year) === year);
  const released = months.map((label, i) => ({ label, count: selected.reduce((n, y) => n + y.months[i]!, 0) }));
  const wordMax = Math.max(1, ...d.words.map(x => x.count));
  const platforms = d.platforms.map(x => ({ ...x, label: x.label === 'Linux(SteamOS)' ? 'Linux' : x.label }));
  return <>
    <dl className="dashboard-metrics" aria-label="Catalog overview">
      <div><dt><Icon name="gamepad" />Total games</dt><dd><span>{number(d.total_games)}</span><p>Unique eligible games</p></dd></div>
      <div><dt><Icon name="sliders" />Avg. price</dt><dd><span>{d.avg_price_cents === null ? 'Unknown' : `$${(d.avg_price_cents / 100).toFixed(2)}`}</span><p>Original/list USD · <Coverage data={d} field="original_price" /></p></dd></div>
      <div><dt><Icon name="arrow" />Avg. discount</dt><dd><span>{d.avg_discount_percent === null ? 'Unknown' : `${d.avg_discount_percent.toFixed(2)}%`}</span><p><Coverage data={d} field="discount" /></p></dd></div>
      <div><dt><Icon name="compass" />Total developers</dt><dd><span>{number(d.total_developers)}</span><p><Coverage data={d} field="developers" /> games</p></dd></div>
    </dl>
    {d.total_games === 0 ? <div className="dashboard-empty"><h2>No games in this snapshot.</h2><p>The charts will appear when an eligible catalog is published.</p></div> : <>
      <nav className="dashboard-sections" aria-label="Dashboard sections"><a href="#dashboard-prices"><Icon name="sliders" />Prices &amp; value<Icon name="arrow" /></a><a href="#dashboard-range"><Icon name="book" />Releases &amp; genres<Icon name="arrow" /></a><a href="#dashboard-people"><Icon name="gamepad" />Platforms &amp; people<Icon name="arrow" /></a><a href="#dashboard-themes"><Icon name="chat" />Description themes<Icon name="arrow" /></a></nav>
      <section className="dashboard-section" aria-labelledby="dashboard-prices"><h2 id="dashboard-prices">What does play cost?</h2><p>Recorded US store prices, not live offers. Price charts use original/list USD prices, not discounted checkout prices.</p>
        <div className="dashboard-grid"><Chart title="Free vs paid games" kind="summary-donut" note="Free to play is an explicit source classification. A temporary $0 promotion does not make a paid game free to play." rows={d.free_paid} className="dashboard-free" />
        <Chart title="Games by price range" kind="column" note={<><Coverage compact data={d} field="original_price" /> · recorded list USD</>} rows={d.price_ranges} /></div>
        <Chart title="Games by discount" kind="strip" note={<><Coverage compact data={d} field="discount" />. Percentages use the displayed valid discounts, not the whole catalog.</>} rows={d.discount_ranges} />
      </section>
      <section className="dashboard-section" aria-labelledby="dashboard-range"><h2 id="dashboard-range">A catalog with range.</h2><p>Explore when games arrived and the genres they bring. Multi-genre games count once in each of their genres.</p>
        <div className="dashboard-grid dashboard-range-grid"><Chart title="Games released by month" kind="line" note={<><Coverage compact data={d} field="release_month" /> month. Year-only dates are not assigned a month.</>} rows={released}>
          <div className="dashboard-year"><label htmlFor="release-year">Release year</label><select id="release-year" value={year} onChange={e => setYear(e.target.value)}><option value="all">All years</option>{d.release_years.map(y => <option key={y.year} value={y.year}>{y.year}</option>)}</select></div>
        </Chart><Chart title="Top 15 game genres" note={<><Coverage compact data={d} field="genres" /> games. Full genre labels are retained.</>} rows={d.genres} className="dashboard-ranked" /></div>
      </section>
      <section className="dashboard-section" aria-labelledby="dashboard-people"><h2 id="dashboard-people">Platforms. Makers. Players.</h2><p>The support, studios and review sentiments recorded for this catalog.</p>
        <div className="dashboard-grid"><Chart title="Supported platforms" kind="stack" note="Linux counts verified Linux support only. Independent SteamOS / Steam Deck compatibility has not been verified." rows={platforms}>
          <details className="dashboard-platforms dashboard-values"><summary>Support coverage</summary><ul>{platforms.filter(x => x.count > 0 || x.unsupported > 0).map(x => <li key={x.label}><strong>{x.label}</strong><p>{[x.count > 0 ? `${number(x.count)} supported` : '', x.unsupported > 0 ? `${number(x.unsupported)} unsupported` : ''].filter(Boolean).join(' · ')}</p></li>)}</ul></details>
        </Chart><Chart title="Review type distribution" kind="donut" note="Steam’s sentiment labels only; low-review-count labels are excluded. Percentages use the displayed categories. All languages, all purchase types, off-topic activity filtered." rows={d.reviews.filter(x => !/^\d+\s+user reviews?$/i.test(x.label.trim()))} /></div>
        <Chart title="Top 10 developers by game count" kind="lollipop" note="Each developer counts once per game. Co-developed games count for multiple developers. Names are normalized for spacing and case, never split at commas." rows={d.developers} className="dashboard-developers" />
      </section>
      <section className="dashboard-section" aria-labelledby="dashboard-themes"><h2 id="dashboard-themes">What’s in a description?</h2><p>Recurring words from the actual catalog descriptions. Larger words appear more often; these are themes, not verified gameplay attributes.</p>
        {d.words.length ? <div className="dashboard-word-cloud" aria-label="Description word cloud">{d.words.filter(x => x.count > 0).map(x => <span key={x.label} style={{ '--word-size': `${1 + Math.sqrt(x.count / wordMax) * 2.4}rem` } as CSSProperties} title={`${x.label}: ${number(x.count)} occurrences`}>{x.label}</span>)}</div> : <p>No description terms are available.</p>}
        <details className="dashboard-values"><summary>View word counts and method</summary><p>Top 60 terms by occurrence, then alphabetical ties. All descriptions are processed (up to the catalog’s 16,000-character limit per game); there is no combined-text truncation. Unicode normalization and case folding, 3–24-letter terms, English function-word and game/store boilerplate stopwords. No stemming. Layout follows deterministic frequency order.</p><p><Coverage compact data={d} field="description" /> descriptions.</p>
          <ol className="dashboard-word-counts">{d.words.filter(x => x.count > 0).map(x => <li key={x.label}><span>{x.label}</span><strong>{number(x.count)}</strong></li>)}</ol></details>
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
