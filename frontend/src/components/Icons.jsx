// Стрелка вправо [>]
export const ArrowRightIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/450)} viewBox="0 0 450 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 200H100V250H0V0H100V50H50V200Z" fill={color}/>
    <path d="M150 50V0H200V50H150ZM200 100V50H250V100H200ZM250 100H300V150H250V100ZM250 200H200V150H250V200ZM200 200V250H150V200H200Z" fill={color}/>
    <path d="M350 250V200H400V50H350V0H450V250H350Z" fill={color}/>
  </svg>
);

// Многоточие
export const DotsIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/450)} viewBox="0 0 450 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 200H100V250H0V0H100V50H50V200Z" fill={color}/>
    <path d="M150 250V200H200V250H150Z" fill={color}/>
    <path d="M250 250V200H300V250H250Z" fill={color}/>
    <path d="M350 250V200H400V50H350V0H450V250H350Z" fill={color}/>
  </svg>
);

// Информация [i]
export const InfoIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (300/350)} viewBox="0 0 350 300" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 250H100V300H0V50H100V100H50V250Z" fill={color}/>
    <path d="M150 50V0H200V50H150ZM200 300H150V100H200V300Z" fill={color}/>
    <path d="M250 300V250H300V100H250V50H350V300H250Z" fill={color}/>
  </svg>
);

// Подсказка / вопрос [?]
export const HintIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/450)} viewBox="0 0 450 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 200H100V250H0V0H100V50H50V200Z" fill={color}/>
    <path d="M150 50V0H250V50H150ZM300 100H250V50H300V100ZM250 100V150H200V100H250ZM200 250V200H250V250H200Z" fill={color}/>
    <path d="M350 250V200H400V50H350V0H450V250H350Z" fill={color}/>
  </svg>
);

// Выход из сессии
export const ExitIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/350)} viewBox="0 0 350 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M250 200V250H200V150H0V100H200V0H250V50H300V100H350V150H300V200H250Z" fill={color}/>
  </svg>
);

// Стрелка вниз [v]
export const ChevronDownIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (150/250)} viewBox="0 0 250 150" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M200 0L250 0L250 50L200 50L200 0ZM150 50L200 50L200 100L150 100L150 50ZM150 100L150 150L100 150L100 100L150 100ZM50 100L50 50L100 50L100 100L50 100ZM50 50L0 50L0 0L50 0L50 50Z" fill={color}/>
  </svg>
);

// Граф
export const GraphIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (245/302)} viewBox="0 0 302 245" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path fillRule="evenodd" clipRule="evenodd" d="M243 133V108H218V133H243Z" fill={color}/>
    <path fillRule="evenodd" clipRule="evenodd" d="M59 108V133H84V108H59Z" fill={color}/>
    <path d="M193 161H109V133H84V183H109V245H193V183H218V133H193V161Z" fill={color}/>
    <path fillRule="evenodd" clipRule="evenodd" d="M59 84H84V58H218V84H243V108H268V84H302V0H218V32H84V0H0V84H34V108H59V84Z" fill={color}/>
  </svg>
);

// Левый сайдбар открыт
export const LeftBarOpenIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/308)} viewBox="0 0 308 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path fillRule="evenodd" clipRule="evenodd" d="M308 250H0V0H308V250ZM25.4967 25.5102V224.49H282.503V25.5102H25.4967Z" fill={color}/>
    <path d="M50.9934 51.0204H127.483V198.98H50.9934V51.0204Z" fill={color}/>
  </svg>
);

// Левый сайдбар закрыт
export const LeftBarCloseIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/308)} viewBox="0 0 308 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path fillRule="evenodd" clipRule="evenodd" d="M308 250H0V0H308V250ZM25.4967 25.5102V224.49H282.503V25.5102H25.4967Z" fill={color}/>
    <path d="M50.9934 51.0204H76.4901V198.98H50.9934V51.0204Z" fill={color}/>
  </svg>
);

// Несколько точек (мультиточка)
export const MultipointIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (50/250)} viewBox="0 0 250 50" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M0 50V0H50V50H0Z" fill={color}/>
    <path d="M100 50V0H150V50H100Z" fill={color}/>
    <path d="M200 50V0H250V50H200Z" fill={color}/>
  </svg>
);

// Свернуть
export const MinimizeIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (150/250)} viewBox="0 0 250 150" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 150L0 150L0 100L50 100L50 150ZM100 100L50 100L50 50L100 50L100 100ZM100 50L100 0L150 0L150 50L100 50ZM200 50L200 100L150 100L150 50L200 50ZM200 100L250 100L250 150L200 150L200 100Z" fill={color}/>
  </svg>
);

// Иконка мониторинга
export const MonitoringIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/500)} viewBox="0 0 500 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 200H100V250H0V0H100V50H50V200Z" fill={color}/>
    <path d="M400 250V200H450V50H400V0H500V250H400Z" fill={color}/>
    <path d="M300 250V0H350V250H300Z" fill={color}/>
    <path d="M275 150V100H225V150V200V250H275V200V150Z" fill={color}/>
    <path d="M200 200V150V100V50H150V100V150V200V250H200V200Z" fill={color}/>
  </svg>
);

// Плюс
export const PlusIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size} viewBox="0 0 150 150" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 150V100H0V50H50V0H100V50H150V100H100V150H50Z" fill={color}/>
  </svg>
);

// Перезагрузка
export const ReloadIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (350/300)} viewBox="0 0 300 350" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M250 350H300V300V150V100H250H200V0H150V50H100V100H50V150H100V200H150V250H200V150H250V300H50V200H0V350H50H250Z" fill={color}/>
  </svg>
);

// Две стрелки (смена окружения)
export const TwoArrowsIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (286/450)} viewBox="0 0 450 286" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M368.182 163.429V204.286H327.273V122.571H163.636V81.7143H327.273V0H368.182V40.8571H409.091V81.7143H450V122.571H409.091V163.429H368.182Z" fill={color}/>
    <path d="M81.8182 245.143V286H122.727V204.286H286.364V163.429H122.727V81.7143H81.8182V122.571H40.9091V163.429H0V204.286H40.9091V245.143H81.8182Z" fill={color}/>
  </svg>
);

// Иконка проверки / галочка
export const CheckIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <svg width={size} height={size * (250/450)} viewBox="0 0 450 250" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M50 200H100V250H0V0H100V50H50V200Z" fill={color}/>
    <path d="M150 50V0H200V50H150ZM200 100V50H250V100H200ZM250 100H300V150H250V100ZM250 200H200V150H250V200ZM200 200V250H150V200H200Z" fill={color}/>
    <path d="M350 250V200H400V50H350V0H450V250H350Z" fill={color}/>
  </svg>
);

export const ChevronLeftIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <ChevronDownIcon
    size={size}
    color={color}
    style={{ transform: 'rotate(90deg)', ...(props.style || {}) }}
    {...props}
  />
);

export const ChevronRightIcon = ({ size = 16, color = 'currentColor', ...props }) => (
  <ChevronDownIcon
    size={size}
    color={color}
    style={{ transform: 'rotate(-90deg)', ...(props.style || {}) }}
    {...props}
  />
);