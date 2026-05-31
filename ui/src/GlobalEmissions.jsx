import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  Gauge,
  Layers,
  Leaf,
  Minus,
  Plus,
  RotateCcw,
  Search,
  X,
  Zap,
} from 'lucide-react';

import { ALL_CONTINENTS } from './continents';
import { COUNTRIES, DATA_SOURCES, GLOBAL_BASELINES } from './globalEmissionsData';
import './GlobalEmissions.css';

const DEG = Math.PI / 180;
const MIX_KEYS = ['coal', 'gas', 'oil', 'nuclear', 'hydro', 'wind', 'solar', 'other'];
const COUNTRY_LABEL_CODES = new Set(['CN', 'US', 'IN', 'RU', 'JP', 'DE', 'BR', 'AU', 'ZA', 'SA', 'FR', 'GB', 'CA', 'IR', 'ID', 'TR']);
const MAX_CO2 = Math.max(...COUNTRIES.map((country) => country.co2));
const MAX_INTENSITY = Math.max(...COUNTRIES.map((country) => country.co2 / Math.max(country.energy, 1)));

const VIEW_MODES = [
  { id: 'co2', label: 'CO2', Icon: Activity },
  { id: 'renewables', label: 'Clean Mix', Icon: Leaf },
  { id: 'intensity', label: 'Intensity', Icon: Gauge },
];

const FLIGHT_CORRIDORS = [
  ['US', 'GB'],
  ['GB', 'IN'],
  ['FR', 'JP'],
  ['CN', 'AU'],
  ['AE', 'SG'],
  ['BR', 'ZA'],
  ['ES', 'MX'],
  ['DE', 'KR'],
  ['CA', 'FR'],
  ['NG', 'GB'],
];

const MIX_COLORS = {
  coal: '#8b5e34',
  gas: '#60a5fa',
  oil: '#f97316',
  nuclear: '#a78bfa',
  hydro: '#38bdf8',
  wind: '#22c55e',
  solar: '#facc15',
  other: '#14b8a6',
};

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const numeric = (value) => (Number.isFinite(Number(value)) ? Number(value) : 0);
const lerp = (a, b, t) => a + (b - a) * t;
const mixColor = (a, b, t) => a.map((channel, index) => Math.round(lerp(channel, b[index], t)));
const rgba = ([r, g, b], alpha) => `rgba(${r},${g},${b},${alpha})`;
const rgb = ([r, g, b]) => `rgb(${r},${g},${b})`;

const formatNumber = (value, digits = 0) => {
  if (!Number.isFinite(Number(value))) return 'n/a';
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
};

const normalizeLng = (lng) => {
  let normalized = lng;
  while (normalized > 180) normalized -= 360;
  while (normalized < -180) normalized += 360;
  return normalized;
};

const lngDelta = (from, to) => {
  let delta = to - from;
  if (delta > 180) delta -= 360;
  if (delta < -180) delta += 360;
  return delta;
};

const densifyCoords = (coords, maxStep = 3.5) => {
  if (!coords.length) return coords;
  const result = [];
  for (let index = 0; index < coords.length - 1; index += 1) {
    const [latA, lngA] = coords[index];
    const [latB, lngB] = coords[index + 1];
    const dLat = latB - latA;
    const dLng = lngDelta(lngA, lngB);
    const steps = Math.max(1, Math.ceil(Math.max(Math.abs(dLat), Math.abs(dLng)) / maxStep));
    result.push([latA, lngA]);
    for (let step = 1; step < steps; step += 1) {
      const t = step / steps;
      result.push([latA + dLat * t, normalizeLng(lngA + dLng * t)]);
    }
  }
  result.push(coords[coords.length - 1]);
  return result;
};

const LANDMASSES = ALL_CONTINENTS.map((continent) => ({
  ...continent,
  coords: densifyCoords(continent.coords),
}));

const latLngTo3D = (lat, lng, radius) => {
  const phi = (90 - lat) * DEG;
  const theta = (lng + 180) * DEG;
  return [
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  ];
};

const rotY = (x, y, z, angle) => [
  x * Math.cos(angle) + z * Math.sin(angle),
  y,
  -x * Math.sin(angle) + z * Math.cos(angle),
];

const rotX = (x, y, z, angle) => [
  x,
  y * Math.cos(angle) - z * Math.sin(angle),
  y * Math.sin(angle) + z * Math.cos(angle),
];

const project3D = (x, y, z, cx, cy) => {
  const factor = 860 / (860 + z);
  return [cx + x * factor, cy - y * factor, factor, z];
};

const getRenewableShare = (country) => (
  numeric(country.hydro) + numeric(country.wind) + numeric(country.solar) + numeric(country.other)
);

const getFossilShare = (country) => numeric(country.coal) + numeric(country.gas) + numeric(country.oil);
const getLowCarbonShare = (country) => getRenewableShare(country) + numeric(country.nuclear);
const getEmissionIntensity = (country) => country.co2 / Math.max(country.energy, 1);
const getCo2PerCapita = (country) => country.co2 / Math.max(country.pop, 0.1);
const getCo2PerGdp = (country) => (country.gdp ? (country.co2 / country.gdp) * 1000 : null);

const getViewValue = (country, viewMode) => {
  if (viewMode === 'renewables') return clamp(getLowCarbonShare(country) / 100, 0, 1);
  if (viewMode === 'intensity') return clamp(getEmissionIntensity(country) / MAX_INTENSITY, 0, 1);
  return clamp(country.co2 / MAX_CO2, 0, 1);
};

const getCountryColor = (country, viewMode) => {
  const value = getViewValue(country, viewMode);
  if (viewMode === 'renewables') {
    return mixColor([148, 163, 184], [34, 197, 94], Math.pow(value, 0.72));
  }
  if (viewMode === 'intensity') {
    return mixColor([56, 189, 248], [244, 63, 94], Math.pow(value, 0.86));
  }
  if (value > 0.55) return mixColor([250, 204, 21], [248, 113, 113], (value - 0.55) / 0.45);
  return mixColor([125, 211, 252], [250, 204, 21], value / 0.55);
};

const getNodeRadius = (country, zoom, viewMode) => {
  const value = getViewValue(country, viewMode);
  return (1.35 + Math.sqrt(value) * 4.25) * zoom;
};

const getCountryFlag = (country) => country.code
  .toUpperCase()
  .split('')
  .map((char) => String.fromCodePoint(127397 + char.charCodeAt(0)))
  .join('');

const getMetricForMode = (country, viewMode) => {
  if (viewMode === 'renewables') return { label: 'Low-carbon mix', value: `${formatNumber(getLowCarbonShare(country), 1)}%` };
  if (viewMode === 'intensity') return { label: 'CO2 intensity', value: `${formatNumber(getEmissionIntensity(country), 2)} Mt/TWh` };
  return { label: 'Annual CO2', value: `${formatNumber(country.co2, 1)} Mt` };
};

const getQuadraticPoint = (t, start, control, end) => ({
  x: (1 - t) * (1 - t) * start.x + 2 * (1 - t) * t * control.x + t * t * end.x,
  y: (1 - t) * (1 - t) * start.y + 2 * (1 - t) * t * control.y + t * t * end.y,
});

const getQuadraticTangent = (t, start, control, end) => ({
  x: 2 * (1 - t) * (control.x - start.x) + 2 * t * (end.x - control.x),
  y: 2 * (1 - t) * (control.y - start.y) + 2 * t * (end.y - control.y),
});

const drawBackdrop = (ctx, width, height, timeMs) => {
  const bg = ctx.createLinearGradient(0, 0, width, height);
  bg.addColorStop(0, '#07111f');
  bg.addColorStop(0.45, '#101317');
  bg.addColorStop(1, '#130c0b');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, width, height);

  ctx.lineWidth = 1;
  for (let i = 0; i < 16; i += 1) {
    const x = (i / 15) * width;
    ctx.strokeStyle = 'rgba(255,255,255,0.026)';
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x - width * 0.1, height);
    ctx.stroke();
  }

  for (let i = 0; i < 90; i += 1) {
    const seed = i + 1;
    const x = ((Math.sin(seed * 128.8) + 1) * 0.5) * width;
    const y = ((Math.cos(seed * 74.2) + 1) * 0.5) * height;
    const twinkle = 0.35 + 0.25 * Math.sin(timeMs * 0.0012 + seed);
    const size = 0.65 + (seed % 4) * 0.3;
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,255,255,${0.08 + twinkle * 0.1})`;
    ctx.fill();
  }
};

const drawEmissionPlume = (ctx, px, py, scale, country, timeMs, isSelected) => {
  const intensity = clamp(country.co2 / 4500, 0.1, 1);
  const fossil = clamp(getFossilShare(country) / 100, 0, 1);
  const plumeHeight = (44 + intensity * 84) * scale;
  const particleCount = 9 + Math.round(intensity * 15);
  const haze = mixColor([148, 163, 184], [249, 115, 22], fossil);
  const ember = mixColor([251, 191, 36], [239, 68, 68], intensity);
  const baseAlpha = 0.055 + intensity * 0.11 + (isSelected ? 0.06 : 0);

  for (let h = 0; h < 2; h += 1) {
    const gradient = ctx.createRadialGradient(px, py - h * 8 * scale, 0, px, py - h * 8 * scale, (16 + intensity * 30) * scale);
    gradient.addColorStop(0, rgba(haze, baseAlpha));
    gradient.addColorStop(0.55, rgba(ember, 0.035 + intensity * 0.06));
    gradient.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(px, py - h * 8 * scale, (16 + intensity * 30) * scale, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let i = 0; i < particleCount; i += 1) {
    const phase = (timeMs * 0.00025 + i / particleCount + country.lat * 0.01) % 1;
    const driftX = Math.sin(timeMs * 0.0012 + i * 1.37 + country.lng * 0.03) * (8 + intensity * 16) * scale * phase;
    const driftY = -phase * plumeHeight + Math.cos(timeMs * 0.0008 + i * 0.91) * 3 * scale;
    const radius = (2.8 + intensity * 9) * (0.4 + (1 - phase) * 0.8) * scale;
    const alpha = (0.05 + intensity * (0.12 + fossil * 0.08)) * (1 - phase * phase);
    const particle = ctx.createRadialGradient(px + driftX, py + driftY, 0, px + driftX, py + driftY, radius * 2.2);
    particle.addColorStop(0, rgba(ember, alpha + (isSelected ? 0.05 : 0)));
    particle.addColorStop(0.5, rgba(haze, alpha * 0.45));
    particle.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = particle;
    ctx.beginPath();
    ctx.arc(px + driftX, py + driftY, radius * 2.2, 0, Math.PI * 2);
    ctx.fill();
  }
};

const drawAircraft = (ctx, x, y, angle, scale, color, alpha) => {
  const size = clamp(scale, 0.82, 1.5);
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);

  ctx.strokeStyle = rgba(color, alpha * 0.38);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(-18 * size, 0);
  ctx.lineTo(-31 * size, 0);
  ctx.stroke();

  ctx.fillStyle = rgba(color, alpha);
  ctx.beginPath();
  ctx.moveTo(12 * size, 0);
  ctx.lineTo(1 * size, -2.6 * size);
  ctx.lineTo(-10 * size, -6.4 * size);
  ctx.lineTo(-6 * size, -1.8 * size);
  ctx.lineTo(-19 * size, -1.2 * size);
  ctx.lineTo(-19 * size, 1.2 * size);
  ctx.lineTo(-6 * size, 1.8 * size);
  ctx.lineTo(-10 * size, 6.4 * size);
  ctx.lineTo(1 * size, 2.6 * size);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
};

const drawAmbientAircraft = (ctx, startPoint, endPoint, flightIndex, timeMs, options = {}) => {
  const emphasized = Boolean(options.emphasized);
  const traffic = options.traffic || (emphasized ? 2 : 1);
  const flightColor = [
    [45, 212, 191],
    [125, 211, 252],
    [250, 204, 21],
    [167, 139, 250],
  ][flightIndex % 4];
  const flightStrength = clamp(options.strength || 0.48 + (flightIndex % 5) * 0.08, 0.18, 0.9);
  const arcLift = (30 + flightStrength * 46) * Math.min(startPoint.scale, endPoint.scale);
  const start = { x: startPoint.px, y: startPoint.py };
  const end = { x: endPoint.px, y: endPoint.py };
  const control = {
    x: (start.x + end.x) / 2,
    y: (start.y + end.y) / 2 - arcLift - (emphasized ? 12 : 0),
  };

  if (options.showPath) {
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.quadraticCurveTo(control.x, control.y, end.x, end.y);
    ctx.strokeStyle = rgba(flightColor, 0.035 + flightStrength * 0.035);
    ctx.lineWidth = 0.55 + flightStrength * 0.25;
    ctx.setLineDash([4, 10]);
    ctx.lineDashOffset = -timeMs * (0.012 + flightStrength * 0.012);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  const glowT = (timeMs * (0.00024 + flightStrength * 0.00008) + flightIndex * 0.21) % 1;
  const glowPos = getQuadraticPoint(glowT, start, control, end);
  ctx.fillStyle = rgba(flightColor, 0.1 + flightStrength * 0.1);
  ctx.beginPath();
  ctx.arc(glowPos.x, glowPos.y, 1.2 + flightStrength * 1.1, 0, Math.PI * 2);
  ctx.fill();

  for (let planeIndex = 0; planeIndex < traffic; planeIndex += 1) {
    const planeT = (timeMs * (0.00007 + flightStrength * 0.000022 + planeIndex * 0.000003) + flightIndex * 0.17 + planeIndex * 0.28) % 1;
    const planePos = getQuadraticPoint(planeT, start, control, end);
    const tangent = getQuadraticTangent(planeT, start, control, end);
    const planeAngle = Math.atan2(tangent.y, tangent.x);
    const trailSegments = emphasized ? 11 : 7;

    for (let trailIndex = trailSegments; trailIndex >= 1; trailIndex -= 1) {
      const currentT = (planeT - trailIndex * 0.018 + 1) % 1;
      const nextT = (planeT - (trailIndex - 1) * 0.018 + 1) % 1;
      const currentPoint = getQuadraticPoint(currentT, start, control, end);
      const nextPoint = getQuadraticPoint(nextT, start, control, end);
      const trailAlpha = (0.12 + flightStrength * 0.12 + (emphasized ? 0.04 : 0)) * (trailIndex / trailSegments);
      ctx.strokeStyle = rgba(flightColor, trailAlpha * 0.38);
      ctx.lineWidth = (0.55 + flightStrength * 0.52 + (emphasized ? 0.2 : 0)) * (trailIndex / trailSegments);
      ctx.beginPath();
      ctx.moveTo(currentPoint.x, currentPoint.y);
      ctx.lineTo(nextPoint.x, nextPoint.y);
      ctx.stroke();
    }

    drawAircraft(
      ctx,
      planePos.x,
      planePos.y,
      planeAngle,
      0.46 + flightStrength * 0.22 + (emphasized ? 0.06 : 0),
      flightColor,
      0.5 + flightStrength * 0.22 + (emphasized ? 0.06 : 0)
    );
  }
};

const MixBar = ({ label, pct, color }) => (
  <div className="ge-mix-bar-row">
    <span className="ge-mix-label">{label}</span>
    <div className="ge-mix-bar-track">
      <div className="ge-mix-bar-fill" style={{ width: `${clamp(numeric(pct), 0, 100)}%`, background: color }} />
    </div>
    <span className="ge-mix-pct">{formatNumber(numeric(pct), 1)}%</span>
  </div>
);

const Stat = ({ label, value, unit }) => (
  <div className="ge-detail-stat">
    <p className="ge-detail-stat-label">{label}</p>
    <p className="ge-detail-stat-value">
      {value}
      {unit && <span className="ge-detail-stat-unit"> {unit}</span>}
    </p>
  </div>
);

const GlobalEmissions = () => {
  const canvasRef = useRef(null);
  const rot = useRef({ rx: 0.35, ry: -0.42 });
  const drag = useRef(null);
  const autoRot = useRef(true);
  const projCache = useRef([]);
  const sizeRef = useRef({ w: 800, h: 560 });
  const zoomRef = useRef(1);

  const [selected, setSelected] = useState(null);
  const [tooltip, setTooltip] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [viewMode, setViewMode] = useState('co2');
  const [query, setQuery] = useState('');

  const updateZoom = useCallback((nextZoom) => {
    const clamped = clamp(nextZoom, 0.82, 1.85);
    zoomRef.current = clamped;
    setZoomLevel(Number(clamped.toFixed(2)));
  }, []);

  const focusCountry = useCallback((country) => {
    setSelected(country);
    autoRot.current = false;
    rot.current = {
      rx: clamp(country.lat * 0.012, -0.92, 0.92),
      ry: -(country.lng + 90) * DEG,
    };
  }, []);

  const resetView = useCallback(() => {
    rot.current = { rx: 0.35, ry: -0.42 };
    autoRot.current = true;
    setSelected(null);
    updateZoom(1);
  }, [updateZoom]);

  const draw = useCallback((timeMs = 0) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const { w, h } = sizeRef.current;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(w, h) * 0.38 * zoomRef.current;
    const { rx, ry } = rot.current;

    drawBackdrop(ctx, w, h, timeMs);

    const halo = ctx.createRadialGradient(cx, cy, radius * 0.3, cx, cy, radius * 1.5);
    halo.addColorStop(0, 'rgba(255, 255, 255, 0)');
    halo.addColorStop(0.68, 'rgba(34, 197, 94, 0.045)');
    halo.addColorStop(1, 'rgba(59, 130, 246, 0)');
    ctx.fillStyle = halo;
    ctx.fillRect(0, 0, w, h);

    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    const ocean = ctx.createRadialGradient(cx - radius * 0.26, cy - radius * 0.28, radius * 0.18, cx, cy, radius * 1.08);
    ocean.addColorStop(0, '#20384a');
    ocean.addColorStop(0.44, '#101b22');
    ocean.addColorStop(1, '#06090d');
    ctx.fillStyle = ocean;
    ctx.fill();
    ctx.strokeStyle = 'rgba(203, 213, 225, 0.3)';
    ctx.lineWidth = 1.2;
    ctx.stroke();

    const atmosphere = ctx.createRadialGradient(cx, cy, radius * 0.92, cx, cy, radius * 1.12);
    atmosphere.addColorStop(0, 'rgba(255,255,255,0)');
    atmosphere.addColorStop(0.72, 'rgba(125,211,252,0.08)');
    atmosphere.addColorStop(1, 'rgba(34,211,238,0.3)');
    ctx.strokeStyle = atmosphere;
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.01, 0, Math.PI * 2);
    ctx.stroke();

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(timeMs * 0.00005);
    ctx.scale(1.16, 0.54);
    ctx.beginPath();
    ctx.setLineDash([8, 10]);
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(125, 211, 252, 0.16)';
    ctx.arc(0, 0, radius * 1.18, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
    ctx.setLineDash([]);

    ctx.lineWidth = 0.32;
    for (let lat = -75; lat <= 75; lat += 15) {
      ctx.beginPath();
      let started = false;
      for (let lng = 0; lng <= 360; lng += 2) {
        let [x, y, z] = latLngTo3D(lat, lng, radius);
        [x, y, z] = rotY(x, y, z, ry);
        [x, y, z] = rotX(x, y, z, rx);
        if (z < -10) {
          started = false;
          continue;
        }
        const [px, py] = project3D(x, y, z, cx, cy);
        const alpha = Math.max(0, (z + 10) / (radius + 10)) * 0.14;
        ctx.strokeStyle = `rgba(226, 232, 240, ${alpha})`;
        if (!started) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
        started = true;
      }
      ctx.stroke();
    }

    for (let lng = 0; lng < 360; lng += 15) {
      ctx.beginPath();
      let started = false;
      for (let lat = -90; lat <= 90; lat += 2) {
        let [x, y, z] = latLngTo3D(lat, lng, radius);
        [x, y, z] = rotY(x, y, z, ry);
        [x, y, z] = rotX(x, y, z, rx);
        if (z < -10) {
          started = false;
          continue;
        }
        const [px, py] = project3D(x, y, z, cx, cy);
        const alpha = Math.max(0, (z + 10) / (radius + 10)) * 0.1;
        ctx.strokeStyle = `rgba(226, 232, 240, ${alpha})`;
        if (!started) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
        started = true;
      }
      ctx.stroke();
    }

    LANDMASSES.forEach((continent) => {
      const points = [];
      let allOnFront = true;
      continent.coords.forEach(([lat, lng]) => {
        let [x, y, z] = latLngTo3D(lat, lng, radius);
        [x, y, z] = rotY(x, y, z, ry);
        [x, y, z] = rotX(x, y, z, rx);
        if (z > -10) {
          const [px, py] = project3D(x, y, z, cx, cy);
          points.push({ px, py, visible: true, z });
        } else {
          points.push({ px: 0, py: 0, visible: false, z });
          allOnFront = false;
        }
      });

      const visibleCount = points.filter((point) => point.visible).length;
      if (visibleCount <= 2) return;

      ctx.beginPath();
      let started = false;
      points.forEach((point) => {
        if (point.visible) {
          if (!started) ctx.moveTo(point.px, point.py);
          else ctx.lineTo(point.px, point.py);
          started = true;
        } else {
          started = false;
        }
      });
      if (allOnFront) {
        ctx.closePath();
        ctx.fillStyle = 'rgba(34, 197, 94, 0.105)';
        ctx.fill();
      }

      ctx.beginPath();
      started = false;
      points.forEach((point) => {
        if (point.visible) {
          if (!started) ctx.moveTo(point.px, point.py);
          else ctx.lineTo(point.px, point.py);
          started = true;
        } else {
          started = false;
        }
      });
      ctx.strokeStyle = 'rgba(226, 232, 240, 0.62)';
      ctx.lineWidth = 1.05;
      ctx.stroke();
    });

    const projected = COUNTRIES.map((country, index) => {
      let [x, y, z] = latLngTo3D(country.lat, country.lng, radius);
      [x, y, z] = rotY(x, y, z, ry);
      [x, y, z] = rotX(x, y, z, rx);
      const [px, py, scale] = project3D(x, y, z, cx, cy);
      return { px, py, visible: z > 0, idx: index, z, scale };
    });
    const visibleSorted = projected.filter((point) => point.visible).sort((a, b) => a.z - b.z);

    FLIGHT_CORRIDORS.forEach(([fromCode, toCode], index) => {
      const start = visibleSorted.find((point) => COUNTRIES[point.idx].code === fromCode);
      const end = visibleSorted.find((point) => COUNTRIES[point.idx].code === toCode);
      if (!start || !end) return;
      drawAmbientAircraft(ctx, start, end, index, timeMs, {
        traffic: index < 4 ? 2 : 1,
        showPath: false,
      });
    });

    visibleSorted.forEach((point) => {
      const country = COUNTRIES[point.idx];
      const nodeZoom = 0.82 + zoomRef.current * 0.26;
      const radiusPx = getNodeRadius(country, nodeZoom, viewMode) * point.scale;
      const color = getCountryColor(country, viewMode);
      const modeValue = getViewValue(country, viewMode);
      const isSelected = selected?.code === country.code;

      if (country.co2 > 120 || isSelected) {
        drawEmissionPlume(ctx, point.px, point.py, point.scale, country, timeMs, isSelected);
      }

      if (country.co2 > 300 || modeValue > 0.72 || isSelected) {
        const pulseCount = country.co2 > 3000 ? 3 : country.co2 > 1000 || modeValue > 0.84 ? 2 : 1;
        for (let r = 0; r < pulseCount; r += 1) {
          const pulsePhase = (timeMs * 0.0006 + r * (1 / pulseCount) + point.idx * 0.1) % 1;
          const pulseRadius = radiusPx * (2.1 + pulsePhase * 3.1);
          const pulseAlpha = (0.09 + (isSelected ? 0.06 : 0)) * (1 - pulsePhase);
          ctx.strokeStyle = rgba(color, pulseAlpha);
          ctx.lineWidth = 1.2 - pulsePhase * 0.8;
          ctx.beginPath();
          ctx.arc(point.px, point.py, pulseRadius, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      const glow = ctx.createRadialGradient(point.px, point.py, 0, point.px, point.py, radiusPx * (isSelected ? 4.8 : 2.8));
      glow.addColorStop(0, rgba(color, isSelected ? 0.5 : 0.28));
      glow.addColorStop(0.65, rgba(color, isSelected ? 0.12 : 0.08));
      glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(point.px, point.py, radiusPx * (isSelected ? 4.8 : 2.8), 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = rgba(color, isSelected ? 1 : 0.9);
      ctx.beginPath();
      ctx.arc(point.px, point.py, isSelected ? radiusPx * 1.45 : radiusPx, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = `rgba(255,255,255,${isSelected ? 0.95 : clamp(0.22 + modeValue * 0.38, 0.2, 0.52)})`;
      ctx.lineWidth = isSelected ? 1.8 : 0.75;
      ctx.beginPath();
      ctx.arc(point.px, point.py, radiusPx + 2.2, 0, Math.PI * 2);
      ctx.stroke();

      if (isSelected || (COUNTRY_LABEL_CODES.has(country.code) && point.scale > 0.62)) {
        ctx.fillStyle = 'rgba(248,250,252,0.86)';
        ctx.font = `${isSelected ? '700' : '600'} ${isSelected ? 11 : 9}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText(isSelected ? country.name : country.code, point.px, point.py - radiusPx - (isSelected ? 11 : 9));
      }
    });

    projCache.current = projected;

    const activeMode = VIEW_MODES.find((mode) => mode.id === viewMode);
    ctx.textAlign = 'left';
    ctx.fillStyle = 'rgba(226,232,240,0.52)';
    ctx.font = '700 8px monospace';
    ctx.fillText(`SCARI GLOBAL FIELD - ${activeMode?.label.toUpperCase() || 'CO2'}`, 16, 22);
    ctx.fillStyle = 'rgba(226,232,240,0.38)';
    ctx.font = '8px monospace';
    ctx.fillText(`${COUNTRIES.length} countries - CO2 ${GLOBAL_BASELINES.co2Year}; electricity ${GLOBAL_BASELINES.electricityYear}`, 16, 35);
    ctx.textAlign = 'right';
    ctx.fillStyle = 'rgba(226,232,240,0.36)';
    ctx.fillText(`Zoom ${Math.round(zoomRef.current * 100)}%`, w - 16, h - 14);

    ctx.textAlign = 'left';
    const legendY = h - 18;
    [
      [[56, 189, 248], 'low'],
      [[250, 204, 21], 'mid'],
      [[248, 113, 113], 'high'],
      [[45, 212, 191], 'plane'],
    ].forEach(([color, label], index) => {
      const x = 16 + index * 70;
      ctx.fillStyle = rgb(color);
      ctx.beginPath();
      ctx.arc(x, legendY, 3.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = 'rgba(226,232,240,0.42)';
      ctx.font = '8px sans-serif';
      ctx.fillText(label, x + 8, legendY + 3);
    });
  }, [selected, viewMode]);

  useEffect(() => {
    let raf;
    const loop = (time) => {
      if (autoRot.current && !drag.current) rot.current.ry += 0.0014;
      draw(time);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [draw]);

  useEffect(() => {
    const element = canvasRef.current?.parentElement;
    if (!element) return undefined;
    const observer = new ResizeObserver((entries) => {
      entries.forEach((entry) => {
        sizeRef.current = {
          w: Math.max(320, entry.contentRect.width),
          h: Math.max(500, entry.contentRect.height),
        };
      });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const handleDown = useCallback((event) => {
    autoRot.current = false;
    const rect = canvasRef.current.getBoundingClientRect();
    drag.current = { x: event.clientX - rect.left, y: event.clientY - rect.top, moved: false };
    setIsDragging(true);
  }, []);

  const handleMove = useCallback((event) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = event.clientX - rect.left;
    const my = event.clientY - rect.top;

    if (drag.current) {
      const dx = mx - drag.current.x;
      const dy = my - drag.current.y;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.current.moved = true;
      rot.current.ry += dx * 0.005;
      rot.current.rx = clamp(rot.current.rx + dy * 0.005, -1.2, 1.2);
      drag.current.x = mx;
      drag.current.y = my;
      setTooltip(null);
      return;
    }

    let found = -1;
    for (const point of projCache.current) {
      if (!point.visible) continue;
      const country = COUNTRIES[point.idx];
      const hitRadius = getNodeRadius(country, 0.82 + zoomRef.current * 0.26, viewMode) * point.scale + 5;
      if (Math.sqrt((mx - point.px) ** 2 + (my - point.py) ** 2) < hitRadius) {
        found = point.idx;
        break;
      }
    }

    if (found >= 0) {
      const country = COUNTRIES[found];
      const metric = getMetricForMode(country, viewMode);
      setTooltip({
        x: mx + 14,
        y: my - 10,
        name: `${getCountryFlag(country)} ${country.name}`,
        metricLabel: metric.label,
        metricValue: metric.value,
        renewables: getRenewableShare(country),
      });
    } else {
      setTooltip(null);
    }
  }, [viewMode]);

  const handleUp = useCallback(() => {
    drag.current = null;
    setIsDragging(false);
    setTimeout(() => {
      if (!drag.current) autoRot.current = true;
    }, 4500);
  }, []);

  const handleWheel = useCallback((event) => {
    event.preventDefault();
    autoRot.current = false;
    updateZoom(zoomRef.current - event.deltaY * 0.0012);
  }, [updateZoom]);

  const handleClick = useCallback((event) => {
    if (drag.current?.moved) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = event.clientX - rect.left;
    const my = event.clientY - rect.top;
    for (const point of projCache.current) {
      if (!point.visible) continue;
      const country = COUNTRIES[point.idx];
      const hitRadius = getNodeRadius(country, 0.82 + zoomRef.current * 0.26, viewMode) * point.scale + 5;
      if (Math.sqrt((mx - point.px) ** 2 + (my - point.py) ** 2) < hitRadius) {
        setSelected(country);
        return;
      }
    }
    setSelected(null);
  }, [viewMode]);

  const topRenewable = useMemo(() => [...COUNTRIES].sort((a, b) => getLowCarbonShare(b) - getLowCarbonShare(a))[0], []);
  const topEmitter = useMemo(() => [...COUNTRIES].sort((a, b) => b.co2 - a.co2)[0], []);
  const lowestIntensity = useMemo(() => (
    [...COUNTRIES].filter((country) => country.energy > 30).sort((a, b) => getEmissionIntensity(a) - getEmissionIntensity(b))[0]
  ), []);
  const topEmitterList = useMemo(() => [...COUNTRIES].sort((a, b) => b.co2 - a.co2).slice(0, 6), []);
  const cleanLeaders = useMemo(() => (
    [...COUNTRIES].filter((country) => country.energy > 30).sort((a, b) => getEmissionIntensity(a) - getEmissionIntensity(b)).slice(0, 5)
  ), []);
  const filteredCountries = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const matches = normalizedQuery
      ? COUNTRIES.filter((country) => (
        country.name.toLowerCase().includes(normalizedQuery)
        || country.code.toLowerCase().includes(normalizedQuery)
        || country.iso3.toLowerCase().includes(normalizedQuery)
        || country.region.toLowerCase().includes(normalizedQuery)
      ))
      : [...COUNTRIES];

    return matches
      .sort((a, b) => getViewValue(b, viewMode) - getViewValue(a, viewMode))
      .slice(0, 8);
  }, [query, viewMode]);

  const totalTrackedCo2 = useMemo(() => COUNTRIES.reduce((sum, country) => sum + country.co2, 0), []);
  const totalTrackedEnergy = useMemo(() => COUNTRIES.reduce((sum, country) => sum + country.energy, 0), []);
  const averageLowCarbon = useMemo(() => (
    COUNTRIES.reduce((sum, country) => sum + getLowCarbonShare(country), 0) / COUNTRIES.length
  ), []);

  const selectedMetric = selected ? getMetricForMode(selected, viewMode) : null;

  return (
    <div className="ge-container">
      <div className="ge-map-section">
        <div className="ge-map-title-overlay">
          <h3>SCARI Global Carbon Field</h3>
          <p>Territorial CO2, electricity mix, intensity and grid signals for sustainable infrastructure planning.</p>
        </div>

        <div className="ge-map-topbar">
          <div className="ge-map-chip">
            <span className="ge-chip-label">Tracked CO2</span>
            <strong>{formatNumber(totalTrackedCo2 / 1000, 1)} Gt</strong>
            <span>{formatNumber((totalTrackedCo2 / GLOBAL_BASELINES.co2Mt) * 100, 0)}% of global {GLOBAL_BASELINES.co2Year}</span>
          </div>
          <div className="ge-map-chip">
            <span className="ge-chip-label">Electricity</span>
            <strong>{formatNumber(totalTrackedEnergy / 1000, 1)} PWh</strong>
            <span>{formatNumber((totalTrackedEnergy / GLOBAL_BASELINES.electricityTwh) * 100, 0)}% of global {GLOBAL_BASELINES.electricityYear}</span>
          </div>
          <div className="ge-map-chip">
            <span className="ge-chip-label">Cleanest mix</span>
            <strong>{topRenewable.name}</strong>
            <span>{formatNumber(getLowCarbonShare(topRenewable), 0)}% low-carbon</span>
          </div>
        </div>

        <div className="ge-map-toolbar">
          <div className="ge-mode-switch" aria-label="Map layer">
            {VIEW_MODES.map(({ id, label, Icon: ModeIcon }) => (
              <button
                key={id}
                type="button"
                className={`ge-mode-btn ${viewMode === id ? 'active' : ''}`}
                onClick={() => setViewMode(id)}
                title={label}
              >
                {React.createElement(ModeIcon, { size: 14 })}
                <span>{label}</span>
              </button>
            ))}
          </div>
          <div className="ge-control-stack" aria-label="Map controls">
            <button type="button" className="ge-control-btn" onClick={() => updateZoom(zoomRef.current + 0.12)} aria-label="Zoom in" title="Zoom in">
              <Plus size={14} />
            </button>
            <button type="button" className="ge-control-btn" onClick={() => updateZoom(zoomRef.current - 0.12)} aria-label="Zoom out" title="Zoom out">
              <Minus size={14} />
            </button>
            <button type="button" className="ge-control-btn" onClick={resetView} aria-label="Reset view" title="Reset view">
              <RotateCcw size={14} />
            </button>
          </div>
          <span className="ge-zoom-readout">{Math.round(zoomLevel * 100)}%</span>
        </div>

        <div className="ge-map-canvas-wrap">
          <canvas
            ref={canvasRef}
            style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
            onMouseDown={handleDown}
            onMouseMove={handleMove}
            onMouseUp={handleUp}
            onWheel={handleWheel}
            onMouseLeave={() => {
              drag.current = null;
              setIsDragging(false);
              setTooltip(null);
            }}
            onClick={handleClick}
          />
        </div>

        <div className="ge-side-panel">
          <div className="ge-rail-card ge-search-card">
            <p className="ge-rail-title"><Search size={12} /> Country Explorer</p>
            <div className="ge-search-field">
              <Search size={13} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Country, code or region"
                aria-label="Search countries"
              />
            </div>
            <div className="ge-country-results">
              {filteredCountries.map((country) => {
                const metric = getMetricForMode(country, viewMode);
                return (
                  <button
                    key={country.code}
                    className={`ge-rail-item ${selected?.code === country.code ? 'active' : ''}`}
                    onClick={() => focusCountry(country)}
                  >
                    <span>{getCountryFlag(country)} {country.name}</span>
                    <span>{metric.value}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="ge-rail-card">
            <p className="ge-rail-title"><Zap size={12} /> Largest Emitters</p>
            {topEmitterList.map((country) => (
              <button
                key={country.code}
                className={`ge-rail-item ${selected?.code === country.code ? 'active' : ''}`}
                onClick={() => focusCountry(country)}
              >
                <span>{getCountryFlag(country)} {country.name}</span>
                <span>{formatNumber(country.co2, 0)} Mt</span>
              </button>
            ))}
          </div>

          <div className="ge-rail-card">
            <p className="ge-rail-title"><Gauge size={12} /> Lowest Intensity</p>
            {cleanLeaders.map((country) => (
              <button
                key={country.code}
                className={`ge-rail-item ge-clean ${selected?.code === country.code ? 'active' : ''}`}
                onClick={() => focusCountry(country)}
              >
                <span>{getCountryFlag(country)} {country.name}</span>
                <span>{formatNumber(getEmissionIntensity(country), 2)}</span>
              </button>
            ))}
          </div>

        </div>

        <div className="ge-map-footer-overlay">
          <span className="ge-map-hint">{DATA_SOURCES.co2}. Aircraft are visual motion only.</span>
          <div className="ge-map-mini-legend">
            <span className="ge-legend-pill"><span className="ge-legend-dot ge-legend-node" />Country node</span>
            <span className="ge-legend-pill"><span className="ge-legend-dot ge-legend-plume" />CO2 plume</span>
            <span className="ge-legend-pill"><span className="ge-legend-dot ge-legend-flight" />Animated aircraft</span>
            <span className="ge-legend-pill"><span className="ge-legend-dot ge-legend-ring" />Orbit</span>
          </div>
        </div>

        {tooltip && (
          <div className="ge-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
            <span className="ge-tooltip-name">{tooltip.name}</span>
            <span>{tooltip.metricLabel}: {tooltip.metricValue}</span>
            <span>{formatNumber(tooltip.renewables, 0)}% renewables</span>
          </div>
        )}

        {selected && (
          <div className="ge-detail-overlay">
            <div className="ge-detail-header">
              <div>
                <span className="ge-detail-flag">{getCountryFlag(selected)}</span>
                <p className="ge-detail-country">{selected.name}</p>
                <span className="ge-detail-meta">{selected.region}</span>
              </div>
              <button className="ge-detail-close" onClick={() => setSelected(null)} aria-label="Close country detail">
                <X size={14} />
              </button>
            </div>

            <div className="ge-mode-readout">
              <Layers size={14} />
              <span>{selectedMetric.label}</span>
              <strong>{selectedMetric.value}</strong>
            </div>

            <hr className="ge-detail-divider" />
            <p className="ge-detail-section-title">Key Metrics</p>
            <div className="ge-detail-stat-grid">
              <Stat label="CO2 emissions" value={formatNumber(selected.co2, 1)} unit="Mt" />
              <Stat label="Electricity" value={formatNumber(selected.energy, 1)} unit="TWh" />
              <Stat label="Population" value={formatNumber(selected.pop, 1)} unit="M" />
              <Stat label="GDP PPP" value={selected.gdp ? `$${formatNumber(selected.gdp, 0)}` : 'n/a'} unit={selected.gdp ? 'B' : ''} />
              <Stat label="CO2 / capita" value={formatNumber(getCo2PerCapita(selected), 1)} unit="t" />
              <Stat label="CO2 / GDP" value={getCo2PerGdp(selected) ? formatNumber(getCo2PerGdp(selected), 0) : 'n/a'} unit={getCo2PerGdp(selected) ? 't/$M' : ''} />
              <Stat label="Low-carbon mix" value={formatNumber(getLowCarbonShare(selected), 1)} unit="%" />
              <Stat label="Fossil mix" value={formatNumber(getFossilShare(selected), 1)} unit="%" />
            </div>

            <hr className="ge-detail-divider" />
            <p className="ge-detail-section-title">Electricity Mix</p>
            {MIX_KEYS.map((key) => (
              <MixBar key={key} label={key[0].toUpperCase() + key.slice(1)} pct={selected[key]} color={MIX_COLORS[key]} />
            ))}

            <hr className="ge-detail-divider" />
            <p className="ge-detail-section-title">Data Freshness</p>
            <div className="ge-source-grid">
              <span>CO2 {selected.co2Year}</span>
              <span>Electricity {selected.energyYear}</span>
              <span>Mix {selected.mixYear}</span>
              <span>Population {selected.popYear}</span>
              <span>{selected.gdpYear ? `GDP ${selected.gdpYear}` : 'GDP n/a'}</span>
            </div>
          </div>
        )}
      </div>

      <div className="ge-stats-row">
        <div className="ge-stat-card"><span className="ge-stat-card-label">Countries Tracked</span><span className="ge-stat-card-value">{COUNTRIES.length}</span><span className="ge-stat-card-sub">Expanded country panel</span></div>
        <div className="ge-stat-card"><span className="ge-stat-card-label">Total CO2 Tracked</span><span className="ge-stat-card-value">{formatNumber(totalTrackedCo2 / 1000, 1)} Gt</span><span className="ge-stat-card-sub">{formatNumber((totalTrackedCo2 / GLOBAL_BASELINES.co2Mt) * 100, 0)}% of global {GLOBAL_BASELINES.co2Year}</span></div>
        <div className="ge-stat-card"><span className="ge-stat-card-label">Total Electricity</span><span className="ge-stat-card-value">{formatNumber(totalTrackedEnergy / 1000, 1)} PWh</span><span className="ge-stat-card-sub">{formatNumber((totalTrackedEnergy / GLOBAL_BASELINES.electricityTwh) * 100, 0)}% of global {GLOBAL_BASELINES.electricityYear}</span></div>
        <div className="ge-stat-card"><span className="ge-stat-card-label">Top Emitter</span><span className="ge-stat-card-value">{topEmitter.name}</span><span className="ge-stat-card-sub">{formatNumber(topEmitter.co2, 0)} Mt CO2</span></div>
        <div className="ge-stat-card"><span className="ge-stat-card-label">Lowest Intensity</span><span className="ge-stat-card-value">{lowestIntensity.name}</span><span className="ge-stat-card-sub">{formatNumber(getEmissionIntensity(lowestIntensity), 2)} Mt/TWh</span></div>
        <div className="ge-stat-card"><span className="ge-stat-card-label">Avg. Low Carbon</span><span className="ge-stat-card-value">{formatNumber(averageLowCarbon, 1)}%</span><span className="ge-stat-card-sub">Mean across tracked countries</span></div>
      </div>

      <div className="ge-source-note">
        <span>{DATA_SOURCES.electricity}</span>
        <span>{DATA_SOURCES.population}</span>
        <span>{DATA_SOURCES.gdp}</span>
      </div>
    </div>
  );
};

export default GlobalEmissions;
