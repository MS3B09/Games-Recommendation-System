import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore, type FormEvent, type KeyboardEvent } from 'react';
import Markdown, { type Components } from 'react-markdown';
import type { Recommendation } from './api/discovery';
import { createConversation, freshConversation, sendAssistant, readConversation, forgetConversation, type AssistantTurn } from './api/assistant';
import { ServiceError } from './api/client';
import { clearAvailability, readAvailability, rememberAvailability, retryWait, serviceError } from './api/errors';
import ErrorNotice, { useRecoveryClock } from './ErrorNotice';
import { assistantPort, archiveMessages, clearAssistant, emptyAssistant, readAssistant, writeAssistant, type ServerAssistantSession as AssistantSession } from './server-assistant-session';
import { Artwork, GameEssentials, SaveButton } from './GuestGameRow';
import { cacheGame, type GuestSnapshot, type GuestStore } from './guest-store';
import Icon from './Icon';

const mobilePanel = () => window.matchMedia('(max-width: 640px)').matches;
const starters = [
  { label: 'A story to get lost in', message: 'I want a game with a memorable story. Help me find one.' },
  { label: 'Something to play together', message: 'Help me find a game to play with friends.' },
  { label: 'A different kind of game', message: 'I want to try something different. Can you help me narrow it down?' },
];
const markdownComponents: Components = {
  // Reply headings stay below the dialog's heading, regardless of source level.
  h1: ({ children }) => <h3 className="assistant-markdown-title">{children}</h3>,
  h2: ({ children }) => <h3 className="assistant-markdown-subtitle">{children}</h3>,
  h3: 'h3', h4: 'h3', h5: 'h3', h6: 'h3',
  a: ({ href, children }) => href
    ? <a href={href} target="_blank" rel="noopener noreferrer">{children}<span className="study-sr"> (opens in a new tab)</span></a>
    : <>{children}</>,
  pre: ({ children }) => <pre tabIndex={0} role="region" aria-label="Code block">{children}</pre>,
};
function subscribeViewport(change: () => void) {
  const media = window.matchMedia('(max-width: 640px)');
  media.addEventListener('change', change);
  return () => media.removeEventListener('change', change);
}

function ChatGame({ result, store, state }: { result: Recommendation; store: GuestStore; state: GuestSnapshot }) {
  const { game } = result;
  return <article className="assistant-game" aria-label={game.title}>
    <div className="assistant-game-heading"><div className="assistant-art"><Artwork game={game} /></div>
      <div><h3>{game.title}</h3><p>{game.price ? `$${(game.price.amount_cents / 100).toFixed(2)} USD` : 'Price unknown'}<span>Recorded price</span></p></div></div>
    <details className="assistant-details"><summary>View details<span className="study-sr"> for {game.title}</span><Icon name="chevron" /></summary><div>
      <GameEssentials game={game} showTraits />
      <div className="assistant-game-actions"><SaveButton game={cacheGame(game)} store={store} state={state} /><a href={game.store_url} target="_blank" rel="noreferrer">View on Steam<span className="study-sr"> (opens in a new tab)</span><Icon name="external" /></a></div>
    </div></details>
  </article>;
}

export default function FloatingAssistant({ store, state }: { store: GuestStore; state: GuestSnapshot }) {
  const [open, setOpen] = useState(false);
  const [greetingVisible, setGreetingVisible] = useState(true);
  const mobile = useSyncExternalStore(subscribeViewport, mobilePanel);
  const [saved, setSaved] = useState(readAssistant);
  const session = saved.value;
  const [loading, setLoading] = useState(false);
  const [readingHistory, setReadingHistory] = useState(false);
  const [historyFailed, setHistoryFailed] = useState(false);
  const [availability, setAvailability] = useState(readAvailability);
  const [error, setError] = useState<ServiceError | null>(() => readAvailability() ?? (session.messages.at(-1)?.role === 'user' ? serviceError('chat_interrupted') : null));
  const [confirmNew, setConfirmNew] = useState(false);
  const activeError = error ?? availability;
  const now = useRecoveryClock(activeError?.retryAt);
  const blocked = Math.max(retryWait(availability, now), retryWait(error, now));
  const input = useRef<HTMLTextAreaElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const log = useRef<HTMLDivElement>(null);
  const panel = useRef<HTMLElement>(null);
  const pending = useRef<AbortController | null>(null);
  const serial = useRef(0);
  const lastRequest = useRef<AssistantTurn | null>(null);
  const historyRequest = useRef<AbortController | null>(null);
  const prependedHistory = useRef(false);
  useEffect(() => { if (open) input.current?.focus({ preventScroll: true }); }, [open, mobile]);
  useLayoutEffect(() => {
    if (!open || !mobile || !panel.current) return;
    const siblings = Array.from(panel.current.parentElement?.children ?? []).filter((element): element is HTMLElement => element instanceof HTMLElement && element !== panel.current);
    const previous = siblings.map(element => ({ element, inert: element.inert }));
    for (const { element } of previous) element.inert = true;
    return () => { for (const { element, inert } of previous) element.inert = inert; };
  }, [open, mobile]);
  useEffect(() => {
    if (open && log.current) {
      log.current.scrollTop = prependedHistory.current ? 0 : session.messages.length || loading || error ? log.current.scrollHeight : 0;
      prependedHistory.current = false;
    }
  }, [open, session.messages, loading, error]);
  useEffect(() => () => { pending.current?.abort(); historyRequest.current?.abort(); }, []);
  useEffect(() => {
    const failed = () => setSaved(current => ({ ...current, notice: 'Another tab cleared device data, but this server chat could not be erased. Keep this tab open and use New chat to retry erasure.' }));
    window.addEventListener('game-discovery:chat-erasure-failed', failed);
    return () => window.removeEventListener('game-discovery:chat-erasure-failed', failed);
  }, []);

  function persist(value: AssistantSession) {
    const ok = saved.writable && writeAssistant(value);
    setSaved({ value, writable: saved.writable, notice: ok ? '' : saved.notice || 'Your browser couldn’t save access to this server chat. Keep this tab open.' });
  }
  function close() { setOpen(false); requestAnimationFrame(() => launcher.current?.focus({ preventScroll: true })); }
  function openChat() { setGreetingVisible(false); setOpen(true); void loadHistory(true); }
  async function loadHistory(latest = false) {
    if (!session.remote || !session.remoteReady || pending.current || historyRequest.current) return;
    const controller = new AbortController(); historyRequest.current = controller;
    setReadingHistory(true);
    const epoch = serial.current;
    try {
      const page = await readConversation(session.remote, latest ? Number.MAX_SAFE_INTEGER : session.historyBefore, controller.signal);
      if (controller.signal.aborted || epoch !== serial.current) return;
      setHistoryFailed(false);
      if (!session.pending) setError(null);
      const completedPending = session.pending && page.events.some(e => e.id === session.pending!.turn_id && e.output);
      const stalePending = session.pending && !completedPending && session.pending.revision !== page.revision;
      const restored = archiveMessages(page.events);
      if (latest && session.pending && !stalePending && !page.events.some(e => e.id === session.pending!.turn_id)) {
        restored.push({ role: 'user', content: session.pending.message, games: [], notices: [] });
      }
      const value = { ...session, remote: { ...session.remote, revision: page.revision },
        messages: latest ? restored : [...restored, ...session.messages],
        pending: completedPending || stalePending ? null : session.pending, totalTurns: page.total, historyBefore: page.offset };
      prependedHistory.current = !latest;
      setSaved(current => {
        if (epoch !== serial.current || current.value.remote?.conversation_id !== session.remote?.conversation_id) return current;
        const draft = current.value.draft || (stalePending ? session.pending!.message : '');
        const updated = { ...value, draft };
        const ok = current.writable && writeAssistant(updated);
        return { value: updated, writable: current.writable,
          notice: stalePending ? 'This chat changed elsewhere. Your unsent message is in the composer for review.'
            : ok ? '' : current.notice || 'Your browser couldn’t save access to this server chat. Keep this tab open.' };
      });
      if (completedPending) { lastRequest.current = null; setError(null); }
      if (stalePending) {
        lastRequest.current = null; setError(null);
      }
    } catch (failure) {
      if (!controller.signal.aborted && epoch === serial.current) {
        setHistoryFailed(true);
        setError(failure instanceof ServiceError ? failure : serviceError('network_error'));
      }
    } finally { if (historyRequest.current === controller) { historyRequest.current = null; setReadingHistory(false); } }
  }
  function useYourTaste() {
    close();
    requestAnimationFrame(() => document.getElementById('taste')?.querySelector<HTMLButtonElement>('button')?.focus());
  }
  function chooseStarter(message: string) {
    persist({ ...session, draft: message });
    input.current?.focus({ preventScroll: true });
  }
  async function newChat() {
    setHistoryFailed(false);
    serial.current++; pending.current?.abort(); historyRequest.current?.abort(); pending.current = null; lastRequest.current = null;
    setLoading(true);
    if (session.remote) {
      try { await forgetConversation(session.remote, new AbortController().signal); }
      catch (failure) { setLoading(false); setConfirmNew(false); setError(failure instanceof ServiceError ? failure : serviceError('network_error')); return; }
    }
    const writable = clearAssistant();
    setSaved({ value: emptyAssistant(), writable: writable || !!assistantPort(),
      notice: writable ? '' : 'This chat was cleared in this tab, but your browser couldn’t remove the saved copy. Clear this site’s data in browser settings to erase it.' });
    if (!retryWait(availability, now)) setAvailability(null);
    setConfirmNew(false); setLoading(false); setError(retryWait(availability, now) ? availability : null); input.current?.focus({ preventScroll: true });
  }
  function requestNewChat() {
    if (session.messages.length || session.draft.trim()) setConfirmNew(true);
    else void newChat();
  }
  function editMessage() {
    serial.current++; historyRequest.current?.abort();
    if (!session.draft.trim() && session.messages.at(-1)?.role === 'user') {
      persist({ ...session, draft: session.messages.at(-1)!.content, messages: session.messages.slice(0, -1), pending: null });
      lastRequest.current = null;
    }
    setError(null); input.current?.focus({ preventScroll: true });
  }
  async function send(retry = false) {
    if (pending.current || blocked > 0) return;
    const text = retry ? session.messages.at(-1)?.content ?? '' : session.draft.trim();
    if (!text.trim()) return;
    if (availability && retryWait(availability, now) === 0) { setAvailability(null); clearAvailability(); }
    const messages = retry ? session.messages.slice(0, -1) : session.messages;
    const remote = session.remote ?? freshConversation();
    let body: AssistantTurn = retry && (lastRequest.current || session.pending) ? (lastRequest.current || session.pending)!
      : { ...remote, turn_id: crypto.randomUUID(), message: text };
    let next: AssistantSession = { ...(retry ? session : { ...session, draft: '', messages: [...session.messages, { role: 'user', content: text, games: [], notices: [] }] }), remote, pending: body };
    lastRequest.current = body;
    persist(next);
    const controller = new AbortController(); pending.current = controller;
    const turn = ++serial.current;
    setLoading(true); setError(null); setHistoryFailed(false);
    try {
      if (!session.remoteReady) {
        const created = await createConversation(remote, messages.map(m => ({ role: m.role, content: m.content, game_ids: m.games.map(c => c.game.app_id) })), controller.signal);
        if (controller.signal.aborted || turn !== serial.current) return;
        body = { ...body, revision: created.revision };
        next = { ...next, remote: created, remoteReady: true, pending: body };
        lastRequest.current = body; persist(next);
      }
      const response = await sendAssistant(body, controller.signal);
      if (!controller.signal.aborted && turn === serial.current) {
        // Preserve a draft typed while the model was answering. Only chat state
        // comes back from this endpoint; device preferences are never updated.
        setSaved(current => {
          const value = { ...next, draft: current.value.draft, remote: { ...next.remote!, revision: response.revision }, pending: null,
            totalTurns: response.total_turns,
            messages: [...next.messages, { role: 'assistant' as const, content: response.message, games: response.games, notices: response.notices }] };
          const ok = current.writable && writeAssistant(value);
          return { value, writable: current.writable, notice: ok ? '' : current.notice || 'Your browser couldn’t save this chat. You can keep chatting, but reloading may lose the conversation.' };
        });
      }
    } catch (failure) {
      if (!controller.signal.aborted && turn === serial.current) {
        const nextError = failure instanceof ServiceError ? failure : serviceError('unexpected_error');
        setError(nextError);
        if (nextError.retryAt) { rememberAvailability(nextError); setAvailability(nextError); }
      }
    } finally { if (pending.current === controller) { pending.current = null; setLoading(false); } }
  }
  function submit(event: FormEvent) { event.preventDefault(); void send(); }
  function panelKeys(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close(); return; }
    if (event.key !== 'Tab' || !mobile) return;
    const controls = Array.from(panel.current?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], summary, textarea, [tabindex="0"]') ?? [])
      .filter(element => element.getClientRects().length > 0);
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }

  return <>
    {greetingVisible && !open && !session.messages.length && <aside className="assistant-greeting" aria-label="Game assistant invitation">
      <button type="button" className="assistant-greeting-copy" onClick={openChat}>What would you like to play?<span>Let’s find your next game.</span></button>
      <button type="button" className="assistant-greeting-dismiss" aria-label="Dismiss assistant greeting" onClick={() => { setGreetingVisible(false); launcher.current?.focus({ preventScroll: true }); }}><Icon name="close" /></button>
    </aside>}
    <button className="assistant-launcher" ref={launcher} type="button" aria-label={open ? 'Close assistant' : 'Ask the assistant'} aria-expanded={open} aria-controls="game-assistant" onClick={() => open ? close() : openChat()}><Icon name={open ? 'close' : 'gamepad'} /></button>
    {open && <section id="game-assistant" ref={panel} className="assistant-panel" role="dialog" aria-modal={mobile} aria-labelledby="assistant-title"
      onKeyDown={panelKeys}>
      <div className="assistant-header"><div className="assistant-identity"><Icon name="gamepad" /><h2 id="assistant-title">Game assistant</h2></div><div className="assistant-header-actions"><button type="button" className="assistant-new" onClick={requestNewChat}><Icon name="plus" />New chat</button><button type="button" className="assistant-close" onClick={close} aria-label="Close game assistant"><Icon name="close" /></button></div></div>
      <div className="assistant-log" ref={log} role="log" aria-label="Assistant conversation" aria-live="polite" aria-relevant="additions text">
        {session.remoteReady && session.historyBefore > 0 && <button className="assistant-history" type="button" disabled={readingHistory || loading} onClick={() => void loadHistory()}>Load earlier messages</button>}
        {!session.messages.length && <div className="assistant-welcome"><h3>What would you<br />like to play?</h3><p>A familiar feeling. A new obsession.<br />Tell me what you’re in the mood for.</p>
          <div className="assistant-starters" aria-label="Conversation starters">{starters.map(starter => <button type="button" key={starter.label} onClick={() => chooseStarter(starter.message)}>{starter.label}<Icon name="arrow" /></button>)}</div>
        </div>}
        {session.messages.map((item, index) => <div className={`assistant-message assistant-message-${item.role}`} key={index}>
          <p className="assistant-speaker">{item.role === 'assistant' && <Icon name="gamepad" />}{item.role === 'user' ? 'You' : 'Assistant'}</p>
          {item.role === 'assistant'
            ? <div className="assistant-prose assistant-markdown"><Markdown skipHtml disallowedElements={['img']} components={markdownComponents}>{item.content}</Markdown></div>
            : <p className="assistant-prose">{item.content}</p>}
          {item.games.map(result => <ChatGame key={result.game.app_id} result={result} store={store} state={state} />)}
          {!!item.games.length && !!item.notices.length && <p className="assistant-notices">{item.notices.join(' ')}</p>}
        </div>)}
      </div>
      <div className={`assistant-status${activeError || confirmNew ? ' assistant-status--recovery' : ''}`}>{loading && <p className="assistant-thinking" role="status"><span aria-hidden="true"><i /><i /><i /></span>Putting a reply together…</p>}
        {readingHistory && <p role="status">Loading chat history…</p>}
        {activeError && !confirmNew && <ErrorNotice error={activeError}
          retryLabel={historyFailed ? 'Retry chat history' : 'Retry message'}
          onRetry={historyFailed ? () => void loadHistory(true) : session.messages.at(-1)?.role === 'user' ? () => void send(true) : undefined}
          onEdit={editMessage} onNewChat={requestNewChat} onDiscover={useYourTaste} onBack={useYourTaste} />}
        {confirmNew && <div className="assistant-reset-confirm" role="group" aria-label="Confirm new chat"><p>Start a new chat? This erases this chat’s server history and starts with empty memory.</p>
          <button type="button" disabled={loading && !session.remoteReady} onClick={() => void newChat()}>Start new chat</button><button type="button" onClick={() => { setConfirmNew(false); input.current?.focus(); }}>Keep chatting</button></div>}
        {saved.notice && <p role="status">{saved.notice}</p>}</div>
      <form className="assistant-composer" onSubmit={submit}><label className="study-sr" htmlFor="assistant-message">Message the assistant</label>
        <div><textarea id="assistant-message" ref={input} rows={1} maxLength={2000} value={session.draft} placeholder="Ask about games…"
          onChange={event => persist({ ...session, draft: event.target.value })} />
          <button type="submit" disabled={loading || blocked > 0 || !session.draft.trim()} aria-label={blocked ? `Send available in ${blocked} seconds` : 'Send message'}><Icon name="arrow" /></button></div>
      </form>
    </section>}
  </>;
}
