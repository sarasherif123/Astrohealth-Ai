export function Spark({ pts = [70, 72, 71, 74, 73, 76, 72], c = "#00e5ff" }) {
  if (!pts || pts.length === 0) pts = [0, 0];
  const mn = Math.min(...pts);
  const mx = Math.max(...pts);
  const denom = (mx - mn) || 1;
  const p = pts
    .map((v, i) => `${i * (100 / Math.max(pts.length - 1, 1))},${22 - ((v - mn) / denom) * 20}`)
    .join(" ");

  return (
    <svg viewBox="0 0 100 24" width="100%" height="24" preserveAspectRatio="none">
      <polyline points={p} fill="none" stroke={c} strokeWidth="1.8" />
    </svg>
  );
}

export function Chart({ series = [], xl = [], ymin = 0, ymax = 100, yt = [] }) {
  const W = 420, H = 230, L = 40, B = 30, T = 10, R = 10, iw = W - L - R, ih = H - T - B;
  const len = Math.max(series[0]?.v?.length || 1, 2);
  const X = (i) => L + (i * iw) / (len - 1);
  const Y = (v) => T + ih - ((v - ymin) / (ymax - ymin || 1)) * ih;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%">
      {yt.map((t) => (
        <g key={t}>
          <line x1={L} x2={W - R} y1={Y(t)} y2={Y(t)} stroke="rgba(56, 189, 248, 0.10)" strokeDasharray="3 3" />
          <text x={L - 6} y={Y(t) + 4} textAnchor="end" fill="#8b9bb4" fontSize="10">
            {t}
          </text>
        </g>
      ))}
      <line x1={L} x2={L} y1={T} y2={T + ih} stroke="rgba(56, 189, 248, 0.25)" />
      <line x1={L} x2={W - R} y1={T + ih} y2={T + ih} stroke="rgba(56, 189, 248, 0.25)" />
      {xl.map((l, i) => (
        <text key={l + i} x={L + (i * iw) / Math.max(xl.length - 1, 1)} y={H - 8} textAnchor="middle" fill="#8b9bb4" fontSize="10">
          {l}
        </text>
      ))}
      {series.map((s) => (
        <g key={s.n}>
          <polyline
            fill="none"
            stroke={s.c}
            strokeWidth="2"
            points={s.v.map((v, i) => `${X(i)},${Y(v)}`).join(" ")}
          />
          {s.v.map(
            (v, i) =>
              i % (s.dots || 1) === 0 && (
                <circle key={i} cx={X(i)} cy={Y(v)} r="3" fill="#0d1829" stroke={s.c} strokeWidth="2" />
              )
          )}
        </g>
      ))}
    </svg>
  );
}
