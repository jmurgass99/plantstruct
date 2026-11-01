import van from "vanjs-core";
import type { SemanticShellCourse } from "./data-model.ts";
import { solveTankApi650Wasm } from "./solver/wasmSolver.ts";
import { fetchPlantstructHealthApi } from "./solver/apiClient.ts";
import { createTankViewer3D } from "./viewer/getViewer3D.ts";
import { renderHoopStressChart, renderMassSplitChart } from "./ui/getTankCharts.ts";

const { div, h2, h3, label, input, span, strong, canvas, button } = van.tags;

const diameterM = van.state(16.0);
const liquidHeightM = van.state(8.8);
const ringsPerCourse = van.state(4);
const saImpulsive = van.state(0.30);

const maxHoopText = van.state("0.0 MPa");
const tcText = van.state("0.00 s");
const wiText = van.state("0.0 %");
const ringsText = van.state("16");
const apiStatus = van.state("Modo WASM local");

const viewerWrap = div({ class: "viewer-wrap" });
const hoopCanvas = canvas({ class: "chart" });
const massCanvas = canvas({ class: "chart" });
const viewer = createTankViewer3D(viewerWrap);

const defaultCourses: SemanticShellCourse[] = [
  { id: "COURSE-1", heightM: 2.4, thicknessMm: 14 },
  { id: "COURSE-2", heightM: 2.4, thicknessMm: 11 },
  { id: "COURSE-3", heightM: 2.4, thicknessMm: 8 },
  { id: "COURSE-4", heightM: 2.4, thicknessMm: 6 },
];

async function recompute() {
  const res = await solveTankApi650Wasm(
    diameterM.val,
    liquidHeightM.val,
    defaultCourses,
    ringsPerCourse.val,
    saImpulsive.val
  );
  maxHoopText.val = `${res.maxHoopMpa.toFixed(1)} MPa`;
  tcText.val = `${res.convectivePeriodS.toFixed(2)} s`;
  wiText.val = `${(res.impulsiveMassRatio * 100).toFixed(1)} %`;
  ringsText.val = `${res.rings.length}`;
  viewer.update(diameterM.val, liquidHeightM.val, res);
  renderHoopStressChart(hoopCanvas, res);
  renderMassSplitChart(massCanvas, res);
}

van.derive(() => {
  void recompute();
});

const app = div(
  { class: "layout" },
  div(
    { class: "panel" },
    h2("PlantStruct API 650 3D"),
    div(
      { class: "control-row" },
      label(() => `Diámetro del tanque D = ${diameterM.val.toFixed(1)} m`),
      input({
        type: "range",
        min: "8.0",
        max: "32.0",
        step: "1.0",
        value: diameterM,
        oninput: (e: Event) => (diameterM.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Nivel de líquido H_L = ${liquidHeightM.val.toFixed(1)} m`),
      input({
        type: "range",
        min: "3.0",
        max: "9.4",
        step: "0.2",
        value: liquidHeightM,
        oninput: (e: Event) => (liquidHeightM.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Anillos por virola (TankCourseMapping) = ${ringsPerCourse.val}`),
      input({
        type: "range",
        min: "1",
        max: "10",
        step: "1",
        value: ringsPerCourse,
        oninput: (e: Event) => (ringsPerCourse.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Aceleración impulsiva A_i = ${saImpulsive.val.toFixed(2)} g`),
      input({
        type: "range",
        min: "0.05",
        max: "0.60",
        step: "0.05",
        value: saImpulsive,
        oninput: (e: Event) => (saImpulsive.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "kpi-grid" },
      div({ class: "kpi" }, span("Tensión σ_h,máx"), strong(maxHoopText)),
      div({ class: "kpi" }, span("Periodo chapoteo T_c"), strong(tcText)),
      div({ class: "kpi" }, span("Fracción impulsiva W_i"), strong(wiText)),
      div({ class: "kpi" }, span("Anillos de manto"), strong(ringsText))
    ),
    button(
      {
        onclick: async () => {
          const ok = await fetchPlantstructHealthApi("http://localhost:8000");
          apiStatus.val = ok ? "FastAPI sincronizado OK" : "FastAPI offline (usando WASM local)";
        },
      },
      "Sincronizar con FastAPI"
    ),
    span({ style: "font-size:0.75rem;color:#94a3b8" }, apiStatus)
  ),
  viewerWrap,
  div(
    { class: "panel" },
    h3("Tensión Circunferencial Hidrostática + Sísmica"),
    hoopCanvas,
    h3("Partición de Masas de Housner (API 650 E)"),
    massCanvas
  )
);

document.getElementById("app")?.appendChild(app);
