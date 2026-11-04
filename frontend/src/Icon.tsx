type IconName = 'compass' | 'search' | 'arrow' | 'sliders' | 'server' | 'book' | 'external' | 'close' | 'check' | 'plus' | 'chevron' | 'chat' | 'gamepad';

const paths: Record<IconName, string> = {
  compass: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm4 5-2.5 5.5L8 16l2.5-5.5L16 8Z',
  search: 'M20 20l-5-5M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13Z',
  arrow: 'M4 12h16m-6-6 6 6-6 6',
  sliders: 'M4 7h5m4 0h7M4 17h9m4 0h3M9 4v6m4-6v6m0 4v6m4-6v6',
  server: 'M4 4h16v6H4V4Zm0 10h16v6H4v-6ZM7 7h.01M7 17h.01M11 7h6m-6 10h6',
  book: 'M12 5v15m0-15C9 3 5 3 3 4v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-2-1-6-1-9 1Z',
  external: 'M14 3h7v7m0-7L10 14M10 3H3v18h18v-7',
  close: 'm6 6 12 12M18 6 6 18',
  check: 'm5 12 4 4L19 6',
  plus: 'M12 5v14M5 12h14',
  chevron: 'm6 9 6 6 6-6',
  chat: 'M4 4h16v12H9l-5 4V4Zm4 5h8m-8 3h5',
  gamepad: 'M8 7h8a4 4 0 0 1 3.9 3.1l1.3 5.8a2.4 2.4 0 0 1-4 2.2L14.5 16h-5l-2.7 2.1a2.4 2.4 0 0 1-4-2.2l1.3-5.8A4 4 0 0 1 8 7Zm-.5 3v4M5.5 12h4m6-1h.01m2 2h.01M10 7V5h4',
};

export default function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
