// Set API_URL at build time (e.g. in Vercel); local dev uses the default.
// vite.config.js maps it to import.meta.env.VITE_API_URL.
export const API_URL =
    import.meta.env.VITE_API_URL || "http://localhost:8000";

// Keep in step with the API's `limit` maximum.
export const JOB_LIMIT = 600;

export const SAVED_KEY = "engineerd-saved-jobs";


// ============================================================
// JUNIOR-FIT LABELS
// ============================================================

// Plain-language copy for each label. `help` shows in the badge
// tooltip and the legend.
export const FIT_INFO = {
    "junior-friendly": {
        label: "Junior-friendly",
        help: "Entry-level, and asks for 0-2 years of experience.",
    },
    "junior-unconfirmed": {
        label: "Junior-Unconfirmed",
        help: "The job board tags this role as junior, but the posting doesn't back that up. Read the details before you apply.",
    },
    "ghost-junior": {
        label: "Ghost junior",
        help: "Labelled junior or entry-level, but the posting actually asks for 3+ years of experience.",
    },
    "stretch": {
        label: "Stretch role",
        help: "Mid-level, or asks for 3-4 years. A reach if you are just starting out.",
    },
    "senior": {
        label: "Senior-level",
        help: "Senior title, or asks for 5+ years of experience.",
    },
    "unverified": {
        label: "Not verified",
        help: "Labelled junior by the job board, but we could not read the posting to confirm what it asks for.",
    },
    "unclear": {
        label: "No level listed",
        help: "No seniority or years of experience found in the posting.",
    },
};

export const LEGEND_ORDER = [
    "junior-friendly",
    "junior-unconfirmed",
    "ghost-junior",
    "stretch",
    "senior",
    "unverified",
    "unclear",
];

// Reasons the "N+ yrs" meter already shows, so they aren't repeated.
const METER_REASON = /^(Asks for|No experience required)/;


// ============================================================
// YEARS-REQUIRED OPTIONS
// ============================================================

// Max years required for each Advanced option. "any" means no limit.
export const ENTRY_MAX_YEARS = {
    any: undefined,
    none: 0,
    "1": 1,
    "2": 2,
};

export const ENTRY_OPTIONS = [
    { value: "any", label: "Any" },
    { value: "none", label: "No experience" },
    { value: "1", label: "0–1 yrs" },
    { value: "2", label: "0–2 yrs" },
];


// ============================================================
// FILTERING
// ============================================================

const SENIOR_TITLE = /\b(senior|sr\.?|staff|principal|lead|director|chief|manager)\b/i;

function levelsOf(job) {
    return (job.experience_level ?? "")
        .toLowerCase()
        .split(",")
        .map((level) => level.trim());
}

// Experience filter. The fit label (years + title) is the primary
// signal, so Junior agrees with the badge. Source tags are a fallback
// for jobs we could not analyse (Wellfound has none).
export function matchesExperience(job, experience) {
    if (experience === "any") {
        return true;
    }

    const title = job.title ?? "";
    const levels = levelsOf(job);

    const clearlySenior = SENIOR_TITLE.test(title);
    const seniorFit = job.fit_label === "senior";
    const juniorFit =
        job.fit_label === "junior-friendly" ||
        job.fit_label === "junior-unconfirmed" ||
        job.fit_label === "ghost-junior";

    const taggedJunior =
        levels.some((level) =>
            ["junior", "entry level/new grad", "entry level", "new grad"].includes(level)
        ) &&
        !levels.some((level) =>
            ["mid level", "senior", "expert", "expert or higher"].includes(level)
        );

    const taggedSenior = levels.some((level) =>
        ["mid level", "senior", "expert", "expert or higher"].includes(level)
    );

    if (experience === "junior") {
        return !clearlySenior && !seniorFit && (juniorFit || taggedJunior);
    }

    return clearlySenior || seniorFit || taggedSenior;
}

// Jobs with no stated requirement are excluded from the years filter:
// we can't say they're entry-level, and this filter is for ones that are.
export function matchesYears(job, entryYears) {
    const maxYears = ENTRY_MAX_YEARS[entryYears];

    if (maxYears === undefined) {
        return true;
    }

    return (
        job.years_required !== null &&
        job.years_required !== undefined &&
        job.years_required <= maxYears
    );
}

export function filterJobs(jobs, filters) {
    const {
        remote,
        experience,
        entryYears,
        hideGhost,
        showSaved,
        savedIds,
    } = filters;

    return jobs.filter((job) => {
        if (showSaved && !savedIds.includes(job.id)) {
            return false;
        }

        if (remote !== "all" && job.work_model?.toLowerCase() !== remote) {
            return false;
        }

        if (!matchesExperience(job, experience)) {
            return false;
        }

        if (!matchesYears(job, entryYears)) {
            return false;
        }

        if (hideGhost && job.fit_label === "ghost-junior") {
            return false;
        }

        return true;
    });
}


// ============================================================
// CARD TEXT
// ============================================================

// The reason line under a card. Senior and unclear badges already say
// everything, so they get no extra line.
export function fitReason(job) {
    if (job.fit_label === "senior" || job.fit_label === "unclear") {
        return "";
    }

    return (job.fit_reasons ?? [])
        .filter((reason) => !METER_REASON.test(reason))
        .join(" · ");
}

export function formatSalary(job) {
    if (!job.salary_min) {
        return null;
    }

    const annual = job.salary_period === "annually";

    const amount = (value) =>
        annual
            ? `$${Math.round(value / 1000)}k`
            : `$${Number(value).toLocaleString()}`;

    const range = job.salary_max
        ? `${amount(job.salary_min)} – ${amount(job.salary_max)}`
        : amount(job.salary_min);

    const suffix = {
        hourly: " / hr",
        daily: " / day",
        monthly: " / mo",
        annually: " / yr",
    }[job.salary_period] ?? "";

    return range + suffix;
}

export function formatPostedTime(postedAt) {
    if (!postedAt) {
        return { text: "Unknown", type: "unknown" };
    }

    const postedDate = new Date(postedAt);
    const now = new Date();

    const postedDay = new Date(
        postedDate.getFullYear(),
        postedDate.getMonth(),
        postedDate.getDate()
    );

    const today = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate()
    );

    const dayDifference = Math.round(
        (today - postedDay) / (1000 * 60 * 60 * 24)
    );

    if (dayDifference === 0) {
        return { text: "Today", type: "today" };
    }

    if (dayDifference === 1) {
        return { text: "Yesterday", type: "yesterday" };
    }

    if (dayDifference >= 2 && dayDifference <= 6) {
        return { text: `${dayDifference} days ago`, type: "recent" };
    }

    return {
        text: postedDate.toLocaleDateString("en-CA", {
            year: "numeric",
            month: "short",
            day: "numeric",
        }),
        type: "older",
    };
}

// Job Bank titles arrive in lowercase; fix the casing of known terms.
const TITLE_CASE = {
    ai: "AI", api: "API", apis: "APIs", aws: "AWS", azure: "Azure",
    c: "C", "c++": "C++", "c#": "C#", css: "CSS", devops: "DevOps",
    etl: "ETL", gis: "GIS", html: "HTML", ios: "iOS", it: "IT",
    java: "Java", javascript: "JavaScript", js: "JS", kotlin: "Kotlin",
    ml: "ML", mysql: "MySQL", node: "Node", "node.js": "Node.js",
    php: "PHP", postgresql: "PostgreSQL", python: "Python", react: "React",
    "react.js": "React.js", sql: "SQL", typescript: "TypeScript",
    ui: "UI", ux: "UX", vue: "Vue",
};

export function formatJobTitle(job) {
    if (!job.title) {
        return "";
    }

    if (job.source !== "Job Bank") {
        return job.title;
    }

    return job.title
        .split(" ")
        .map((word) => {
            const key = word.toLowerCase();

            if (TITLE_CASE[key]) {
                return TITLE_CASE[key];
            }

            return word.charAt(0).toUpperCase() + word.slice(1);
        })
        .join(" ");
}

// Hue for a card's spine and badge, by experience demanded.
export function yearsTone(years) {
    if (years === null || years === undefined) return "unknown";
    if (years <= 2) return "low";
    if (years <= 4) return "mid";
    return "high";
}


// ============================================================
// SAVED JOBS (per browser, so a failed read just means "none")
// ============================================================

export function loadSavedIds() {
    try {
        const saved = localStorage.getItem(SAVED_KEY);

        return saved ? JSON.parse(saved) : [];
    } catch {
        return [];
    }
}

export function storeSavedIds(ids) {
    try {
        localStorage.setItem(SAVED_KEY, JSON.stringify(ids));
    } catch {
        // Private mode or blocked storage: saving still works for this visit.
    }
}


// ============================================================
// ACTIVITY
// ============================================================

// "2026-10-13" -> "Today" | "Yesterday" | "Mon, Oct 6"
export function formatDayLabel(isoDate, now = new Date()) {
    const day = new Date(`${isoDate}T00:00:00`);

    const startOf = (date) =>
        new Date(date.getFullYear(), date.getMonth(), date.getDate());

    const diff = Math.round(
        (startOf(now) - startOf(day)) / (1000 * 60 * 60 * 24)
    );

    if (diff === 0) return "today";
    if (diff === 1) return "yesterday";

    return day.toLocaleDateString("en-CA", {
        weekday: "short",
        month: "short",
        day: "numeric",
    });
}
