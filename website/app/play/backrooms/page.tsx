'use client';

import dynamic from 'next/dynamic';

// Dynamic import with SSR disabled — Three.js MUST only run in the browser
const Game = dynamic(() => import('./Game'), {
  ssr: false,
  loading: () => (
    <div style={{
      width: '100vw', height: '100vh', background: '#000',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: '"Courier New", monospace', color: '#e8b547',
      fontSize: '1.5rem', letterSpacing: '0.2em',
    }}>
      LOADING TAPE...
    </div>
  ),
});

export default function BackroomsPage() {
  return <Game />;
}
