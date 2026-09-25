import type sample from '../data/demo.json';

export type Project = (typeof sample.projects)[number];
export type PortfolioData = Omit<typeof sample, 'resume'> & {
  resume: { title: string; summary: string; file_url: string | null } | null;
};
export type Section =
  | 'Overview'
  | 'About me'
  | 'Projects'
  | 'Skills'
  | 'Experience'
  | 'Education'
  | 'Certificates'
  | 'Resume'
  | 'Contact';
export const sectionSlug = (section: Section) =>
  section.toLowerCase().replaceAll(' ', '-');
export const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(
  /\/$/,
  '',
);
// Empty loading state only. Personal content always comes from Django.
export const initialPortfolio: PortfolioData = {
  profile: {
    name: '',
    headline: '',
    location: '',
    intro: '',
    bio: '',
    about: '',
    email: '',
    github_url: '',
    linkedin_url: '',
    avatar_url: '',
    available: false,
    is_demo: false,
  },
  projects: [],
  skills: [],
  experience: [],
  education: [],
  certificates: [],
  resume: null,
};

export function safeUrl(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  try {
    const url = new URL(
      value,
      typeof window === 'undefined'
        ? 'https://portfolio.invalid'
        : window.location.origin,
    );
    return ['https:', 'http:'].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}

export function dateLabel(value: string | null): string {
  if (!value) return 'Present';
  const date = new Date(value + 'T00:00:00');
  return Number.isNaN(date.getTime())
    ? ''
    : new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric' }).format(
        date,
      );
}

export async function loadPortfolio(
  signal: AbortSignal,
): Promise<PortfolioData> {
  const response = await fetch(`${apiBase}/portfolio/site/`, {
    signal,
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });
  if (!response.ok)
    throw new Error(`Portfolio request failed (${response.status})`);
  const data = (await response.json()) as Record<string, unknown>;
  if (
    !data ||
    typeof data !== 'object' ||
    !data.profile ||
    typeof data.profile !== 'object' ||
    !('name' in data.profile) ||
    typeof data.profile.name !== 'string' ||
    !['projects', 'skills', 'experience', 'education', 'certificates'].every(
      (key) => Array.isArray(data[key]),
    )
  ) {
    throw new Error('The portfolio response is incomplete.');
  }
  return data as PortfolioData;
}
