import { useEffect, useMemo, useRef, useState } from "react";

import JobCard from "../components/JobCard";
import FitBadge from "../components/FitBadge";
import ActivityChart from "../components/ActivityChart";
import { IconChevron, IconGitHub, IconRefresh } from "../components/Icons";
import SiteFooter, { REPO_URL } from "../components/SiteFooter";
import SkillWheel from "../components/SkillWheel";
import ThemeToggle from "../components/ThemeToggle";
import {
    fetchIngestStatus,
    fetchJobs,
    fetchSummary,
    readAdminToken,
    startIngest,
    STATUS_POLL_MS,
    storeAdminToken,
} from "../lib/api";
import {
    ENTRY_OPTIONS,
    FIT_INFO,
    LEGEND_ORDER,
    filterJobs,
    matchesExperience,
    loadSavedIds,
    storeSavedIds,
} from "../lib/jobs";
import { formatAgo, formatClock } from "../lib/status";


const COUNTRY_OPTIONS = [
    { value: "canada", label: "Canada", code: "CA" },
    { value: "usa", label: "United States", code: "US" },
    { value: "north-america", label: "North America", code: "NA" },
];

const EXPERIENCE_OPTIONS = [
    { value: "any", label: "Any" },
    { value: "junior", label: "Junior" },
    { value: "senior", label: "Senior+" },
];

const WORK_OPTIONS = [
    { value: "all", label: "All" },
    { value: "remote", label: "Remote" },
    { value: "hybrid", label: "Hybrid" },
    { value: "on-site", label: "On-site" },
];

const THEME_KEY = "engineerd-theme";

// "light" | "dark" once the viewer has chosen; null means follow the system.
function readStoredTheme() {
    try {
        const stored = localStorage.getItem(THEME_KEY);

        return stored === "light" || stored === "dark" ? stored : null;
    } catch {
        return null;
    }
}

function storeTheme(theme) {
    try {
        localStorage.setItem(THEME_KEY, theme);
    } catch {
        // Blocked storage: the choice still applies for this visit.
    }
}

const DEFAULT_FILTERS = {
    market: "canada",
    remote: "all",
    experience: "junior",
    entryYears: "any",
    hideGhost: false,
};


function Segmented({ label, options, value, onChange }) {
    return (
        <div className="control">
            <span className="control-label">{label}</span>
            <div className="segmented" role="group" aria-label={label}>
                {options.map((option) => (
                    <button
                        key={option.value}
                        className={option.value === value ? "active" : ""}
                        aria-pressed={option.value === value}
                        onClick={() => onChange(option.value)}
                        title={option.title}
                    >
                        {option.code && (
                            <span className="country-code">{option.code}</span>
                        )}
                        {option.label}
                        {option.count > 0 && ` (${option.count})`}
                    </button>
                ))}
            </div>
        </div>
    );
}


export default function Dashboard() {
    const [jobs, setJobs] = useState([]);
    const [loadError, setLoadError] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [refreshMessage, setRefreshMessage] = useState("");
    const [ingest, setIngest] = useState(null);
    const [dataVersion, setDataVersion] = useState(0);

    const [filters, setFilters] = useState(DEFAULT_FILTERS);
    const [showSaved, setShowSaved] = useState(false);
    const [advancedOpen, setAdvancedOpen] = useState(false);
    const [legendOpen, setLegendOpen] = useState(false);
    const [applyOpen, setApplyOpen] = useState(false);

    const [savedIds, setSavedIds] = useState(loadSavedIds);

    const [activity, setActivity] = useState([]);
    const [topSkills, setTopSkills] = useState([]);

    const [theme, setTheme] = useState(readStoredTheme);

    // Hidden refresh control: six quick clicks on the logo reveal it.
    const [adminOpen, setAdminOpen] = useState(false);
    const logoClicks = useRef([]);


    /* ============================================================
       DATA
       ============================================================ */

    // Loads on mount, and again whenever new jobs have landed.
    useEffect(() => {
        let cancelled = false;

        Promise.all([fetchJobs(filters.market), fetchSummary(filters.market)])
            .then(([data, summary]) => {
                if (!cancelled) {
                    setJobs(data);
                    setLoadError(false);
                    setActivity(summary.activity);
                    setTopSkills(summary.topSkills);
                }
            })
            .catch((error) => {
                console.error("Failed to load jobs:", error);

                if (!cancelled) {
                    setLoadError(true);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [dataVersion, filters.market]);

    // Keeps the "updated" line current, and reloads the list when a
    // scheduled refresh finishes while the page is open.
    useEffect(() => {
        let cancelled = false;
        let lastSeen = null;

        const poll = () =>
            fetchIngestStatus()
                .then((status) => {
                    if (cancelled) {
                        return;
                    }

                    setIngest(status);

                    if (lastSeen && status.last_success_at !== lastSeen) {
                        setDataVersion((version) => version + 1);
                    }

                    lastSeen = status.last_success_at;
                })
                .catch(() => {
                    // Status is informational; a missed poll is fine.
                });

        poll();

        const timer = setInterval(poll, STATUS_POLL_MS);

        return () => {
            cancelled = true;
            clearInterval(timer);
        };
    }, []);

    function onLogoClick() {
        const now = Date.now();

        logoClicks.current = [
            ...logoClicks.current.filter((time) => now - time < 4000),
            now,
        ];

        if (logoClicks.current.length >= 6) {
            logoClicks.current = [];
            setAdminOpen(true);
        }
    }

    async function handleRefresh() {
        let token = readAdminToken();

        if (!token) {
            token = window.prompt("Admin token") || "";

            if (!token) {
                return;
            }

            storeAdminToken(token);
        }

        setIsRefreshing(true);
        setRefreshMessage("");

        try {
            const result = await startIngest(filters.market, token);

            if (result.status === 403) {
                storeAdminToken("");
                setRefreshMessage("Admin token rejected. Click the logo again to retry.");
            } else if (result.status === 409) {
                setRefreshMessage(
                    "A refresh is already running. The list will update when it finishes."
                );
            } else if (!result.ok) {
                setRefreshMessage(
                    "The refresh didn’t finish. Your list is unchanged."
                );
            } else {
                setDataVersion((version) => version + 1);
            }
        } catch (error) {
            console.error("Unable to update jobs:", error);
            setRefreshMessage(
                "Can’t reach the Engineerd API right now. Your list is unchanged."
            );
        } finally {
            setIsRefreshing(false);
        }
    }


    /* ============================================================
       THEME
       ============================================================ */

    useEffect(() => {
        const root = document.documentElement;

        if (theme) {
            root.dataset.theme = theme;
        } else {
            delete root.dataset.theme;
        }
    }, [theme]);

    const systemPrefersDark =
        typeof window !== "undefined" &&
        window.matchMedia?.("(prefers-color-scheme: dark)").matches;

    const isDark = theme ? theme === "dark" : systemPrefersDark;

    // Same logo and size in both themes: black in light mode, orange in dark.
    const logo = {
        file: "/EngineerdLogo.svg",
        width: 80,
        height: 64,
        color: isDark ? "var(--accent)" : "var(--ink)",
    };

    function toggleTheme() {
        const next = isDark ? "light" : "dark";

        storeTheme(next);
        setTheme(next);
    }


    /* ============================================================
       SAVED
       ============================================================ */

    function toggleSaved(jobId) {
        setSavedIds((current) => {
            const updated = current.includes(jobId)
                ? current.filter((id) => id !== jobId)
                : [...current, jobId];

            storeSavedIds(updated);

            return updated;
        });
    }


    /* ============================================================
       FILTERS
       ============================================================ */

    const setFilter = (key) => (value) =>
        setFilters((current) => ({ ...current, [key]: value }));

    const filtersChanged = JSON.stringify(filters) !== JSON.stringify(DEFAULT_FILTERS);

    const advancedActive =
        (filters.entryYears !== "any" ? 1 : 0) + (filters.hideGhost ? 1 : 0);

    const visibleJobs = useMemo(
        () =>
            filterJobs(jobs, {
                remote: filters.remote,
                experience: filters.experience,
                entryYears: filters.entryYears,
                hideGhost: filters.hideGhost,
                showSaved,
                savedIds,
            }),
        [jobs, filters, showSaved, savedIds]
    );

    const stats = useMemo(() => {
        const total = jobs.length;
        const juniorCount = jobs.filter((job) => matchesExperience(job, "junior")).length;
        const seniorCount = jobs.filter((job) => matchesExperience(job, "senior")).length;
        const ghost = jobs.filter((job) => job.fit_label === "ghost-junior").length;
        const withYears = jobs.filter((job) => job.years_required !== null && job.years_required !== undefined).length;

        return {
            total,
            juniorCount,
            seniorCount,
            ghost,
            withYears,
            withYearsPct: total ? Math.round((withYears / total) * 100) : 0,
        };
    }, [jobs]);

    function resetFilters() {
        setFilters(DEFAULT_FILTERS);
        setShowSaved(false);
    }


    /* ============================================================
       RENDER
       ============================================================ */

    return (
        <div className="app">

            <header className="nav">

                <div className="brand" onClick={onLogoClick}>
                    <span
                        className="brand-mark"
                        role="img"
                        aria-label="Engineerd"
                        style={{
                            width: logo.width,
                            height: logo.height,
                            background: logo.color,
                            maskImage: `url(${logo.file})`,
                            WebkitMaskImage: `url(${logo.file})`,
                        }}
                    />
                </div>

                <div className="nav-actions">

                    <a
                        className="github-link"
                        href={REPO_URL}
                        target="_blank"
                        rel="noreferrer"
                    >
                        <IconGitHub />
                        GitHub
                    </a>

                    <ThemeToggle isDark={isDark} onToggle={toggleTheme} />

                </div>


            </header>

            <main className="page">

                <section className="hero">

                    <div className="hero-copy">

                        <p className="eyebrow">Engineerd · job discovery</p>

                        <h1>
                            Every level, <em>honestly</em> labelled.
                        </h1>

                        <p className="lede">
                            Job boards tag roles junior, mid or senior, and they
                            rarely agree. We read each posting and show what it
                            really asks for, from entry-level to senior+.
                        </p>

                        <p className="freshness">
                            {ingest?.running
                                ? "Updating now…"
                                : ingest?.last_success_at
                                ? `Updated ${formatAgo(ingest.last_success_at)}`
                                : null}
                            {!ingest?.running && ingest?.next_run_at &&
                                ` · next update ${formatClock(ingest.next_run_at)}`}
                        </p>

                    </div>

                    <aside className="hero-side">
                        <ActivityChart days={activity} />

                    </aside>

                    <dl className="stats">

                        <div>
                            <dt>All postings</dt>
                            <dd>{stats.total}</dd>
                        </div>

                        <div className="stat-good">
                            <dt>Junior</dt>
                            <dd>{stats.juniorCount}</dd>
                        </div>

                        <div className="stat-senior">
                            <dt>Senior+</dt>
                            <dd>{stats.seniorCount}</dd>
                        </div>

                        <div>
                            <dt title="Share of postings that say how many years of experience they want">
                                Experience listed
                            </dt>
                            <dd>{stats.withYearsPct}%</dd>
                            <p className="stat-note">
                                say how many years they want
                            </p>
                        </div>

                        <div className="stat-skills">
                            <dt>Top skills</dt>
                            <dd>
                                <SkillWheel skills={topSkills} />
                            </dd>
                        </div>

                    </dl>

                </section>

                {loadError && (
                    <div className="notice notice-error" role="alert">
                        Can’t reach the Engineerd API right now. Start the backend
                        and refresh the page.
                    </div>
                )}

                {refreshMessage && (
                    <div className="notice notice-error" role="alert">
                        {refreshMessage}
                    </div>
                )}

                <section className="toolbar" aria-label="Filters">

                    <div className="tabs" role="tablist">
                        <button
                            role="tab"
                            aria-selected={!showSaved}
                            className={!showSaved ? "active" : ""}
                            onClick={() => setShowSaved(false)}
                        >
                            Jobs <span className="count">{jobs.length}</span>
                        </button>
                        <button
                            role="tab"
                            aria-selected={showSaved}
                            className={showSaved ? "active" : ""}
                            onClick={() => setShowSaved(true)}
                        >
                            Saved <span className="count">{savedIds.length}</span>
                        </button>
                    </div>

                    <div className="toolbar-actions">

                        {filtersChanged && (
                            <button className="text-button" onClick={resetFilters}>
                                Reset
                            </button>
                        )}

                    </div>

                </section>

                <section className="filters">

                    <Segmented
                        label="Country"
                        options={COUNTRY_OPTIONS}
                        value={filters.market}
                        onChange={setFilter("market")}
                    />

                    <Segmented
                        label="Experience"
                        options={EXPERIENCE_OPTIONS}
                        value={filters.experience}
                        onChange={setFilter("experience")}
                    />

                    <Segmented
                        label="Work type"
                        options={WORK_OPTIONS}
                        value={filters.remote}
                        onChange={setFilter("remote")}
                    />

                    <div className="control">
                        <span className="control-label">More</span>
                        <button
                            className="advanced-toggle"
                            onClick={() => setAdvancedOpen((open) => !open)}
                            aria-expanded={advancedOpen}
                        >
                            Advanced
                            {advancedActive > 0 && (
                                <span className="advanced-count">{advancedActive}</span>
                            )}
                            <span className={`chevron ${advancedOpen ? "open" : ""}`}>
                                <IconChevron />
                            </span>
                        </button>
                    </div>

                </section>

                {advancedOpen && (
                    <section className="advanced-panel" aria-label="Advanced filters">


                        <Segmented
                            label="Years required"
                            options={ENTRY_OPTIONS}
                            value={filters.entryYears}
                            onChange={setFilter("entryYears")}
                        />

                        <Segmented
                            label="Ghost junior"
                            options={[
                                { value: false, label: "Show all" },
                                {
                                    value: true,
                                    label: "Hide",
                                    title: FIT_INFO["ghost-junior"].help,
                                    count: stats.ghost,
                                },
                            ]}
                            value={filters.hideGhost}
                            onChange={setFilter("hideGhost")}
                        />

                        {adminOpen && (
                        <div className="refresh-row">
                                <button
                                    className="refresh-button"
                                    onClick={handleRefresh}
                                    disabled={isRefreshing || ingest?.running}
                                >
                                    {isRefreshing || ingest?.running ? (
                                        <>
                                            <span className="spinner" aria-hidden="true" />
                                            Finding jobs…
                                        </>
                                    ) : (
                                        <>
                                            <IconRefresh />
                                            Find new jobs
                                        </>
                                    )}
                                </button>
                                <span className="hint">
                                    Jobs also refresh on a schedule. Use this to see new ones now.
                                </span>
                            </div>
                        )}

                    </section>
                )}

                <div className="results-meta">

                    <span>
                        <strong>{visibleJobs.length}</strong>{" "}
                        {showSaved ? "saved" : "matching"} {visibleJobs.length === 1 ? "job" : "jobs"}
                    </span>

                    <div className="meta-actions">
                        <button
                            className="text-button legend-toggle"
                            onClick={() => setApplyOpen((open) => !open)}
                            aria-expanded={applyOpen}
                        >
                            How to apply
                        </button>

                        <button
                            className="text-button legend-toggle"
                            onClick={() => setLegendOpen((open) => !open)}
                            aria-expanded={legendOpen}
                        >
                            What do the labels mean?
                        </button>
                    </div>

                </div>

                {applyOpen && (
                    <section className="legend apply-help" aria-label="How to apply">
                        <p>
                            My recommendation, as the developer of Engineerd:
                        </p>
                        <ul className="apply-steps">
                            <li>
                                Create a free account on Built In or Wellfound,
                                then apply to the company from there. Both sites
                                ask you to sign in before they show the
                                application.
                            </li>
                            <li>
                                Or search the company name on Google, find its
                                careers page, and apply on the company's own
                                site. Use the job title and location from the
                                Engineerd card to find the same posting.
                            </li>
                        </ul>
                    </section>
                )}

                {legendOpen && (
                    <section className="legend" aria-label="What the labels mean">
                        <p>
                            Job boards label roles “junior” loosely. Each card
                            shows what the posting actually asks for, read from
                            the full listing.
                        </p>
                        <ul>
                            {LEGEND_ORDER.map((key) => (
                                <li key={key}>
                                    <FitBadge label={key} />
                                    <span>{FIT_INFO[key].help}</span>
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                {visibleJobs.length === 0 ? (
                    <div className="empty">
                        <h3>
                            {showSaved
                                ? "Nothing saved matches these filters."
                                : "No jobs match these filters."}
                        </h3>
                        <p>Try a wider experience range or a different work type.</p>
                        {filtersChanged && (
                            <button className="primary-button" onClick={resetFilters}>
                                Reset filters
                            </button>
                        )}
                    </div>
                ) : (
                    <section className="job-grid">
                        {visibleJobs.map((job) => (
                            <JobCard
                                key={job.id}
                                job={job}
                                saved={savedIds.includes(job.id)}
                                onToggleSave={toggleSaved}
                            />
                        ))}
                    </section>
                )}

            </main>

            <SiteFooter />

        </div>
    );
}
