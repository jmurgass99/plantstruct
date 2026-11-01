import type { SemanticShellCourse, TankResult } from "../data-model.ts";
import { getTankCourseMesh } from "../mesh/getMesh.ts";

// Binario WebAssembly compilado desde api650Kernel.cpp
const WASM_B64 =
  "AGFzbQEAAAABEAJgBHx8fHwBfGADfHx8AXwDAwIAAQUDAQABBy8CFWhvb3BIeWRyb3N0YXRpY1N0cmVzcwAAE3Nsb3NoaW5nRnJlcVNxdWFyZWQAAQokAg0AIAAgAaIgAqIgA6MLFABE2/l+arx0/T8gAKIgAaMgAqIL";

function decodeBase64(b64: string): Uint8Array {
  if (typeof Buffer !== "undefined") {
    return new Uint8Array(Buffer.from(b64, "base64"));
  }
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export interface Api650WasmExports {
  hoopHydrostaticStress: (gamma: number, depth: number, radius: number, tMm: number) => number;
  sloshingFreqSquared: (g: number, radius: number, tanhVal: number) => number;
}

let cachedExports: Api650WasmExports | null = null;

export async function initApi650Wasm(): Promise<Api650WasmExports> {
  if (cachedExports) return cachedExports;
  const { instance } = await WebAssembly.instantiate(decodeBase64(WASM_B64));
  cachedExports = instance.exports as unknown as Api650WasmExports;
  return cachedExports;
}

export async function solveTankApi650Wasm(
  diameterM: number,
  liquidHeightM: number,
  courses: SemanticShellCourse[],
  ringsPerCourse: number,
  saImpulsive: number
): Promise<TankResult> {
  const wasm = await initApi650Wasm();
  const { rings, mapping } = getTankCourseMesh(courses, ringsPerCourse);
  const radiusM = diameterM / 2.0;
  const gamma = 9.80665;

  const kh = (3.682 * liquidHeightM) / diameterM;
  const tanhVal = Math.tanh(kh);
  const omegaCSq = wasm.sloshingFreqSquared(gamma, radiusM, tanhVal);
  const convectivePeriodS = (2 * Math.PI) / Math.sqrt(Math.max(omegaCSq, 1e-6));

  const dOverH = diameterM / Math.max(liquidHeightM, 0.5);
  const impulsiveMassRatio =
    dOverH >= 1.333 ? Math.tanh(0.866 * dOverH) / (0.866 * dOverH) : 1.0 - 0.218 * dOverH;
  const convectiveMassRatio = ((0.23 * diameterM) / liquidHeightM) * tanhVal;

  let maxHoopMpa = 0;
  for (const r of rings) {
    const depth = Math.max(0, liquidHeightM - r.zMidM);
    r.hoopHydroMpa = wasm.hoopHydrostaticStress(gamma, depth, radiusM, r.thicknessMm);
    r.hoopSeismicMpa = r.hoopHydroMpa * (0.68 * saImpulsive + 0.12);
    r.hoopTotalMpa = r.hoopHydroMpa + r.hoopSeismicMpa;
    if (r.hoopTotalMpa > maxHoopMpa) maxHoopMpa = r.hoopTotalMpa;
  }

  return {
    rings,
    mapping,
    convectivePeriodS,
    impulsiveMassRatio,
    convectiveMassRatio,
    maxHoopMpa,
  };
}
