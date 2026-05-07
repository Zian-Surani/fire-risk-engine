"use client";

import React, { useEffect, useRef } from "react";
import type { Marker } from "@/lib/api";

type Props = {
  lat: number;
  lng: number;
  visible: boolean;
  markers: Marker[];
  opacity: number; // 0..1 for cross-fade
};

/** Inject Leaflet CSS into <head> once, before any map is created */
function ensureLeafletCSS() {
  if (typeof document === "undefined") return;
  if (document.getElementById("leaflet-css-link")) return;
  const link = document.createElement("link");
  link.id = "leaflet-css-link";
  link.rel = "stylesheet";
  link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  link.crossOrigin = "";
  document.head.appendChild(link);
}

export function StreetMapView({ lat, lng, visible, markers, opacity }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersLayerRef = useRef<any>(null);
  const tileLayerRef = useRef<any>(null);

  // ── Boot Leaflet once ────────────────────────────────────────────────────
  useEffect(() => {
    if (typeof window === "undefined") return;

    ensureLeafletCSS();

    // `cancelled` handles React StrictMode's double-invoke: if cleanup runs
    // before the async init resolves, we bail out and don't mount the map.
    let cancelled = false;

    const init = async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !containerRef.current) return;

      // If Leaflet already attached itself to this DOM node (StrictMode second
      // mount or hot-reload), tear it down first so we don't get the
      // "Map container is already initialized" error.
      const el = containerRef.current as any;
      if (el._leaflet_id) {
        try { L.map(el).remove(); } catch (_) {}
        el._leaflet_id = undefined;
      }
      if (mapRef.current) {
        try { mapRef.current.remove(); } catch (_) {}
        mapRef.current = null;
      }

      if (cancelled) return;

      // Fix broken default marker icon paths in Next.js / webpack
      // @ts-ignore
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = L.map(containerRef.current, {
        center: [lat, lng],
        zoom: 14,
        zoomControl: false,
        attributionControl: true,
        preferCanvas: true,
        renderer: L.canvas({ tolerance: 6 }),
      });

      // Standard OSM tiles — bright, reliable, no API key needed
      const tile = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 20,
        crossOrigin: "anonymous",
      });
      tile.addTo(map);
      tileLayerRef.current = tile;

      L.control.zoom({ position: "bottomright" }).addTo(map);
      markersLayerRef.current = L.layerGroup().addTo(map);
      mapRef.current = map;

      // Tile images load asynchronously — force a size recalc to fill the div
      setTimeout(() => { if (!cancelled) map.invalidateSize(); }, 100);
      setTimeout(() => { if (!cancelled) map.invalidateSize(); }, 600);
    };

    init();

    return () => {
      cancelled = true;
      if (mapRef.current) {
        try { mapRef.current.remove(); } catch (_) {}
        mapRef.current = null;
        markersLayerRef.current = null;
        tileLayerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Sync centre ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current) return;
    mapRef.current.setView([lat, lng], mapRef.current.getZoom(), {
      animate: true,
      duration: 0.6,
    });
  }, [lat, lng]);

  // ── Force resize when becoming visible ───────────────────────────────────
  useEffect(() => {
    if (visible && mapRef.current) {
      setTimeout(() => mapRef.current?.invalidateSize(), 60);
    }
  }, [visible]);

  // ── Auto-centre on markers when first received ───────────────────────────
  useEffect(() => {
    if (!mapRef.current) return;
    const valid = (markers ?? []).filter(
      (m) => typeof m.latitude === "number" && typeof m.longitude === "number"
    );
    if (valid.length === 0) return;

    import("leaflet").then(({ default: L }) => {
      if (!mapRef.current) return;
      if (valid.length === 1) {
        mapRef.current.setView([valid[0].latitude, valid[0].longitude], 14, { animate: true });
      } else {
        const bounds = L.latLngBounds(valid.map((m) => [m.latitude, m.longitude] as [number, number]));
        mapRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 15, animate: true });
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [markers.length > 0 ? markers[0]?.latitude : null]);

  // ── Draw heat map markers ─────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !markersLayerRef.current) return;

    import("leaflet").then(({ default: L }) => {
      markersLayerRef.current.clearLayers();

      (markers ?? []).forEach((m) => {
        if (typeof m.latitude !== "number" || typeof m.longitude !== "number") return;

        const color = m.marker_color || "#ff5722";
        const severity = Math.max(1, m.visual_severity_level || 2);
        const latlng: [number, number] = [m.latitude, m.longitude];

        // ── Outer halo ────────────────────────────────────────────────
        L.circleMarker(latlng, {
          radius: 22 + severity * 5,
          color: color,
          weight: 0,
          fillColor: color,
          fillOpacity: 0.06,
        }).addTo(markersLayerRef.current);

        // ── Mid pulse ring ────────────────────────────────────────────
        L.circleMarker(latlng, {
          radius: 13 + severity * 3,
          color: color,
          weight: 1.5,
          fillColor: color,
          fillOpacity: 0.15,
          opacity: 0.7,
        }).addTo(markersLayerRef.current);

        // ── Core dot ──────────────────────────────────────────────────
        const core = L.circleMarker(latlng, {
          radius: 6,
          color: "#fff",
          weight: 1.5,
          fillColor: color,
          fillOpacity: 1,
          opacity: 1,
        }).addTo(markersLayerRef.current);

        // ── Tooltip ───────────────────────────────────────────────────
        const label = m.display_district ?? "Zone";
        const band = m.adjusted_risk_band ?? "UNKNOWN";
        core.bindTooltip(
          `<div class="fire-tooltip" style="--c:${color}">
            <span class="fire-tooltip-band">${band} RISK</span>
            <span class="fire-tooltip-name">${label}</span>
          </div>`,
          { permanent: false, direction: "top", className: "fire-tooltip-wrapper" }
        );
      });
    });
  }, [markers]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity,
        // Smooth ease for the cross-fade
        transition: "opacity 0.9s cubic-bezier(0.4, 0, 0.2, 1)",
        pointerEvents: opacity > 0.45 ? "auto" : "none",
        zIndex: opacity > 0.45 ? 10 : 3,
        borderRadius: "inherit",
        overflow: "hidden",
      }}
    >
      {/* ── Tooltip + Leaflet theme overrides ──────────────────────── */}
      <style>{`
        /* Make the map tiles visible and bright */
        .leaflet-container {
          background: #e8e0d8 !important;
          font-family: inherit;
        }

        /* Attribution bar */
        .leaflet-control-attribution {
          font-size: 9px !important;
          background: rgba(255,255,255,0.75) !important;
          color: #555 !important;
          border-radius: 6px 0 0 0 !important;
          padding: 2px 6px !important;
        }
        .leaflet-control-attribution a { color: #e55 !important; }

        /* Zoom buttons */
        .leaflet-bar a {
          background: #fff !important;
          color: #333 !important;
          border-color: #ccc !important;
          font-size: 16px !important;
          font-weight: 700 !important;
        }
        .leaflet-bar a:hover { background: #f0f0f0 !important; }

        /* Heat-map tooltip */
        .fire-tooltip-wrapper {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 0 !important;
        }
        .fire-tooltip-wrapper::before { display: none !important; }

        .fire-tooltip {
          background: rgba(255,255,255,0.96);
          border-left: 4px solid var(--c, #ff5722);
          border-radius: 8px;
          padding: 6px 12px;
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 110px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.18);
        }
        .fire-tooltip-band {
          font-size: 9px;
          font-weight: 800;
          letter-spacing: .1em;
          color: var(--c, #ff5722);
          text-transform: uppercase;
        }
        .fire-tooltip-name {
          font-size: 12px;
          font-weight: 700;
          color: #111;
        }
      `}</style>

      {/* ── Map canvas ───────────────────────────────────────────────── */}
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {/* ── "Street View · Live" badge ───────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 14,
          zIndex: 900,
          background: "rgba(255,255,255,0.92)",
          border: "1.5px solid rgba(255,87,34,0.35)",
          borderRadius: 10,
          padding: "5px 12px",
          display: "flex",
          alignItems: "center",
          gap: 7,
          backdropFilter: "blur(6px)",
          pointerEvents: "none",
          boxShadow: "0 2px 12px rgba(0,0,0,0.12)",
        }}
      >
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: "#ff5722",
            boxShadow: "0 0 6px #ff5722",
            display: "inline-block",
            animation: "osmPulse 1.4s ease-in-out infinite",
          }}
        />
        <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: "0.13em", color: "#333", textTransform: "uppercase" }}>
          Street View · OpenStreetMap
        </span>
        <style>{`
          @keyframes osmPulse {
            0%,100% { opacity:1; transform:scale(1); }
            50% { opacity:0.5; transform:scale(1.4); }
          }
        `}</style>
      </div>
    </div>
  );
}
