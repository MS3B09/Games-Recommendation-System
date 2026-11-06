import { useEffect, useRef, useState, type CSSProperties } from 'react';
import type { Data, Layout } from 'plotly.js';
import type { Count } from './api/analytics';

const colors = ['#e3fb76', '#8995f0', '#f5bd79', '#79cec4', '#d99ad1', '#c1c7da', '#a4c77c', '#e7a399'];
const text = (s: string) => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

export default function DashboardPlot({ rows, kind, title }: { rows: (Count & { unsupported?: number; unknown?: number })[]; kind: 'donut' | 'line' | 'column' | 'rank' | 'stack'; title: string }) {
  const element = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState('loading');
  const [hidden, setHidden] = useState<string[]>([]);
  const [reset, setReset] = useState(0);
  const total = rows.reduce((n, row) => n + row.count, 0);
  useEffect(() => {
    const node = element.current;
    if (!node || !total) return;
    let disposed = false;
    let purge: (() => void) | undefined;
    void import('plotly.js-basic-dist-min').then(async ({ default: plot }) => {
      if (disposed) return;
      const labels = rows.map(r => text(r.label));
      const scale = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--study-scale')) || 1;
      const values = rows.map(r => r.count);
      const rank = kind === 'rank';
      const indices = rows.map((_, i) => i);
      const axis = { gridcolor: '#30384e', zerolinecolor: '#41485e', fixedrange: false, automargin: true, tickfont: { size: 11 * scale }, color: '#b8bed1' };
      const layout: Partial<Layout> = {
        barmode: 'stack',
        autosize: true, height: (rank ? Math.max(320, rows.length * 30 + 60) : 300) * scale,
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { family: 'Manrope Variable, sans-serif', color: '#f5f6ef', size: 12 * scale },
        margin: { t: 18 * scale, r: 14 * scale, b: 50 * scale, l: (rank ? 120 : 42) * scale }, showlegend: false,
        dragmode: 'zoom', hovermode: 'closest',
        hoverlabel: { bgcolor: '#f5f6ef', bordercolor: '#f5f6ef', font: { color: '#111525', size: 13 * scale } },
        xaxis: rank ? { ...axis, rangemode: 'tozero', dtick: total < 5 ? 1 : undefined } : { ...axis, tickmode: 'array', tickvals: indices, ticktext: labels, showgrid: false },
        yaxis: rank ? { ...axis, tickmode: 'array', tickvals: indices, ticktext: labels.map(s => s.length > 24 ? s.slice(0, 22) + '…' : s), autorange: 'reversed', showgrid: false } : { ...axis, rangemode: 'tozero' },
        hiddenlabels: hidden.map(text),
      };
      let data: Data[];
      if (kind === 'donut') {
        layout.margin = { t: 12 * scale, r: 12 * scale, b: 12 * scale, l: 12 * scale };
        data = [{ type: 'pie', labels, values, hole: .68, sort: false, textinfo: 'none', marker: { colors, line: { color: '#111525', width: 3 } }, hovertemplate: '%{label}<br>%{value:,} games · %{percent}<extra></extra>' }];
      } else if (kind === 'line') {
        data = [{ type: 'scatter', x: indices, y: values, customdata: labels, mode: 'lines+markers', line: { color: colors[1], width: 3 }, marker: { size: 7, color: colors[0] }, fill: 'tozeroy', fillcolor: 'rgba(137,149,240,.12)', hovertemplate: '%{customdata}<br>%{y:,} releases<extra></extra>' }];
      } else if (kind === 'stack') {
        data = (['Supported', 'Unsupported', 'Unknown'] as const).map((name, i) => ({ type: 'bar', name, x: indices, y: rows.map(r => i === 0 ? r.count : i === 1 ? r.unsupported ?? 0 : r.unknown ?? 0), customdata: labels, marker: { color: colors[i] }, hovertemplate: `%{customdata}<br>${name}: %{y:,} games<extra></extra>` }));
      } else {
        data = [{ type: 'bar', x: rank ? values : indices, y: rank ? indices : values, customdata: labels, orientation: rank ? 'h' : 'v', marker: { color: rank ? colors[0] : colors[1] }, hovertemplate: `%{customdata}<br>%{${rank ? 'x' : 'y'}:,} games<extra></extra>` }];
      }
      purge = () => plot.purge(node);
      await plot.react(node, data, layout, { responsive: true, displayModeBar: false, scrollZoom: false, showTips: false, doubleClick: 'reset', staticPlot: false });
      if (disposed) { plot.purge(node); return; }
      setStatus('ready');
    }).catch(() => { if (!disposed) setStatus('error'); });
    return () => { disposed = true; purge?.(); };
  }, [rows, kind, hidden, reset, total]);
  if (!total) return <p className="dashboard-note">No recorded data for this chart.</p>;
  return <div className="dashboard-interactive" data-chart-kind={kind}>
    {kind === 'stack' && <p className="dashboard-stack-key">{['Supported', 'Unsupported', 'Unknown'].map((label, i) => <span key={label}><span className="dashboard-legend-dot" style={{ background: colors[i] }} aria-hidden="true" />{label}</span>)}</p>}
    <div ref={element} className="dashboard-plot" aria-hidden="true" data-ready={status === 'ready'} style={{ '--plot-height': `${kind === 'rank' ? Math.max(320, rows.length * 30 + 60) : 300}px` } as CSSProperties} />
    {status !== 'ready' && <p role="status" className="dashboard-note">{status === 'error' ? 'Interactive chart unavailable. Use the exact values below, or reload to try again.' : 'Preparing interactive chart…'}</p>}
    {kind === 'donut' ? <div className="dashboard-legend" role="group" aria-label={`${title} legend`}>
      {rows.map((row, i) => <button type="button" key={row.label} aria-pressed={!hidden.includes(row.label)} onClick={() => setHidden(current => current.includes(row.label) ? current.filter(x => x !== row.label) : [...current, row.label])}>
        <span className="dashboard-legend-dot" style={{ background: colors[i % colors.length] }} aria-hidden="true" /><span>{row.label}</span><strong>{row.count.toLocaleString('en-US')}</strong><small>{(row.count / total * 100).toFixed(1)}%</small>
      </button>)}<p>Toggle a category to compare. Percentages above use the full chart total.</p>
    </div> : <div className="dashboard-plot-tools"><p>Hover or tap for values. Drag to zoom.</p><button type="button" onClick={() => setReset(n => n + 1)} aria-label={`Reset view: ${title}`}>Reset view</button></div>}
  </div>;
}
