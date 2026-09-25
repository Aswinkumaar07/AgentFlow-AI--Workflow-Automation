import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

type LandingTheme = 'light' | 'dark';

interface LandingThemeCtx {
  theme: LandingTheme;
  toggle: () => void;
}

const Ctx = createContext<LandingThemeCtx>({ theme: 'light', toggle: () => {} });

export function LandingThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<LandingTheme>(() => {
    return (localStorage.getItem('landing-theme') as LandingTheme) ?? 'dark';
  });

  useEffect(() => {
    // Apply class to a wrapper div — NOT to <html> so app theme is unaffected
    localStorage.setItem('landing-theme', theme);
  }, [theme]);

  const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  return (
    <Ctx.Provider value={{ theme, toggle }}>
      <div className={theme} style={{ colorScheme: theme }}>
        {children}
      </div>
    </Ctx.Provider>
  );
}

export function useLandingTheme() {
  return useContext(Ctx);
}
