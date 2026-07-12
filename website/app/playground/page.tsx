'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Navbar } from '@/components/Navbar';
import { getAccessToken, getStoredSession, type LocalSession } from '@/lib/auth';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  orchestration?: OrchestrationData;
  activity?: ActivityEvent[];
  startedAt?: number;
  completedAt?: number;
};

type OrchestrationData = {
  taskType: string;
  tier: string;
  models: { name: string; response: string; latency: number; correct: boolean }[];
  aggregator: string;
  consensus: number;
  qaScore: number;
  codeVerified: boolean;
  totalLatency: string | number;
  cost: string;
  techniques?: string[];
};

type ProgressStep = {
  label: string;
  detail?: string;
  status: 'active' | 'done' | 'error';
};

type ActivityEvent = {
  heading: string;
  detail?: string;
  kind: 'intent' | 'routing' | 'research' | 'model' | 'verification' | 'result' | 'error';
  status: 'active' | 'done' | 'error';
};

type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
  pinned?: boolean;
  profile?: ModelProfile;
};

type ModelProfile = 'pro' | 'lite';

type WorkspaceProject = {
  id: string;
  title: string;
  profile: ModelProfile;
  updated_at: number;
};

const EXAMPLE_PROMPTS = [
  'What is 9.9 vs 9.11 — which is larger?',
  'Write a Python function to merge two sorted lists',
  'Explain quantum entanglement in simple terms',
  'What is the derivative of x³ + 2x² - 5x + 1?',
];

export default function PlaygroundPage() {
  const [session, setSession] = useState<LocalSession | null>(null);
  const [sessionChecked, setSessionChecked] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [modelProfile, setModelProfile] = useState<ModelProfile>('pro');
  const [workspaceProjects, setWorkspaceProjects] = useState<WorkspaceProject[]>([]);
  const [activeWorkspaceProjectId, setActiveWorkspaceProjectId] = useState<string | null>(null);
  const [workspaceState, setWorkspaceState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [input, setInput] = useState('');
  const [status, setStatus] = useState<'ready' | 'submitted' | 'streaming' | 'error'>('ready');
  const [showOrchestration, setShowOrchestration] = useState<string | null>(null);
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null);
  const [limitMessage, setLimitMessage] = useState<string | null>(null);
  const [showUpgradeBanner, setShowUpgradeBanner] = useState(false);
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  // Index of the assistant message currently being streamed — avoids
  // creating a new message bubble on every chunk (the old code searched
  // for an assistant with content === '' which never existed, so every
  // chunk pushed a new message and the response repeated N times).
  const streamingIdxRef = useRef<number>(-1);
  const historyReadyRef = useRef(false);

  useEffect(() => {
    let mounted = true;

    getStoredSession()
      .then((stored) => {
        if (!mounted) return;
        setSession(stored);
        setSessionChecked(true);
      })
      .catch(() => {
        if (!mounted) return;
        setSession(null);
        setSessionChecked(true);
      });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!session?.email) return;
    const key = conversationStorageKey(session.id);
    const saved = window.localStorage.getItem(key) || window.localStorage.getItem(legacyConversationStorageKey(session.email));
    try {
      const parsed = saved ? JSON.parse(saved) as Conversation[] : [];
      if (parsed.length > 0) {
        const ordered = sortConversations(parsed);
        setConversations(ordered);
        setActiveConversationId(ordered[0].id);
        setMessages(ordered[0].messages || []);
        setModelProfile(ordered[0].profile === 'lite' ? 'lite' : 'pro');
        window.localStorage.setItem(key, JSON.stringify(ordered));
      } else {
        const initial = createConversation();
        setConversations([initial]);
        setActiveConversationId(initial.id);
        setMessages([]);
        setModelProfile('pro');
      }
    } catch {
      const initial = createConversation();
      setConversations([initial]);
      setActiveConversationId(initial.id);
      setMessages([]);
      setModelProfile('pro');
    }
    historyReadyRef.current = true;
  }, [session?.email, session?.id]);

  useEffect(() => {
    if (!session?.id || !historyReadyRef.current || !activeConversationId) return;
    setConversations((previous) => {
      const next = previous.map((conversation) => conversation.id === activeConversationId
        ? { ...conversation, messages, profile: modelProfile, updatedAt: Date.now() }
        : conversation);
      window.localStorage.setItem(conversationStorageKey(session.id), JSON.stringify(next));
      return next;
    });
  }, [activeConversationId, messages, modelProfile, session?.id]);

  const loadWorkspaceProjects = useCallback(async () => {
    if (!session?.id) return;
    setWorkspaceState('loading');
    try {
      const token = await getAccessToken();
      if (!token) return;
      const response = await fetch('/api/projects', { headers: { Authorization: `Bearer ${token}` } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !Array.isArray(data.projects)) throw new Error(data.error || 'Workspace storage is unavailable.');
      const projects = data.projects as WorkspaceProject[];
      setWorkspaceProjects(projects);
      setActiveWorkspaceProjectId((current) => current && projects.some((project) => project.id === current) ? current : projects[0]?.id || null);
      setWorkspaceState('idle');
    } catch {
      // The user can still chat and download files when project storage is
      // temporarily unavailable. Never render an operational error as no data.
      setWorkspaceState('error');
    }
  }, [session?.id]);

  useEffect(() => {
    void loadWorkspaceProjects();
  }, [loadWorkspaceProjects]);

  // Check usage on mount and after each query
  const checkUsage = useCallback(async () => {
    try {
      const token = await getAccessToken();
      if (!token) return;
      const res = await fetch('/api/usage/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (data.allowed === false) {
        setLimitMessage(data.message);
        setShowUpgradeBanner(true);
      } else {
        setLimitMessage(null);
      }
    } catch (err) {
      // Silently fail — don't block the user if the check endpoint is down
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (session) checkUsage();
  }, [checkUsage, session]);

  const addProgress = useCallback((step: ProgressStep) => {
    setProgressSteps((prev) => {
      const next = prev.map((item) =>
        item.status === 'active' && step.status === 'active' ? { ...item, status: 'done' as const } : item
      );
      return [...next, step].slice(-8);
    });
  }, []);

  const addActivity = useCallback((messageIndex: number, step: ProgressStep) => {
    const event = toActivityEvent(step);
    setMessages((prev) => {
      if (messageIndex < 0 || messageIndex >= prev.length) return prev;
      const updated = [...prev];
      const activity = [...(updated[messageIndex].activity || [])];
      const lastMatchingIndex = [...activity].map((item) => item.heading).lastIndexOf(event.heading);

      if (step.status === 'done' && lastMatchingIndex >= 0) {
        activity[lastMatchingIndex] = { ...activity[lastMatchingIndex], ...event, status: 'done' };
      } else {
        for (let index = activity.length - 1; index >= 0; index -= 1) {
          if (activity[index].status === 'active') {
            activity[index] = { ...activity[index], status: 'done' };
            break;
          }
        }
        activity.push(event);
      }

      updated[messageIndex] = { ...updated[messageIndex], activity };
      return updated;
    });
  }, []);

  const handleSend = useCallback(async () => {
    if (!session) {
      window.location.href = '/login?returnTo=/playground';
      return;
    }
    if (!input.trim() || status === 'submitted' || status === 'streaming') return;

    // Check if user has reached free tier limit
    if (limitMessage) {
      setShowUpgradeBanner(true);
      return;
    }

    const userMessage: Message = { role: 'user', content: input.trim() };
    if (activeConversationId) {
      setConversations((previous) => previous.map((conversation) => conversation.id === activeConversationId && conversation.messages.length === 0
        ? { ...conversation, title: conversationTitle(userMessage.content), updatedAt: Date.now() }
        : conversation));
    }
    const initialActivity: ActivityEvent = {
      heading: describeIntent(userMessage.content),
      kind: 'intent',
      status: 'active',
    };
    setMessages((prev) => {
      streamingIdxRef.current = prev.length + 1;
      return [...prev, userMessage, { role: 'assistant', content: '', activity: [initialActivity], startedAt: Date.now() }];
    });
    setInput('');
    setStatus('submitted');
    const queuedProgress: ProgressStep = { label: 'Queued request', detail: 'Preparing orchestration plan', status: 'active' };
    setProgressSteps([queuedProgress]);
    addActivity(streamingIdxRef.current, queuedProgress);
    abortControllerRef.current = new AbortController();

    try {
      const token = await getAccessToken();
      if (!token) {
        window.location.href = '/login?returnTo=/playground';
        return;
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ messages: [...messages, userMessage], profile: modelProfile }),
        signal: abortControllerRef.current?.signal,
      });

      if (!response.ok) throw new Error(`API returned ${response.status}`);

      setStatus('streaming');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let orchestrationData: OrchestrationData | undefined;
      let streamBuffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          streamBuffer += decoder.decode(value, { stream: true });
          const lines = streamBuffer.split('\n');
          streamBuffer = lines.pop() || '';

          for (const line of lines) {
            const trimmedLine = line.trimEnd();
            if (trimmedLine.startsWith('data: ') && trimmedLine !== 'data: [DONE]') {
              try {
                const data = JSON.parse(trimmedLine.slice(6));
                if (data.chunk) {
                  assistantContent += data.chunk;
                  const idx = streamingIdxRef.current;
                  setMessages((prev) => {
                    if (idx < 0 || idx >= prev.length) return prev;
                    const updated = [...prev];
                    updated[idx] = { ...updated[idx], role: 'assistant', content: assistantContent };
                    return updated;
                  });
                }
                if (data.orchestration) {
                  orchestrationData = data.orchestration;
                }
                if (data.progress) {
                  const progress = {
                    label: data.progress.label || 'Working',
                    detail: data.progress.detail,
                    status: data.progress.status || 'active',
                  } as ProgressStep;
                  addProgress(progress);
                  addActivity(streamingIdxRef.current, progress);
                }
              } catch {}
            }
          }
        }
      }

      // Attach orchestration metadata to the streamed assistant message.
      if (orchestrationData) {
        const idx = streamingIdxRef.current;
        setMessages((prev) => {
          if (idx < 0 || idx >= prev.length) return prev;
          const updated = [...prev];
          updated[idx] = { ...updated[idx], orchestration: orchestrationData };
          return updated;
        });
      }

      const completedIndex = streamingIdxRef.current;
      streamingIdxRef.current = -1;
      abortControllerRef.current = null;
      setProgressSteps((prev) => prev.map((item) => item.status === 'active' ? { ...item, status: 'done' } : item));
      setMessages((prev) => prev.map((message, index) => ({
        ...message,
        activity: message.activity?.map((item) => item.status === 'active' ? { ...item, status: 'done' } : item),
        completedAt: index === completedIndex ? Date.now() : message.completedAt,
      })));
      setStatus('ready');
    } catch (err) {
      abortControllerRef.current = null;
      if (err instanceof Error && err.name === 'AbortError') {
        setStatus('ready');
      } else {
        setStatus('error');
        setProgressSteps((prev) => [...prev, { label: 'Generation failed', detail: 'Please retry or simplify the request.', status: 'error' }]);
        const index = streamingIdxRef.current;
        setMessages((prev) => {
          if (index < 0 || index >= prev.length) return [...prev, { role: 'assistant', content: 'Something went wrong. Please try again.' }];
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            content: 'Something went wrong. Please try again.',
            completedAt: Date.now(),
            activity: [...(updated[index].activity || []), {
              heading: 'The workflow could not complete',
              detail: 'Please retry or simplify the request.',
              kind: 'error',
              status: 'error',
            }],
          };
          return updated;
        });
        streamingIdxRef.current = -1;
      }
    }
  }, [input, status, messages, limitMessage, checkUsage, session, activeConversationId, modelProfile, addProgress, addActivity]);

  const handleStop = () => {
    abortControllerRef.current?.abort();
    setStatus('ready');
  };

  const handleNewConversation = () => {
    if (status === 'submitted' || status === 'streaming') return;
    const conversation = createConversation();
    setConversations((previous) => [conversation, ...previous]);
    setActiveConversationId(conversation.id);
    setMessages([]);
    setModelProfile('pro');
    setShowOrchestration(null);
  };

  const createWorkspaceProject = useCallback(async () => {
    if (!session?.id) throw new Error('Sign in to create a project.');
    const token = await getAccessToken();
    if (!token) throw new Error('Sign in to create a project.');
    const response = await fetch('/api/projects', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: `Untitled project ${workspaceProjects.length + 1}`, profile: modelProfile }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.project) throw new Error(data.error || 'Could not create a project.');
    const project = data.project as WorkspaceProject;
    setWorkspaceProjects((previous) => [project, ...previous]);
    setActiveWorkspaceProjectId(project.id);
    setWorkspaceState('idle');
    return project;
  }, [modelProfile, session?.id, workspaceProjects.length]);

  const saveHtmlToWorkspace = useCallback(async (html: string) => {
    let projectId = activeWorkspaceProjectId;
    if (!projectId) projectId = (await createWorkspaceProject()).id;
    const token = await getAccessToken();
    if (!token) throw new Error('Sign in to save a project file.');
    const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/files`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ filePath: 'index.html', language: 'html', content: html }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.file) throw new Error(data.error || 'Could not save index.html.');
    setActiveWorkspaceProjectId(projectId);
    await loadWorkspaceProjects();
    return data.file as { file_path: string };
  }, [activeWorkspaceProjectId, createWorkspaceProject, loadWorkspaceProjects]);

  const handleSelectConversation = (conversation: Conversation) => {
    if (status === 'submitted' || status === 'streaming') return;
    setActiveConversationId(conversation.id);
    setMessages(conversation.messages || []);
    setModelProfile(conversation.profile === 'lite' ? 'lite' : 'pro');
    setShowOrchestration(null);
  };

  const handleDeleteConversation = (conversationId: string) => {
    if (status === 'submitted' || status === 'streaming') return;
    const remaining = conversations.filter((conversation) => conversation.id !== conversationId);
    const nextConversation = remaining[0] || createConversation();
    const next = remaining.length > 0 ? remaining : [nextConversation];
    setConversations(next);
    if (session?.id) window.localStorage.setItem(conversationStorageKey(session.id), JSON.stringify(next));
    if (activeConversationId === conversationId) {
      setActiveConversationId(nextConversation.id);
      setMessages(nextConversation.messages || []);
      setShowOrchestration(null);
    }
  };

  const handleTogglePin = (conversationId: string) => {
    setConversations((previous) => {
      const next = sortConversations(previous.map((conversation) => conversation.id === conversationId
        ? { ...conversation, pinned: !conversation.pinned }
        : conversation));
      if (session?.id) window.localStorage.setItem(conversationStorageKey(session.id), JSON.stringify(next));
      return next;
    });
  };

  const visibleConversations = sortConversations(conversations);

  if (sessionChecked && !session) {
    return (
      <>
        <Navbar />
        <main className="min-h-screen pt-28 px-6 bg-bg-primary" id="main-content">
          <div className="container-max">
            <div className="card max-w-xl mx-auto text-center">
              <h1 className="text-2xl font-serif text-text-primary mb-3">Sign in to use the playground</h1>
              <p className="text-sm text-text-secondary mb-6">
                Playground usage is now tied to your account so chat history, credits, logs, and API activity stay together.
              </p>
              <a href="/login?returnTo=/playground" className="btn-accent">Sign In</a>
            </div>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="flex h-screen pt-16 bg-bg-primary">
        <h1 className="sr-only">TemuClaude Playground</h1>

        <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-border-subtle bg-bg-secondary/50 p-3" aria-label="Chat history">
          <button onClick={handleNewConversation} disabled={status === 'submitted' || status === 'streaming'} className="btn-secondary w-full justify-start !px-3 !py-2 disabled:opacity-50">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
            New chat
          </button>
          <div className="mt-5 flex items-center justify-between px-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Projects</span>
            <button
              onClick={() => void createWorkspaceProject().catch(() => setWorkspaceState('error'))}
              className="rounded-sm px-1 text-sm text-text-muted hover:text-accent-primary"
              title="Create project"
              aria-label="Create project"
            >+</button>
          </div>
          <div className="mt-2 space-y-1">
            {workspaceState === 'loading' && <p className="px-2 py-1 text-[11px] text-text-muted">Loading projects…</p>}
            {workspaceState === 'error' && <p className="px-2 py-1 text-[11px] leading-relaxed text-accent-fig">Project storage is unavailable. Chats and downloads still work.</p>}
            {workspaceState === 'idle' && workspaceProjects.length === 0 && <p className="px-2 py-1 text-[11px] text-text-muted">Save a deliverable to start a project.</p>}
            {workspaceProjects.slice(0, 6).map((project) => (
              <button
                key={project.id}
                onClick={() => setActiveWorkspaceProjectId(project.id)}
                title={project.title}
                className={`block w-full truncate rounded-sm px-2 py-1.5 text-left text-xs ${activeWorkspaceProjectId === project.id ? 'bg-bg-tertiary text-text-primary' : 'text-text-secondary hover:bg-bg-tertiary/60'}`}
              >
                {project.title}
              </button>
            ))}
          </div>
          <div className="mt-5 px-2 text-[10px] font-mono uppercase tracking-wider text-text-muted">Recent chats</div>
          <div className="mt-2 flex-1 space-y-1 overflow-y-auto">
            {visibleConversations.map((conversation) => (
              <div key={conversation.id} className={`group flex items-center gap-1 rounded-sm ${activeConversationId === conversation.id ? 'bg-bg-tertiary' : 'hover:bg-bg-tertiary/60'}`}>
                <button
                  onClick={() => handleSelectConversation(conversation)}
                  className={`min-w-0 flex-1 truncate px-3 py-2.5 text-left text-sm ${activeConversationId === conversation.id ? 'text-text-primary font-medium' : 'text-text-secondary'}`}
                  title={conversation.title}
                >
                  {conversation.title}
                </button>
                <div className="mr-1 hidden items-center gap-0.5 group-hover:flex group-focus-within:flex">
                  <button
                    onClick={() => handleTogglePin(conversation.id)}
                    aria-label={`${conversation.pinned ? 'Unpin' : 'Pin'} ${conversation.title}`}
                    title={conversation.pinned ? 'Unpin chat' : 'Pin chat'}
                    className="group/pin relative rounded-sm p-1.5 text-text-muted hover:bg-white hover:text-accent-primary"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill={conversation.pinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M12 17v5M8 3h8l-1 7 3 3H6l3-3-1-7Z" /></svg>
                    <span role="tooltip" className="pointer-events-none absolute right-0 top-full z-10 mt-1 hidden whitespace-nowrap rounded-sm bg-bg-dark px-2 py-1 text-[10px] text-white shadow-sm group-hover/pin:block">{conversation.pinned ? 'Unpin chat' : 'Pin chat'}</span>
                  </button>
                  <button
                    onClick={() => handleDeleteConversation(conversation.id)}
                    aria-label={`Delete ${conversation.title}`}
                    title="Delete chat"
                    className="group/delete relative rounded-sm p-1.5 text-text-muted hover:bg-white hover:text-accent-fig"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2m-7 0 1 14h4l1-14" /></svg>
                    <span role="tooltip" className="pointer-events-none absolute right-0 top-full z-10 mt-1 hidden whitespace-nowrap rounded-sm bg-bg-dark px-2 py-1 text-[10px] text-white shadow-sm group-hover/delete:block">Delete chat</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
          <p className="px-2 pt-3 text-[10px] leading-relaxed text-text-muted">Chats stay in this browser. Project files are saved to your account.</p>
        </aside>

        <main className="flex-1 flex flex-col h-[calc(100vh-4rem)] bg-bg-primary" aria-label="TemuClaude Playground" id="main-content">
          {/* Free tier limit banner */}
          {showUpgradeBanner && limitMessage && (
            <div className="bg-accent-primary/10 border-b border-accent-primary/20 px-4 py-3">
              <div className="max-w-3xl mx-auto flex items-center justify-between gap-4">
                <p className="text-sm text-text-primary">{limitMessage}</p>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button onClick={() => setShowUpgradeBanner(false)} className="text-text-muted hover:text-text-primary text-xs" aria-label="Dismiss">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                  </button>
                  <a href="/pricing" className="btn-accent text-xs !py-1.5 !px-3">Upgrade</a>
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
              {/* Empty State */}
              {messages.length === 0 && (
                <div className="text-center pt-12">
                  <h2 className="text-2xl font-serif text-text-primary mb-2" style={{ fontWeight: 300 }}>
                    Ask TemuClaude anything
                  </h2>
                  <p className="text-text-secondary mb-8">
                    One model. Eight minds behind the scenes. One superior answer.
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {EXAMPLE_PROMPTS.map((prompt, i) => (
                      <button
                        key={i}
                        onClick={() => setInput(prompt)}
                        className="badge-muted hover:bg-bg-tertiary hover:text-text-primary transition-colors cursor-pointer"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Agent transcript */}
              {messages.map((message, i) => (
                <div key={i} className={message.role === 'user' ? 'flex justify-end' : 'max-w-full'}>
                  <div className={message.role === 'user' ? 'max-w-[85%] bg-bg-dark text-text-inverse rounded-sm px-4 py-3' : 'border-l border-border-default pl-4 md:pl-5'}>
                    {message.role === 'assistant' && message.activity && message.activity.length > 0 && (
                      <AgentActivity
                        events={message.activity}
                        durationMs={message.completedAt && message.startedAt ? message.completedAt - message.startedAt : null}
                        expanded={(i === messages.length - 1 && (status === 'submitted' || status === 'streaming')) || expandedActivity === String(i)}
                        onToggle={() => setExpandedActivity((current) => current === String(i) ? null : String(i))}
                      />
                    )}
                    <div
                      className={`whitespace-pre-wrap text-sm leading-relaxed ${message.role === 'user' ? 'text-text-inverse' : 'text-text-primary'} ${message.role === 'assistant' && message.activity?.length ? 'mt-4' : ''}`}
                      role={message.role === 'assistant' ? 'status' : undefined}
                      aria-live={message.role === 'assistant' ? 'polite' : undefined}
                      aria-atomic="false"
                    >
                      {message.content || (message.role === 'assistant' && status === 'submitted' ? 'Working…' : '')}
                      {status === 'streaming' && i === messages.length - 1 && message.role === 'assistant' && (
                        <span className="inline-block w-2 h-4 bg-accent-primary ml-0.5 animate-blink" />
                      )}
                    </div>

                    {message.role === 'assistant' && <CodeArtifact content={message.content} onSaveToWorkspace={saveHtmlToWorkspace} />}

                    {/* Orchestration summary bar */}
                    {message.orchestration && message.role === 'assistant' && (
                      <div className="mt-3 pt-3 border-t border-border-subtle">
                        <button
                          onClick={() => setShowOrchestration(showOrchestration === String(i) ? null : String(i))}
                          className="flex items-center gap-2 text-xs text-text-muted hover:text-text-primary transition-colors"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <path d="M12 6v6l4 2" />
                          </svg>
                          {message.orchestration.models.length} models · {message.orchestration.totalLatency}s · {message.orchestration.cost}
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ transform: showOrchestration === String(i) ? 'rotate(180deg)' : 'none', transition: 'transform 150ms' }}>
                            <polyline points="6 9 12 15 18 9" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Orchestration Detail Panel */}
          {showOrchestration && messages[parseInt(showOrchestration)]?.orchestration && (
            <OrchestrationPanel
              data={messages[parseInt(showOrchestration)].orchestration!}
              onClose={() => setShowOrchestration(null)}
            />
          )}

          {/* Input Bar */}
          <div className="border-t border-border-subtle bg-bg-primary p-4">
            <div className="max-w-3xl mx-auto">
              {(status === 'submitted' || status === 'streaming') && progressSteps.length > 0 && (
                <p className="mb-2 text-xs text-text-muted" aria-live="polite">TemuClaude is working…</p>
              )}
              <div className="rounded-md border border-border-default bg-bg-primary shadow-[0_1px_6px_rgba(26,24,22,0.04)] focus-within:border-accent-primary">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask TemuClaude anything..."
                  rows={4}
                  className="block h-[118px] w-full resize-none overflow-x-hidden overflow-y-auto border-0 bg-transparent px-4 py-3 text-sm text-text-primary outline-none placeholder:text-text-muted focus:border-0 focus:ring-0"
                  aria-label="Enter your question"
                  disabled={status === 'submitted' || status === 'streaming'}
                />
                <div className="flex items-center justify-between gap-3 border-t border-border-subtle px-3 py-2">
                  <span className="text-[11px] text-text-muted">Enter to send · Shift+Enter for a new line</span>
                  <div className="flex items-center gap-2">
                    <label className="sr-only" htmlFor="model-profile">Model profile</label>
                    <select
                      id="model-profile"
                      value={modelProfile}
                      onChange={(event) => setModelProfile(event.target.value as ModelProfile)}
                      disabled={status === 'submitted' || status === 'streaming'}
                      className="max-w-[11.5rem] appearance-none bg-transparent py-1 pr-5 text-xs font-medium text-text-secondary outline-none disabled:opacity-50"
                      title={modelProfile === 'pro' ? 'TemuClaude Pro: full orchestration' : 'TemuClaude Lite: cost-bounded routing'}
                    >
                      <option value="pro">TemuClaude Pro</option>
                      <option value="lite">TemuClaude Lite</option>
                    </select>
                    {status === 'submitted' || status === 'streaming' ? (
                      <button
                        onClick={handleStop}
                        className="flex h-8 w-8 items-center justify-center rounded-sm border border-border-default text-text-primary hover:border-accent-primary"
                        aria-label="Stop generating"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
                      </button>
                    ) : (
                      <button
                        onClick={handleSend}
                        disabled={!input.trim()}
                        className="flex h-8 w-8 items-center justify-center rounded-sm bg-accent-primary text-white disabled:cursor-not-allowed disabled:opacity-40"
                        aria-label="Send message"
                      >
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

function conversationStorageKey(userId: string) {
  return `temuclaude:playground:${userId}:conversations`;
}

function legacyConversationStorageKey(email: string) {
  return `temuclaude:playground:${email.toLowerCase()}:conversations`;
}

function createConversation(): Conversation {
  return {
    id: `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: 'New chat',
    messages: [],
    updatedAt: Date.now(),
  };
}

function conversationTitle(content: string) {
  const compact = content.replace(/\s+/g, ' ').trim();
  return compact.length > 40 ? `${compact.slice(0, 40)}…` : compact || 'New chat';
}

function sortConversations(conversations: Conversation[]) {
  return [...conversations].sort((left, right) => Number(Boolean(right.pinned)) - Number(Boolean(left.pinned)) || right.updatedAt - left.updatedAt);
}

function describeIntent(prompt: string) {
  const normalized = prompt.toLowerCase();
  if (/compare|cost|price|cheaper|pricing/.test(normalized)) {
    return 'I’ll compare the options against the relevant trade-offs and calculate the difference.';
  }
  if (/code|function|bug|error|typescript|python|javascript|implement/.test(normalized)) {
    return 'I’ll inspect the problem, work through an implementation, and check the result.';
  }
  if (/research|latest|news|current|search|source/.test(normalized)) {
    return 'I’ll research the current evidence, verify the important details, and synthesize an answer.';
  }
  return 'I’ll analyze the request, select the right reasoning path, and check the answer before responding.';
}

function toActivityEvent(step: ProgressStep): ActivityEvent {
  const label = step.label.toLowerCase();
  if (label.includes('queued')) return { heading: 'Prepared a work plan', detail: step.detail, kind: 'routing', status: step.status };
  if (label.includes('classifying')) return { heading: 'Understood the request', detail: step.detail, kind: 'routing', status: step.status };
  if (label.includes('routing')) return { heading: 'Selected a response plan', detail: step.detail, kind: 'routing', status: step.status };
  if (label.includes('search')) return { heading: label.includes('complete') ? 'Finished web research' : 'Searched the web', detail: step.detail, kind: 'research', status: step.status };
  if (label.includes('draft') || label.includes('calling')) return { heading: 'Consulted the selected model', detail: step.detail, kind: 'model', status: step.status };
  if (label.includes('review')) return { heading: 'Cross-checked candidate answers', detail: step.detail, kind: 'verification', status: step.status };
  if (label.includes('aggregat')) return { heading: 'Synthesized the strongest answer', detail: step.detail, kind: 'model', status: step.status };
  if (label.includes('consistency') || label.includes('verif') || label.includes('quality')) return { heading: 'Verified the result', detail: step.detail, kind: 'verification', status: step.status };
  if (label.includes('stream')) return { heading: 'Prepared the final response', detail: step.detail, kind: 'result', status: step.status };
  if (step.status === 'error') return { heading: 'Recovered from a workflow issue', detail: step.detail, kind: 'error', status: step.status };
  return { heading: step.label, detail: step.detail, kind: 'model', status: step.status };
}

function AgentActivity({
  events,
  durationMs,
  expanded,
  onToggle,
}: {
  events: ActivityEvent[];
  durationMs: number | null;
  expanded: boolean;
  onToggle: () => void;
}) {
  const duration = durationMs === null ? 'Working' : `Worked for ${(durationMs / 1000).toFixed(durationMs < 10_000 ? 1 : 0)}s`;

  if (!expanded) {
    return (
      <button onClick={onToggle} className="flex items-center gap-2 text-xs text-text-secondary hover:text-text-primary transition-colors" aria-expanded="false">
        <span className="h-1.5 w-1.5 rounded-full bg-accent-olive" aria-hidden="true" />
        <span>{duration} · {events.length} {events.length === 1 ? 'step' : 'steps'}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><polyline points="6 9 12 15 18 9" /></svg>
      </button>
    );
  }

  return (
    <div className="space-y-1.5 text-[13px] leading-5" aria-label="TemuClaude work log">
      {durationMs !== null && (
        <button onClick={onToggle} className="mb-1 flex items-center gap-2 text-xs text-text-muted hover:text-text-primary transition-colors" aria-expanded="true">
          <span className="h-1.5 w-1.5 rounded-full bg-accent-olive" aria-hidden="true" />
          <span>{duration} · {events.length} {events.length === 1 ? 'step' : 'steps'}</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><polyline points="6 15 12 9 18 15" /></svg>
        </button>
      )}
      {events.map((event, index) => (
        <div key={`${event.heading}-${index}`} className={`flex items-start gap-2 ${event.kind === 'intent' ? 'pb-2 text-text-primary' : 'text-text-secondary'}`}>
          <span className={`mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full ${
            event.status === 'error' ? 'bg-accent-fig' : event.status === 'active' ? 'bg-accent-primary animate-pulse' : event.kind === 'intent' ? 'bg-accent-primary' : 'bg-text-muted/70'
          }`} aria-hidden="true" />
          <div>
            <p className={event.kind === 'intent' ? 'text-text-primary' : 'font-mono text-xs text-text-primary'}>{event.heading}</p>
            {event.detail && <p className="text-xs text-text-muted">{event.detail}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

function CodeArtifact({ content, onSaveToWorkspace }: { content: string; onSaveToWorkspace: (html: string) => Promise<{ file_path: string }> }) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [isolatedPreview, setIsolatedPreview] = useState<{ previewUrl: string; downloadUrl: string; expiresAt: string } | null>(null);
  const [isolatedPreviewState, setIsolatedPreviewState] = useState<'idle' | 'starting' | 'error'>('idle');
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const html = extractHtmlArtifact(content);
  if (!html) return null;

  const copy = async () => {
    await navigator.clipboard?.writeText(html);
  };
  const download = () => {
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = href;
    anchor.download = 'temuclaude-game.html';
    anchor.click();
    URL.revokeObjectURL(href);
  };
  const runIsolatedPreview = async () => {
    setIsolatedPreviewState('starting');
    try {
      const token = await getAccessToken();
      if (!token) throw new Error('Sign in to run an isolated preview.');
      const response = await fetch('/api/sandbox/preview', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ html }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data?.preview?.previewUrl || !data?.preview?.downloadUrl) {
        throw new Error(data?.error || 'Could not start the isolated preview.');
      }
      setIsolatedPreview(data.preview);
      setPreviewOpen(true);
      setIsolatedPreviewState('idle');
    } catch (error) {
      setIsolatedPreview(null);
      setIsolatedPreviewState('error');
    }
  };
  const saveToWorkspace = async () => {
    setSaveState('saving');
    try {
      await onSaveToWorkspace(html);
      setSaveState('saved');
    } catch {
      setSaveState('error');
    }
  };

  return (
    <div className="mt-3 border-t border-border-subtle pt-3 text-xs">
      <div className="flex items-center gap-2">
        <span className="font-mono text-text-muted">HTML deliverable</span>
        <button onClick={() => setPreviewOpen((open) => !open)} className="text-accent-primary hover:underline" aria-expanded={previewOpen}>
          {previewOpen ? 'Close preview' : 'Preview'}
        </button>
        <button onClick={runIsolatedPreview} disabled={isolatedPreviewState === 'starting'} className="text-text-secondary hover:text-text-primary disabled:opacity-50">
          {isolatedPreviewState === 'starting' ? 'Starting isolated preview…' : 'Run isolated preview'}
        </button>
        <button onClick={copy} className="text-text-secondary hover:text-text-primary">Copy</button>
        <button onClick={download} className="text-text-secondary hover:text-text-primary">Download .html</button>
        <button onClick={saveToWorkspace} disabled={saveState === 'saving' || saveState === 'saved'} className="text-text-secondary hover:text-text-primary disabled:opacity-50">
          {saveState === 'saving' ? 'Saving…' : saveState === 'saved' ? 'Saved to project' : 'Save to project'}
        </button>
      </div>
      {isolatedPreviewState === 'error' && (
        <p className="mt-2 text-xs text-accent-fig">The isolated preview could not start. The downloadable HTML is still available.</p>
      )}
      {saveState === 'error' && (
        <p className="mt-2 text-xs text-accent-fig">This file could not be saved to the selected project. Your download is still available.</p>
      )}
      {previewOpen && (
        <div className="mt-3 overflow-hidden rounded-sm border border-border-default bg-white">
          <div className="flex items-center justify-between gap-3 border-b border-border-subtle bg-bg-secondary px-3 py-2 font-mono text-[11px] text-text-muted">
            <span>{isolatedPreview ? 'Preview · isolated workspace' : 'Preview · sandboxed'}</span>
            {isolatedPreview && <a href={isolatedPreview.downloadUrl} target="_blank" rel="noopener noreferrer" className="text-accent-primary hover:underline">Download isolated artifact</a>}
          </div>
          {isolatedPreview ? (
            <iframe
              title="Isolated generated HTML preview"
              src={isolatedPreview.previewUrl}
              sandbox="allow-scripts"
              referrerPolicy="no-referrer"
              className="h-[32rem] w-full bg-white"
            />
          ) : (
            <iframe
              title="Generated HTML preview"
              srcDoc={sandboxPreviewDocument(html)}
              sandbox="allow-scripts"
              referrerPolicy="no-referrer"
              className="h-[32rem] w-full bg-white"
            />
          )}
        </div>
      )}
    </div>
  );
}

function extractHtmlArtifact(content: string): string | null {
  const fenced = content.match(/```(?:html|htm)\s*\n([\s\S]*?)```/i);
  if (fenced?.[1]?.trim()) return fenced[1].trim();
  const start = content.search(/<!doctype\s+html\b|<html\b/i);
  if (start < 0) return null;
  const candidate = content.slice(start).trim();
  // Avoid presenting a prose fragment as a runnable file. A complete HTML
  // answer can be fenced or raw, but it must still close its document.
  return /<\/html>\s*$/i.test(candidate) ? candidate : null;
}

function sandboxPreviewDocument(html: string): string {
  // Generated code is untrusted. The preview has an opaque origin and a CSP
  // that permits only its inline code; it cannot access TemuClaude data,
  // navigate the parent page, submit forms, or call out to another service.
  const policy = "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; media-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'\">";
  return /<head[^>]*>/i.test(html)
    ? html.replace(/<head([^>]*)>/i, `<head$1>${policy}`)
    : `${policy}${html}`;
}

function OrchestrationPanel({ data, onClose }: { data: OrchestrationData; onClose: () => void }) {
  return (
    <div className="border-t border-border-subtle bg-bg-secondary max-h-[40vh] overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-text-primary">How this answer was built</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary" aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-accent-olive/20 flex items-center justify-center flex-shrink-0">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
            </div>
            <div>
              <div className="text-sm font-medium text-text-primary">Understanding your question</div>
              <div className="text-xs text-text-muted">Classified as: {data.taskType} · Routed to: {data.tier} tier</div>
            </div>
          </div>

          {data.models.length > 1 && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-primary/20 flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#E25822" strokeWidth="2"><circle cx="12" cy="12" r="3" /></svg>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-text-primary mb-2">Combining multiple answers ({data.models.length} models)</div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {data.models.map((model, i) => (
                    <div key={i} className="bg-white border border-border-subtle rounded-sm p-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-text-primary">{model.name}</span>
                        <span className={`text-xs ${model.correct ? 'text-accent-olive' : 'text-accent-fig'}`}>
                          {model.correct ? '✓' : '✗'}
                        </span>
                      </div>
                      <p className="text-xs text-text-muted line-clamp-2">{model.response}</p>
                      <div className="text-xs text-text-muted mt-1">{model.latency}s</div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-text-muted mt-2">
                  Aggregated by: {data.aggregator} · Consensus: {data.consensus}/3 agree
                </div>
              </div>
            </div>
          )}

          {data.codeVerified && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-olive/20 flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <div>
                <div className="text-sm font-medium text-text-primary">Code verification</div>
                <div className="text-xs text-text-muted">✓ Verified — code output matches the answer</div>
              </div>
            </div>
          )}

          {data.qaScore > 0 && (
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-olive/20 flex items-center justify-center flex-shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <div>
                <div className="text-sm font-medium text-text-primary">Quality check</div>
                <div className="text-xs text-text-muted">Self-QA score: {data.qaScore}/10 · {data.qaScore >= 8 ? '✓ Passed' : '⚠ Below threshold'}</div>
              </div>
            </div>
          )}

          <div className="flex items-center gap-4 pt-2 border-t border-border-subtle text-xs text-text-muted">
            <span>Total: {data.totalLatency}s</span>
            <span>·</span>
            <span>{data.models.length} models</span>
          </div>
        </div>
      </div>
    </div>
  );
}
