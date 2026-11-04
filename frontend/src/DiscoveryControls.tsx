import { useEffect, useId, useRef, useState, type CSSProperties } from 'react';
import Icon from './Icon';

type Option<T extends string> = { value: T; label: string };
export function MultiChoice<T extends string>({ title, values, options, onChange, onOpen, limit = 30 }: {
  title: string; values: T[]; options: readonly Option<T>[]; onChange: (values: T[]) => void; onOpen?: () => void; limit?: number;
}) {
  const details = useRef<HTMLDetailsElement>(null);
  const valueId = useId();
  const [open, setOpen] = useState(false);
  const chosen = values.map((value) => options.find((option) => option.value === value)?.label ?? value);
  const summary = chosen.length > 2 ? `${chosen[0]} +${chosen.length - 1}` : chosen.join(', ') || 'Any';
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => { if (details.current && !details.current.contains(event.target as Node)) details.current.open = false; };
    document.addEventListener('pointerdown', outside);
    return () => document.removeEventListener('pointerdown', outside);
  }, [open]);
  return <fieldset className="study-choice"><legend>{title}</legend>
    <details ref={details} className="study-multiselect" onToggle={(event) => { setOpen(event.currentTarget.open); if (event.currentTarget.open) onOpen?.(); }}
      onKeyDown={(event) => { if (event.key === 'Escape' && details.current) { event.preventDefault(); details.current.open = false; details.current.querySelector('summary')?.focus(); } }}>
      <summary aria-label={`Choose ${title.toLowerCase()}`} aria-describedby={valueId}><span id={valueId} title={chosen.join(', ') || 'Any'}>{summary}</span><Icon name="chevron" /></summary>
      <div className="study-choice-options">
        {options.map((option) => <label key={option.value} className="study-check"><input type="checkbox" checked={values.includes(option.value)}
          disabled={!values.includes(option.value) && values.length >= limit}
          onChange={(event) => onChange(event.target.checked ? [...values, option.value] : values.filter((value) => value !== option.value))} />{option.label}</label>)}
        <button type="button" className="study-clear-choice" disabled={!values.length} aria-label={`Clear ${title.toLowerCase()}`} onClick={() => onChange([])}>Clear selection</button>
      </div>
    </details>
  </fieldset>;
}

const money = (cents: number) => `$${(cents / 100).toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
export function PriceRange({ minimum, maximum, ceiling, disabled, unbounded, onChange }: {
  minimum: number; maximum: number; ceiling: number; disabled: boolean; unbounded: boolean; onChange: (minimum: number, maximum: number) => void;
}) {
  const id = useId();
  const style = { '--price-start': `${minimum / ceiling * 100}%`, '--price-end': `${maximum / ceiling * 100}%` } as CSSProperties;
  return <fieldset className="study-price-range" disabled={disabled} aria-describedby={`${id}-values`}><legend>Price range <span>USD</span></legend>
    <div className="study-price-well"><div className="study-price-values" id={`${id}-values`}><span>{minimum === 0 ? 'Free to play' : money(minimum)}</span><span>{unbounded ? 'Any price' : maximum === 0 ? 'Free only' : money(maximum)}</span></div>
    <div className="study-price-track" style={style}>
      <div className="study-price-rail" aria-hidden="true"><span /></div>
      <input type="range" min={0} max={ceiling} step={1} value={minimum} style={{ zIndex: minimum === ceiling ? 4 : 2 }} aria-label="Minimum recorded price" aria-valuemax={maximum}
        aria-valuetext={minimum === 0 ? 'Free to play, zero dollars' : `${money(minimum)} USD`}
        onChange={(event) => onChange(Math.min(Number(event.target.value), maximum), maximum)} />
      <input type="range" min={0} max={ceiling} step={1} value={maximum} style={{ zIndex: 3 }} aria-label="Maximum recorded price" aria-valuemin={minimum}
        aria-valuetext={unbounded ? 'No maximum price' : maximum === 0 ? 'Free-to-play games only' : `${money(maximum)} USD`}
        onChange={(event) => onChange(minimum, Math.max(Number(event.target.value), minimum))} />
    </div>
    </div>
  </fieldset>;
}
