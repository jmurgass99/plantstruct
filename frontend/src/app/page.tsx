import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-3">IndustrialJm</h1>
        <p className="text-slate-400 mb-8">
          Tanques API 650, anclajes y pandeo de cascarón.
        </p>
        <Link href="/buckling" className="inline-block px-5 py-3 rounded bg-blue-600 hover:bg-blue-700 text-white">
          Visor pandeo 3D
        </Link>
      </div>
    </main>
  )
}
