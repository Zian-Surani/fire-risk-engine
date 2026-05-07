"use client";
/**
 * Thin hook that maintains a WebSocket connection to /ws/live and calls
 * `onEvent` for every received message.  Automatically reconnects after
 * a brief delay when the socket closes.
 */

import { useEffect, useRef } from "react";
import { createLiveSocket, type WsEvent } from "@/lib/api";

const RECONNECT_DELAY_MS = 3000;

export function useLiveSocket(onEvent: (e: WsEvent) => void): void {
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let destroyed = false;

    function connect() {
      if (destroyed) return;
      ws = createLiveSocket(
        (e) => onEventRef.current(e),
        () => {
          if (!destroyed) {
            timer = setTimeout(connect, RECONNECT_DELAY_MS);
          }
        }
      );
    }

    connect();

    return () => {
      destroyed = true;
      if (timer) clearTimeout(timer);
      ws?.close();
    };
  }, []);
}

