"use client";

import React, { useEffect, useState, useRef, useMemo, useCallback } from "react";
import Globe from "react-globe.gl";
import type { Marker } from "@/lib/api";
import { StreetMapView } from "./StreetMapView";

export type DistrictGlobeProps = {
  markers: Marker[];
  mapHeightClass?: string;
  className?: string;
  children?: React.ReactNode;
  locationQuery?: string | null;
};

/**
 * View mode:
 *  "street" – OSM flat map is fully visible (default, stays put)
 *  "globe"  – 3D globe is shown; OSM fades in only when camera drops close
 */
type ViewMode = "street" | "globe";

/** Altitude below which OSM starts fading in (only used in globe mode) */
const STREET_THRESHOLD = 0.12;
/** Altitude where OSM becomes fully opaque (only in globe mode) */
const FULL_MAP_THRESHOLD = 0.04;

export function DistrictGlobe({
  markers,
  mapHeightClass = "h-[520px]",
  className = "",
  children,
  locationQuery,
}: DistrictGlobeProps) {
  const globeEl = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>(0);

  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [clickCoords, setClickCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<any>(null);

  // ── Mode: start in "street" so OSM shows immediately ──────────────────────
  const [mode, setMode] = useState<ViewMode>("street");

  // Globe camera state – only actively polled while in "globe" mode
  const [camAlt, setCamAlt] = useState(1.5);
  const [camCenter, setCamCenter] = useState({ lat: 36.7, lng: -119.7 });

  // Effective OSM opacity:
  //   street mode → always 1
  //   globe mode  → derived from camera altitude (0 far, 1 close)
  const osmOpacity =
    mode === "street"
      ? 1
      : Math.min(
          1,
          Math.max(
            0,
            (STREET_THRESHOLD - camAlt) / (STREET_THRESHOLD - FULL_MAP_THRESHOLD)
          )
        );

  // Auto-snap back to street mode once the globe camera zooms all the way in
  useEffect(() => {
    if (mode === "globe" && camAlt < FULL_MAP_THRESHOLD) {
      setMode("street");
    }
  }, [camAlt, mode]);

  // ── Resize observer ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      if (!entries?.[0]) return;
      const { width, height } = entries[0].contentRect;
      if (width > 0 && height > 0) setDimensions({ width, height });
    });
    observer.observe(containerRef.current);
    const rect = containerRef.current.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0)
      setDimensions({ width: rect.width, height: rect.height });
    return () => observer.disconnect();
  }, []);

  // ── Globe controls (runs once globe is mounted) ───────────────────────────
  useEffect(() => {
    if (!globeEl.current || dimensions.width === 0) return;
    const controls = globeEl.current.controls();
    if (controls) {
      controls.minDistance = 101.5;
      controls.maxDistance = 800;
      controls.enablePan = true;
      controls.enableDamping = true;
      controls.dampingFactor = 0.12;
      controls.rotateSpeed = 0.7;
      controls.zoomSpeed = 1.4;
    }
  }, [dimensions]);

  // ── rAF altitude tracker (only active in globe mode) ─────────────────────
  useEffect(() => {
    if (mode !== "globe") {
      cancelAnimationFrame(rafRef.current);
      return;
    }
    const tick = () => {
      if (globeEl.current) {
        const pov = globeEl.current.pointOfView();
        if (pov) {
          setCamAlt(pov.altitude ?? 1.5);
          setCamCenter({ lat: pov.lat ?? 36.7, lng: pov.lng ?? -119.7 });
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [mode, dimensions]);

  // ── Rings data ─────────────────────────────────────────────────────────────
  const ringsData = useMemo(() => {
    return (markers ?? [])
      .filter((m) => typeof m.latitude === "number" && typeof m.longitude === "number")
      .map((m) => ({
        lat: m.latitude,
        lng: m.longitude,
        maxR: (m.visual_severity_level || 3) * 1.5,
        propagationSpeed: 0.8,
        repeatPeriod: 1500,
        color: m.marker_color || "#71d7cd",
      }));
  }, [markers]);

  // ── Auto-zoom: only runs once when entering globe mode with markers ────────
  const hasAutoZoomed = useRef(false);
  useEffect(() => {
    if (mode !== "globe" || !globeEl.current) {
      hasAutoZoomed.current = false;
      return;
    }
    if (hasAutoZoomed.current) return;

    const valid = (markers ?? []).filter(
      (m) => typeof m.latitude === "number" && typeof m.longitude === "number"
    );

    if (valid.length > 0) {
      hasAutoZoomed.current = true;
      const avgLat = valid.reduce((s, m) => s + m.latitude, 0) / valid.length;
      const avgLng = valid.reduce((s, m) => s + m.longitude, 0) / valid.length;
      // Start at region level → animate to city level → auto-snap to street
      globeEl.current.pointOfView({ lat: avgLat, lng: avgLng, altitude: 1.2 }, 0);
      setTimeout(() => {
        globeEl.current?.pointOfView({ lat: avgLat, lng: avgLng, altitude: 0.06 }, 2400);
      }, 300);
    } else if (locationQuery?.trim()) {
      hasAutoZoomed.current = true;
      fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
          locationQuery.trim()
        )}`
      )
        .then((r) => r.json())
        .then((data) => {
          if (data?.length > 0) {
            const lat = parseFloat(data[0].lat);
            const lng = parseFloat(data[0].lon);
            setClickCoords({ lat, lng });
            setCamCenter({ lat, lng });
            globeEl.current?.pointOfView({ lat, lng, altitude: 0.06 }, 2000);
          }
        })
        .catch(() => {});
    } else {
      // No markers—show globe at a nice overview altitude, user zooms manually
      hasAutoZoomed.current = true;
      globeEl.current.pointOfView({ lat: 36.7, lng: -119.7, altitude: 1.5 }, 800);
    }
  }, [mode, markers, locationQuery]);

  // ── "Globe View" button: switch to globe + zoom out ───────────────────────
  const switchToGlobe = useCallback(() => {
    setMode("globe");
    hasAutoZoomed.current = false; // allow auto-zoom to re-run
  }, []);

  // ── "Street View" button: lock to OSM ─────────────────────────────────────
  const switchToStreet = useCallback(() => {
    setMode("street");
  }, []);

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden ${mapHeightClass} ${className} z-0 flex items-center justify-center bg-[#05080a]`}
    >
      {/* ── 3D Globe layer ───────────────────────────────────────────────── */}
      {/* Rendered behind the OSM map; pointer-events disabled in street mode */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          // In street mode keep globe invisible but mounted so it stays warm
          opacity: Math.max(0, 1 - osmOpacity * 1.5),
          transition: "opacity 0.8s cubic-bezier(0.4,0,0.2,1)",
          pointerEvents: mode === "globe" && osmOpacity < 0.5 ? "auto" : "none",
        }}
      >
        {dimensions.width > 0 && dimensions.height > 0 && (
          <Globe
            ref={globeEl}
            width={dimensions.width}
            height={dimensions.height}
            globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
            bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
            backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
            backgroundColor="rgba(0,0,0,0)"
            pointsData={markers ?? []}
            pointLat="latitude"
            pointLng="longitude"
            pointColor={(d: any) => d.marker_color || "#ffb4ab"}
            pointRadius={(d: any) => {
              if (d.adjusted_risk_band === "HIGH") return 0.6;
              if (d.adjusted_risk_band === "MEDIUM") return 0.4;
              return 0.25;
            }}
            pointAltitude={0.025}
            pointsMerge={false}
            pointResolution={12}
            ringsData={ringsData}
            ringColor={(d: any) => d.color}
            ringMaxRadius="maxR"
            ringPropagationSpeed="propagationSpeed"
            ringRepeatPeriod="repeatPeriod"
            onPointClick={(point: any) => {
              setClickCoords({ lat: point.latitude, lng: point.longitude });
              setCamCenter({ lat: point.latitude, lng: point.longitude });
              globeEl.current?.pointOfView(
                { lat: point.latitude, lng: point.longitude, altitude: 0.04 },
                1000
              );
            }}
            onPointHover={(point: any) => setHoveredPoint(point)}
            atmosphereColor="#71d7cd"
            atmosphereAltitude={0.2}
          />
        )}
      </div>

      {/* ── OSM Street map ───────────────────────────────────────────────── */}
      {/* Always mounted so Leaflet doesn't re-init on every mode switch */}
      <StreetMapView
        lat={mode === "street" ? (camCenter.lat || 36.7) : camCenter.lat}
        lng={mode === "street" ? (camCenter.lng || -119.7) : camCenter.lng}
        visible={osmOpacity > 0}
        markers={markers}
        opacity={osmOpacity}
      />

      {/* ── Mode toggle buttons ──────────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          bottom: 56,
          left: 16,
          zIndex: 900,
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        {mode === "street" && (
          <button
            onClick={switchToGlobe}
            style={{
              background: "rgba(255,255,255,0.9)",
              border: "1.5px solid rgba(255,87,34,0.35)",
              borderRadius: 10,
              padding: "6px 12px",
              fontSize: 9,
              fontWeight: 800,
              letterSpacing: "0.12em",
              color: "#c0310a",
              cursor: "pointer",
              backdropFilter: "blur(6px)",
              textTransform: "uppercase",
              display: "flex",
              alignItems: "center",
              gap: 6,
              whiteSpace: "nowrap",
              boxShadow: "0 2px 12px rgba(0,0,0,0.12)",
            }}
          >
            🌍 Globe View
          </button>
        )}
        {mode === "globe" && osmOpacity < 0.9 && (
          <button
            onClick={switchToStreet}
            style={{
              background: "rgba(255,255,255,0.9)",
              border: "1.5px solid rgba(255,87,34,0.35)",
              borderRadius: 10,
              padding: "6px 12px",
              fontSize: 9,
              fontWeight: 800,
              letterSpacing: "0.12em",
              color: "#c0310a",
              cursor: "pointer",
              backdropFilter: "blur(6px)",
              textTransform: "uppercase",
              display: "flex",
              alignItems: "center",
              gap: 6,
              whiteSpace: "nowrap",
              boxShadow: "0 2px 12px rgba(0,0,0,0.12)",
            }}
          >
            🗺️ Street View
          </button>
        )}
      </div>

      {/* ── Coord HUD (globe mode only) ──────────────────────────────────── */}
      {clickCoords && mode === "globe" && osmOpacity < 0.5 && (
        <div className="absolute bottom-6 right-6 z-[600] flex items-center gap-4 clay-panel px-6 py-3 bg-[#0a0f14]/80 backdrop-blur-md border border-outline-variant/20 animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="flex flex-col items-center">
            <span className="text-[9px] text-slate-500 uppercase tracking-widest whitespace-nowrap">LATITUDE</span>
            <span className="text-primary font-mono tracking-wider">{clickCoords.lat.toFixed(4)}</span>
          </div>
          <div className="w-[1px] h-6 bg-outline-variant/30" />
          <div className="flex flex-col items-center">
            <span className="text-[9px] text-slate-500 uppercase tracking-widest whitespace-nowrap">LONGITUDE</span>
            <span className="text-secondary font-mono tracking-wider">{clickCoords.lng.toFixed(4)}</span>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); setClickCoords(null); }}
            className="ml-2 text-slate-500 hover:text-white transition-colors"
          >
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}

      {/* ── Hover tooltip (globe mode only) ─────────────────────────────── */}
      {hoveredPoint && mode === "globe" && osmOpacity < 0.3 && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-24 pointer-events-none z-[600] animate-in zoom-in-95 duration-200">
          <div className="relative">
            <div
              className="px-3 py-2 rounded-xl border backdrop-blur-md shadow-2xl flex flex-col items-center text-center gap-0.5"
              style={{
                backgroundColor: "rgba(10, 15, 20, 0.9)",
                borderColor: `${hoveredPoint.marker_color}40`,
                boxShadow: `0 8px 32px ${hoveredPoint.marker_color}20`,
              }}
            >
              <span className="text-[9px] font-bold tracking-widest uppercase opacity-60">TACTICAL ZONE</span>
              <span className="text-[14px] font-headline font-bold text-white whitespace-nowrap">
                {hoveredPoint.display_district}
              </span>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: hoveredPoint.marker_color }} />
                <span className="text-[10px] font-bold tracking-wider" style={{ color: hoveredPoint.marker_color }}>
                  {hoveredPoint.adjusted_risk_band} RISK
                </span>
              </div>
            </div>
            <div
              className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 rotate-45 border-r border-b"
              style={{ backgroundColor: "rgba(10, 15, 20, 0.9)", borderColor: `${hoveredPoint.marker_color}40` }}
            />
          </div>
        </div>
      )}

      {/* ── Edge fades (globe mode only) ─────────────────────────────────── */}
      {mode === "globe" && osmOpacity < 0.7 && (
        <>
          <div className="absolute top-0 inset-x-0 h-16 bg-gradient-to-b from-[#0a0f14] to-transparent pointer-events-none z-[400]" />
          <div className="absolute bottom-0 inset-x-0 h-16 bg-gradient-to-t from-[#0a0f14] to-transparent pointer-events-none z-[400]" />
        </>
      )}

      <div className="absolute inset-0 z-[500] pointer-events-none flex p-8">
        {children}
      </div>
    </div>
  );
}
