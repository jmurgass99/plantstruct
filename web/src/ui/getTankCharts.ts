import type { TankResult } from "../data-model.ts";

export function renderHoopStressChart(canvas: HTMLCanvasElement, res: TankResult): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const maxZ = Math.max(...res.rings.map((r) => r.zMidM + 0.5 * r.dzM), 1);
  const maxS = Math.max(res.maxHoopMpa, 1);

  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2;
  ctx.beginPath();
  res.rings.forEach((r, idx) => {
    const x = 36 + (r.hoopHydroMpa / maxS) * (w - 56);
    const y = h - 22 - (r.zMidM / maxZ) * (h - 42);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.strokeStyle = "#f97316";
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  res.rings.forEach((r, idx) => {
    const x = 36 + (r.hoopTotalMpa / maxS) * (w - 56);
    const y = h - 22 - (r.zMidM / maxZ) * (h - 42);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`Tensión circunferencial σ_h(z) — máx = ${res.maxHoopMpa.toFixed(1)} MPa`, 42, 30);
}

export function renderMassSplitChart(canvas: HTMLCanvasElement, res: TankResult): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const wi = Math.min(1, res.impulsiveMassRatio);
  const wc = Math.min(1, res.convectiveMassRatio);

  const hImp = wi * (h - 52);
  const hConv = wc * (h - 52);

  ctx.fillStyle = "#06b6d4";
  ctx.fillRect(75, h - 22 - hImp, 70, hImp);
  ctx.fillStyle = "#f59e0b";
  ctx.fillRect(195, h - 22 - hConv, 70, hConv);

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`W_i/W_L = ${(wi * 100).toFixed(1)}%`, 70, h - 8);
  ctx.fillText(`W_c/W_L = ${(wc * 100).toFixed(1)}%`, 190, h - 8);
}
