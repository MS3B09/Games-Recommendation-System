import type { DiscoverResponse, Filters } from './api/discovery';
import { label } from './GuestGameRow';

const conflictLabels: Record<string, string> = { max_price_cents: 'Maximum recorded price', min_price_cents: 'Minimum recorded price',
  platforms: 'Required platforms', required_modes: 'Required play modes', free_only: 'Free-to-play only',
  price_operator: 'Upper price boundary', platform_match: 'Platform matching' };
function conflictValue(field: string, raw: string, criteria: Filters): string {
  let value: unknown;
  try { value = JSON.parse(raw); } catch { return raw; }
  if (field === 'max_price_cents' || field === 'min_price_cents') {
    if (value === null) return field === 'max_price_cents' ? 'No maximum' : 'No minimum';
    if (typeof value === 'number') return `${field === 'min_price_cents' ? 'At least' : criteria.price_operator === 'lt' ? 'Under' : 'Up to'} $${(value / 100).toFixed(2)} USD`;
  }
  if (Array.isArray(value)) return value.length ? value.map((item) => String(item) === 'mac' ? 'macOS' : label(String(item))).join(', ') : 'Any';
  if (typeof value === 'boolean') return value ? 'Required' : 'Not required';
  if (field === 'price_operator') return value === 'lt' ? 'Exclusive (under)' : 'Inclusive (up to)';
  if (field === 'platform_match') return value === 'all' ? 'All selected platforms' : 'Any selected platform';
  return String(value);
}

export function CriteriaSummary({ criteria }: { criteria: Filters }) {
  const budget = criteria.free_only ? 'Explicit free-to-play' : criteria.max_price_cents === null ? 'No maximum price'
    : `${criteria.price_operator === 'lt' ? 'Under' : 'Up to'} $${(criteria.max_price_cents / 100).toFixed(2)} USD`;
  const items = [budget, ...(criteria.min_price_cents ? [`At least $${(criteria.min_price_cents / 100).toFixed(2)} USD`] : []),
    ...(criteria.platforms.length ? [`${criteria.platforms.map((item) => item === 'mac' ? 'macOS' : label(item)).join(' / ')} · ${criteria.platform_match}`] : ['Any platform']),
    ...criteria.required_modes.map(label), ...criteria.required_genres.map(label),
    ...(criteria.excluded_ids.length ? [`${criteria.excluded_ids.length} exact exclusions`] : [])];
  return <ul className="study-criteria" aria-label="Applied hard criteria">{items.map((item) => <li key={item}>{item}</li>)}</ul>;
}
export default function HybridSummary({ response, loading, resolve }: { response: DiscoverResponse; loading: boolean; resolve: (choice: 'controls' | 'text') => void }) {
  const conflicts = response.conflicts ?? [];
  return <div className="study-hybrid-summary">
    <p className="study-criteria-lead">Applied to this search · Hard criteria</p><CriteriaSummary criteria={response.effective_criteria as Filters} />
    {response.effective_query && <p className="study-soft-query"><strong>Soft text preference</strong> {response.effective_query}</p>}
    {!!response.unresolved_preferences?.length && <div className="study-uncertainty"><h3>What we cannot verify.</h3><ul>{response.unresolved_preferences.map((item) => <li key={item}>{item}</li>)}</ul></div>}
    {!!conflicts.length && <section className="study-conflict" aria-labelledby="study-conflict-title"><h3 id="study-conflict-title">Your words and limits differ.</h3>
      <p>Results below keep your existing controls. Choose whether to apply all proposed changes; nothing has been silently relaxed.</p>
      <dl>{conflicts.map((item) => <div key={item.field}><dt>{conflictLabels[item.field] ?? label(item.field.replaceAll('_', '-'))}</dt><dd>Current: {conflictValue(item.field, item.current, response.effective_criteria as Filters)} · Text proposes: {conflictValue(item.field, item.proposed, (response.proposed_criteria ?? response.effective_criteria) as Filters)}</dd></div>)}</dl>
      {response.proposed_criteria && <><p>Proposed hard criteria</p><CriteriaSummary criteria={response.proposed_criteria as Filters} /></>}
      <div className="study-conflict-actions"><button type="button" disabled={loading} onClick={() => resolve('controls')}>Keep my controls</button><button type="button" disabled={loading} onClick={() => resolve('text')}>Apply text changes</button></div>
    </section>}
    {!!response.degraded_reasons?.length && <div className="study-ai-state" role="status"><p>{response.degraded_reasons.join(' ')}</p></div>}
  </div>;
}
