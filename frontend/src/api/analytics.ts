import type { components } from './schema';
import { request } from './discovery';

export type AnalyticsResponse = components['schemas']['AnalyticsResponse'];
export type Analytics = components['schemas']['CatalogAnalytics'];
export type Count = components['schemas']['AnalyticsCount'];

const record = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const count = (v: unknown): v is number => Number.isSafeInteger(v) && Number(v) >= 0;
const date = (v: unknown) => typeof v === 'string' && Number.isFinite(Date.parse(v));
function rows(v: unknown, max: number): v is Count[] {
  return Array.isArray(v) && v.length <= max && v.every(x => record(x) && typeof x.label === 'string'
    && x.label.length > 0 && x.label.length <= 300 && count(x.count)) && new Set(v.map(x => x.label)).size === v.length;
}
export function isAnalytics(value: unknown): value is AnalyticsResponse {
  if (!record(value) || !record(value.data)) return false;
  const d = value.data;
  if (typeof value.catalog_version !== 'string' || !value.catalog_version || d.catalog_version !== value.catalog_version
    || !date(value.catalog_created_at) || typeof value.analytics_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(value.analytics_sha256)
    || d.format !== 'catalog-analytics-v1' || !count(d.total_games) || d.total_games > 2000 || !count(d.total_developers)
    || !(d.observed_from === null || date(d.observed_from)) || !(d.observed_until === null || date(d.observed_until))
    || ![d.avg_price_cents, d.avg_discount_percent].every(x => x === null || (typeof x === 'number' && Number.isFinite(x) && x >= 0))
    || (typeof d.avg_discount_percent === 'number' && d.avg_discount_percent > 100) || !record(d.coverage)) return false;
  const keys = ['original_price', 'discount', 'developers', 'release_month', 'reviews', 'description', 'genres'];
  const coverage = d.coverage;
  if (!keys.every(key => {
    const c = coverage[key];
    return record(c) && count(c.known) && count(c.unknown) && count(c.invalid) && c.known + c.unknown + c.invalid === d.total_games;
  })) return false;
  if (!rows(d.free_paid, 3) || d.free_paid.length !== 3 || !rows(d.price_ranges, 6) || d.price_ranges.length !== 6
    || !rows(d.discount_ranges, 7) || d.discount_ranges.length !== 7 || !rows(d.genres, 15) || !rows(d.developers, 10)
    || !rows(d.reviews, 30) || !rows(d.words, 60) || !rows(d.platforms, 3) || d.platforms.length !== 3
    || !Array.isArray(d.release_years) || d.release_years.length > 1000
    || !d.release_years.every(x => record(x) && count(x.year) && x.year >= 1 && x.year <= 9999 && count(x.unknown_month)
      && Array.isArray(x.months) && x.months.length === 12 && x.months.every(count))) return false;
  const sum = (v: Count[]) => v.reduce((n, x) => n + x.count, 0);
  const price = d.coverage.original_price as { known: number };
  const discount = d.coverage.discount as { known: number };
  const release = d.coverage.release_month as { known: number };
  return sum(d.free_paid) === d.total_games && sum(d.reviews) === d.total_games && sum(d.price_ranges) === price.known
    && sum(d.discount_ranges) === discount.known && (d.avg_price_cents === null) === (price.known === 0)
    && (d.avg_discount_percent === null) === (discount.known === 0)
    && d.platforms.every((x: unknown) => record(x) && count(x.count) && count(x.unsupported) && count(x.unknown) && x.count + x.unsupported + x.unknown === d.total_games)
    && d.release_years.reduce((n, x) => n + x.months.reduce((a: number, b: number) => a + b, 0), 0) === release.known;
}
export const getAnalytics = (signal: AbortSignal) => request('/api/v1/analytics', isAnalytics, signal);
