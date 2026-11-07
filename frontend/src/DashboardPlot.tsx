import { useEffect, useRef, useState, type CSSProperties } from 'react';
import type { Data, Layout } from 'plotly.js';
import type { Count } from './api/analytics';

const colors = ['#e3fb76', '#8995f0', '#f5bd79', '#79cec4', '#d99ad1', '#c1c7da', '#a4c77c', '#e7a399'];
const text = (s: string) => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
export type DashboardPlotKind = 'donut' | 'summary-donut' | 'line' | 'column' | 'rank' | 'stack' | 'strip' | 'lollipop';

export default function DashboardPlot({ rows, kind, title }: { rows: (Count & { unsupported?: number; unknown?: number })[]; kind: DashboardPlotKind; title: string }) {
  const element = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState('loading');
  const [hidden, setHidden] = useState<string[]>([]);
  const [reset, setReset] = useState(0);
  const [hovered, setHovered] = useState<number | null>(null);
  const total = rows.reduce((n, row) => n + row.count, 0);
  const available = kind === 'stack' ? total + rows.reduce((n, row) => n + (row.unsupported ?? 0), 0) : total;
  const donut = kind === 'donut' || kind === 'summary-donut';
  const height = kind === 'strip' ? 100 : kind === 'rank' ? Math.max(320, rows.length * 30 + 60) : 300;
  useEffect(() => {
    const node = element.current;
    if (!node || !available || kind === 'lollipop') return;
    let disposed = false;
    let purge: (() => void) | undefined;
    void import('plotly.js-basic-dist-min').then(async ({ default: plot }) => {
      if (disposed) return;
      const labels = rows.map(r => text(r.label));
      const scale = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--study-scale')) || 1;
      const values = rows.map(r => r.count);
      const rank = kind === 'rank';
      const indices = rows.map((_, i) => i);
      const axis = { gridcolor: '#30384e', zerolinecolor: '#41485e', fixedrange: false, automargin: true, ticklabeloverflow: 'allow' as const, tickfont: { size: 11 * scale }, color: '#b8bed1' };
      const layout: Partial<Layout> = {
        barmode: 'stack',
        autosize: true, height: height * scale,
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { family: 'Manrope Variable, sans-serif', color: '#f5f6ef', size: 12 * scale },
        margin: { t: 18 * scale, r: (rank ? 42 : 14) * scale, b: 50 * scale, l: (rank ? 120 : kind === 'line' ? 32 : 42) * scale }, showlegend: false,
        dragmode: 'zoom', hovermode: 'closest',
        hoverlabel: { bgcolor: '#f5f6ef', bordercolor: '#f5f6ef', font: { color: '#111525', size: 13 * scale } },
        xaxis: rank ? { ...axis, automargin: false, rangemode: 'tozero', range: [0, Math.max(...values) * 1.18], dtick: total < 5 ? 1 : undefined } : { ...axis, automargin: kind !== 'line', tickmode: 'array', tickvals: indices, ticktext: labels, showgrid: false },
        yaxis: rank ? { ...axis, tickmode: 'array', tickvals: indices, ticktext: labels.map(s => s.length > 24 ? s.slice(0, 22) + '…' : s), autorange: 'reversed', showgrid: false } : { ...axis, rangemode: 'tozero' },
        hiddenlabels: hidden.map(text),
      };
      let data: Data[];
      if (donut) {
        const percentages = values.map(value => `${(value / total * 100).toFixed(1)}%`);
        layout.margin = { t: 28 * scale, r: 34 * scale, b: 28 * scale, l: 34 * scale };
        if (kind === 'summary-donut') layout.annotations = [{ text: `${total.toLocaleString('en-US')}<br><span style="font-size:${11 * scale}px">games</span>`, x: .5, y: .5, xref: 'paper', yref: 'paper', showarrow: false, font: { size: 22 * scale, color: '#f5f6ef' } }];
        data = [{ type: 'pie', labels, values, hole: .68, sort: false, text: percentages, customdata: percentages, textinfo: 'text', textposition: 'outside', automargin: true, textfont: { color: '#f5f6ef', size: 12 * scale }, marker: { colors, line: { color: '#111525', width: 3 } }, hovertemplate: '%{label}<br>%{value:,} games · %{customdata}<extra></extra>' }];
      } else if (kind === 'strip') {
        layout.margin = { t: 60 * scale, r: 0, b: 0, l: 0 };
        layout.xaxis = { visible: false, fixedrange: true, range: [0, total] };
        layout.yaxis = { visible: false, fixedrange: true, range: [-.5, .5] };
        layout.dragmode = false;
        data = rows.map((row, i) => ({ type: 'bar', orientation: 'h', x: [row.count], y: [0], width: 1,
          marker: { color: colors[i % colors.length] }, hoverinfo: 'none' }));
      } else if (kind === 'line') {
        data = [{ type: 'scatter', x: indices, y: values, customdata: labels, mode: 'lines+markers', line: { color: colors[1], width: 3 }, marker: { size: values.map(v => v > 0 ? 7 : 0), color: colors[0] }, fill: 'tozeroy', fillcolor: 'rgba(137,149,240,.12)', hovertemplate: values.map(v => v > 0 ? '%{customdata}<br>%{y:,} releases<extra></extra>' : '<extra></extra>') }];
      } else if (kind === 'stack') {
        data = (['Supported', 'Unsupported'] as const).flatMap((name, i) => {
          const counts = rows.map(r => i === 0 ? r.count : r.unsupported ?? 0);
          return counts.some(v => v > 0) ? [{ type: 'bar' as const, name, x: indices, y: counts.map(v => v || null), text: counts.map(v => v ? v.toLocaleString('en-US') : ''), textposition: 'inside' as const, insidetextanchor: 'middle' as const, textfont: { color: '#111525', size: 12 * scale }, customdata: labels, marker: { color: colors[i] }, hovertemplate: `%{customdata}<br>${name}: %{y:,} games<extra></extra>` }] : [];
        });
      } else {
        if (!rank) layout.yaxis = { ...layout.yaxis, range: [0, Math.max(...values) * 1.18] };
        data = [{ type: 'bar', x: rank ? values : indices, y: rank ? indices : values, text: values.map(v => v.toLocaleString('en-US')), textposition: 'outside', textfont: { color: '#f5f6ef', size: 12 * scale }, cliponaxis: false, customdata: labels, orientation: rank ? 'h' : 'v', marker: { color: rank ? colors[0] : colors[1] }, hovertemplate: `%{customdata}<br>%{${rank ? 'x' : 'y'}:,} games<extra></extra>` }];
      }
      purge = () => plot.purge(node);
      const graph = await plot.react(node, data, layout, { responsive: true, displayModeBar: false, scrollZoom: false, showTips: false, doubleClick: 'reset', staticPlot: false });
      if (disposed) { plot.purge(node); return; }
      if (kind === 'strip') {
        graph.on('plotly_hover', event => { if (!disposed) setHovered(event.points[0]?.curveNumber ?? null); });
        graph.on('plotly_unhover', () => { if (!disposed) setHovered(null); });
      }
      setStatus('ready');
    }).catch(() => { if (!disposed) setStatus('error'); });
    return () => { disposed = true; purge?.(); };
  }, [rows, kind, hidden, reset, total, available, donut, height]);
  if (!available) return <p className="dashboard-note">No recorded data for this chart.</p>;
  if (kind === 'strip' || kind === 'lollipop') return <div className="dashboard-interactive" data-chart-kind={kind}>
    {kind === 'strip' && hovered !== null && rows[hovered] && <div className="dashboard-discount-hover" role="tooltip" style={{ left: `clamp(0px, calc(${(rows.slice(0, hovered).reduce((n, r) => n + r.count, 0) + rows[hovered]!.count / 2) / total * 100}% - 80px), calc(100% - 160px))` }}>
      <span>{rows[hovered]!.label}</span><br />{rows[hovered]!.count.toLocaleString('en-US')} games · {(rows[hovered]!.count / total * 100).toFixed(1)}%
    </div>}
    {kind === 'strip' && <><div ref={element} className="dashboard-plot" aria-hidden="true" data-ready={status === 'ready'} style={{ '--plot-height': `${height}px` } as CSSProperties} />
      {status !== 'ready' && <p role="status" className="dashboard-note">{status === 'error' ? 'Interactive chart unavailable. Values are shown below; reload to try again.' : 'Preparing interactive chart…'}</p>}</>}
    <ul className={kind === 'strip' ? 'dashboard-share-values' : 'dashboard-lollipops'}>{rows.map((row, i) => <li key={row.label}>
      {kind === 'strip' ? <><div><span className="dashboard-legend-dot" style={{ background: colors[i % colors.length] }} aria-hidden="true" /><span>{row.label}</span><strong>{row.count.toLocaleString('en-US')}</strong></div><p>{(row.count / total * 100).toFixed(1)}% of {total.toLocaleString('en-US')} games</p></> : <>
        <span className="dashboard-developer-name">{row.label}</span><div className="dashboard-lollipop-track" aria-hidden="true"><span style={{ width: `${row.count / Math.max(...rows.map(r => r.count)) * 100}%` }} /></div><strong>{row.count.toLocaleString('en-US')}</strong>
      </>}
    </li>)}</ul>
  </div>;
  return <div className={`dashboard-interactive${kind === 'summary-donut' ? ' dashboard-donut-summary' : ''}`} data-chart-kind={kind} data-status={status}>
    {kind === 'stack' && <p className="dashboard-stack-key">{['Supported', 'Unsupported'].map((label, i) => rows.some(r => (i === 0 ? r.count : r.unsupported ?? 0) > 0) && <span key={label}><span className="dashboard-legend-dot" style={{ background: colors[i] }} aria-hidden="true" />{label}</span>)}</p>}
    <div ref={element} className="dashboard-plot" aria-hidden="true" data-ready={status === 'ready'} style={{ '--plot-height': `${height}px` } as CSSProperties} />
    {status !== 'ready' && <p role="status" className="dashboard-note">{status === 'error' ? 'Interactive chart unavailable. Values are shown below; reload to try again.' : 'Preparing interactive chart…'}</p>}
    {donut ? <div className="dashboard-legend" role="group" aria-label={`${title} legend`}>
      {rows.map((row, i) => <button type="button" key={row.label} aria-pressed={!hidden.includes(row.label)} onClick={() => setHidden(current => current.includes(row.label) ? current.filter(x => x !== row.label) : [...current, row.label])}>
        <span className="dashboard-legend-dot" style={{ background: colors[i % colors.length] }} aria-hidden="true" /><span>{row.label}</span><strong>{row.count.toLocaleString('en-US')}</strong><small>{(row.count / total * 100).toFixed(1)}%</small>
      </button>)}<p>Toggle a category to compare.</p>
    </div> : <div className="dashboard-plot-tools"><p>Hover or tap for values. Drag to zoom.</p><button type="button" onClick={() => setReset(n => n + 1)} aria-label={`Reset view: ${title}`}>Reset view</button></div>}
  </div>;
}
