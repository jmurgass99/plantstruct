import * as THREE from "three";
import type { TankResult } from "../data-model.ts";

export function createTankViewer3D(container: HTMLElement): {
  update: (diameterM: number, liquidHeightM: number, res: TankResult) => void;
} {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x060a12);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 250);
  camera.position.set(22, 14, 24);
  camera.lookAt(0, 4.5, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  container.appendChild(renderer.domElement);

  const ambient = new THREE.AmbientLight(0xffffff, 0.72);
  const dir = new THREE.DirectionalLight(0xffffff, 0.9);
  dir.position.set(16, 25, 18);
  scene.add(ambient, dir);

  const group = new THREE.Group();
  scene.add(group);

  let waveSurface: THREE.Mesh | null = null;
  let phase = 0;

  const resize = () => {
    const w = container.clientWidth || 640;
    const h = container.clientHeight || 480;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener("resize", resize);
  setTimeout(resize, 0);

  const animate = () => {
    requestAnimationFrame(animate);
    phase += 0.035;
    if (waveSurface) {
      waveSurface.rotation.z = Math.sin(phase) * 0.085;
    }
    group.rotation.y += 0.002;
    renderer.render(scene, camera);
  };
  animate();

  return {
    update(diameterM: number, liquidHeightM: number, res: TankResult) {
      while (group.children.length > 0) group.remove(group.children[0]);
      const radius = diameterM / 2;
      const sMax = Math.max(res.maxHoopMpa, 1);

      for (const r of res.rings) {
        const ratio = Math.min(1, r.hoopTotalMpa / sMax);
        const color = new THREE.Color().setHSL(0.55 * (1 - ratio), 0.85, 0.5);
        const cylGeo = new THREE.CylinderGeometry(radius, radius, r.dzM * 0.94, 36, 1, true);
        const cylMat = new THREE.MeshStandardMaterial({
          color,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.76,
        });
        const ringMesh = new THREE.Mesh(cylGeo, cylMat);
        ringMesh.position.set(0, r.zMidM, 0);
        group.add(ringMesh);
      }

      // Superficie libre del líquido con modo convectivo de chapoteo
      const surfGeo = new THREE.CylinderGeometry(radius * 0.96, radius * 0.96, 0.25, 32);
      const surfMat = new THREE.MeshStandardMaterial({
        color: 0x06b6d4,
        transparent: true,
        opacity: 0.8,
      });
      waveSurface = new THREE.Mesh(surfGeo, surfMat);
      waveSurface.position.set(0, liquidHeightM, 0);
      group.add(waveSurface);
    },
  };
}
