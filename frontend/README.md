# IndustrialJm — frontend Next.js

Frontend Next.js 14 (App Router) + TypeScript + Tailwind para estructuras
industriales (tanques API 650, anclajes, pandeo de cascarón).

## Páginas

| Ruta        | Issue        | Descripción                                       |
| ----------- | ------------ | ------------------------------------------------- |
| `/`         | —            | Landing simple                                    |
| `/buckling` | IDEAS_20 #18 | Visor 3D R3F del modo de pandeo (cilindro paramétrico con sliders n_circ / n_long / amplitud) |

## Quickstart

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

Variables:

- `NEXT_PUBLIC_API_URL` — base del backend FastAPI (`industrialjm.api.app`).
  Por defecto `http://localhost:8000`.

## Dependencias notables

- `next@14.2.5`, `react@18`, `tailwindcss@3`
- `@react-three/fiber@8` + `@react-three/drei@9` + `three@0.166`
- `axios` para HTTP

## Estado

Verificación visual **pendiente** — los archivos se escribieron sin levantar
`npm run dev` en este lote (limitación de entorno).
