'use client';

import { useState, type SyntheticEvent } from 'react';
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Award,
  BriefcaseBusiness,
  Check,
  Code2,
  Copy,
  ExternalLink,
  FileText,
  Folder,
  GraduationCap,
  LayoutGrid,
  Mail,
  MapPin,
  Search,
  Send,
  Terminal,
} from 'lucide-react';
import Image from 'next/image';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import {
  apiBase,
  dateLabel,
  safeUrl,
  type PortfolioData,
  type Project,
  type Section,
} from '@/lib/portfolio';

type Props = {
  data: PortfolioData;
  navigate: (section: Section) => void;
  openProject: (project: Project) => void;
  connected: boolean;
};

export function ProjectArtwork({
  project,
  large = false,
}: {
  project: Project;
  large?: boolean;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const url = safeUrl(project.image_url);
  return (
    <div
      className={`project-visual ${['blue', 'green', 'violet', 'orange'].includes(project.accent) ? project.accent : 'blue'} ${large ? 'large' : ''}`}
    >
      {url && !imageFailed ? (
        <Image
          width={640}
          height={400}
          src={url}
          alt={project.title}
          loading="lazy"
          onError={() => setImageFailed(true)}
        />
      ) : (
        <>
          <span className="project-symbol">
            {project.category === 'Backend' ? (
              <Terminal />
            ) : project.slug === 'fieldnotes' ? (
              <FileText />
            ) : (
              <LayoutGrid />
            )}
          </span>
          <strong>{project.title}</strong>
          <span>{project.category}</span>
        </>
      )}
    </div>
  );
}

function ProjectCard({
  project,
  openProject,
}: {
  project: Project;
  openProject: (project: Project) => void;
}) {
  return (
    <button className="project-card" onClick={() => openProject(project)}>
      <ProjectArtwork project={project} />
      <div className="project-caption">
        <h3>
          {project.title}
          <ArrowUpRight size={15} />
        </h3>
        <p>{project.summary}</p>
        <div className="tags">
          {project.technologies.slice(0, 3).map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
      </div>
    </button>
  );
}

function Heading({
  eyebrow,
  title,
  text,
}: {
  eyebrow: string;
  title: string;
  text?: string;
}) {
  return (
    <header className="panel-heading">
      <span className="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      {text && <p>{text}</p>}
    </header>
  );
}

export function Overview({ data, navigate, openProject }: Props) {
  const { profile, projects } = data;
  return (
    <>
      <div className="welcome-eyebrow">
        <span className="wave" aria-hidden="true">
          ✳
        </span>{' '}
        HELLO, WORLD
      </div>
      <h1>
        I&apos;m {profile.name.split(' ')[0]}
        <span className="accent-dot">.</span>
        <br />
        {profile.intro || 'I build for the web.'}
      </h1>
      <p className="intro">{profile.bio}</p>
      <div className="intro-meta">
        {profile.location && (
          <span>
            <MapPin size={14} />
            {profile.location}
          </span>
        )}
        <span>
          <i />
          {profile.available
            ? 'Open to opportunities'
            : 'Focused on current projects'}
        </span>
      </div>
      <div className="intro-actions">
        <button className="primary-button" onClick={() => navigate('Projects')}>
          Explore my work
          <ArrowRight size={16} />
        </button>
        {data.resume && (
          <button
            className="secondary-button"
            onClick={() => navigate('Resume')}
          >
            <ArrowDownToLine size={16} />
            View resume
          </button>
        )}
      </div>
      <div className="section-heading">
        <div>
          <span className="eyebrow">A FEW THINGS I&apos;VE BUILT</span>
          <h2>Selected work</h2>
        </div>
        <button className="text-button" onClick={() => navigate('Projects')}>
          All projects
          <ArrowUpRight size={16} />
        </button>
      </div>
      <div className="project-grid">
        {projects
          .filter((p) => p.featured)
          .slice(0, 3)
          .map((project) => (
            <ProjectCard
              key={project.slug}
              project={project}
              openProject={openProject}
            />
          ))}
      </div>
      {!projects.some((p) => p.featured) && (
        <Empty text="New work is on the way." />
      )}
      <footer className="overview-footer">
        <span>Good software starts with a conversation.</span>
        <button onClick={() => navigate('Contact')} className="text-button">
          Let&apos;s talk
          <ArrowUpRight size={15} />
        </button>
      </footer>
    </>
  );
}

export function Projects({ data, openProject }: Props) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All work');
  const categories = [
    'All work',
    ...new Set(data.projects.map((p) => p.category)),
  ];
  const projects = data.projects.filter(
    (p) =>
      (category === 'All work' || p.category === category) &&
      `${p.title} ${p.summary} ${p.technologies.join(' ')}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <>
      <Heading
        eyebrow="IDEAS, BUILT INTO THINGS"
        title="My projects"
        text="A collection of experiments, useful tools, and carefully considered experiences."
      />
      <label className="search-field">
        <Search size={17} />
        <input
          aria-label="Search projects"
          placeholder="Search projects or technologies..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <span>{projects.length} results</span>
      </label>
      <Tabs
        value={category}
        onValueChange={(v) => setCategory(String(v))}
        className="project-tabs"
      >
        <TabsList variant="line">
          {categories.map((c) => (
            <TabsTrigger key={c} value={c}>
              {c}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value={category}>
          <div className="project-grid all-projects">
            {projects.map((project) => (
              <ProjectCard
                key={project.slug}
                project={project}
                openProject={openProject}
              />
            ))}
          </div>
          {!projects.length && <Empty text="No projects match your search." />}
        </TabsContent>
      </Tabs>
    </>
  );
}

export function About({ data, navigate }: Props) {
  const p = data.profile;
  const avatarUrl = safeUrl(p.avatar_url);
  return (
    <>
      <Heading
        eyebrow="THE PERSON BEHIND THE PIXELS"
        title="A little about me."
      />
      <div className="about-identity">
        {avatarUrl ? (
          <Image
            width={85}
            height={85}
            className="profile-photo"
            src={avatarUrl}
            alt={p.name}
          />
        ) : (
          <div className="profile-monogram">
            {p.name
              .split(' ')
              .map((s) => s[0])
              .slice(0, 2)
              .join('')}
          </div>
        )}
        <div>
          <h2>{p.name}</h2>
          <p>{p.headline}</p>
          {p.location && (
            <span>
              <MapPin size={14} />
              {p.location}
            </span>
          )}
        </div>
      </div>
      <div className="prose">
        {p.about.split('\n\n').map((paragraph, i) => (
          <p key={i}>{paragraph}</p>
        ))}
      </div>
      <div className="about-principles">
        <div>
          <Code2 />
          <h3>Built with intention</h3>
          <p>Readable code, considered choices, and a foundation that lasts.</p>
        </div>
        <div>
          <LayoutGrid />
          <h3>Made for people</h3>
          <p>
            Accessible, responsive experiences with attention to the small
            details.
          </p>
        </div>
      </div>
      <button className="primary-button" onClick={() => navigate('Contact')}>
        Start a conversation
        <ArrowUpRight size={16} />
      </button>
    </>
  );
}

export function Skills({ data }: Props) {
  return (
    <>
      <Heading
        eyebrow="MY EVERYDAY TOOLKIT"
        title="Tools of the trade."
        text="The languages, frameworks, and tools I work with."
      />
      {[...new Set(data.skills.map((s) => s.category))].map((category) => (
        <section key={category} className="skills-section">
          <h2>{category}</h2>
          <div className="skills-grid">
            {data.skills
              .filter((s) => s.category === category)
              .map((skill) => (
                <div className="skill-item" key={skill.name}>
                  <span className="skill-icon">
                    <Code2 size={19} />
                  </span>
                  <div>
                    <h3>{skill.name}</h3>
                    <span>{skill.level}</span>
                  </div>
                </div>
              ))}
          </div>
        </section>
      ))}
      {!data.skills.length && <Empty text="The toolkit is being updated." />}
    </>
  );
}

export function Experience({ data }: Props) {
  return (
    <>
      <Heading
        eyebrow="LEARNING BY BUILDING"
        title="Where I've been."
        text="The teams, challenges, and experiences that have shaped my work."
      />
      <div className="timeline">
        {data.experience.map((item, i) => (
          <article key={i}>
            <span className="timeline-marker">
              <BriefcaseBusiness size={17} />
            </span>
            <div className="timeline-meta">
              <span>
                {dateLabel(item.start_date)} - {dateLabel(item.end_date)}
              </span>
              {!item.end_date && <span className="current-badge">Current</span>}
            </div>
            <h2>{item.role}</h2>
            <h3>
              {item.company} <span>· {item.location}</span>
            </h3>
            <p>{item.description}</p>
          </article>
        ))}
      </div>
      {!data.experience.length && (
        <Empty text="Experience details are coming soon." />
      )}
    </>
  );
}

export function Education({ data }: Props) {
  return (
    <>
      <Heading eyebrow="A FOUNDATION FOR CURIOSITY" title="Always learning." />
      <div className="timeline">
        {data.education.map((item, i) => (
          <article key={i}>
            <span className="timeline-marker">
              <GraduationCap size={18} />
            </span>
            <div className="timeline-meta">
              {dateLabel(item.start_date)} - {dateLabel(item.end_date)}
            </div>
            <h2>{item.degree}</h2>
            <h3>{item.institution}</h3>
            <p>{item.description}</p>
            <span className="muted-label">
              <MapPin size={13} />
              {item.location}
            </span>
          </article>
        ))}
      </div>
      {!data.education.length && (
        <Empty text="Education details are coming soon." />
      )}
    </>
  );
}

export function Certificates({ data }: Props) {
  return (
    <>
      <Heading
        eyebrow="SMALL MILESTONES, CONTINUED GROWTH"
        title="Certificates."
      />
      <div className="certificate-list">
        {data.certificates.map((item, i) => (
          <article key={i}>
            <div className="certificate-seal">
              <Award size={30} />
            </div>
            <div>
              <span className="eyebrow">{item.issuer}</span>
              <h2>{item.title}</h2>
              <p>{item.description}</p>
              <span className="muted-label">
                Issued {dateLabel(item.issued_date)}
              </span>
              {safeUrl(item.credential_url) && (
                <a
                  className="text-button"
                  href={safeUrl(item.credential_url)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View credential
                  <ExternalLink size={14} />
                </a>
              )}
            </div>
          </article>
        ))}
      </div>
      {!data.certificates.length && (
        <Empty text="Certificates are being updated." />
      )}
    </>
  );
}

export function Resume({ data }: Props) {
  const { profile, resume } = data;
  if (!resume) {
    return (
      <>
        <Heading eyebrow="THE SHORT VERSION" title="My resume." />
        <Empty text="A resume hasn't been added yet." />
      </>
    );
  }
  return (
    <>
      <div className="resume-actions">
        <Heading eyebrow="THE SHORT VERSION" title="My resume." />
        {safeUrl(resume?.file_url) ? (
          <a
            className="primary-button"
            href={safeUrl(resume?.file_url)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ArrowDownToLine size={16} />
            Open PDF
          </a>
        ) : (
          <button className="secondary-button" onClick={() => window.print()}>
            <ArrowDownToLine size={16} />
            Print / save PDF
          </button>
        )}
      </div>
      <article className="resume-document">
        <header>
          <h2>{profile.name}</h2>
          <strong>{profile.headline}</strong>
          <p>
            {profile.location}
            {profile.email && ` · ${profile.email}`}
          </p>
          {profile.is_demo && (
            <span className="sample-label">Sample resume</span>
          )}
        </header>
        <p>{resume?.summary || profile.bio}</p>
        <h3>Experience</h3>
        {data.experience.map((item, i) => (
          <section key={i}>
            <div className="resume-line">
              <strong>
                {item.role} · {item.company}
              </strong>
              <span>
                {dateLabel(item.start_date)} - {dateLabel(item.end_date)}
              </span>
            </div>
            <p>{item.description}</p>
          </section>
        ))}
        <h3>Selected projects</h3>
        {data.projects.slice(0, 3).map((p) => (
          <section key={p.slug}>
            <strong>{p.title}</strong>
            <p>
              {p.summary} {p.technologies.join(', ')}.
            </p>
          </section>
        ))}
        <h3>Skills</h3>
        <p>{data.skills.map((s) => s.name).join(' · ')}</p>
        <h3>Education</h3>
        {data.education.map((item, i) => (
          <p key={i}>
            <strong>{item.degree}</strong>
            <br />
            {item.institution} · {dateLabel(item.end_date)}
          </p>
        ))}
      </article>
    </>
  );
}

export function Contact({ data, connected }: Props) {
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>(
    'idle',
  );
  const [error, setError] = useState('');
  const [consent, setConsent] = useState(false);
  const [copied, setCopied] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  async function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!connected || !consent || status === 'sending') return;
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    setStatus('sending');
    setError('');
    try {
      const response = await fetch(`${apiBase}/contact/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
        signal: AbortSignal.timeout(12000),
      });
      if (!response.ok) {
        if (response.status === 429)
          throw new Error('Too many messages. Please try again in an hour.');
        const details = await response.json().catch(() => null);
        throw new Error(
          details
            ? Object.entries(details)
                .map(([field, message]) => `${field}: ${String(message)}`)
                .join(' ')
            : 'Your message could not be sent. Please try again.',
        );
      }
      setStatus('sent');
      form.reset();
      setConsent(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Your message could not be sent.',
      );
      setStatus('error');
    }
  }
  async function copyEmail() {
    try {
      await navigator.clipboard.writeText(data.profile.email);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError(
        'Copy is unavailable. You can select the email address instead.',
      );
    }
  }
  return (
    <>
      <Heading
        eyebrow="GOOD THINGS START WITH HELLO"
        title="Let's build something."
        text="Have a project in mind, a question, or just want to say hello? I'd love to hear from you."
      />
      <div className="contact-links">
        {data.profile.email && (
          <div>
            <Mail size={18} />
            <span>{data.profile.email}</span>
            <button
              aria-label="Copy email address"
              className="icon-button"
              onClick={copyEmail}
            >
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
          </div>
        )}
        {safeUrl(data.profile.github_url) && (
          <a
            href={safeUrl(data.profile.github_url)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Code2 size={18} />
            GitHub
            <ArrowUpRight size={14} />
          </a>
        )}
        {safeUrl(data.profile.linkedin_url) && (
          <a
            href={safeUrl(data.profile.linkedin_url)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <BriefcaseBusiness size={18} />
            LinkedIn
            <ArrowUpRight size={14} />
          </a>
        )}
      </div>
      {!connected && (
        <p className="notice">
          This preview is not connected to the inbox. No messages can be sent
          right now.
        </p>
      )}
      {status === 'sent' ? (
        <output className="message-success">
          <Check size={30} />
          <h2>Message received.</h2>
          <p>Thanks for reaching out. Your message is in my inbox.</p>
          <button
            className="secondary-button"
            onClick={() => setStatus('idle')}
          >
            Write another message
          </button>
        </output>
      ) : (
        <form onSubmit={submit} className="contact-form">
          <div className="form-row">
            <label>
              Your name
              <input
                name="name"
                autoComplete="name"
                required
                maxLength={100}
                placeholder="Alex Smith"
              />
            </label>
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="email"
                required
                maxLength={254}
                placeholder="alex@company.com"
              />
            </label>
          </div>
          <label>
            Subject
            <input
              name="subject"
              required
              maxLength={160}
              placeholder="A project, an opportunity, an idea..."
            />
          </label>
          <label>
            Your message
            <textarea
              name="message"
              required
              minLength={10}
              maxLength={5000}
              rows={5}
              placeholder="Tell me a little about what you have in mind."
            />
          </label>
          <label className="honeypot" aria-hidden="true">
            Website
            <input name="website" tabIndex={-1} autoComplete="off" />
          </label>
          <div className="consent">
            <Checkbox
              id="consent"
              checked={consent}
              onCheckedChange={(v) => setConsent(v === true)}
            />
            <label htmlFor="consent">
              I agree to share these details to receive a reply.
            </label>
          </div>
          <div className="form-footer">
            <button
              className="primary-button"
              disabled={!connected || !consent || status === 'sending'}
              type="submit"
            >
              {status === 'sending' ? 'Sending...' : 'Send message'}
              <Send size={15} />
            </button>
            <button
              type="button"
              className="text-button"
              onClick={() => setPrivacy(true)}
            >
              Privacy
            </button>
          </div>
        </form>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <Dialog open={privacy} onOpenChange={setPrivacy}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Contact privacy</DialogTitle>
            <DialogDescription>
              Your name, email address, subject, and message are stored in the
              portfolio owner&apos;s private inbox so they can respond. Do not
              include passwords or other sensitive information. Contact the
              owner to request deletion. This form does not subscribe you to a
              mailing list.
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </>
  );
}

export function Empty({ text }: { text: string }) {
  return (
    <div className="empty-state">
      <Folder size={28} />
      <p>{text}</p>
    </div>
  );
}
