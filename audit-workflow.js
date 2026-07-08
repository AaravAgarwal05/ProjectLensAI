export const meta = {
  name: 'codebase-audit-and-summary',
  description: 'Audit the codebase for production-readiness and generate a summary of built features',
  phases: [
    { title: 'Feature Mapping' },
    { title: 'Production Readiness Audit' },
    { title: 'Synthesis' }
  ],
};

phase('Feature Mapping');

const summary = await agent(
  "Analyze the completed milestones based on the repository contents (packages/core, packages/shared, apps/backend src, docs, and tests). Summarize what has been built so far, mapping to Milestones 0, 1, 2, and 2.5.",
  { label: 'feature-mapping', phase: 'Feature Mapping' }
);

phase('Production Readiness Audit');

const audit = await agent(
  "Audit the codebase for production readiness. Review: 1) API authentication & authorization (auth middleware, JWT), 2) Database transaction management, session lifecycle, and exception handling, 3) Security practices (handling secrets, environment variable validation), 4) Test coverage and CI completeness, and 5) Docker containerization configuration (health checks, production config). Classify gaps into CRITICAL, HIGH, MEDIUM, and LOW risks.",
  { label: 'production-audit', phase: 'Production Readiness Audit' }
);

phase('Synthesis');

const finalReport = await agent(
  "Consolidate the findings into a comprehensive, highly detailed production-readiness report (Markdown format). Write the final Markdown report to '/home/aarav/ProjectLens-AI/PRODUCTION_READINESS_REPORT.md'.\n\nInputs:\nSummary Analysis:\n" + summary + "\n\nAudit Analysis:\n" + audit,
  { label: 'consolidate', phase: 'Synthesis' }
);
