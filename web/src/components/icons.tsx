interface IconProps {
  className?: string;
}

const base = "h-5 w-5";

export const BrandMark = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M2 12c2.5 0 3-7 5.5-7S10 19 12.5 19 15 12 17.5 12H22" />
  </svg>
);

export const ChatIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a8 8 0 01-8 8H8l-4 3v-5.5A8 8 0 1121 12z" />
  </svg>
);

export const DatabaseIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <ellipse cx="12" cy="6" rx="8" ry="3" />
    <path strokeLinecap="round" d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6" />
    <path strokeLinecap="round" d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" />
  </svg>
);

export const GraphIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <circle cx="6" cy="6" r="2.5" />
    <circle cx="18" cy="10" r="2.5" />
    <circle cx="8" cy="18" r="2.5" />
    <path strokeLinecap="round" d="M8.2 7.3l7.4 2M7.2 15.6l1.6-5.2M15.9 11.9L9.9 16.4" />
  </svg>
);

export const CodeIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 8l-4 4 4 4M15 8l4 4-4 4" />
  </svg>
);

export const SettingsIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <circle cx="12" cy="12" r="3" />
    <path
      strokeLinecap="round"
      d="M12 3v2m0 14v2M4.2 7.5l1.7 1M18.1 15.5l1.7 1M4.2 16.5l1.7-1M18.1 8.5l1.7-1"
    />
  </svg>
);

export const MicIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path strokeLinecap="round" d="M5 11a7 7 0 0014 0M12 18v3" />
  </svg>
);

export const SendIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 12h15M13 6l6 6-6 6" />
  </svg>
);

export const DocIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M14 3v5h5" />
  </svg>
);

export const CheckCircleIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <circle cx="12" cy="12" r="9" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.5 12.5l2.5 2.5 4.5-5" />
  </svg>
);

export const ArrowRightIcon = ({ className = "h-4 w-4" }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h13M12 6l6 6-6 6" />
  </svg>
);

export const CalculatorIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <rect x="5" y="3" width="14" height="18" rx="2" />
    <path strokeLinecap="round" d="M8 7h8M8.5 12h.01M12 12h.01M15.5 12h.01M8.5 16h.01M12 16h.01M15.5 16h.01" />
  </svg>
);

export const GlobeIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <circle cx="12" cy="12" r="9" />
    <path strokeLinecap="round" d="M3 12h18M12 3c2.5 2.6 2.5 15.4 0 18M12 3c-2.5 2.6-2.5 15.4 0 18" />
  </svg>
);

export const HeadsetIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" d="M4 14v-2a8 8 0 1116 0v2" />
    <rect x="2.5" y="14" width="4" height="6" rx="2" />
    <rect x="17.5" y="14" width="4" height="6" rx="2" />
    <path strokeLinecap="round" d="M19.5 20a3 3 0 01-3 3H13" />
  </svg>
);

export const BookIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.5C10.5 5 8.5 4.5 4 4.5v13c4.5 0 6.5.5 8 2 1.5-1.5 3.5-2 8-2v-13c-4.5 0-6.5.5-8 2z" />
    <path strokeLinecap="round" d="M12 6.5v13" />
  </svg>
);

export const UserIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
    <circle cx="12" cy="8" r="3.5" />
    <path strokeLinecap="round" d="M5 20a7 7 0 0114 0" />
  </svg>
);

export const SparkIcon = ({ className = base }: IconProps) => (
  <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.6">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3zM18 15l.8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8L18 15z"
    />
  </svg>
);
