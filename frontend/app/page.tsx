'use client';

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import {
  ArrowLeft,
  ArrowUpRight,
  Award,
  BriefcaseBusiness,
  ChevronRight,
  Code2,
  ExternalLink,
  FileText,
  Folder,
  GraduationCap,
  Home,
  Mail,
  Maximize2,
  Minus,
  Moon,
  RefreshCw,
  Search,
  Settings2,
  Sun,
  Terminal,
  UserRound,
  X,
} from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarProvider,
} from '@/components/ui/sidebar';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { Switch } from '@/components/ui/switch';
import {
  About,
  Certificates,
  Contact,
  Education,
  Experience,
  Overview,
  ProjectArtwork,
  Projects,
  Resume,
  Skills,
} from '@/components/portfolio-panels';
import { useTheme } from '@/lib/theme';
import {
  loadPortfolio,
  safeUrl,
  initialPortfolio,
  sectionSlug,
  type PortfolioData,
  type Project,
  type Section,
} from '@/lib/portfolio';

const sections: { name: Section; icon: typeof Home }[] = [
  { name: 'Overview', icon: Home },
  { name: 'About me', icon: UserRound },
  { name: 'Projects', icon: Folder },
  { name: 'Skills', icon: Code2 },
  { name: 'Experience', icon: BriefcaseBusiness },
  { name: 'Education', icon: GraduationCap },
  { name: 'Certificates', icon: Award },
  { name: 'Resume', icon: FileText },
  { name: 'Contact', icon: Mail },
];
const panels = {
  Overview: Overview,
  'About me': About,
  Projects: Projects,
  Skills: Skills,
  Experience: Experience,
  Education: Education,
  Certificates: Certificates,
  Resume: Resume,
  Contact: Contact,
};
const dockApps: { name: Section; icon: typeof Home; color: string }[] = [
  { name: 'Overview', icon: Home, color: 'blue' },
  { name: 'Projects', icon: Folder, color: 'blue' },
  { name: 'About me', icon: UserRound, color: 'violet' },
  { name: 'Skills', icon: Terminal, color: 'black' },
  { name: 'Resume', icon: FileText, color: 'white' },
  { name: 'Contact', icon: Mail, color: 'green' },
];

function IconButton({
  label,
  children,
  onClick,
}: {
  label: string;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <button
            className="icon-button"
            aria-label={label}
            onClick={onClick}
          />
        }
      >
        {children}
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}

export default function Portfolio() {
  const [data, setData] = useState<PortfolioData>(initialPortfolio);
  const [connection, setConnection] = useState<'loading' | 'live' | 'offline'>(
    'loading',
  );
  const [section, setSection] = useState<Section>('Overview');
  const [clock, setClock] = useState('');
  const [minimized, setMinimized] = useState(false);
  const [maximized, setMaximized] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [preferences, setPreferences] = useState(false);
  const [dark, setDark] = useTheme();
  const [project, setProject] = useState<Project | null>(null);
  const [reload, setReload] = useState(0);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const scrollRef = useRef<HTMLElement>(null);
  const windowRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{
    x: number;
    y: number;
    left: number;
    top: number;
    width: number;
    height: number;
    offsetX: number;
    offsetY: number;
  } | null>(null);
  const { profile } = data;
  const Panel = panels[section];

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    let active = true;
    loadPortfolio(controller.signal)
      .then((value) => {
        if (active) {
          setData(value);
          setConnection('live');
        }
      })
      .catch(() => {
        if (active) setConnection('offline');
      });
    return () => {
      active = false;
      clearTimeout(timeout);
      controller.abort();
    };
  }, [reload]);

  useEffect(() => {
    // Recheck the existing API when returning from the CMS, without a rebuild.
    let timer: ReturnType<typeof setTimeout>;
    const refresh = () => {
      if (document.visibilityState !== 'visible') return;
      clearTimeout(timer);
      timer = setTimeout(() => setReload((value) => value + 1), 150);
    };
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, []);

  useEffect(() => {
    const tick = () =>
      setClock(
        new Intl.DateTimeFormat('en', {
          weekday: 'short',
          hour: 'numeric',
          minute: '2-digit',
        }).format(new Date()),
      );
    tick();
    const timer = setInterval(tick, 30000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
  useEffect(() => {
    const sync = () => {
      const [slug, projectSlug] = window.location.hash.slice(1).split('/');
      const match = sections.find((s) => sectionSlug(s.name) === slug);
      setSection(match?.name || 'Overview');
      setProject(
        projectSlug
          ? data.projects.find((p) => p.slug === projectSlug) || null
          : null,
      );
      setMinimized(false);
    };
    sync();
    window.addEventListener('hashchange', sync);
    return () => window.removeEventListener('hashchange', sync);
  }, [data]);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 0 });
    document.title = profile.name
      ? `${section} | ${profile.name}`
      : 'Portfolio OS';
    document
      .querySelector('meta[name="description"]')
      ?.setAttribute(
        'content',
        profile.bio || 'A personal portfolio workspace.',
      );
  }, [section, profile.name, profile.bio]);

  const navigate = useCallback((name: Section) => {
    setSection(name);
    setProject(null);
    setMinimized(false);
    setSearchOpen(false);
    window.location.hash = sectionSlug(name);
  }, []);
  function openProject(value: Project) {
    setProject(value);
    setSearchOpen(false);
    setSection('Projects');
    window.location.hash = `projects/${value.slug}`;
  }
  function closeProject() {
    setProject(null);
    window.location.hash = 'projects';
  }
  function toggleMaximize() {
    setMaximized((v) => !v);
    setOffset({ x: 0, y: 0 });
  }

  return (
    <TooltipProvider>
      <div className="desktop">
        <a
          className="skip-link"
          href="#content"
          onClick={(e) => {
            e.preventDefault();
            scrollRef.current?.focus();
          }}
        >
          Skip to content
        </a>
        <header className="menubar">
          <div className="menubar-left">
            <button onClick={() => navigate('Overview')} className="os-brand">
              <Terminal size={17} />
              <strong>
                {(profile.name.split(' ')[0] || 'portfolio').toLowerCase()}
                <span>.os</span>
              </strong>
            </button>
            <span className="menu-current">Portfolio</span>
            <button onClick={() => navigate('Projects')}>Work</button>
            <button onClick={() => navigate('Contact')}>Connect</button>
          </div>
          <div className="menubar-right">
            <span className="availability">
              <i />
              {profile.available ? 'Available for work' : 'Focused on building'}
            </span>
            <IconButton
              label="Search portfolio"
              onClick={() => setSearchOpen(true)}
            >
              <Search size={15} />
            </IconButton>
            <time>{clock}</time>
          </div>
        </header>
        <nav className="desktop-shortcuts" aria-label="Desktop shortcuts">
          {dockApps
            .filter((a) =>
              ['About me', 'Projects', 'Resume', 'Contact'].includes(a.name),
            )
            .map(({ name, icon: Icon, color }) => (
              <button key={name} onClick={() => navigate(name)}>
                <span className={'app-icon ' + color}>
                  <Icon />
                </span>
                <span>{name === 'Projects' ? 'My projects' : name}</span>
              </button>
            ))}
        </nav>
        <div
          ref={windowRef}
          style={
            !maximized
              ? { transform: `translate(${offset.x}px,${offset.y}px)` }
              : undefined
          }
          className={
            'workspace-window ' +
            (maximized ? 'maximized ' : '') +
            (minimized ? 'minimized' : '')
          }
        >
          <header
            className="window-titlebar"
            onDoubleClick={(e) => {
              if (!(e.target as HTMLElement).closest('button'))
                toggleMaximize();
            }}
            onPointerDown={(e) => {
              if (
                maximized ||
                window.innerWidth < 761 ||
                (e.target as HTMLElement).closest('button') ||
                !windowRef.current
              )
                return;
              const rect = windowRef.current.getBoundingClientRect();
              drag.current = {
                x: e.clientX,
                y: e.clientY,
                left: rect.left,
                top: rect.top,
                width: rect.width,
                height: rect.height,
                offsetX: offset.x,
                offsetY: offset.y,
              };
              e.currentTarget.setPointerCapture(e.pointerId);
            }}
            onPointerMove={(e) => {
              const d = drag.current;
              if (!d) return;
              const dx = Math.max(
                8 - d.left,
                Math.min(
                  window.innerWidth - d.left - d.width - 8,
                  e.clientX - d.x,
                ),
              );
              const dy = Math.max(
                40 - d.top,
                Math.min(window.innerHeight - d.top - 80, e.clientY - d.y),
              );
              setOffset({ x: d.offsetX + dx, y: d.offsetY + dy });
            }}
            onPointerUp={() => {
              drag.current = null;
            }}
            onPointerCancel={() => {
              drag.current = null;
            }}
          >
            <div className="traffic-lights">
              <IconButton
                label="Close window"
                onClick={() => setMinimized(true)}
              >
                <X size={10} />
              </IconButton>
              <IconButton
                label="Minimize window"
                onClick={() => setMinimized(true)}
              >
                <Minus size={10} />
              </IconButton>
              <IconButton
                label={maximized ? 'Restore window' : 'Maximize window'}
                onClick={toggleMaximize}
              >
                <Maximize2 size={9} />
              </IconButton>
            </div>
            <span>
              <Folder size={15} />
              {profile.name
                ? `${profile.name.split(' ')[0]}'s workspace`
                : 'Portfolio workspace'}
            </span>
            <span className="titlebar-label">PERSONAL PORTFOLIO</span>
          </header>
          <SidebarProvider className="window-body">
            <Sidebar collapsible="none" className="portfolio-sidebar">
              <div className="sidebar-profile">
                <div className="avatar-small">
                  {profile.name
                    .split(' ')
                    .map((s) => s[0])
                    .slice(0, 2)
                    .join('')
                    .toLowerCase()}
                  <span />
                </div>
                <div>
                  <strong>{profile.name}</strong>
                  <span>{profile.headline}</span>
                </div>
              </div>
              <SidebarContent>
                <p className="nav-heading">WORKSPACE</p>
                <nav aria-label="Portfolio sections">
                  {sections.map(({ name, icon: Icon }) => (
                    <button
                      key={name}
                      onClick={() => navigate(name)}
                      aria-label={name}
                      aria-current={section === name ? 'page' : undefined}
                      className={section === name ? 'active' : ''}
                    >
                      <Icon size={17} />
                      <span>{name}</span>
                      {name === 'Projects' && (
                        <span className="nav-count">
                          {data.projects.length}
                        </span>
                      )}
                    </button>
                  ))}
                </nav>
              </SidebarContent>
              <div className="sidebar-bottom">
                {profile.is_demo && (
                  <span className="sample-label">Sample portfolio</span>
                )}
                <span>{profile.location}</span>
                <span className="sidebar-version">
                  Portfolio OS <span>v1.0</span>
                </span>
              </div>
            </Sidebar>
            <div className="window-main">
              <div className="content-toolbar">
                <div className="breadcrumbs">
                  <IconButton
                    label="Back to overview"
                    onClick={() => navigate('Overview')}
                  >
                    <ArrowLeft size={14} />
                  </IconButton>
                  <span>{profile.name}</span>
                  <ChevronRight size={13} />
                  <strong>{section}</strong>
                </div>
                <IconButton
                  label="Search portfolio"
                  onClick={() => setSearchOpen(true)}
                >
                  <Search size={17} />
                </IconButton>
              </div>
              <main
                id="content"
                tabIndex={-1}
                ref={scrollRef}
                className="content-scroll"
              >
                {connection === 'offline' ? (
                  <div className="connection-error">
                    <Folder size={34} />
                    <h1>Temporarily unavailable.</h1>
                    <p>
                      The portfolio could not be loaded. Please try again
                      shortly.
                    </p>
                    <button
                      className="primary-button"
                      onClick={() => (
                        setConnection('loading'),
                        setReload((v) => v + 1)
                      )}
                    >
                      <RefreshCw size={16} />
                      Try again
                    </button>
                  </div>
                ) : connection === 'loading' ? (
                  <output className="connection-error">
                    Loading portfolio...
                  </output>
                ) : (
                  <Panel
                    data={data}
                    navigate={navigate}
                    openProject={openProject}
                    connected={connection === 'live'}
                  />
                )}
              </main>
              <footer className="window-status">
                <span>
                  <i className={connection === 'live' ? '' : 'offline-dot'} />
                  {connection === 'loading'
                    ? 'Connecting...'
                    : connection === 'live'
                      ? 'Workspace up to date'
                      : 'Connection unavailable'}
                  {profile.is_demo && (
                    <span className="mobile-demo"> · Sample content</span>
                  )}
                </span>
                <span>
                  {data.projects.length} projects <span>·</span> Made with care
                </span>
              </footer>
            </div>
          </SidebarProvider>
        </div>
        {minimized && (
          <button
            className="restore-button"
            onClick={() => setMinimized(false)}
          >
            <Folder />
            Open workspace
            <ArrowUpRight size={16} />
          </button>
        )}
        <nav className="dock" aria-label="Quick launch">
          {dockApps.map(({ name, icon: Icon, color }) => (
            <Tooltip key={name}>
              <TooltipTrigger
                render={
                  <button
                    aria-label={'Open ' + name}
                    className={
                      'dock-item ' +
                      (section === name && !minimized ? 'running' : '')
                    }
                    onClick={() => navigate(name)}
                  />
                }
              >
                <span className={'app-icon ' + color}>
                  <Icon />
                </span>
              </TooltipTrigger>
              <TooltipContent>{name}</TooltipContent>
            </Tooltip>
          ))}
          <span className="dock-divider" />
          <IconButton label="Preferences" onClick={() => setPreferences(true)}>
            <Settings2 />
          </IconButton>
        </nav>
        <span className="desktop-caption">
          A workspace. A collection. A little bit of me.
        </span>
        <Dialog open={searchOpen} onOpenChange={setSearchOpen}>
          <DialogContent className="search-dialog">
            <DialogHeader>
              <DialogTitle>Find something</DialogTitle>
              <DialogDescription className="sr-only">
                Search portfolio sections and projects.
              </DialogDescription>
            </DialogHeader>
            <Command>
              <CommandInput placeholder="Search projects, experience, and more..." />
              <CommandList>
                <CommandEmpty>No results found.</CommandEmpty>
                <CommandGroup heading="Workspace">
                  {sections.map(({ name, icon: Icon }) => (
                    <CommandItem
                      key={name}
                      value={name}
                      onSelect={() => navigate(name)}
                    >
                      <Icon size={17} />
                      {name}
                    </CommandItem>
                  ))}
                </CommandGroup>
                <CommandGroup heading="Projects">
                  {data.projects.map((p) => (
                    <CommandItem
                      key={p.slug}
                      value={`${p.title} ${p.technologies.join(' ')}`}
                      onSelect={() => openProject(p)}
                    >
                      <Folder size={17} />
                      {p.title}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </DialogContent>
        </Dialog>
        <Dialog open={preferences} onOpenChange={setPreferences}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Preferences</DialogTitle>
              <DialogDescription>Make yourself at home.</DialogDescription>
            </DialogHeader>
            <div className="preference-row">
              <label htmlFor="theme-switch">
                {dark ? <Moon size={18} /> : <Sun size={18} />}Dark appearance
              </label>
              <Switch
                id="theme-switch"
                checked={dark}
                onCheckedChange={setDark}
              />
            </div>
            <div className="preference-row">
              <span>Portfolio connection</span>
              <span>{connection === 'live' ? 'Connected' : 'Unavailable'}</span>
            </div>
            <button
              className="secondary-button"
              onClick={() => {
                setConnection('loading');
                setReload((v) => v + 1);
                setPreferences(false);
              }}
            >
              <RefreshCw size={15} />
              Refresh content
            </button>
            <button
              className="text-button"
              onClick={() => {
                setOffset({ x: 0, y: 0 });
                setMaximized(false);
                setMinimized(false);
                setPreferences(false);
              }}
            >
              Reset window position
            </button>
          </DialogContent>
        </Dialog>
        <Dialog
          open={!!project}
          onOpenChange={(open) => {
            if (!open) closeProject();
          }}
        >
          <DialogContent className="project-dialog">
            {project && (
              <>
                <ProjectArtwork project={project} large />
                <DialogHeader>
                  <span className="eyebrow">
                    {project.category} · {project.year}
                    {profile.is_demo ? ' · Sample project' : ''}
                  </span>
                  <DialogTitle>{project.title}</DialogTitle>
                  <DialogDescription>{project.summary}</DialogDescription>
                </DialogHeader>
                <p className="project-description">{project.description}</p>
                <div className="tags">
                  {project.technologies.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <div className="project-links">
                  {safeUrl(project.live_url) && (
                    <a
                      className="primary-button"
                      href={safeUrl(project.live_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Visit project
                      <ExternalLink size={15} />
                    </a>
                  )}
                  {safeUrl(project.source_url) && (
                    <a
                      className="secondary-button"
                      href={safeUrl(project.source_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Code2 size={16} />
                      Source code
                    </a>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
