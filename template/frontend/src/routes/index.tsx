import { createFileRoute, Link } from '@tanstack/react-router'
import '@/styles/home.css'

export const Route = createFileRoute('/')({
  component: HomePage,
})

const features = [
  {
    title: 'TanStack Start SSR',
    description: 'Server-side rendering with React for blazing fast initial loads',
    number: '01',
    color: 'lime',
  },
  {
    title: 'FastAPI Backend',
    description: 'Modern Python async API with automatic OpenAPI docs',
    number: '02',
    color: 'cyan',
  },
  {
    title: 'PostgreSQL + SQLAlchemy',
    description: 'Rock-solid async database layer with migrations',
    number: '03',
    color: 'purple',
  },
  {
    title: 'Authentication Built-in',
    description: 'Session-based auth ready to customize',
    number: '04',
    color: 'orange',
  },
  {
    title: 'Docker Compose',
    description: 'One command to spin up your entire stack',
    number: '05',
    color: 'blue',
  },
  {
    title: 'Type-Safe Everything',
    description: 'TypeScript frontend + Pydantic backend = zero runtime surprises',
    number: '06',
    color: 'pink',
  },
]

const techStack = [
  { name: 'React 19', category: 'Frontend' },
  { name: 'TanStack Router', category: 'Frontend' },
  { name: 'TanStack Query', category: 'Frontend' },
  { name: 'Tailwind CSS v4', category: 'Frontend' },
  { name: 'shadcn/ui', category: 'Frontend' },
  { name: 'FastAPI', category: 'Backend' },
  { name: 'SQLAlchemy 2.0', category: 'Backend' },
  { name: 'PostgreSQL', category: 'Backend' },
  { name: 'Alembic', category: 'Backend' },
  { name: 'Pydantic v2', category: 'Backend' },
]

function HomePage() {
  return (
    <div className="demo-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-noise" />
        <div className="hero-grid" />

        <div className="hero-content loaded">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            PRODUCTION READY
          </div>

          <h1 className="hero-title">
            <span className="hero-title-line" style={{ animationDelay: '0ms' }}>
              Full-Stack
            </span>
            <span className="hero-title-line" style={{ animationDelay: '100ms' }}>
              Template
            </span>
            <span className="hero-title-line accent" style={{ animationDelay: '200ms' }}>
              That Works
            </span>
          </h1>

          <p className="hero-subtitle" style={{ animationDelay: '400ms' }}>
            Stop wiring up boilerplate. Start building features.
            <br />
            FastAPI + TanStack Start + PostgreSQL in one command.
          </p>

          <div className="hero-cta-group" style={{ animationDelay: '600ms' }}>
            <Link to="/register" className="cta-primary">
              <span>Get Started</span>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </Link>
            <Link to="/login" className="cta-secondary">
              Sign In
            </Link>
          </div>
        </div>

        <div className="hero-visual loaded">
          <div className="terminal-window" style={{ animationDelay: '800ms' }}>
            <div className="terminal-header">
              <div className="terminal-dots">
                <span />
                <span />
                <span />
              </div>
              <div className="terminal-title">docker-compose up</div>
            </div>
            <div className="terminal-body">
              <div className="terminal-line" style={{ animationDelay: '1000ms' }}>
                <span className="terminal-prompt">$</span> docker-compose up
              </div>
              <div className="terminal-line success" style={{ animationDelay: '1200ms' }}>
                ✓ Frontend ready on http://localhost:3000
              </div>
              <div className="terminal-line success" style={{ animationDelay: '1400ms' }}>
                ✓ Backend API on http://localhost:8000
              </div>
              <div className="terminal-line success" style={{ animationDelay: '1600ms' }}>
                ✓ Database running on port 5432
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="features-section">
        <div className="section-header">
          <h2 className="section-title">
            Everything You Need
            <span className="section-title-underline" />
          </h2>
          <p className="section-description">
            Not another half-baked starter. This is the real deal.
          </p>
        </div>

        <div className="features-grid">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className={`feature-card feature-card-${feature.color}`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="feature-number">{feature.number}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
              <div className="feature-line" />
            </div>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="tech-section">
        <div className="tech-container">
          <div className="tech-header">
            <h2 className="tech-title">Modern Stack</h2>
            <p className="tech-subtitle">
              Built with tools you actually want to use
            </p>
          </div>

          <div className="tech-columns">
            <div className="tech-column">
              <div className="tech-column-label">Frontend</div>
              <div className="tech-list">
                {techStack
                  .filter((tech) => tech.category === 'Frontend')
                  .map((tech, index) => (
                    <div
                      key={tech.name}
                      className="tech-item"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className="tech-item-dot" />
                      {tech.name}
                    </div>
                  ))}
              </div>
            </div>

            <div className="tech-divider" />

            <div className="tech-column">
              <div className="tech-column-label">Backend</div>
              <div className="tech-list">
                {techStack
                  .filter((tech) => tech.category === 'Backend')
                  .map((tech, index) => (
                    <div
                      key={tech.name}
                      className="tech-item"
                      style={{ animationDelay: `${index * 50 + 250}ms` }}
                    >
                      <div className="tech-item-dot" />
                      {tech.name}
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2 className="cta-title">
            Ready to Ship?
          </h2>
          <p className="cta-description">
            Clone, customize, deploy. No PhD required.
          </p>
          <div className="cta-actions">
            <Link to="/register" className="cta-btn-primary">
              Start Building
              <span className="cta-btn-arrow">→</span>
            </Link>
            <Link to="/login" className="cta-btn-ghost">
              Sign In
            </Link>
          </div>
        </div>
        <div className="cta-background" />
      </section>
    </div>
  )
}
