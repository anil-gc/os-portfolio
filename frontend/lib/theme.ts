import { useSyncExternalStore } from 'react';

let temporaryTheme: boolean | undefined;

function getTheme() {
  if (temporaryTheme !== undefined) return temporaryTheme;
  try {
    return localStorage.getItem('portfolio-theme') === 'dark';
  } catch {
    return false;
  }
}

function subscribe(listener: () => void) {
  window.addEventListener('storage', listener);
  window.addEventListener('portfolio-theme-change', listener);
  return () => {
    window.removeEventListener('storage', listener);
    window.removeEventListener('portfolio-theme-change', listener);
  };
}

export function useTheme(): [boolean, (dark: boolean) => void] {
  const dark = useSyncExternalStore(subscribe, getTheme, () => false);
  const setDark = (value: boolean) => {
    temporaryTheme = value;
    try {
      localStorage.setItem('portfolio-theme', value ? 'dark' : 'light');
      temporaryTheme = undefined;
    } catch {
      // Keep the control usable when browser storage is unavailable.
    }
    window.dispatchEvent(new Event('portfolio-theme-change'));
  };
  return [dark, setDark];
}
