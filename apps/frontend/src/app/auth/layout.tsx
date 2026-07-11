/**
 * Auth layout — dark centered canvas for login/register/password routes.
 * No sidebar, no dashboard chrome.
 */

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-[#000000] text-on-surface antialiased flex items-center justify-center p-md relative overflow-hidden">
      {/* Atmospheric background spheres */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-primary/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-secondary/10 blur-[100px] rounded-full" />
      </div>

      <main className="relative z-10 w-full max-w-[420px]">
        {children}
      </main>
    </div>
  )
}
