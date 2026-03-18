import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Minus, Plus, RotateCcw, X } from 'lucide-react';
import { ALL_CONTINENTS } from './continents';
import './GlobalEmissions.css';
const COUNTRIES = [
    { code: "CN", name: "China", flag: "🇨🇳", lat: 35.86, lng: 104.20, co2: 11477, energy: 8849, coal: 60.8, gas: 8.3, oil: 0.6, nuclear: 4.9, hydro: 14.5, wind: 8.5, solar: 4.8, other: 0.6, pop: 1412, gdp: 17963 },
    { code: "US", name: "United States", flag: "🇺🇸", lat: 37.09, lng: -95.71, co2: 4853, energy: 4178, coal: 16.2, gas: 43.1, oil: 0.5, nuclear: 18.6, hydro: 5.9, wind: 10.2, solar: 5.6, other: 1.9, pop: 335, gdp: 26949 },
    { code: "IN", name: "India", flag: "🇮🇳", lat: 20.59, lng: 78.96, co2: 2830, energy: 1858, coal: 74.3, gas: 4.3, oil: 0.5, nuclear: 3.1, hydro: 10.2, wind: 4.6, solar: 5.5, other: 0.5, pop: 1417, gdp: 3737 },
    { code: "RU", name: "Russia", flag: "🇷🇺", lat: 61.52, lng: 105.32, co2: 1764, energy: 1166, coal: 15.8, gas: 47.2, oil: 0.9, nuclear: 19.6, hydro: 17.0, wind: 0.3, solar: 0.4, other: 0.8, pop: 144, gdp: 1862 },
    { code: "JP", name: "Japan", flag: "🇯🇵", lat: 36.20, lng: 138.25, co2: 1067, energy: 989, coal: 30.8, gas: 34.5, oil: 4.4, nuclear: 8.5, hydro: 7.5, wind: 3.0, solar: 10.3, other: 4.0, pop: 125, gdp: 4231 },
    { code: "DE", name: "Germany", flag: "🇩🇪", lat: 51.17, lng: 10.45, co2: 584, energy: 511, coal: 26.1, gas: 14.7, oil: 0.8, nuclear: 0.0, hydro: 3.1, wind: 27.4, solar: 12.4, other: 15.5, pop: 83, gdp: 4456 },
    { code: "KR", name: "South Korea", flag: "🇰🇷", lat: 35.91, lng: 127.77, co2: 586, energy: 594, coal: 33.6, gas: 30.1, oil: 1.1, nuclear: 29.6, hydro: 0.7, wind: 0.9, solar: 5.2, other: 0.8, pop: 52, gdp: 1713 },
    { code: "CA", name: "Canada", flag: "🇨🇦", lat: 56.13, lng: -106.35, co2: 540, energy: 648, coal: 4.8, gas: 15.2, oil: 0.5, nuclear: 13.5, hydro: 58.7, wind: 5.8, solar: 0.7, other: 0.8, pop: 40, gdp: 2139 },
    { code: "SA", name: "Saudi Arabia", flag: "🇸🇦", lat: 23.89, lng: 45.08, co2: 586, energy: 394, coal: 0.0, gas: 39.5, oil: 58.2, nuclear: 0.0, hydro: 0.0, wind: 0.2, solar: 2.1, other: 0.0, pop: 36, gdp: 1069 },
    { code: "BR", name: "Brazil", flag: "🇧🇷", lat: -14.24, lng: -51.93, co2: 457, energy: 688, coal: 2.8, gas: 9.2, oil: 1.9, nuclear: 2.3, hydro: 63.5, wind: 12.8, solar: 5.0, other: 2.5, pop: 215, gdp: 2127 },
    { code: "GB", name: "United Kingdom", flag: "🇬🇧", lat: 55.38, lng: -3.44, co2: 317, energy: 299, coal: 1.3, gas: 38.5, oil: 0.4, nuclear: 14.2, hydro: 2.3, wind: 29.4, solar: 4.3, other: 9.6, pop: 67, gdp: 3332 },
    { code: "FR", name: "France", flag: "🇫🇷", lat: 46.23, lng: 2.21, co2: 285, energy: 474, coal: 0.8, gas: 8.9, oil: 0.5, nuclear: 64.8, hydro: 11.3, wind: 10.2, solar: 4.5, other: 1.0, pop: 68, gdp: 3049 },
    { code: "AU", name: "Australia", flag: "🇦🇺", lat: -25.27, lng: 133.78, co2: 381, energy: 265, coal: 42.7, gas: 19.5, oil: 1.4, nuclear: 0.0, hydro: 5.5, wind: 12.4, solar: 15.2, other: 3.3, pop: 26, gdp: 1693 },
    { code: "IT", name: "Italy", flag: "🇮🇹", lat: 41.87, lng: 12.57, co2: 304, energy: 275, coal: 4.7, gas: 46.5, oil: 2.8, nuclear: 0.0, hydro: 11.3, wind: 7.5, solar: 9.9, other: 17.3, pop: 60, gdp: 2186 },
    { code: "MX", name: "Mexico", flag: "🇲🇽", lat: 23.63, lng: -102.55, co2: 420, energy: 326, coal: 4.3, gas: 60.5, oil: 6.9, nuclear: 3.6, hydro: 9.1, wind: 6.8, solar: 6.5, other: 2.3, pop: 130, gdp: 1414 },
    { code: "ID", name: "Indonesia", flag: "🇮🇩", lat: -0.79, lng: 113.92, co2: 619, energy: 317, coal: 60.9, gas: 18.1, oil: 2.5, nuclear: 0.0, hydro: 6.9, wind: 0.2, solar: 0.4, other: 11.0, pop: 275, gdp: 1319 },
    { code: "ZA", name: "South Africa", flag: "🇿🇦", lat: -30.56, lng: 22.94, co2: 435, energy: 239, coal: 82.6, gas: 3.1, oil: 0.4, nuclear: 4.6, hydro: 1.2, wind: 5.8, solar: 2.3, other: 0.0, pop: 60, gdp: 399 },
    { code: "PL", name: "Poland", flag: "🇵🇱", lat: 51.92, lng: 19.15, co2: 287, energy: 163, coal: 62.6, gas: 7.5, oil: 1.1, nuclear: 0.0, hydro: 1.5, wind: 13.8, solar: 5.2, other: 8.3, pop: 38, gdp: 811 },
    { code: "TR", name: "Turkey", flag: "🇹🇷", lat: 38.96, lng: 35.24, co2: 371, energy: 333, coal: 33.5, gas: 22.3, oil: 0.3, nuclear: 0.0, hydro: 19.8, wind: 10.6, solar: 5.9, other: 7.6, pop: 85, gdp: 1108 },
    { code: "ES", name: "Spain", flag: "🇪🇸", lat: 40.46, lng: -3.75, co2: 220, energy: 268, coal: 1.4, gas: 28.4, oil: 1.1, nuclear: 20.3, hydro: 9.5, wind: 22.4, solar: 14.5, other: 2.4, pop: 48, gdp: 1580 },
    { code: "TH", name: "Thailand", flag: "🇹🇭", lat: 15.87, lng: 100.99, co2: 269, energy: 195, coal: 18.0, gas: 56.7, oil: 0.5, nuclear: 0.0, hydro: 4.0, wind: 2.5, solar: 3.6, other: 14.7, pop: 72, gdp: 515 },
    { code: "EG", name: "Egypt", flag: "🇪🇬", lat: 26.82, lng: 30.80, co2: 235, energy: 209, coal: 0.0, gas: 76.8, oil: 9.9, nuclear: 0.0, hydro: 6.1, wind: 4.1, solar: 2.7, other: 0.4, pop: 105, gdp: 404 },
    { code: "AR", name: "Argentina", flag: "🇦🇷", lat: -38.42, lng: -63.62, co2: 162, energy: 150, coal: 1.0, gas: 55.4, oil: 6.5, nuclear: 5.5, hydro: 18.2, wind: 9.0, solar: 3.4, other: 1.0, pop: 46, gdp: 641 },
    { code: "NO", name: "Norway", flag: "🇳🇴", lat: 60.47, lng: 8.47, co2: 33, energy: 156, coal: 0.1, gas: 2.5, oil: 0.1, nuclear: 0.0, hydro: 88.2, wind: 8.6, solar: 0.1, other: 0.4, pop: 5, gdp: 579 },
    { code: "SE", name: "Sweden", flag: "🇸🇪", lat: 60.13, lng: 18.64, co2: 32, energy: 163, coal: 0.3, gas: 1.0, oil: 0.2, nuclear: 29.4, hydro: 40.8, wind: 19.5, solar: 1.5, other: 7.3, pop: 10, gdp: 589 },
    { code: "NG", name: "Nigeria", flag: "🇳🇬", lat: 9.08, lng: 8.68, co2: 92, energy: 35, coal: 0.0, gas: 79.8, oil: 0.0, nuclear: 0.0, hydro: 18.3, wind: 0.0, solar: 0.2, other: 1.7, pop: 218, gdp: 472 },
    { code: "AE", name: "UAE", flag: "🇦🇪", lat: 23.42, lng: 53.85, co2: 190, energy: 174, coal: 0.5, gas: 95.4, oil: 0.2, nuclear: 3.9, hydro: 0.0, wind: 0.0, solar: 4.0, other: 0.0, pop: 10, gdp: 509 },
    { code: "CL", name: "Chile", flag: "🇨🇱", lat: -35.68, lng: -71.54, co2: 83, energy: 87, coal: 14.2, gas: 16.3, oil: 4.5, nuclear: 0.0, hydro: 24.8, wind: 14.5, solar: 20.2, other: 5.5, pop: 20, gdp: 335 },
    { code: "PK", name: "Pakistan", flag: "🇵🇰", lat: 30.38, lng: 69.35, co2: 220, energy: 145, coal: 15.2, gas: 36.4, oil: 5.5, nuclear: 8.5, hydro: 27.2, wind: 3.0, solar: 2.0, other: 2.2, pop: 230, gdp: 376 },
    { code: "NZ", name: "New Zealand", flag: "🇳🇿", lat: -40.90, lng: 174.89, co2: 30, energy: 44, coal: 2.3, gas: 13.0, oil: 0.2, nuclear: 0.0, hydro: 56.0, wind: 7.0, solar: 1.1, other: 20.4, pop: 5, gdp: 247 },
    { code: "MY", name: "Malaysia", flag: "🇲🇾", lat: 4.21, lng: 101.98, co2: 248, energy: 180, coal: 28.5, gas: 47.5, oil: 1.0, nuclear: 0.0, hydro: 18.5, wind: 0.0, solar: 2.8, other: 1.7, pop: 33, gdp: 408 },
    { code: "VN", name: "Vietnam", flag: "🇻🇳", lat: 14.06, lng: 108.28, co2: 282, energy: 266, coal: 45.8, gas: 12.2, oil: 1.0, nuclear: 0.0, hydro: 29.0, wind: 3.0, solar: 5.5, other: 3.5, pop: 99, gdp: 408 },
    { code: "PH", name: "Philippines", flag: "🇵🇭", lat: 12.88, lng: 121.77, co2: 153, energy: 109, coal: 47.0, gas: 21.0, oil: 2.5, nuclear: 0.0, hydro: 10.0, wind: 3.0, solar: 4.0, other: 12.5, pop: 115, gdp: 435 },
    { code: "BD", name: "Bangladesh", flag: "🇧🇩", lat: 23.68, lng: 90.36, co2: 96, energy: 93, coal: 5.0, gas: 80.0, oil: 5.0, nuclear: 0.0, hydro: 1.5, wind: 0.1, solar: 1.0, other: 7.4, pop: 170, gdp: 460 },
    { code: "UA", name: "Ukraine", flag: "🇺🇦", lat: 48.38, lng: 31.17, co2: 106, energy: 119, coal: 19.0, gas: 9.0, oil: 0.5, nuclear: 55.0, hydro: 6.0, wind: 3.5, solar: 4.0, other: 3.0, pop: 38, gdp: 179 },
    { code: "KZ", name: "Kazakhstan", flag: "🇰🇿", lat: 48.02, lng: 66.92, co2: 200, energy: 112, coal: 66.5, gas: 22.0, oil: 2.0, nuclear: 0.0, hydro: 8.0, wind: 1.2, solar: 0.6, other: 0.0, pop: 19, gdp: 260 },
    { code: "FI", name: "Finland", flag: "🇫🇮", lat: 61.92, lng: 25.75, co2: 33, energy: 78, coal: 3.0, gas: 4.0, oil: 0.3, nuclear: 33.0, hydro: 22.0, wind: 17.0, solar: 0.5, other: 20.2, pop: 6, gdp: 300 },
    { code: "DK", name: "Denmark", flag: "🇩🇰", lat: 56.26, lng: 9.50, co2: 22, energy: 34, coal: 5.0, gas: 7.0, oil: 0.5, nuclear: 0.0, hydro: 0.1, wind: 55.0, solar: 7.5, other: 24.9, pop: 6, gdp: 401 },
    { code: "IS", name: "Iceland", flag: "🇮🇸", lat: 64.96, lng: -19.02, co2: 2, energy: 19, coal: 0.0, gas: 0.0, oil: 0.1, nuclear: 0.0, hydro: 70.0, wind: 0.1, solar: 0.0, other: 29.8, pop: 0.4, gdp: 31 },
    { code: "PT", name: "Portugal", flag: "🇵🇹", lat: 39.40, lng: -8.22, co2: 36, energy: 50, coal: 0.0, gas: 22.0, oil: 1.5, nuclear: 0.0, hydro: 25.0, wind: 25.5, solar: 7.0, other: 19.0, pop: 10, gdp: 277 },
    { code: "AT", name: "Austria", flag: "🇦🇹", lat: 47.52, lng: 14.55, co2: 55, energy: 67, coal: 1.5, gas: 14.0, oil: 0.5, nuclear: 0.0, hydro: 55.0, wind: 11.0, solar: 5.0, other: 13.0, pop: 9, gdp: 516 },
    { code: "CH", name: "Switzerland", flag: "🇨🇭", lat: 46.82, lng: 8.23, co2: 31, energy: 60, coal: 0.0, gas: 3.0, oil: 0.3, nuclear: 32.0, hydro: 56.0, wind: 0.4, solar: 6.5, other: 1.8, pop: 9, gdp: 860 },
    { code: "IL", name: "Israel", flag: "🇮🇱", lat: 31.05, lng: 34.85, co2: 66, energy: 77, coal: 16.0, gas: 62.0, oil: 1.0, nuclear: 0.0, hydro: 0.0, wind: 0.5, solar: 10.5, other: 10.0, pop: 10, gdp: 525 },
    { code: "IE", name: "Ireland", flag: "🇮🇪", lat: 53.14, lng: -7.69, co2: 33, energy: 34, coal: 1.0, gas: 49.0, oil: 1.5, nuclear: 0.0, hydro: 3.0, wind: 34.0, solar: 1.0, other: 10.5, pop: 5, gdp: 504 },
    { code: "BE", name: "Belgium", flag: "🇧🇪", lat: 50.50, lng: 4.47, co2: 87, energy: 80, coal: 0.5, gas: 26.0, oil: 0.3, nuclear: 41.0, hydro: 0.5, wind: 13.0, solar: 6.5, other: 12.2, pop: 12, gdp: 624 },
    { code: "NL", name: "Netherlands", flag: "🇳🇱", lat: 52.13, lng: 5.29, co2: 137, energy: 113, coal: 8.0, gas: 40.0, oil: 0.5, nuclear: 3.0, hydro: 0.1, wind: 17.0, solar: 6.0, other: 25.4, pop: 18, gdp: 1092 },
    { code: "CZ", name: "Czech Republic", flag: "🇨🇿", lat: 49.82, lng: 15.47, co2: 92, energy: 73, coal: 39.0, gas: 8.0, oil: 0.3, nuclear: 37.0, hydro: 2.5, wind: 1.5, solar: 4.0, other: 7.7, pop: 11, gdp: 330 },
    { code: "CO", name: "Colombia", flag: "🇨🇴", lat: 4.57, lng: -74.30, co2: 80, energy: 82, coal: 6.0, gas: 16.0, oil: 3.0, nuclear: 0.0, hydro: 68.0, wind: 0.5, solar: 2.5, other: 4.0, pop: 52, gdp: 344 },
    { code: "PE", name: "Peru", flag: "🇵🇪", lat: -9.19, lng: -75.02, co2: 52, energy: 58, coal: 1.0, gas: 36.0, oil: 5.0, nuclear: 0.0, hydro: 48.0, wind: 3.0, solar: 3.5, other: 3.5, pop: 34, gdp: 242 },
    { code: "KE", name: "Kenya", flag: "🇰🇪", lat: -0.02, lng: 37.91, co2: 18, energy: 13, coal: 0.0, gas: 0.0, oil: 11.0, nuclear: 0.0, hydro: 30.0, wind: 15.0, solar: 2.0, other: 42.0, pop: 54, gdp: 113 },
    { code: "MA", name: "Morocco", flag: "🇲🇦", lat: 31.79, lng: -7.09, co2: 72, energy: 42, coal: 38.0, gas: 10.0, oil: 6.0, nuclear: 0.0, hydro: 4.0, wind: 16.0, solar: 5.0, other: 21.0, pop: 37, gdp: 142 },
];
const TOTAL_GLOBAL_CO2 = COUNTRIES.reduce((s, c) => s + c.co2, 0);
const TOTAL_GLOBAL_ENERGY = COUNTRIES.reduce((s, c) => s + c.energy, 0);
const DEG = Math.PI / 180;
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const latLngTo3D = (lat, lng, R) => {
    const phi = (90 - lat) * DEG, theta = (lng + 180) * DEG;
    return [-R * Math.sin(phi) * Math.cos(theta), R * Math.cos(phi), R * Math.sin(phi) * Math.sin(theta)];
};
const rotY = (x, y, z, a) => [x * Math.cos(a) + z * Math.sin(a), y, -x * Math.sin(a) + z * Math.cos(a)];
const rotX = (x, y, z, a) => [x, y * Math.cos(a) - z * Math.sin(a), y * Math.sin(a) + z * Math.cos(a)];
const proj = (x, y, z, cx, cy) => { const f = 860 / (860 + z); return [cx + x * f, cy - y * f, f, z]; };
const dotR = (co2, zoom = 1) => (2.4 + Math.sqrt(co2 / 12000) * 8.8) * zoom;
const renewCol = (country) => {
    const renewable = country.hydro + country.wind + country.solar + (country.other || 0);
    const luminance = Math.round(138 + clamp(renewable, 0, 80) * 1.25);
    return [luminance, luminance, luminance];
};
const COUNTRY_LABEL_CODES = new Set(['CN', 'US', 'IN', 'RU', 'JP', 'DE', 'BR', 'AU', 'ZA', 'SA', 'FR', 'GB', 'CA']);
const getRenewableShare = (country) => country.hydro + country.wind + country.solar + (country.other || 0);
const getEmissionIntensity = (country) => country.co2 / Math.max(country.energy, 1);

const drawBackdrop = (ctx, w, h, timeMs) => {
    const bg = ctx.createLinearGradient(0, 0, w, h);
    bg.addColorStop(0, '#040404');
    bg.addColorStop(0.45, '#111111');
    bg.addColorStop(1, '#020202');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    const nebula = ctx.createRadialGradient(w * 0.22, h * 0.18, 10, w * 0.22, h * 0.18, w * 0.55);
    nebula.addColorStop(0, 'rgba(255, 255, 255, 0.10)');
    nebula.addColorStop(0.55, 'rgba(255, 255, 255, 0.03)');
    nebula.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = nebula;
    ctx.fillRect(0, 0, w, h);

    const ember = ctx.createRadialGradient(w * 0.82, h * 0.2, 10, w * 0.82, h * 0.2, w * 0.38);
    ember.addColorStop(0, 'rgba(255, 255, 255, 0.08)');
    ember.addColorStop(0.6, 'rgba(255, 255, 255, 0.02)');
    ember.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = ember;
    ctx.fillRect(0, 0, w, h);

    ctx.lineWidth = 1;
    for (let i = 0; i < 14; i++) {
        const x = (i / 13) * w;
        ctx.strokeStyle = 'rgba(255,255,255,0.02)';
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x - w * 0.12, h);
        ctx.stroke();
    }

    const scanY = ((Math.sin(timeMs * 0.0003) + 1) * 0.5) * h;
    const scan = ctx.createLinearGradient(0, scanY - 12, 0, scanY + 12);
    scan.addColorStop(0, 'rgba(255,255,255,0)');
    scan.addColorStop(0.5, 'rgba(255,255,255,0.035)');
    scan.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = scan;
    ctx.fillRect(0, scanY - 12, w, 24);

    for (let i = 0; i < 90; i++) {
        const seed = i + 1;
        const x = ((Math.sin(seed * 128.8) + 1) * 0.5) * w;
        const y = ((Math.cos(seed * 74.2) + 1) * 0.5) * h;
        const twinkle = 0.35 + 0.25 * Math.sin(timeMs * 0.0012 + seed);
        const size = 0.7 + (seed % 4) * 0.35;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${0.08 + twinkle * 0.12})`;
        ctx.fill();
    }
};

const drawEmissionPlume = (ctx, px, py, scale, country, timeMs, isSelected) => {
    const intensity = clamp(country.co2 / 5000, 0.08, 1);
    const plumeHeight = (35 + intensity * 65) * scale;
    const particleCount = 7 + Math.round(intensity * 10);

    for (let s = 0; s < 3; s++) {
        const sp = (timeMs * 0.0003 + s * 0.33 + country.lat * 0.005) % 1;
        const sx = Math.sin(timeMs * 0.0008 + s * 2.1) * (3 + intensity * 5) * scale;
        const sy = -sp * plumeHeight * 0.5;
        const sa = (0.02 + intensity * 0.04) * (1 - sp);
        ctx.fillStyle = `rgba(255,255,255,${sa})`;
        ctx.beginPath();
        ctx.ellipse(px + sx, py + sy, (4 + intensity * 8) * scale, (1.5 + intensity * 3) * scale, 0, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.strokeStyle = `rgba(255,255,255,${isSelected ? 0.18 : 0.09})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(px, py - 2 * scale);
    ctx.bezierCurveTo(
        px + 5 * scale, py - plumeHeight * 0.25,
        px - 3 * scale, py - plumeHeight * 0.55,
        px + 2 * scale, py - plumeHeight * 0.78
    );
    ctx.stroke();

    for (let i = 0; i < particleCount; i++) {
        const phase = (timeMs * 0.00025 + i / particleCount + country.lat * 0.01) % 1;
        const wanderX = Math.sin(timeMs * 0.0012 + i * 1.37 + country.lng * 0.03) * (8 + intensity * 16) * scale;
        const wanderY = Math.cos(timeMs * 0.0008 + i * 0.91) * 3 * scale;
        const driftX = wanderX * phase;
        const driftY = -phase * plumeHeight + wanderY;
        const radius = (2.8 + intensity * 9) * (0.4 + (1 - phase) * 0.8) * scale;
        const alpha = (0.05 + intensity * 0.2) * (1 - phase * phase);
        const tone = Math.round(240 - phase * 80);
        const plume = ctx.createRadialGradient(px + driftX, py + driftY, 0, px + driftX, py + driftY, radius * 2.2);
        plume.addColorStop(0, `rgba(${tone}, ${tone}, ${tone}, ${alpha + (isSelected ? 0.06 : 0)})`);
        plume.addColorStop(0.45, `rgba(${tone - 20}, ${tone - 20}, ${tone - 20}, ${alpha * 0.5})`);
        plume.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = plume;
        ctx.beginPath();
        ctx.arc(px + driftX, py + driftY, radius * 2.2, 0, Math.PI * 2);
        ctx.fill();
    }
};
const MixBar = ({ label, pct, color }) => (
    <div className="ge-mix-bar-row">
        <span className="ge-mix-label">{label}</span>
        <div className="ge-mix-bar-track"><div className="ge-mix-bar-fill" style={{ width: `${pct}%`, background: color }} /></div>
        <span className="ge-mix-pct">{pct.toFixed(1)}%</span>
    </div>
);
const GlobalEmissions = () => {
    const canvasRef = useRef(null);
    const [selected, setSelected] = useState(null);
    const [tooltip, setTooltip] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [zoomLevel, setZoomLevel] = useState(1);
    const rot = useRef({ rx: 0.35, ry: -0.4 });
    const drag = useRef(null);
    const autoRot = useRef(true);
    const projCache = useRef([]);
    const sz = useRef({ w: 800, h: 560 });
    const zoomRef = useRef(1);

    const updateZoom = useCallback((nextZoom) => {
        const clamped = clamp(nextZoom, 0.82, 1.85);
        zoomRef.current = clamped;
        setZoomLevel(Number(clamped.toFixed(2)));
    }, []);

    const resetView = useCallback(() => {
        rot.current = { rx: 0.35, ry: -0.4 };
        autoRot.current = true;
        updateZoom(1);
    }, [updateZoom]);

    const draw = useCallback((timeMs = 0) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const { w, h } = sz.current;
        const dpr = window.devicePixelRatio || 1;
        canvas.width = w * dpr; canvas.height = h * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        const cx = w / 2, cy = h / 2;
        const R = Math.min(w, h) * 0.38 * zoomRef.current;
        const { rx, ry } = rot.current;
        drawBackdrop(ctx, w, h, timeMs);
        const halo = ctx.createRadialGradient(cx, cy, R * 0.45, cx, cy, R * 1.45);
        halo.addColorStop(0, 'rgba(255, 255, 255, 0)');
        halo.addColorStop(0.7, 'rgba(255, 255, 255, 0.05)');
        halo.addColorStop(1, 'rgba(255, 255, 255, 0)');
        ctx.fillStyle = halo;
        ctx.fillRect(0, 0, w, h);
        ctx.beginPath();
        ctx.arc(cx, cy, R, 0, Math.PI * 2);
        const ocean = ctx.createRadialGradient(cx - R * 0.25, cy - R * 0.25, R * 0.15, cx, cy, R * 1.05);
        ocean.addColorStop(0, '#1a1a1a');
        ocean.addColorStop(0.45, '#0d0d0d');
        ocean.addColorStop(1, '#030303');
        ctx.fillStyle = ocean;
        ctx.fill();
        ctx.lineWidth = 1.2;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.26)';
        ctx.stroke();
        const atmosphere = ctx.createRadialGradient(cx, cy, R * 0.92, cx, cy, R * 1.12);
        atmosphere.addColorStop(0, 'rgba(255, 255, 255, 0)');
        atmosphere.addColorStop(0.75, 'rgba(255, 255, 255, 0.025)');
        atmosphere.addColorStop(1, 'rgba(255, 255, 255, 0.24)');
        ctx.strokeStyle = atmosphere;
        ctx.lineWidth = 10;
        ctx.beginPath();
        ctx.arc(cx, cy, R * 1.01, 0, Math.PI * 2);
        ctx.stroke();
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(timeMs * 0.00005);
        ctx.scale(1.16, 0.54);
        ctx.beginPath();
        ctx.setLineDash([8, 10]);
        ctx.lineWidth = 1;
        ctx.strokeStyle = 'rgba(255,255,255,0.08)';
        ctx.arc(0, 0, R * 1.18, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
        ctx.setLineDash([]);
        ctx.lineWidth = 0.3;
        for (let lat = -75; lat <= 75; lat += 15) {
            ctx.beginPath();
            let started = false;
            for (let lng = 0; lng <= 360; lng += 2) {
                let [x, y, z] = latLngTo3D(lat, lng, R);
                [x, y, z] = rotY(x, y, z, ry);[x, y, z] = rotX(x, y, z, rx);
                if (z < -10) { started = false; continue; }
                const [px, py] = proj(x, y, z, cx, cy);
                const alpha = Math.max(0, (z + 10) / (R + 10)) * 0.12;
                ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
                if (!started) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                started = true;
            }
            ctx.stroke();
        }
        for (let lng = 0; lng < 360; lng += 15) {
            ctx.beginPath();
            let started = false;
            for (let lat = -90; lat <= 90; lat += 2) {
                let [x, y, z] = latLngTo3D(lat, lng, R);
                [x, y, z] = rotY(x, y, z, ry);[x, y, z] = rotX(x, y, z, rx);
                if (z < -10) { started = false; continue; }
                const [px, py] = proj(x, y, z, cx, cy);
                const alpha = Math.max(0, (z + 10) / (R + 10)) * 0.08;
                ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
                if (!started) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                started = true;
            }
            ctx.stroke();
        }
        ctx.lineWidth = 1.25;
        ALL_CONTINENTS.forEach(cont => {
            const contPoints = [];
            let allOnFront = true;
            cont.coords.forEach(([lat, lng]) => {
                let [x, y, z] = latLngTo3D(lat, lng, R);
                [x, y, z] = rotY(x, y, z, ry);[x, y, z] = rotX(x, y, z, rx);
                if (z > -10) {
                    const [px, py] = proj(x, y, z, cx, cy);
                    contPoints.push({ px, py, vis: true });
                } else {
                    contPoints.push({ px: 0, py: 0, vis: false });
                    allOnFront = false;
                }
            });
            const visCount = contPoints.filter(p => p.vis).length;
            if (visCount > 2) {
                ctx.beginPath();
                let s = false;
                contPoints.forEach(p => {
                    if (p.vis) { if (!s) ctx.moveTo(p.px, p.py); else ctx.lineTo(p.px, p.py); s = true; }
                    else s = false;
                });
                if (allOnFront) ctx.closePath();
                ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
                ctx.fill();
            }
            ctx.beginPath();
            let started = false;
            contPoints.forEach(p => {
                if (p.vis) { if (!started) ctx.moveTo(p.px, p.py); else ctx.lineTo(p.px, p.py); started = true; }
                else started = false;
            });
            ctx.shadowBlur = 12;
            ctx.shadowColor = 'rgba(255, 255, 255, 0.08)';
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.55)';
            ctx.stroke();
        });
        ctx.shadowBlur = 0;
        const projected = [];
        COUNTRIES.forEach((c, i) => {
            let [x, y, z] = latLngTo3D(c.lat, c.lng, R);
            [x, y, z] = rotY(x, y, z, ry);[x, y, z] = rotX(x, y, z, rx);
            const vis = z > 0;
            const [px, py, pf] = proj(x, y, z, cx, cy);
            projected.push({ px, py, visible: vis, idx: i, z, scale: pf });
        });
        const visibleSorted = projected
            .filter(point => point.visible)
            .sort((a, b) => a.z - b.z);

        const topEmitters = [...COUNTRIES].sort((a, b) => b.co2 - a.co2).slice(0, 5).map(c => c.code);
        const topProjected = visibleSorted.filter(p => topEmitters.includes(COUNTRIES[p.idx].code));
        if (topProjected.length >= 2) {
            for (let i = 0; i < topProjected.length - 1; i++) {
                const a = topProjected[i], b = topProjected[i + 1];
                const flowPhase = (timeMs * 0.0004 + i * 0.25) % 1;
                const midX = (a.px + b.px) / 2;
                const midY = (a.py + b.py) / 2 - 30 * Math.min(a.scale, b.scale);
                ctx.beginPath();
                ctx.moveTo(a.px, a.py);
                ctx.quadraticCurveTo(midX, midY, b.px, b.py);
                ctx.strokeStyle = `rgba(255,255,255,${0.04 + 0.03 * Math.sin(timeMs * 0.002 + i)})`;
                ctx.lineWidth = 0.6;
                ctx.setLineDash([4, 8]);
                ctx.lineDashOffset = -timeMs * 0.03;
                ctx.stroke();
                ctx.setLineDash([]);

                const dotT = flowPhase;
                const dotX = (1 - dotT) * (1 - dotT) * a.px + 2 * (1 - dotT) * dotT * midX + dotT * dotT * b.px;
                const dotY = (1 - dotT) * (1 - dotT) * a.py + 2 * (1 - dotT) * dotT * midY + dotT * dotT * b.py;
                ctx.fillStyle = `rgba(255,255,255,${0.2 + 0.15 * (1 - dotT)})`;
                ctx.beginPath();
                ctx.arc(dotX, dotY, 1.8, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        visibleSorted.forEach(point => {
            const country = COUNTRIES[point.idx];
            const radius = dotR(country.co2, 0.82 + zoomRef.current * 0.26) * point.scale;
            const [cr, cg, cb] = renewCol(country);
            const emissionIntensity = getEmissionIntensity(country);
            const isSelected = selected?.code === country.code;
            if (country.co2 > 120 || isSelected) {
                drawEmissionPlume(ctx, point.px, point.py, point.scale, country, timeMs, isSelected);
            }

            if (country.co2 > 300) {
                const pulseCount = country.co2 > 3000 ? 3 : country.co2 > 1000 ? 2 : 1;
                for (let r = 0; r < pulseCount; r++) {
                    const pulsePhase = (timeMs * 0.0006 + r * (1 / pulseCount) + point.idx * 0.1) % 1;
                    const pulseRadius = radius * (2.5 + pulsePhase * 5);
                    const pulseAlpha = (0.12 + (isSelected ? 0.08 : 0)) * (1 - pulsePhase);
                    ctx.strokeStyle = `rgba(${cr},${cg},${cb},${pulseAlpha})`;
                    ctx.lineWidth = (1.2 - pulsePhase * 0.8);
                    ctx.beginPath();
                    ctx.arc(point.px, point.py, pulseRadius, 0, Math.PI * 2);
                    ctx.stroke();
                }
            }

            const glow = ctx.createRadialGradient(point.px, point.py, 0, point.px, point.py, radius * (isSelected ? 7.5 : 4.5));
            glow.addColorStop(0, `rgba(${cr},${cg},${cb},${isSelected ? 0.5 : 0.28})`);
            glow.addColorStop(0.65, `rgba(${cr},${cg},${cb},${isSelected ? 0.12 : 0.08})`);
            glow.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = glow;
            ctx.beginPath();
            ctx.arc(point.px, point.py, radius * (isSelected ? 7.5 : 4.5), 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = `rgba(${cr},${cg},${cb},${isSelected ? 1 : 0.9})`;
            ctx.beginPath();
            ctx.arc(point.px, point.py, isSelected ? radius * 1.45 : radius, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = `rgba(255,255,255,${isSelected ? 0.95 : clamp(0.18 + emissionIntensity / 120, 0.2, 0.46)})`;
            ctx.lineWidth = isSelected ? 1.8 : 0.7;
            ctx.beginPath();
            ctx.arc(point.px, point.py, radius + 2.2, 0, Math.PI * 2);
            ctx.stroke();

            if (isSelected || (COUNTRY_LABEL_CODES.has(country.code) && point.scale > 0.62)) {
                ctx.fillStyle = 'rgba(255,255,255,0.82)';
                ctx.font = `${isSelected ? '700' : '600'} ${isSelected ? 11 : 9}px sans-serif`;
                ctx.textAlign = 'center';
                ctx.fillText(isSelected ? country.name : country.code, point.px, point.py - radius - (isSelected ? 11 : 9));
            }
        });
        projCache.current = projected;
        ctx.textAlign = 'left';
        ctx.fillStyle = 'rgba(255,255,255,0.12)';
        ctx.font = '600 8px monospace';
        ctx.fillText('GLOBAL ENERGY · EMISSIONS', 16, 22);
        ctx.fillStyle = 'rgba(255,255,255,0.10)'; ctx.font = '8px monospace';
        ctx.fillText(`${COUNTRIES.length} countries · IEA/OWID 2023 · drag to rotate`, 16, 35);
        ctx.textAlign = 'right'; ctx.fillStyle = 'rgba(255,255,255,0.08)';
        ctx.fillText(`Zoom ${Math.round(zoomRef.current * 100)}%`, w - 16, h - 14);
        ctx.textAlign = 'left';
        const ly = h - 18;
        [[248, 248, 248, 'low'], [214, 214, 214, 'steady'], [170, 170, 170, 'high'], [120, 120, 120, 'plume']].forEach(([r, g, b, l], i) => {
            const lx = 16 + i * 74;
            ctx.fillStyle = `rgb(${r},${g},${b})`;
            ctx.beginPath(); ctx.arc(lx, ly, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.font = '8px sans-serif';
            ctx.fillText(l, lx + 7, ly + 3);
        });
        ctx.fillText('· Size = CO₂', 16 + 4 * 74, ly + 3);
    }, [selected]);
    useEffect(() => {
        let raf;
        const loop = (time) => { if (autoRot.current && !drag.current) rot.current.ry += 0.0015; draw(time); raf = requestAnimationFrame(loop); };
        raf = requestAnimationFrame(loop);
        return () => cancelAnimationFrame(raf);
    }, [draw]);
    useEffect(() => {
        const el = canvasRef.current?.parentElement;
        if (!el) return;
        const obs = new ResizeObserver(entries => { for (const e of entries) sz.current = { w: e.contentRect.width, h: Math.max(500, e.contentRect.height) }; });
        obs.observe(el);
        return () => obs.disconnect();
    }, []);
    const handleDown = useCallback(e => {
        autoRot.current = false;
        const r = canvasRef.current.getBoundingClientRect();
        drag.current = { x: e.clientX - r.left, y: e.clientY - r.top, moved: false };
        setIsDragging(true);
    }, []);
    const handleMove = useCallback(e => {
        const r = canvasRef.current?.getBoundingClientRect();
        if (!r) return;
        const mx = e.clientX - r.left, my = e.clientY - r.top;
        if (drag.current) {
            const dx = mx - drag.current.x, dy = my - drag.current.y;
            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.current.moved = true;
            rot.current.ry += dx * 0.005;
            rot.current.rx = Math.max(-1.2, Math.min(1.2, rot.current.rx + dy * 0.005));
            drag.current.x = mx; drag.current.y = my;
            setTooltip(null);
            return;
        }
        let found = -1;
        for (const p of projCache.current) {
            if (!p.visible) continue;
            const c = COUNTRIES[p.idx];
            if (Math.sqrt((mx - p.px) ** 2 + (my - p.py) ** 2) < dotR(c.co2, 0.82 + zoomRef.current * 0.26) + 8) { found = p.idx; break; }
        }
        if (found >= 0) {
            const c = COUNTRIES[found], ren = (c.hydro + c.wind + c.solar + (c.other || 0)).toFixed(0);
            setTooltip({ x: mx + 14, y: my - 10, name: `${c.flag} ${c.name}`, co2: c.co2, ren, intensity: getEmissionIntensity(c).toFixed(1) });
        } else setTooltip(null);
    }, []);
    const handleUp = useCallback(() => {
        drag.current = null;
        setIsDragging(false);
        setTimeout(() => { if (!drag.current) autoRot.current = true; }, 4000);
    }, []);
    const handleWheel = useCallback((e) => {
        e.preventDefault();
        autoRot.current = false;
        updateZoom(zoomRef.current - e.deltaY * 0.0012);
    }, [updateZoom]);
    const handleClick = useCallback(e => {
        if (drag.current?.moved) return;
        const r = canvasRef.current?.getBoundingClientRect();
        if (!r) return;
        const mx = e.clientX - r.left, my = e.clientY - r.top;
        for (const p of projCache.current) {
            if (!p.visible) continue;
            const c = COUNTRIES[p.idx];
            if (Math.sqrt((mx - p.px) ** 2 + (my - p.py) ** 2) < dotR(c.co2, 0.82 + zoomRef.current * 0.26) + 8) { setSelected(c); return; }
        }
        setSelected(null);
    }, []);
    const topRenewable = [...COUNTRIES].sort((a, b) => (b.hydro + b.wind + b.solar) - (a.hydro + a.wind + a.solar))[0];
    const topEmitter = [...COUNTRIES].sort((a, b) => b.co2 - a.co2)[0];
    const lowestIntensity = [...COUNTRIES].filter(country => country.energy > 30).sort((a, b) => getEmissionIntensity(a) - getEmissionIntensity(b))[0];
    const avgRenPct = (COUNTRIES.reduce((s, c) => s + c.hydro + c.wind + c.solar, 0) / COUNTRIES.length).toFixed(1);
    const topEmitterList = [...COUNTRIES].sort((a, b) => b.co2 - a.co2).slice(0, 6);
    const cleanLeaders = [...COUNTRIES].filter(country => country.energy > 30).sort((a, b) => getEmissionIntensity(a) - getEmissionIntensity(b)).slice(0, 4);
    return (
        <div className="ge-container">
            <div className="ge-map-section" style={{ minHeight: '560px' }}>
                <div className="ge-map-title-overlay">
                    <h3>Global Carbon Field</h3>
                    <p>Globe with geometric wireframes of 
                        each national energy footprint.</p>
                </div>
                <div className="ge-map-topbar">
                    <div className="ge-map-chip">
                        <span className="ge-chip-label">Largest plume</span>
                        <strong>{topEmitter.name}</strong>
                        <span>{topEmitter.co2.toLocaleString()} Mt CO2</span>
                    </div>
                    <div className="ge-map-chip">
                        <span className="ge-chip-label">Cleanest mix</span>
                        <strong>{topRenewable.name}</strong>
                        <span>{getRenewableShare(topRenewable).toFixed(0)}% clean</span>
                    </div>
                    <div className="ge-map-chip">
                        <span className="ge-chip-label">Best intensity</span>
                        <strong>{lowestIntensity.name}</strong>
                        <span>{getEmissionIntensity(lowestIntensity).toFixed(1)} Mt/TWh</span>
                    </div>
                </div>
                <div className="ge-map-toolbar">
                    <span className="ge-toolbar-label">View</span>
                    <div className="ge-control-stack">
                        <button type="button" className="ge-control-btn" onClick={() => updateZoom(zoomRef.current + 0.12)} aria-label="Zoom in">
                            <Plus size={14} />
                        </button>
                        <button type="button" className="ge-control-btn" onClick={() => updateZoom(zoomRef.current - 0.12)} aria-label="Zoom out">
                            <Minus size={14} />
                        </button>
                        <button type="button" className="ge-control-btn" onClick={resetView} aria-label="Reset view">
                            <RotateCcw size={14} />
                        </button>
                    </div>
                    <span className="ge-zoom-readout">{Math.round(zoomLevel * 100)}%</span>
                </div>
                <div className="ge-map-canvas-wrap" style={{ height: '100%' }}>
                    <canvas ref={canvasRef} style={{ width: '100%', height: '560px', cursor: isDragging ? 'grabbing' : 'grab' }}
                        onMouseDown={handleDown} onMouseMove={handleMove} onMouseUp={handleUp}
                        onWheel={handleWheel}
                        onMouseLeave={() => { drag.current = null; setIsDragging(false); setTooltip(null); }} onClick={handleClick} />
                </div>
                <div className="ge-side-panel">
                    <div className="ge-rail-card">
                        <p className="ge-rail-title">Largest Emitters</p>
                        {topEmitterList.map(country => (
                            <button key={country.code} className={`ge-rail-item ${selected?.code === country.code ? 'active' : ''}`} onClick={() => setSelected(country)}>
                                <span>{country.flag} {country.name}</span>
                                <span>{country.co2.toLocaleString()} Mt</span>
                            </button>
                        ))}
                    </div>
                    <div className="ge-rail-card">
                        <p className="ge-rail-title">Lowest Carbon Intensity</p>
                        {cleanLeaders.map(country => (
                            <button key={country.code} className={`ge-rail-item ge-clean ${selected?.code === country.code ? 'active' : ''}`} onClick={() => setSelected(country)}>
                                <span>{country.flag} {country.name}</span>
                                <span>{getEmissionIntensity(country).toFixed(1)}</span>
                            </button>
                        ))}
                    </div>
                </div>
                <div className="ge-map-footer-overlay">
                    <span className="ge-map-hint">Drag to rotate, use the wheel or controls to zoom, and click any country to inspect its energy profile.</span>
                    <div className="ge-map-mini-legend">
                        <span className="ge-legend-pill"><span className="ge-legend-dot ge-legend-node" />Country node</span>
                        <span className="ge-legend-pill"><span className="ge-legend-dot ge-legend-plume" />CO2 plume</span>
                        <span className="ge-legend-pill"><span className="ge-legend-dot ge-legend-ring" />Geometric orbit</span>
                    </div>
                </div>
                {tooltip && (
                    <div className="ge-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
                        <span className="ge-tooltip-name">{tooltip.name}</span>
                        {tooltip.co2.toLocaleString()} Mt CO₂ · {tooltip.ren}% renewable
                    </div>
                )}
                {selected && (
                    <div className="ge-detail-overlay">
                        <div className="ge-detail-header">
                            <div><span className="ge-detail-flag">{selected.flag}</span><p className="ge-detail-country">{selected.name}</p></div>
                            <button className="ge-detail-close" onClick={() => setSelected(null)}><X size={14} /></button>
                        </div>
                        <hr className="ge-detail-divider" />
                        <p className="ge-detail-section-title">Key Metrics</p>
                        <div className="ge-detail-stat-grid">
                            <div className="ge-detail-stat"><p className="ge-detail-stat-label">CO₂ Emissions</p><p className="ge-detail-stat-value">{selected.co2.toLocaleString()} <span className="ge-detail-stat-unit">Mt</span></p></div>
                            <div className="ge-detail-stat"><p className="ge-detail-stat-label">Electricity</p><p className="ge-detail-stat-value">{selected.energy.toLocaleString()} <span className="ge-detail-stat-unit">TWh</span></p></div>
                            <div className="ge-detail-stat"><p className="ge-detail-stat-label">Population</p><p className="ge-detail-stat-value">{selected.pop} <span className="ge-detail-stat-unit">M</span></p></div>
                            <div className="ge-detail-stat"><p className="ge-detail-stat-label">GDP</p><p className="ge-detail-stat-value">${selected.gdp.toLocaleString()} <span className="ge-detail-stat-unit">B</span></p></div>
                            <div className="ge-detail-stat"><p className="ge-detail-stat-label">CO₂ / capita</p><p className="ge-detail-stat-value">{(selected.co2 / selected.pop).toFixed(1)} <span className="ge-detail-stat-unit">t</span></p></div>
                            <div className="ge-detail-stat"><p className="ge-detail-stat-label">CO₂ / GDP</p><p className="ge-detail-stat-value">{(selected.co2 / selected.gdp * 1000).toFixed(0)} <span className="ge-detail-stat-unit">t/$M</span></p></div>
                        </div>
                        <hr className="ge-detail-divider" />
                        <p className="ge-detail-section-title">Energy Mix</p>
                        <MixBar label="Coal" pct={selected.coal} color="#f5f5f5" />
                        <MixBar label="Gas" pct={selected.gas} color="#dfdfdf" />
                        <MixBar label="Oil" pct={selected.oil} color="#bebebe" />
                        <MixBar label="Nuclear" pct={selected.nuclear} color="#9d9d9d" />
                        <MixBar label="Hydro" pct={selected.hydro} color="#ececec" />
                        <MixBar label="Wind" pct={selected.wind} color="#d8d8d8" />
                        <MixBar label="Solar" pct={selected.solar} color="#c8c8c8" />
                        <MixBar label="Other" pct={selected.other} color="#8a8a8a" />
                        <hr className="ge-detail-divider" />
                        <p className="ge-detail-section-title">Renewable Share</p>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '8px' }}>
                            <span style={{ fontSize: '28px', fontWeight: 800, color: '#fff', fontFamily: 'var(--font-mono)' }}>{(selected.hydro + selected.wind + selected.solar + (selected.other || 0)).toFixed(0)}%</span>
                            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)' }}>of electricity</span>
                        </div>
                        <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                            <div style={{ height: '100%', borderRadius: '3px', width: `${selected.hydro + selected.wind + selected.solar + (selected.other || 0)}%`, background: 'linear-gradient(90deg,#f4f4f5,#d4d4d8,#a1a1aa)', transition: 'width 0.5s' }} />
                        </div>
                    </div>
                )}
            </div>
            <div className="ge-stats-row">
                <div className="ge-stat-card"><span className="ge-stat-card-label">Countries Tracked</span><span className="ge-stat-card-value">{COUNTRIES.length}</span><span className="ge-stat-card-sub">IEA &amp; OWID 2023</span></div>
                <div className="ge-stat-card"><span className="ge-stat-card-label">Total CO₂ (tracked)</span><span className="ge-stat-card-value">{(TOTAL_GLOBAL_CO2 / 1000).toFixed(1)} Gt</span><span className="ge-stat-card-sub">~{((TOTAL_GLOBAL_CO2 / 37400) * 100).toFixed(0)}% of global</span></div>
                <div className="ge-stat-card"><span className="ge-stat-card-label">Total Electricity</span><span className="ge-stat-card-value">{(TOTAL_GLOBAL_ENERGY / 1000).toFixed(1)} PWh</span><span className="ge-stat-card-sub">~{((TOTAL_GLOBAL_ENERGY / 29165) * 100).toFixed(0)}% of global</span></div>
                <div className="ge-stat-card"><span className="ge-stat-card-label">Top Emitter</span><span className="ge-stat-card-value">{topEmitter.name}</span><span className="ge-stat-card-sub">{topEmitter.co2.toLocaleString()} Mt</span></div>
                <div className="ge-stat-card"><span className="ge-stat-card-label">Most Renewable</span><span className="ge-stat-card-value">{topRenewable.name}</span><span className="ge-stat-card-sub">{(topRenewable.hydro + topRenewable.wind + topRenewable.solar).toFixed(0)}% clean</span></div>
                <div className="ge-stat-card"><span className="ge-stat-card-label">Avg. Renewable</span><span className="ge-stat-card-value">{avgRenPct}%</span><span className="ge-stat-card-sub">Mean across nations</span></div>
            </div>
        </div>
    );
};
export default GlobalEmissions;
