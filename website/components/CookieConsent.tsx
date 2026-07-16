'use client';

import { useState, useEffect } from 'react';

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('temuclaude_cookie_consent');
    if (!consent) {
      setVisible(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('temuclaude_cookie_consent', 'accepted');
    setVisible(false);
  };

  const handleReject = () => {
    localStorage.setItem('temuclaude_cookie_consent', 'rejected');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      className="fixed top-20 left-4 right-4 z-[90] bg-bg-primary border border-border-subtle shadow-lg rounded-md sm:left-auto sm:max-w-xl"
      role="region"
      aria-label="Cookie consent"
    >
      <div className="px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-sm text-text-secondary text-center sm:text-left">
          We use cookies to improve your experience. Read our{' '}
          <a href="/privacy" className="text-accent-primary hover:underline">Privacy Policy</a>.
        </p>
        <div className="flex gap-2 flex-shrink-0">
          <button
            onClick={handleReject}
            className="btn-secondary text-xs !px-4 !py-2"
          >
            Reject
          </button>
          <button
            onClick={handleAccept}
            className="btn-primary text-xs !px-4 !py-2"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
