import { useEffect, useRef } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';
import { WS_URL } from '../api/client';

export default function Terminal({ sessionId, token, active }) {
  const containerRef = useRef(null);
  const xtermRef = useRef(null);
  const wsRef = useRef(null);
  const fitAddonRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !sessionId || !token) return;

    const term = new XTerm({
      theme: {
        background: '#0d0d0d',
        foreground: '#e0e0e0',
        cursor: '#4ade80',
        cursorAccent: '#0d0d0d',
        selectionBackground: '#333333',
        black: '#1a1a1a',
        brightBlack: '#555555',
        red: '#e05252',
        brightRed: '#e05252',
        green: '#4ade80',
        brightGreen: '#4ade80',
        yellow: '#e8a040',
        brightYellow: '#e8a040',
        blue: '#5588ff',
        brightBlue: '#5588ff',
        magenta: '#cc66ff',
        brightMagenta: '#cc66ff',
        cyan: '#40d0e0',
        brightCyan: '#40d0e0',
        white: '#e0e0e0',
        brightWhite: '#ffffff',
      },
      fontFamily: 'JetBrains Mono, Fira Code, monospace',
      fontSize: 13,
      lineHeight: 1.4,
      cursorBlink: true,
      cursorStyle: 'block',
      scrollback: 1000,
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);
    term.open(containerRef.current);
    fitAddon.fit();

    const ws = new WebSocket(
      `${WS_URL}/api/v1/ws/terminal?token=${token}&cols=${term.cols}&rows=${term.rows}`
    );

    xtermRef.current = term;
    fitAddonRef.current = fitAddon;

    wsRef.current = ws;

    // отправляем текущий размер терминала
    const sendResize = () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'resize',
          cols: term.cols,
          rows: term.rows,
        }));
      }
    };

    ws.onopen = () => {
      term.writeln('\x1b[32mСоединение установлено\x1b[0m');
      // отправляем размер сразу после подключения
      sendResize();
    };

    ws.onmessage = (event) => {
      term.write(event.data);
    };

    ws.onclose = () => {
      term.writeln('\r\n\x1b[33mСоединение закрыто\x1b[0m');
    };

    ws.onerror = () => {
      term.writeln('\r\n\x1b[31mОшибка подключения\x1b[0m');
    };

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    });

    // отправляем новый размер при resize терминала
    term.onResize(() => {
      sendResize();
    });

    const handleResize = () => {
      fitAddon.fit();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      ws.close();
      term.dispose();
    };
  }, [sessionId, token]);

  useEffect(() => {
    if (active && fitAddonRef.current) {
      setTimeout(() => fitAddonRef.current?.fit(), 50);
    }
  }, [active]);

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', padding: '8px' }}
    />
  );
}