export interface SemanticShellCourse {
  id: string;
  heightM: number;
  thicknessMm: number;
}

export interface TankCourseMapping {
  courseToRings: Map<string, number[]>;
  ringToCourse: Map<number, string>;
  frameToElements: Map<string, number[]>;
}

export interface TankShellRing {
  index: number;
  courseId: string;
  zMidM: number;
  dzM: number;
  thicknessMm: number;
  hoopHydroMpa: number;
  hoopSeismicMpa: number;
  hoopTotalMpa: number;
}

export interface TankResult {
  rings: TankShellRing[];
  mapping: TankCourseMapping;
  convectivePeriodS: number;
  impulsiveMassRatio: number;
  convectiveMassRatio: number;
  maxHoopMpa: number;
}
