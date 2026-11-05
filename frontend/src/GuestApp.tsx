import { useEffect, useState, useSyncExternalStore } from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource-variable/manrope';
import Icon from './Icon';
import GuestDiscovery from './GuestDiscovery';
import GuestLibrary from './GuestLibrary';
import GuestDashboard from './GuestDashboard';
import FloatingAssistant from './FloatingAssistant';
import { eraseServerAssistant } from './server-assistant-session';
import { createGuestStore, GUEST_KEY, OWNED_PREFIX, type GuestSnapshot } from './guest-store';
import './current-original.css';

function storage(kind: 'localStorage' | 'sessionStorage') {
  try { return window[kind]; } catch { return null; }
}
const guestStore = createGuestStore(storage('localStorage'), storage('sessionStorage'));
let externalReset: Promise<void> | null = null;
window.addEventListener('storage', (event) => {
  if (!(event.key === null || event.key === GUEST_KEY || event.key?.startsWith(OWNED_PREFIX))) return;
  if (event.key === `${OWNED_PREFIX}reset` && event.newValue === null) return;
  const reset = event.key === null || event.key === `${OWNED_PREFIX}reset` || (event.key === GUEST_KEY && event.newValue === null);
  if (!reset) { guestStore.externalChange(false); return; }
  if (externalReset) return;
  externalReset = eraseServerAssistant().then(() => guestStore.externalChange(true)).catch(() => {
    window.dispatchEvent(new Event('game-discovery:chat-erasure-failed'));
  }).finally(() => { externalReset = null; });
});

function GuestApp({ state }: { state: GuestSnapshot }) {
  const [clearError, setClearError] = useState('');
  const [clearing, setClearing] = useState(false);
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const changed = () => setHash(window.location.hash);
    window.addEventListener('hashchange', changed);
    return () => window.removeEventListener('hashchange', changed);
  }, []);
  async function clearData() {
    if (clearing) return;
    setClearing(true); setClearError('');
    try { await eraseServerAssistant(); guestStore.clear(); }
    catch { setClearError('We couldn’t erase the server chat. Your access has been kept. Keep this tab open and try Clear my saved data again.'); }
    finally { setClearing(false); }
  }
  const savedPage = window.location.pathname === '/saved';
  const dashboardPage = window.location.pathname === '/dashboard';
  const discoveryPage = ['/', '/current-original.html', '/index.html'].includes(window.location.pathname);
  return <div className="study-shell">
    <a className="study-skip" href={savedPage ? '#saved-title' : dashboardPage ? '#dashboard-title' : discoveryPage ? '#taste' : '#not-found'}>Skip to {savedPage ? 'saved games' : dashboardPage ? 'dashboard' : discoveryPage ? 'your taste' : 'content'}</a>
    <header className="study-header">
      <a className="study-brand" href="/"><Icon name="compass" /><span>Game Discovery</span><small>Steam</small></a>
      <nav aria-label="Main navigation"><a href={discoveryPage ? '#taste' : '/#taste'} aria-current={discoveryPage && hash !== '#possibilities' ? 'location' : undefined}>Your taste</a><a href={discoveryPage ? '#possibilities' : '/#possibilities'} aria-current={discoveryPage && hash === '#possibilities' ? 'location' : undefined}>Discover</a><a href="/dashboard" aria-current={dashboardPage ? 'page' : undefined}>Dashboard</a><a href="/saved" aria-current={savedPage ? 'page' : undefined}>Saved games ({state.data.saved.length})</a></nav>
    </header>
    <main>
      {savedPage ? <GuestLibrary store={guestStore} state={state} /> : dashboardPage ? <GuestDashboard /> : discoveryPage ? <GuestDiscovery store={guestStore} state={state} />
        : <section className="study-library"><h1 id="not-found">Page not found.</h1><p>This address is not part of Game Discovery.</p><a href="/">Back to discovery</a></section>}
    </main>
    <footer className="study-footer">
      <div><p>{state.persistent ? 'Saved on this device' : 'Temporary in this tab'} · Guest-first. No sign-in required.</p><p>US store snapshots · Recorded USD, not live purchase prices.</p></div>
      <details className="study-device"><summary>Your device data</summary><div>
        <p>{state.persistent ? 'Favorites, preferences, saved games, feedback and up to 20 recent discovery summaries are saved in this browser.' : 'Changes are currently kept in this tab only because browser persistence is unavailable.'} Data does not sync between browsers or devices, and clearing browser storage erases it.</p>
        <p>Main discovery sends selected favorite IDs, relevant preferences and feedback to the recommendation API, not your saved list or recent history. Checking saved-game availability sends the saved IDs you ask to check.</p>
        <p>The independent assistant stores this chat’s complete messages, preferences, corrections and displayed game records on our server. Relevant conversation and catalog evidence go to Groq when needed. This tab keeps a private chat-access key and a recent-message cache; browser storage is not the full chat history. Chat does not read your main preferences or saved list. Saving a chat game still uses your device-saved list.</p>
        <p>Older messages are paged into the assistant’s working context without deleting the originals. If chat storage fills up, new turns stop rather than silently erasing history.</p>
        <p>New chat erases the current server chat and starts with empty, independent memory. Clear my saved data erases this tab’s server chat before removing this app’s local/session data and restoring the Hades, Windows and $20 defaults. Keep the tab open if erasure fails. Clearing browser storage directly removes your chat-access key, not the server archive; erase the chat here first. Unrelated websites’ data is not affected.</p>
        <button type="button" disabled={clearing} onClick={() => void clearData()}>{clearing ? 'Clearing saved data…' : 'Clear my saved data'}</button>
        {clearError && <p role="alert">{clearError}</p>}
        {!state.persistent && <button type="button" onClick={() => guestStore.retry()}>Try saving again</button>}
      </div></details>
      <p className="study-device-notice" role="status">{state.notice}</p>
    </footer>
    <FloatingAssistant store={guestStore} state={state} />
  </div>;
}
function Root() {
  const state = useSyncExternalStore(guestStore.subscribe, guestStore.getSnapshot);
  return <GuestApp key={state.epoch} state={state} />;
}
createRoot(document.getElementById('root')!).render(<Root />);
