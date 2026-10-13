import { useEffect, useState } from "react";

// Plain-language copy for the junior-fit badges. `help` is shown in
// the legend and as the badge tooltip.
const FIT_INFO = {
    "junior-friendly": {
        label: "Junior-friendly",
        help: "Entry-level, and asks for 0-2 years of experience.",
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

const LEGEND_ORDER = [
    "junior-friendly",
    "ghost-junior",
    "stretch",
    "senior",
    "unverified",
    "unclear",
];

// Reasons that the "Asks N+ yrs" pill already shows.
const PILL_REASON = /^(Asks for|No experience required)/;

const MAX_SKILLS = 5;

// Years-required options in the Advanced panel. "any" means no limit.
const ENTRY_MAX_YEARS = {
    any: undefined,
    none: 0,
    "1": 1,
    "2": 2,
};

const ENTRY_OPTIONS = [
    { value: "any", label: "Any" },
    { value: "none", label: "No experience" },
    { value: "1", label: "0–1 yrs" },
    { value: "2", label: "0–2 yrs" },
];

function Dashboard() {
    const [jobs, setJobs] = useState([]);

    const [remoteFilter, setRemoteFilter] = useState("all");
    const [hideGhost, setHideGhost] = useState(false);

    // Advanced panel: "any" | "none" | "1" | "2" (max years required)
    const [advancedOpen, setAdvancedOpen] = useState(false);
    const [entryYears, setEntryYears] = useState("any");
    const [experienceFilter, setExperienceFilter] = useState("junior");

    const [isRefreshing, setIsRefreshing] = useState(false);
    const [market, setMarket] = useState("canada");

    const [savedJobs, setSavedJobs] = useState(() => {
        const saved = localStorage.getItem("engineerd-saved-jobs");
        return saved ? JSON.parse(saved) : [];
    });

    const [showSaved, setShowSaved] = useState(false);


    /* ============================================================
       LOAD JOBS
       ============================================================ */

    useEffect(() => {
        async function loadJobs() {
            try {
                const response = await fetch(
                    "http://localhost:8000/jobs/"
                );

                if (!response.ok) {
                    throw new Error("Failed to fetch jobs");
                }

                const data = await response.json();

                setJobs(data);
            } catch (error) {
                console.error(
                    "Failed to load jobs:",
                    error
                );
            }
        }

        loadJobs();
    }, []);


    /* ============================================================
       INGEST JOBS
       ============================================================ */

    
async function handleRefresh() {
    setIsRefreshing(true);

    try {
        const ingestResponse = await fetch(
            `http://localhost:8000/jobs/ingest?market=${market}`,
            {
                method: "POST",
            }
        );

        if (!ingestResponse.ok) {
            throw new Error("Failed to ingest jobs");
        }

        const response = await fetch(
            "http://localhost:8000/jobs/?limit=400"
        );

        if (!response.ok) {
            throw new Error("Failed to fetch jobs");
        }

        const data = await response.json();
        setJobs(data);
    } catch (error) {
        console.error("Unable to update jobs:", error);
    } finally {
        setIsRefreshing(false);
    }
}



    /* ============================================================
       POSTED DATE
       ============================================================ */

    function formatPostedTime(postedAt) {
        if (!postedAt) {
            return {
                text: "Unknown",
                type: "unknown",
            };
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
            (today - postedDay) /
                (1000 * 60 * 60 * 24)
        );

        if (dayDifference === 0) {
            return {
                text: "Today",
                type: "today",
            };
        }

        if (dayDifference === 1) {
            return {
                text: "Yesterday",
                type: "yesterday",
            };
        }

        if (
            dayDifference >= 2 &&
            dayDifference <= 6
        ) {
            return {
                text: `${dayDifference} days ago`,
                type: "recent",
            };
        }

        return {
            text: postedDate.toLocaleDateString(
                "en-CA",
                {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                }
            ),
            type: "older",
        };
    }


    /* ============================================================
       SAVED JOBS
       ============================================================ */

    function toggleSaved(jobId) {
        setSavedJobs((current) => {
            const isSaved = current.includes(jobId);

            const updated = isSaved
                ? current.filter(
                    (id) => id !== jobId
                )
                : [...current, jobId];

            localStorage.setItem(
                "engineerd-saved-jobs",
                JSON.stringify(updated)
            );

            return updated;
        });
    }


    function fitReason(job) {
        // For these the badge already says everything.
        if (job.fit_label === "senior" || job.fit_label === "unclear") {
            return "";
        }

        return (job.fit_reasons ?? [])
            .filter((reason) => !PILL_REASON.test(reason))
            .join(" · ");
    }


    function isJobSaved(jobId) {
        return savedJobs.includes(jobId);
    }


    /* ============================================================
       JOB TITLE FORMATTING
       ============================================================ */

    function formatJobTitle(job) {
        if (!job.title) {
            return "";
        }

        if (job.source !== "Job Bank") {
            return job.title;
        }

        const specialCases = {
            ai: "AI",
            api: "API",
            apis: "APIs",
            aws: "AWS",
            azure: "Azure",
            c: "C",
            "c++": "C++",
            "c#": "C#",
            css: "CSS",
            devops: "DevOps",
            etl: "ETL",
            gis: "GIS",
            html: "HTML",
            ios: "iOS",
            it: "IT",
            java: "Java",
            javascript: "JavaScript",
            js: "JS",
            kotlin: "Kotlin",
            ml: "ML",
            mysql: "MySQL",
            node: "Node",
            "node.js": "Node.js",
            php: "PHP",
            postgresql: "PostgreSQL",
            python: "Python",
            react: "React",
            "react.js": "React.js",
            sql: "SQL",
            typescript: "TypeScript",
            ui: "UI",
            ux: "UX",
            vue: "Vue",
        };

        return job.title
            .split(" ")
            .map((word) => {
                const key = word.toLowerCase();

                if (specialCases[key]) {
                    return specialCases[key];
                }

                return (
                    word.charAt(0).toUpperCase() +
                    word.slice(1)
                );
            })
            .join(" ");
    }


    /* ============================================================
       FILTER JOBS
       ============================================================ */

    const advancedActiveCount =
        (hideGhost ? 1 : 0) + (entryYears !== "any" ? 1 : 0);

    const ghostCount = jobs.filter(
        (job) => job.fit_label === "ghost-junior"
    ).length;

    const filteredJobs = jobs.filter((job) => {

        const matchesRemote =
            remoteFilter === "all" ||
            job.work_model?.toLowerCase() === remoteFilter;



        const experience = (job.experience_level ?? "").toLowerCase();
        const title = (job.title ?? "").toLowerCase();

        const levels = experience
            .split(",")
            .map((level) => level.trim());

        const clearlySeniorTitle =
            /\b(senior|sr\.?|staff|principal|lead|director|chief|manager)\b/i.test(title);

        // The fit label (from years + title) is the primary signal, so
        // the Junior filter agrees with the badge. Source tags are a
        // fallback for jobs we could not analyse (Wellfound has none).
        const juniorFit =
            job.fit_label === "junior-friendly" ||
            job.fit_label === "ghost-junior";

        const seniorFit = job.fit_label === "senior";

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

        const matchesExperience =
            experienceFilter === "all" ||
            (experienceFilter === "junior" &&
                !clearlySeniorTitle &&
                !seniorFit &&
                (juniorFit || taggedJunior)) ||
            (experienceFilter === "senior" &&
                (clearlySeniorTitle || seniorFit || taggedSenior));

        const matchesSaved =
            !showSaved ||
            savedJobs.includes(job.id);

        const matchesGhost =
            !hideGhost ||
            job.fit_label !== "ghost-junior";

        // Jobs with no stated requirement are excluded here: we can't
        // say they're entry-level, and the point of this filter is to
        // only show ones that are.
        const maxYears = ENTRY_MAX_YEARS[entryYears];

        const matchesEntry =
            maxYears === undefined ||
            (job.years_required !== null &&
                job.years_required !== undefined &&
                job.years_required <= maxYears);


        return (
            matchesRemote &&
            matchesExperience &&
            matchesSaved &&
            matchesGhost &&
            matchesEntry
        );
    });


    return (
        <div className="app">

            {/* ====================================================
                HEADER
                ==================================================== */}

            <header className="topbar">

                <div className="topbar-inner">

                    <img
                        src="/EngineerdLogoWhite.svg"
                        alt="Engineerd"
                        className="logo"
                    />

                    <div className="topbar-actions">

                        <button
                            className="header-refresh"
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                        >

                            {isRefreshing ? (
                                <>
                                    <span className="spinner"></span>
                                    Finding Jobs...
                                </>
                            ) : (
                                <>
                                    <span>↻</span>
                                    Find New Jobs
                                </>
                            )}

                        </button>

                    </div>

                </div>

            </header>


            {/* ====================================================
                MAIN
                ==================================================== */}

            <main className="dashboard">


                {/* =================================================
                    PAGE HEADING
                    ================================================= */}

                <section className="page-heading">

                    <div className="page-heading-content">

                        <span className="eyebrow">
                            ENGINEERD JOB DISCOVERY
                        </span>

                        <h1>
                            Find your next technical role.
                        </h1>

                        <p>
                            Fresh jobs aggregated from multiple
                            sources and organized in one place.
                        </p>

                    </div>


                    {/* =================================================
                        JOB / SAVED TABS
                        ================================================= */}

                    <div className="jobs-view-tabs">

                        <button
                            className={
                                !showSaved
                                    ? "active"
                                    : ""
                            }
                            onClick={() =>
                                setShowSaved(false)
                            }
                        >

                            <span>
                                Jobs
                            </span>

                            <span className="tab-count">
                                {jobs.length}
                            </span>

                        </button>


                        <button
                            className={
                                showSaved
                                    ? "active"
                                    : ""
                            }
                            onClick={() =>
                                setShowSaved(true)
                            }
                        >

                            <span>
                                ♡ Saved
                            </span>

                            {savedJobs.length > 0 && (
                                <span className="tab-count">
                                    {savedJobs.length}
                                </span>
                            )}

                        </button>

                    </div>

                </section>


                {/* =================================================
                    FILTERS
                    ================================================= */}

                <div className="jobs-content">

                    <div className="filter-panel">

                        <div className="filter-group">

                            <span className="filter-label">
                                Country
                            </span>

                            <div className="segmented-control country-control">

                                <button
                                    className={
                                        market === "canada"
                                            ? "active canada"
                                            : ""
                                    }
                                    onClick={() => setMarket("canada")}
                                >
                                    <span className="country-code">CA</span>
                                    <span>Canada</span>
                                </button>

                                <button
                                    className={
                                        market === "usa"
                                            ? "active usa"
                                            : ""
                                    }
                                    onClick={() => setMarket("usa")}
                                >
                                    <span className="country-code">US</span>
                                    <span>United States</span>
                                </button>

                                <button
                                    className={
                                        market === "north-america"
                                            ? "active north-america"
                                            : ""
                                    }
                                    onClick={() => setMarket("north-america")}
                                >
                                    <span className="country-code">NA</span>
                                    <span>North America</span>
                                </button>

                            </div>

                        </div>


                        <div className="filter-group">

                            <span className="filter-label">
                                Experience
                            </span>

                            <div className="segmented-control">

                                <button
                                    className={
                                        experienceFilter === "all"
                                            ? "active"
                                            : ""
                                    }
                                    onClick={() =>
                                        setExperienceFilter("all")
                                    }
                                >
                                    Any
                                </button>

                                <button
                                    className={
                                        experienceFilter === "junior"
                                            ? "active"
                                            : ""
                                    }
                                    onClick={() =>
                                        setExperienceFilter("junior")
                                    }
                                >
                                    Junior
                                </button>

                                <button
                                    className={
                                        experienceFilter === "senior"
                                            ? "active"
                                            : ""
                                    }
                                    onClick={() =>
                                        setExperienceFilter("senior")
                                    }
                                >
                                    Senior+
                                </button>

                            </div>

                        </div>


                        <div className="filter-group">

                            <span className="filter-label">
                                Work Type
                            </span>

                            <div className="segmented-control">

                                <button
                                    className={
                                        remoteFilter === "all"
                                            ? "active"
                                            : ""
                                    }
                                    onClick={() =>
                                        setRemoteFilter("all")
                                    }
                                >
                                    All
                                </button>

                                <button
                                    className={
                                        remoteFilter === "remote"
                                            ? "active"
                                            : ""
                                    }
                                    onClick={() =>
                                        setRemoteFilter("remote")
                                    }
                                >
                                    Remote
                                </button>

                                <button
                                    className={
                                        remoteFilter === "hybrid"
                                            ? "active"
                                            : ""
                                    }
                                    onClick={() =>
                                        setRemoteFilter("hybrid")
                                    }
                                >
                                    Hybrid
                                </button>

                                <button
                                    className={
                                        remoteFilter === "on-site"
                                            ? "active"
                                            : ""
                                    }
                                    onClick={() =>
                                        setRemoteFilter("on-site")
                                    }
                                >
                                    On-site
                                </button>

                            </div>

                        </div>


                    </div>

                    {/* =================================================
                        ADVANCED FILTERS
                        ================================================= */}

                    <div className="advanced">

                        <button
                            className="advanced-toggle"
                            onClick={() => setAdvancedOpen((open) => !open)}
                            aria-expanded={advancedOpen}
                        >
                            Advanced
                            {advancedActiveCount > 0 && (
                                <span className="advanced-count">
                                    {advancedActiveCount}
                                </span>
                            )}
                            <span className={`advanced-chevron ${advancedOpen ? "open" : ""}`}>
                                ▾
                            </span>
                        </button>

                        {advancedOpen && (

                            <div className="advanced-panel">

                                <div className="advanced-row">

                                    <div className="advanced-field">

                                        <span className="filter-label">
                                            Years required
                                        </span>

                                        <div className="segmented-control">

                                            {ENTRY_OPTIONS.map((option) => (
                                                <button
                                                    key={option.value}
                                                    className={
                                                        entryYears === option.value
                                                            ? "active"
                                                            : ""
                                                    }
                                                    onClick={() =>
                                                        setEntryYears(option.value)
                                                    }
                                                >
                                                    {option.label}
                                                </button>
                                            ))}

                                        </div>

                                        <span className="filter-hint">
                                            Only jobs that state a requirement
                                            within this range. Works alongside
                                            the Junior filter.
                                        </span>

                                    </div>

                                    <div className="advanced-field">

                                        <span className="filter-label">
                                            Ghost junior
                                        </span>

                                        <div className="segmented-control">

                                            <button
                                                className={
                                                    !hideGhost ? "active" : ""
                                                }
                                                onClick={() => setHideGhost(false)}
                                            >
                                                Show all
                                            </button>

                                            <button
                                                className={
                                                    hideGhost ? "active" : ""
                                                }
                                                onClick={() => setHideGhost(true)}
                                                title={FIT_INFO["ghost-junior"].help}
                                            >
                                                Hide
                                                {ghostCount > 0 && ` (${ghostCount})`}
                                            </button>

                                        </div>

                                        <span className="filter-hint">
                                            Ghost junior = tagged entry-level,
                                            but asks for 3+ years.
                                        </span>

                                    </div>

                                </div>

                            </div>

                        )}

                    </div>

                    <details className="fit-legend">

                        <summary>
                            What do the junior-fit badges mean?
                        </summary>

                        <p>
                            Job boards label roles "junior" loosely.
                            Engineerd opens each posting, reads the
                            experience it actually asks for, and
                            compares it to the title.
                        </p>

                        <ul>
                            {LEGEND_ORDER.map((key) => (
                                <li key={key}>
                                    <span
                                        className={`fit-badge fit-${key}`}
                                    >
                                        {FIT_INFO[key].label}
                                    </span>
                                    <span>{FIT_INFO[key].help}</span>
                                </li>
                            ))}
                        </ul>

                    </details>


                    {/* =================================================
                        RESULTS
                        ================================================= */}

                    <section className="results-area">


                        <div className="results-header">

                            <span>

                                <strong>
                                    {filteredJobs.length}
                                </strong>{" "}

                                {showSaved
                                    ? "saved jobs"
                                    : "matching jobs"}

                            </span>


                            <span>
                                Newest first
                            </span>

                        </div>


                        {/* =================================================
                            JOB CARDS
                            ================================================= */}

                        <section className="job-list">

                            {filteredJobs.length === 0 ? (

                                <div className="empty-results">

                                    <h3>
                                        No jobs found
                                    </h3>

                                    <p>
                                        Try changing your
                                        filters or finding
                                        new jobs.
                                    </p>

                                </div>

                            ) : (

                                filteredJobs.map((job) => (

                                    <article
                                        className="job-card"
                                        key={job.id}
                                    >


                                        {/* =================================================
                                            CARD HEADER
                                            ================================================= */}

                                        <div className="job-card-header">

                                            <div className="company-logo">

                                                {job.company_logo ? (

                                                    <img
                                                        src={
                                                            job.company_logo
                                                        }
                                                        alt={`${job.company} logo`}
                                                    />

                                                ) : (

                                                    <span>
                                                        {job.company?.charAt(
                                                            0
                                                        )}
                                                    </span>

                                                )}

                                            </div>


                                            <button
                                                className={`save-job ${
                                                    isJobSaved(
                                                        job.id
                                                    )
                                                        ? "saved"
                                                        : ""
                                                }`}
                                                onClick={() =>
                                                    toggleSaved(
                                                        job.id
                                                    )
                                                }
                                                aria-label={
                                                    isJobSaved(
                                                        job.id
                                                    )
                                                        ? "Remove saved job"
                                                        : "Save job"
                                                }
                                            >

                                                <span className="save-icon">

                                                    {isJobSaved(
                                                        job.id
                                                    )
                                                        ? "♥"
                                                        : "♡"}

                                                </span>


                                                <span className="save-text">

                                                    {isJobSaved(
                                                        job.id
                                                    )
                                                        ? "Saved"
                                                        : "Save"}

                                                </span>

                                            </button>

                                        </div>


                                        {/* =================================================
                                            CARD BODY
                                            ================================================= */}

                                        <div className="job-card-body">

                                            <span className="source">
                                                {job.source}
                                            </span>


                                            <h2>
                                                {formatJobTitle(
                                                    job
                                                )}
                                            </h2>


                                            <div className="company">
                                                {job.company}
                                            </div>


                                            <div className="job-meta">

                                                {job.location && (
                                                    <span>
                                                        📍{" "}
                                                        {job.location}
                                                    </span>
                                                )}


                                                {job.work_model && (
                                                    <span
                                                        className={`tag ${
                                                            job.work_model === "Remote"
                                                                ? "remote"
                                                                : ""
                                                        }`}
                                                    >
                                                        {job.work_model}
                                                    </span>
                                                )}


                                                {job.employment_type && (
                                                    <span className="tag">
                                                        {
                                                            job.employment_type
                                                        }
                                                    </span>
                                                )}

                                            </div>


                                            {/* ================================
                                                JUNIOR FIT
                                                ================================ */}

                                            {job.fit_label && (

                                                <div className="job-fit">

                                                    <span
                                                        className={`fit-badge fit-${job.fit_label}`}
                                                        title={FIT_INFO[job.fit_label]?.help}
                                                    >
                                                        {FIT_INFO[job.fit_label]?.label
                                                            ?? job.fit_label}
                                                    </span>

                                                    {job.years_required !== null &&
                                                        job.years_required !== undefined && (
                                                        <span
                                                            className={`years-pill ${
                                                                job.years_required >= 3
                                                                    ? "heavy"
                                                                    : ""
                                                            }`}
                                                            title={
                                                                job.years_evidence
                                                                    ? `"${job.years_evidence}"`
                                                                    : undefined
                                                            }
                                                        >
                                                            {job.years_required === 0
                                                                ? "No experience required"
                                                                : `Asks ${job.years_required}+ yrs`}
                                                        </span>
                                                    )}

                                                    {(job.skills ?? [])
                                                        .slice(0, MAX_SKILLS)
                                                        .map((skill) => (
                                                            <span
                                                                className="tag"
                                                                key={skill}
                                                            >
                                                                {skill}
                                                            </span>
                                                        ))}

                                                    {(job.skills ?? []).length > MAX_SKILLS && (
                                                        <span
                                                            className="tag more"
                                                            title={job.skills
                                                                .slice(MAX_SKILLS)
                                                                .join(", ")}
                                                        >
                                                            +{job.skills.length - MAX_SKILLS}
                                                        </span>
                                                    )}

                                                </div>

                                            )}

                                            {fitReason(job) && (
                                                <p className="fit-why">
                                                    {fitReason(job)}
                                                </p>
                                            )}

                                        </div>


                                        {/* =================================================
                                            CARD FOOTER
                                            ================================================= */}

                                        <div className="job-card-footer">

                                            <div className="job-card-details">


                                                {/* ================================
                                                    SALARY
                                                    ================================ */}

                                                {job.salary_min && (

                                                    <span className="salary">

                                                        {job.salary_period ===
                                                        "annually"
                                                            ? `$${Math.round(
                                                                job.salary_min /
                                                                    1000
                                                            )}k`
                                                            : `$${job.salary_min.toLocaleString()}`}


                                                        {job.salary_max &&
                                                            ` – ${
                                                                job.salary_period ===
                                                                "annually"
                                                                    ? `$${Math.round(
                                                                        job.salary_max /
                                                                            1000
                                                                    )}k`
                                                                    : `$${job.salary_max.toLocaleString()}`
                                                            }`}


                                                        {job.salary_period ===
                                                            "hourly" &&
                                                            " / hr"}


                                                        {job.salary_period ===
                                                            "daily" &&
                                                            " / day"}


                                                        {job.salary_period ===
                                                            "monthly" &&
                                                            " / mo"}


                                                        {job.salary_period ===
                                                            "annually" &&
                                                            " / yr"}

                                                    </span>

                                                )}


                                                {/* ================================
                                                    POSTED
                                                    ================================ */}

                                                <span
                                                    className={`posted-badge posted-${
                                                        formatPostedTime(
                                                            job.posted_at
                                                        ).type
                                                    }`}
                                                >

                                                    {
                                                        formatPostedTime(
                                                            job.posted_at
                                                        ).text
                                                    }

                                                </span>

                                            </div>


                                            {/* ================================
                                                VIEW JOB
                                                ================================ */}

                                            <a
                                                className="view-job"
                                                href={job.url}
                                                target="_blank"
                                                rel="noreferrer"
                                            >

                                                <span>
                                                    View Job
                                                </span>

                                                <span className="view-arrow">
                                                    →
                                                </span>

                                            </a>

                                        </div>

                                    </article>

                                ))

                            )}

                        </section>

                    </section>

                </div>

            </main>

        </div>
    );
}

export default Dashboard;