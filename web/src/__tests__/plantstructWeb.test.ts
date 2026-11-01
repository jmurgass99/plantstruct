import assert from "node:assert/strict";
import { solveTankApi650Wasm } from "../solver/wasmSolver.ts";

const courses = [
  { id: "COURSE-1", heightM: 2.4, thicknessMm: 14 },
  { id: "COURSE-2", heightM: 2.4, thicknessMm: 11 },
  { id: "COURSE-3", heightM: 2.4, thicknessMm: 8 },
  { id: "COURSE-4", heightM: 2.4, thicknessMm: 6 },
];

const res2 = await solveTankApi650Wasm(16.0, 8.8, courses, 2, 0.3);
const res6 = await solveTankApi650Wasm(16.0, 8.8, courses, 6, 0.3);

assert.equal(res2.rings.length, 8);
assert.equal(res6.rings.length, 24);
assert.equal(res6.mapping.courseToRings.get("COURSE-1")?.length, 6);
assert.ok(res6.convectivePeriodS > 2.5 && res6.convectivePeriodS < 6.0);
assert.ok(res6.maxHoopMpa > 40.0);
console.log(
  `PlantStruct WASM test OK: T_c=${res6.convectivePeriodS.toFixed(2)} s, maxHoop=${res6.maxHoopMpa.toFixed(1)} MPa`
);
