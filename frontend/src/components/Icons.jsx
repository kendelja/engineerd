// Small inline icons. They inherit colour from the surrounding text.

const base = {
    width: 16,
    height: 16,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
    focusable: false,
};

export function IconPin(props) {
    return (
        <svg {...base} {...props}>
            <path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z" />
            <circle cx="12" cy="9.5" r="2.5" />
        </svg>
    );
}

export function IconHeart({ filled, ...props }) {
    return (
        <svg {...base} {...props} fill={filled ? "currentColor" : "none"}>
            <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z" />
        </svg>
    );
}

export function IconArrow(props) {
    return (
        <svg {...base} {...props}>
            <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
    );
}

export function IconRefresh(props) {
    return (
        <svg {...base} {...props}>
            <path d="M21 12a9 9 0 1 1-2.6-6.3" />
            <path d="M21 4v5h-5" />
        </svg>
    );
}

export function IconChevron(props) {
    return (
        <svg {...base} {...props}>
            <path d="M6 9l6 6 6-6" />
        </svg>
    );
}

export function IconBriefcase(props) {
    return (
        <svg {...base} {...props}>
            <rect x="3" y="7" width="18" height="13" rx="2" />
            <path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18" />
        </svg>
    );
}

export function IconSun(props) {
    return (
        <svg {...base} {...props}>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </svg>
    );
}

export function IconMoon(props) {
    return (
        <svg {...base} {...props}>
            <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
    );
}

// GitHub mark (filled).
export function IconGitHub(props) {
    return (
        <svg
            width={16}
            height={16}
            viewBox="0 0 16 16"
            fill="currentColor"
            aria-hidden="true"
            focusable="false"
            {...props}
        >
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
        </svg>
    );
}

// LinkedIn "in" tile.
export function IconLinkedIn(props) {
    return (
        <svg
            width={16}
            height={16}
            viewBox="0 0 16 16"
            aria-hidden="true"
            focusable="false"
            {...props}
        >
            <rect x="0" y="0" width="16" height="16" rx="3" fill="currentColor" />
            <text
                x="8"
                y="12.4"
                textAnchor="middle"
                fontSize="11"
                fontWeight="800"
                fontFamily="Inter, Arial, sans-serif"
                fill="var(--surface)"
            >
                in
            </text>
        </svg>
    );
}
