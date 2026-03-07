import React, { useRef, useEffect, useState, useCallback } from 'react';
import { X } from 'lucide-react';
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
const latLngTo3D = (lat, lng, R) => {
    const phi = (90 - lat) * DEG, theta = (lng + 180) * DEG;
    return [-R * Math.sin(phi) * Math.cos(theta), R * Math.cos(phi), R * Math.sin(phi) * Math.sin(theta)];
};
const rotY = (x, y, z, a) => [x * Math.cos(a) + z * Math.sin(a), y, -x * Math.sin(a) + z * Math.cos(a)];
const rotX = (x, y, z, a) => [x, y * Math.cos(a) - z * Math.sin(a), y * Math.sin(a) + z * Math.cos(a)];
const proj = (x, y, z, cx, cy) => { const f = 800 / (800 + z); return [cx + x * f, cy - y * f, f, z]; };
const dotR = (co2) => 2 + (co2 / 12000) * 8;
const renewCol = (c) => { const r = c.hydro + c.wind + c.solar + (c.other || 0); return r >= 70 ? [100, 240, 150] : r >= 40 ? [120, 180, 255] : r >= 20 ? [220, 220, 220] : [255, 130, 110]; };
const GlobalEmissions = () => {
    const canvasRef = useRef(null);
    const [selected, setSelected] = useState(null);
    const [tooltip, setTooltip] = useState(null);
    const rot = useRef({ rx: 0.35, ry: -0.4 });
    const drag = useRef(null);
    const autoRot = useRef(true);
    const projCache = useRef([]);
    const sz = useRef({ w: 800, h: 560 });
    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const { w, h } = sz.current;
        const dpr = window.devicePixelRatio || 1;
        canvas.width = w * dpr; canvas.height = h * dpr;
        ctx.scale(dpr, dpr);
        const cx = w / 2, cy = h / 2;
        const R = Math.min(w, h) * 0.40;
        const { rx, ry } = rot.current;
        ctx.fillStyle = '#080808';
        ctx.fillRect(0, 0, w, h);
        ctx.beginPath();
        ctx.arc(cx, cy, R, 0, Math.PI * 2);
        ctx.fillStyle = '#0F0F12';
        ctx.fill();
        ctx.lineWidth = 0.5;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.stroke();
        ctx.lineWidth = 0.3;
        for (let lat = -75; lat <= 75; lat += 15) {
            ctx.beginPath();
            let started = false;
            for (let lng = 0; lng <= 360; lng += 2) {
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
        ctx.lineWidth = 0.8;
        ALL_CONTINENTS.forEach(cont => {
            ctx.beginPath();
            let started = false;
            cont.coords.forEach(([lat, lng]) => {
                let [x, y, z] = latLngTo3D(lat, lng, R);
                [x, y, z] = rotY(x, y, z, ry);[x, y, z] = rotX(x, y, z, rx);
                if (z > -10) {
                    const [px, py] = proj(x, y, z, cx, cy);
                    if (!started) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                    started = true;
                } else {
                    started = false;
                }
            });
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.stroke();
        });
        const projected = [];
        COUNTRIES.forEach((c, i) => {
            let [x, y, z] = latLngTo3D(c.lat, c.lng, R);
            [x, y, z] = rotY(x, y, z, ry);[x, y, z] = rotX(x, y, z, rx);
            const vis = z > 0;
            const [px, py, pf] = proj(x, y, z, cx, cy);
            projected.push({ px, py, visible: vis, idx: i });
            if (!vis) return;
            const r = dotR(c.co2) * pf;
            const [cr, cg, cb] = renewCol(c);
            const isSel = selected?.code === c.code;
            if (isSel) {
                const g = ctx.createRadialGradient(px, py, 0, px, py, r * 5);
                g.addColorStop(0, `rgba(${cr},${cg},${cb},0.25)`);
                g.addColorStop(1, `rgba(${cr},${cg},${cb},0)`);
                ctx.fillStyle = g;
                ctx.beginPath(); ctx.arc(px, py, r * 5, 0, Math.PI * 2); ctx.fill();
            }
            const a = isSel ? 1.0 : 0.8;
            ctx.fillStyle = `rgba(${cr},${cg},${cb},${a})`;
            ctx.beginPath(); ctx.arc(px, py, isSel ? r * 1.3 : r, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = `rgba(${cr},${cg},${cb},${isSel ? 0.5 : 0.15})`;
            ctx.lineWidth = isSel ? 1.5 : 0.4;
            ctx.beginPath(); ctx.arc(px, py, r + 2, 0, Math.PI * 2); ctx.stroke();
            if (isSel) {
                ctx.fillStyle = 'rgba(255,255,255,0.75)';
                ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'center';
                ctx.fillText(c.name, px, py - r - 8);
            }
        });
        projCache.current = projected;
        ctx.fillStyle = 'rgba(255,255,255,0.22)'; ctx.font = '600 9px sans-serif'; ctx.textAlign = 'left';
        ctx.fillText('GLOBAL ENERGY · EMISSIONS', 16, 22);
        ctx.fillStyle = 'rgba(255,255,255,0.10)'; ctx.font = '8px monospace';
        ctx.fillText(`${COUNTRIES.length} countries · IEA/OWID 2023 · drag to rotate`, 16, 35);
        ctx.textAlign = 'right'; ctx.fillStyle = 'rgba(255,255,255,0.08)';
        ctx.fillText(`UTC ${new Date().toISOString().slice(0, 16)}`, w - 16, h - 14);
        ctx.textAlign = 'left';
        const ly = h - 18;
        [[255, 130, 110, '<20%'], [220, 220, 220, '20-40%'], [120, 180, 255, '40-70%'], [100, 240, 150, '>70%']].forEach(([r, g, b, l], i) => {
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
        const loop = () => { if (autoRot.current && !drag.current) rot.current.ry += 0.0015; draw(); raf = requestAnimationFrame(loop); };
        loop();
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
            if (Math.sqrt((mx - p.px) ** 2 + (my - p.py) ** 2) < dotR(c.co2) + 8) { found = p.idx; break; }
        }
        if (found >= 0) {
            const c = COUNTRIES[found], ren = (c.hydro + c.wind + c.solar + (c.other || 0)).toFixed(0);
            setTooltip({ x: mx + 14, y: my - 10, name: `${c.flag} ${c.name}`, co2: c.co2, ren });
        } else setTooltip(null);
    }, []);
    const handleUp = useCallback(() => {
        const wasDrag = drag.current?.moved;
        drag.current = null;
        if (!wasDrag) {  }
        setTimeout(() => { if (!drag.current) autoRot.current = true; }, 4000);
    }, []);
    const handleClick = useCallback(e => {
        if (drag.current?.moved) return;
        const r = canvasRef.current?.getBoundingClientRect();
        if (!r) return;
        const mx = e.clientX - r.left, my = e.clientY - r.top;
        for (const p of projCache.current) {
            if (!p.visible) continue;
            const c = COUNTRIES[p.idx];
            if (Math.sqrt((mx - p.px) ** 2 + (my - p.py) ** 2) < dotR(c.co2) + 8) { setSelected(c); return; }
        }
        setSelected(null);
    }, []);
    const topRenewable = [...COUNTRIES].sort((a, b) => (b.hydro + b.wind + b.solar) - (a.hydro + a.wind + a.solar))[0];
    const topEmitter = [...COUNTRIES].sort((a, b) => b.co2 - a.co2)[0];
    const avgRenPct = (COUNTRIES.reduce((s, c) => s + c.hydro + c.wind + c.solar, 0) / COUNTRIES.length).toFixed(1);
    const MixBar = ({ label, pct, color }) => (
        <div className="ge-mix-bar-row">
            <span className="ge-mix-label">{label}</span>
            <div className="ge-mix-bar-track"><div className="ge-mix-bar-fill" style={{ width: `${pct}%`, background: color }} /></div>
            <span className="ge-mix-pct">{pct.toFixed(1)}%</span>
        </div>
    );
    return (
        <div className="ge-container">
            <div className="ge-map-section" style={{ minHeight: '560px' }}>
                <div className="ge-map-canvas-wrap" style={{ height: '100%' }}>
                    <canvas ref={canvasRef} style={{ width: '100%', height: '560px', cursor: drag.current ? 'grabbing' : 'grab' }}
                        onMouseDown={handleDown} onMouseMove={handleMove} onMouseUp={handleUp}
                        onMouseLeave={() => { drag.current = null; setTooltip(null); }} onClick={handleClick} />
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
                        <MixBar label="Coal" pct={selected.coal} color="#e74c3c" />
                        <MixBar label="Gas" pct={selected.gas} color="#e67e22" />
                        <MixBar label="Oil" pct={selected.oil} color="#95a5a6" />
                        <MixBar label="Nuclear" pct={selected.nuclear} color="#9b59b6" />
                        <MixBar label="Hydro" pct={selected.hydro} color="#3498db" />
                        <MixBar label="Wind" pct={selected.wind} color="#1abc9c" />
                        <MixBar label="Solar" pct={selected.solar} color="#f1c40f" />
                        <MixBar label="Other" pct={selected.other} color="#7f8c8d" />
                        <hr className="ge-detail-divider" />
                        <p className="ge-detail-section-title">Renewable Share</p>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '8px' }}>
                            <span style={{ fontSize: '28px', fontWeight: 800, color: '#fff', fontFamily: 'var(--font-mono)' }}>{(selected.hydro + selected.wind + selected.solar + (selected.other || 0)).toFixed(0)}%</span>
                            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)' }}>of electricity</span>
                        </div>
                        <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                            <div style={{ height: '100%', borderRadius: '3px', width: `${selected.hydro + selected.wind + selected.solar + (selected.other || 0)}%`, background: 'linear-gradient(90deg,#3498db,#1abc9c,#f1c40f)', transition: 'width 0.5s' }} />
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
