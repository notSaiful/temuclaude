'use client';

import { useEffect, useRef, useState } from 'react';

export function OrchestrationDiagram() {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className="w-full max-w-2xl mx-auto" aria-label="Orchestration diagram showing 5 AI models connecting to Temuclaude">
      <svg viewBox="0 0 600 400" className="w-full h-auto">
        {/* Connection lines */}
        {[
          { x1: 80, y1: 100, x2: 300, y2: 200 },
          { x1: 200, y1: 60, x2: 300, y2: 200 },
          { x1: 300, y1: 40, x2: 300, y2: 200 },
          { x1: 400, y1: 60, x2: 300, y2: 200 },
          { x1: 520, y1: 100, x2: 300, y2: 200 },
        ].map((line, i) => (
          <line
            key={i}
            x1={line.x1}
            y1={line.y1}
            x2={line.x2}
            y2={line.y2}
            stroke="#E25822"
            strokeWidth="2"
            opacity="0.3"
            className={visible ? 'connection-draw' : ''}
            style={{
              strokeDasharray: '500',
              strokeDashoffset: visible ? '0' : '500',
              transition: `stroke-dashoffset 1s ease-out ${i * 0.15}s`,
            }}
          />
        ))}

        {/* Model nodes */}
        {[
          { cx: 80, cy: 100, color: '#E8D5C4', label: 'GLM-5.2', delay: 0 },
          { cx: 200, cy: 60, color: '#D4A574', label: 'DeepSeek', delay: 0.2 },
          { cx: 300, cy: 40, color: '#C97B50', label: 'Kimi K2.6', delay: 0.4 },
          { cx: 400, cy: 60, color: '#D4A574', label: 'MiniMax', delay: 0.6 },
          { cx: 520, cy: 100, color: '#E8D5C4', label: 'Nemotron', delay: 0.8 },
        ].map((node, i) => (
          <g
            key={i}
            style={{
              opacity: visible ? 1 : 0,
              transform: visible ? 'scale(1)' : 'scale(0)',
              transformOrigin: `${node.cx}px ${node.cy}px`,
              transition: `all 0.4s cubic-bezier(0.25, 1, 0.5, 1) ${node.delay}s`,
            }}
          >
            <circle cx={node.cx} cy={node.cy} r="22" fill={node.color} opacity="0.9" />
            <circle
              cx={node.cx}
              cy={node.cy}
              r="22"
              fill="none"
              stroke={node.color}
              strokeWidth="2"
              opacity="0.4"
              className="node-pulse"
            />
            <text
              x={node.cx}
              y={node.cy + 45}
              textAnchor="middle"
              fontSize="11"
              fill="#5E5B56"
              fontFamily="Inter, sans-serif"
              fontWeight="500"
            >
              {node.label}
            </text>
          </g>
        ))}

        {/* Central hub — Temuclaude */}
        <g
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'scale(1)' : 'scale(0)',
            transformOrigin: '300px 200px',
            transition: 'all 0.5s cubic-bezier(0.25, 1, 0.5, 1) 1s',
          }}
        >
          <circle cx="300" cy="200" r="35" fill="#E25822" className="node-pulse" />
          <circle cx="300" cy="200" r="35" fill="none" stroke="#E25822" strokeWidth="2" opacity="0.3" />
          <text
            x="300"
            y="205"
            textAnchor="middle"
            fontSize="14"
            fill="#FAF8F5"
            fontFamily="Inter, sans-serif"
            fontWeight="700"
          >
            T
          </text>
        </g>

        {/* Data pulse particles */}
        {visible && [
          { path: 'M 80 100 L 300 200', delay: 1.5, color: '#E25822' },
          { path: 'M 200 60 L 300 200', delay: 1.7, color: '#E25822' },
          { path: 'M 300 40 L 300 200', delay: 1.9, color: '#E25822' },
          { path: 'M 400 60 L 300 200', delay: 2.1, color: '#E25822' },
          { path: 'M 520 100 L 300 200', delay: 2.3, color: '#E25822' },
        ].map((pulse, i) => (
          <circle key={i} r="4" fill={pulse.color}>
            <animateMotion
              dur="2s"
              repeatCount="indefinite"
              begin={`${pulse.delay}s`}
              path={pulse.path}
            />
            <animate
              attributeName="opacity"
              values="0;1;1;0"
              dur="2s"
              repeatCount="indefinite"
              begin={`${pulse.delay}s`}
            />
          </circle>
        ))}

        {/* Output line from hub */}
        <line
          x1="300"
          y1="235"
          x2="300"
          y2="340"
          stroke="#E25822"
          strokeWidth="2"
          opacity="0.3"
          strokeDasharray="5,5"
          style={{
            opacity: visible ? 0.3 : 0,
            transition: 'opacity 0.5s ease-out 1.5s',
          }}
        />

        {/* Output label */}
        <text
          x="300"
          y="365"
          textAnchor="middle"
          fontSize="13"
          fill="#1A1816"
          fontFamily="Inter, sans-serif"
          fontWeight="600"
          style={{
            opacity: visible ? 1 : 0,
            transition: 'opacity 0.5s ease-out 2s',
          }}
        >
          One superior answer
        </text>
      </svg>
    </div>
  );
}