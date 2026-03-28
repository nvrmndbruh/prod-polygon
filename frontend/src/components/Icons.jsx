// плейсхолдеры для иконок

export function CheckIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16"
      fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect x="1" y="1" width="14" height="14" rx="2"
        stroke="currentColor" strokeWidth="1.5"/>
      <path d="M4.5 8L7 10.5L11.5 5.5" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function HintIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16"
      fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect x="1" y="1" width="14" height="14" rx="2"
        stroke="currentColor" strokeWidth="1.5"/>
      <path d="M6 6C6 4.9 6.9 4 8 4C9.1 4 10 4.9 10 6C10 7.1 8 8 8 9"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <circle cx="8" cy="11.5" r="0.75" fill="currentColor"/>
    </svg>
  );
}

export function ChevronLeftIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16"
      fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M10 3L5 8L10 13" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function ChevronRightIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16"
      fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M6 3L11 8L6 13" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function GraphIcon({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16"
      fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect x="1" y="1" width="14" height="14" rx="2"
        stroke="currentColor" strokeWidth="1.5"/>
      <circle cx="4.5" cy="8" r="1.5" fill="currentColor"/>
      <circle cx="11.5" cy="5" r="1.5" fill="currentColor"/>
      <circle cx="11.5" cy="11" r="1.5" fill="currentColor"/>
      <path d="M6 8H9.5M6.5 7L10 5.5M6.5 9L10 10.5"
        stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
    </svg>
  );
}