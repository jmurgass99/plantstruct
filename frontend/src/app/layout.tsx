import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'IndustrialJm',
  description: 'Industrial structures — tanks, silos, shell buckling',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  )
}
