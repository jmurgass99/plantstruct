import type { SemanticShellCourse, TankCourseMapping, TankShellRing } from "../data-model.ts";

export function getTankCourseMesh(
  courses: SemanticShellCourse[],
  ringsPerCourse: number
): { rings: TankShellRing[]; mapping: TankCourseMapping } {
  const div = Math.max(1, Math.floor(ringsPerCourse));
  const courseToRings = new Map<string, number[]>();
  const ringToCourse = new Map<number, string>();
  const frameToElements = new Map<string, number[]>();
  const rings: TankShellRing[] = [];

  let zCursor = 0;
  for (const c of courses) {
    const dz = c.heightM / div;
    const indices: number[] = [];
    for (let i = 0; i < div; i++) {
      const idx = rings.length;
      rings.push({
        index: idx,
        courseId: c.id,
        zMidM: zCursor + 0.5 * dz,
        dzM: dz,
        thicknessMm: c.thicknessMm,
        hoopHydroMpa: 0,
        hoopSeismicMpa: 0,
        hoopTotalMpa: 0,
      });
      indices.push(idx);
      ringToCourse.set(idx, c.id);
      zCursor += dz;
    }
    courseToRings.set(c.id, indices);
  }

  frameToElements.set("TOP-WIND-GIRDER", rings.length > 0 ? [rings.length - 1] : []);

  return {
    rings,
    mapping: { courseToRings, ringToCourse, frameToElements },
  };
}
