'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';

const commands = [
  { label: 'Go to Home', href: '/', type: 'navigate' },
  { label: 'Open Playground', href: '/playground', type: 'navigate' },
  { label: 'View Models', href: '/models', type: 'navigate' },
  { label: 'Read Docs', href: '/docs', type: 'navigate' },
  { label: 'See Benchmarks', href: '/benchmarks', type: 'navigate' },
  { label: 'View Pricing', href: '/pricing', type: 'navigate' },
  { label: 'Enterprise', href: '/enterprise', type: 'navigate' },
  { label: 'Star on GitHub', href: 'https://github.com/notSaiful/temuclaude', type: 'external' },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const router = useRouter();

  const toggleOpen = useCallback(() => {
    setOpen((prev) => !prev);
    setQuery('');
    setSelected(0);
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggleOpen();
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, toggleOpen]);

  const filtered = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (cmd: typeof commands[0]) => {
    if (cmd.type === 'external') {
      window.open(cmd.href, '_blank', 'noopener noreferrer');
    } else {
      router.push(cmd.href);
    }
    setOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelected((prev) => Math.min(prev + 1, filtered.length - 1));
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelected((prev) => Math.max(prev - 1, 0));
    }
    if (e.key === 'Enter' && filtered[selected]) {
      e.preventDefault();
      handleSelect(filtered[selected]);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4"
          style={{ background: 'rgba(26, 24, 22, 0.3)', backdropFilter: 'blur(4px)' }}
          onClick={() => setOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -8 }}
            transition={{ duration: 0.25, ease: [0.25, 1, 0.5, 1] }}
            className="w-full max-w-lg bg-white rounded-md border border-border-default overflow-hidden"
            style={{ boxShadow: '0px 0px 0px 1px rgba(26, 24, 22, 0.08), rgba(26, 24, 22, 0.08) 0px 12px 40px' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-border-subtle">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8E8B85" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelected(0);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Search commands..."
                className="flex-1 bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted"
                autoFocus
              />
              <kbd className="text-[10px] text-text-muted bg-bg-secondary px-1.5 py-0.5 rounded font-mono">ESC</kbd>
            </div>

            {/* Command list */}
            <div className="max-h-72 overflow-y-auto py-2">
              {filtered.length === 0 && (
                <div className="px-4 py-6 text-center text-sm text-text-muted">
                  No commands found
                </div>
              )}
              {filtered.map((cmd, i) => (
                <button
                  key={cmd.href + cmd.label}
                  onClick={() => handleSelect(cmd)}
                  onMouseEnter={() => setSelected(i)}
                  className={`w-full flex items-center justify-between px-4 py-2.5 text-left transition-colors ${
                    i === selected ? 'bg-bg-secondary' : ''
                  }`}
                >
                  <span className="text-sm text-text-primary">{cmd.label}</span>
                  <div className="flex items-center gap-2">
                    {cmd.type === 'external' && (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8E8B85" strokeWidth="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                    )}
                    {i === selected && (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E25822" strokeWidth="2">
                        <path d="M5 12h14M12 5l7 7-7 7" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-border-subtle flex items-center gap-4 text-[10px] text-text-muted font-mono">
              <span>↑↓ Navigate</span>
              <span>↵ Select</span>
              <span>esc Close</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}