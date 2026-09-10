type Props = { className?: string };

const svg = (className: string | undefined, path: React.ReactNode) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className ?? "h-5 w-5"} aria-hidden>
    {path}
  </svg>
);

export const Icons = {
  logo: ({ className }: Props) => (
    <svg viewBox="0 0 32 32" className={className ?? "h-8 w-8"} aria-hidden>
      <circle cx="16" cy="16" r="16" fill="#2f9e44" />
      <path d="M16 24v-8" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
      <path d="M16 16c-4-1-6-5-6-8 4 1 6 5 6 8z" fill="#d8f3dc" />
      <path d="M16 16c4-1 6-5 6-8-4 1-6 5-6 8z" fill="#fff" />
    </svg>
  ),
  grid: (p: Props) => svg(p.className, <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>),
  users: (p: Props) => svg(p.className, <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></>),
  megaphone: (p: Props) => svg(p.className, <><path d="M3 11v2a1 1 0 0 0 1 1h2l6 4V6L6 10H4a1 1 0 0 0-1 1z" /><path d="M15.5 8.5a5 5 0 0 1 0 7" /><path d="M8 15v4a2 2 0 0 0 2 2h1" /></>),
  cloud: (p: Props) => svg(p.className, <><path d="M20 17.5A4.5 4.5 0 0 0 17 10h-1.3A6.5 6.5 0 1 0 4.5 16.5" /><path d="M8 19h11a3 3 0 0 0 0-6" /></>),
  chart: (p: Props) => svg(p.className, <><path d="M3 3v18h18" /><path d="M7 14l4-4 4 3 5-6" /></>),
  truck: (p: Props) => svg(p.className, <><path d="M3 7h11v10H3z" /><path d="M14 10h4l3 3v4h-7z" /><circle cx="7" cy="18" r="2" /><circle cx="18" cy="18" r="2" /></>),
  file: (p: Props) => svg(p.className, <><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" /></>),
  gear: (p: Props) => svg(p.className, <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></>),
  bell: (p: Props) => svg(p.className, <><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 0 0 4 0" /></>),
  menu: (p: Props) => svg(p.className, <><path d="M4 6h16M4 12h16M4 18h16" /></>),
  close: (p: Props) => svg(p.className, <><path d="M6 6l12 12M18 6L6 18" /></>),
  userPlus: (p: Props) => svg(p.className, <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M19 8v6M22 11h-6" /></>),
  tag: (p: Props) => svg(p.className, <><path d="M20.6 13.4 12 22l-9-9 8.6-8.6A2 2 0 0 1 13 4h6v6a2 2 0 0 1-.4 1.4z" /><circle cx="16" cy="8" r="1" /></>),
  briefcase: (p: Props) => svg(p.className, <><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></>),
  sun: (p: Props) => svg(p.className, <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>),
  rain: (p: Props) => svg(p.className, <><path d="M20 17.5A4.5 4.5 0 0 0 17 10h-1.3A6.5 6.5 0 1 0 4.5 16.5" /><path d="M8 19v2M12 18v3M16 19v2" /></>),
  home: (p: Props) => svg(p.className, <><path d="M3 11 12 3l9 8" /><path d="M5 10v10h14V10" /></>),
  chat: (p: Props) => svg(p.className, <><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></>),
  plus: (p: Props) => svg(p.className, <><path d="M12 5v14M5 12h14" /></>),
  trendUp: (p: Props) => svg(p.className, <><path d="M4 16l6-6 4 4 6-8" /><path d="M14 6h6v6" /></>),
  logout: (p: Props) => svg(p.className, <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></>),
};

export type IconName = keyof typeof Icons;
