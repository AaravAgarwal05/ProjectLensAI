import type { Metadata } from 'next'
import { Providers } from './providers'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'ProjectLens AI',
    template: '%s | ProjectLens AI',
  },
  description: 'Precision Intelligence for your Data Ecosystem',
  icons: { icon: '/Logo.png' },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Geist font */}
        <link
          href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&family=JetBrains+Mono:wght@100..800&family=Fraunces:opsz,wght@9..144,400..700&display=swap"
          rel="stylesheet"
        />
        {/* Material Symbols */}
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        {/* Apply saved appearance (theme / accent / density) before paint to avoid FOUC */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var d=document.documentElement;d.setAttribute('data-theme',localStorage.getItem('lens.theme')||'obsidian');d.setAttribute('data-accent',localStorage.getItem('lens.accent')||'#c0c1ff');if(localStorage.getItem('lens.density')==='high')d.setAttribute('data-density','high');}catch(e){}})();`,
          }}
        />
      </head>
      <body className="min-h-screen antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
