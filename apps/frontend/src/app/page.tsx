'use client'

import {
  Brain,
  Zap,
  FileText,
  Users,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import Link from 'next/link'

const features = [
  {
    icon: Brain,
    title: 'Smart Analysis',
    description:
      'AI-powered document analysis that extracts key insights, summaries, and actionable data from any document format.',
  },
  {
    icon: Zap,
    title: 'Instant Insights',
    description:
      'Get real-time analysis results with intelligent recommendations and data visualization for faster decision-making.',
  },
  {
    icon: FileText,
    title: 'Compare Documents',
    description:
      'Side-by-side document comparison with AI-detected differences, changes, and version tracking.',
  },
  {
    icon: Users,
    title: 'Collaborative Workspace',
    description:
      'Share analyses, annotations, and insights with your team in real time. Built for collaboration.',
  },
]

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="fixed top-0 z-50 w-full border-b border-surface-200/80 bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-primary-700">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-surface-900">
              ProjectLens
            </span>
          </div>
          <nav className="hidden items-center gap-8 md:flex">
            <Link
              href="#features"
              className="text-sm font-medium text-surface-600 transition-colors hover:text-surface-900"
            >
              Features
            </Link>
            <Link href="/login" className="btn-secondary text-sm">
              Sign in
            </Link>
            <Link href="/register" className="btn-primary text-sm">
              Get Started
            </Link>
          </nav>
          <Link
            href="/login"
            className="btn-primary text-sm md:hidden"
          >
            Sign in
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative mt-16 overflow-hidden px-4 pb-20 pt-20 sm:px-6 lg:px-8">
        {/* Background gradient */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-b from-primary-50/50 to-white" />
          <div className="absolute left-1/2 top-0 -translate-x-1/2">
            <div className="h-[600px] w-[600px] rounded-full bg-gradient-to-r from-primary-200/30 to-accent-200/30 blur-3xl" />
          </div>
        </div>

        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-1.5 rounded-full border border-primary-200 bg-primary-50 px-4 py-1.5 text-xs font-medium text-primary-700">
              <Sparkles className="h-3.5 w-3.5" />
              AI-Powered Document Intelligence
            </div>
            <h1 className="animate-fade-in text-4xl font-bold tracking-tight text-surface-900 sm:text-5xl lg:text-6xl">
              <span className="bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
                ProjectLens AI
              </span>
            </h1>
            <p className="animate-fade-in-delay-1 mx-auto mt-6 max-w-2xl text-lg leading-8 text-surface-600">
              Unlock insights from your documents with AI-powered analysis.
              Upload, analyze, and collaborate — transform how your team
              extracts intelligence from documents.
            </p>
            <div className="animate-fade-in-delay-2 mt-10 flex items-center justify-center gap-4">
              <Link href="/register" className="btn-primary text-base">
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="#features"
                className="btn-secondary text-base"
              >
                Learn More
              </Link>
            </div>
          </div>

          {/* Hero visual */}
          <div className="animate-fade-in-delay-3 mx-auto mt-16 max-w-5xl">
            <div className="rounded-2xl border border-surface-200 bg-white/60 p-2 shadow-xl backdrop-blur-sm">
              <div className="rounded-xl border border-surface-100 bg-gradient-to-br from-surface-50 to-white p-8">
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2 space-y-3">
                    <div className="h-3 w-48 rounded-full bg-surface-200" />
                    <div className="h-3 w-64 rounded-full bg-surface-100" />
                    <div className="h-3 w-56 rounded-full bg-surface-100" />
                    <div className="mt-4 flex gap-2">
                      <span className="rounded-md bg-primary-100 px-2.5 py-1 text-xs font-medium text-primary-700">
                        Key Insights
                      </span>
                      <span className="rounded-md bg-accent-100 px-2.5 py-1 text-xs font-medium text-accent-700">
                        Summary
                      </span>
                      <span className="rounded-md bg-surface-100 px-2.5 py-1 text-xs font-medium text-surface-600">
                        Analysis
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 p-4">
                    <Brain className="h-12 w-12 text-white" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="px-4 py-24 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-surface-900">
              Everything you need to analyze documents
            </h2>
            <p className="mt-4 text-lg text-surface-600">
              Powerful features that transform how you work with documents,
              powered by advanced AI.
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <div key={feature.title} className="card group">
                <div className="mb-4 inline-flex rounded-lg bg-primary-50 p-3 ring-1 ring-primary-100 transition-colors group-hover:bg-primary-100">
                  <feature.icon className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-surface-900">
                  {feature.title}
                </h3>
                <p className="text-sm leading-6 text-surface-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-24 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600 via-primary-700 to-accent-600 px-8 py-16 text-center shadow-xl sm:px-16">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-20" />
            <div className="relative">
              <h2 className="text-3xl font-bold tracking-tight text-white">
                Ready to transform your document workflow?
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-lg text-primary-100">
                Join teams that use ProjectLens to analyze, understand, and
                act on their documents faster.
              </p>
              <div className="mt-8 flex items-center justify-center gap-4">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-primary-700 shadow-sm transition-all hover:bg-primary-50"
                >
                  Start Free Trial
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-surface-200 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-primary-500 to-primary-700">
                <Sparkles className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="text-sm font-semibold text-surface-900">
                ProjectLens AI
              </span>
            </div>
            <p className="text-sm text-surface-500">
              &copy; {new Date().getFullYear()} ProjectLens AI. All rights
              reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
