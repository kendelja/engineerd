import { useEffect, useState } from "react";

function Dashboard() {
    const [jobs, setJobs] = useState([]);

    const [search, setSearch] = useState("");
    const [remoteFilter, setRemoteFilter] = useState("all");
    const [sourceFilter, setSourceFilter] = useState("all");
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [market, setMarket] = useState("canada");

    const [savedJobs, setSavedJobs] = useState(() => {
    const saved = localStorage.getItem("engineerd-saved-jobs");
    return saved ? JSON.parse(saved) : [];
    });

    const [showSaved, setShowSaved] = useState(false);

    

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
                console.error("Failed to load jobs:", error);
            }
        }

        loadJobs();
    }, []);

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
                "http://localhost:8000/jobs/"
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

    function formatPostedTime(postedAt) {
        if (!postedAt) {
            return {
                text: "Unknown",
                type: "unknown"
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
            (today - postedDay) / (1000 * 60 * 60 * 24)
        );

        if (dayDifference === 0) {
            return {
                text: "Today",
                type: "today"
            };
        }

        if (dayDifference === 1) {
            return {
                text: "Yesterday",
                type: "yesterday"
            };
        }

        if (dayDifference >= 2 && dayDifference <= 6) {
            return {
                text: `${dayDifference} days ago`,
                type: "recent"
            };
        }

        return {
            text: postedDate.toLocaleDateString("en-CA", {
                year: "numeric",
                month: "short",
                day: "numeric"
            }),
            type: "older"
        };
    }

    function toggleSaved(jobId) {
        setSavedJobs((current) => {
            const isSaved = current.includes(jobId);

            const updated = isSaved
                ? current.filter((id) => id !== jobId)
                : [...current, jobId];

            localStorage.setItem(
                "engineerd-saved-jobs",
                JSON.stringify(updated)
            );

            return updated;
        });
    }

    function isJobSaved(jobId) {
        return savedJobs.includes(jobId);
    }

    const filteredJobs = jobs.filter((job) => {
        const searchText = search.toLowerCase();

        const matchesSearch =
            job.title?.toLowerCase().includes(searchText) ||
            job.company?.toLowerCase().includes(searchText);

        const matchesRemote =
            remoteFilter === "all" ||
            job.remote_type?.toLowerCase() === remoteFilter;

        const matchesSource =
            sourceFilter === "all" ||
            job.source?.toLowerCase() === sourceFilter;

        const matchesSaved =
            !showSaved || savedJobs.includes(job.id);

        return (
            matchesSearch &&
            matchesRemote &&
            matchesSource &&
            matchesSaved
        );
    });

    function formatJobTitle(job) {
        if (!job.title) return "";

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

                return word.charAt(0).toUpperCase() + word.slice(1);
            })
            .join(" ");
    }


    return (
        <div className="app">

            <header className="topbar">
                <img
                    src="/EngineerdLogoWhite.svg"
                    alt="Engineerd"
                    className="logo"
                />

                <div className="job-count">
                    {filteredJobs.length} jobs
                </div>
            </header>


            <main className="dashboard">

                <section className="hero">
                    <h1>One search. Multiple job sources.</h1>
                    <p>
                        Engineerd brings job postings from across the web into one searchable dashboard.
                    </p>
                </section>


                <section className="search-panel">
                    <div className="market-selector">
                        <div className="market-label">
                            <span>SEARCH MARKET</span>
                            <small>Choose where you want to find jobs</small>
                        </div>

                        <div className="market-options">
                            <button
                                className={market === "canada" ? "active" : ""}
                                onClick={() => setMarket("canada")}
                            >
                                <span className="market-flag">CA</span>
                                <span>Canada</span>
                            </button>

                            <button
                                className={market === "usa" ? "active" : ""}
                                onClick={() => setMarket("usa")}
                            >
                                <span className="market-flag">US</span>
                                <span>United States</span>
                            </button>

                            <button
                                className={market === "north-america" ? "active" : ""}
                                onClick={() => setMarket("north-america")}
                            >
                                <span className="market-flag">NA</span>
                                <span>North America</span>
                            </button>
                        </div>
                    </div>

                    <div className="filter-row">
                        <div className="search-wrapper">
                            <span>⌕</span>
                            <input
                                type="text"
                                placeholder="Search jobs or companies..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                        </div>

                        <select
                            value={remoteFilter}
                            onChange={(e) => setRemoteFilter(e.target.value)}
                        >
                            <option value="all">All locations</option>
                            <option value="remote">Remote</option>
                            <option value="remote only">Remote only</option>
                            <option value="on-site">On-site</option>
                        </select>

                        <select
                            value={sourceFilter}
                            onChange={(e) => setSourceFilter(e.target.value)}
                        >
                            <option value="all">All sources</option>
                            <option value="builtin">Built In</option>
                            <option value="wellfound">Wellfound</option>
                        </select>

                        <button
                            className="find-jobs-button"
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                        >
                            {isRefreshing ? (
                                <>
                                    <span className="spinner"></span>
                                    Finding Jobs...
                                </>
                            ) : (
                                "Find New Jobs"
                            )}
                        </button>
                    </div>
                </section>


                <div className="results-header">
                    <span>
                        {filteredJobs.length} matching jobs
                    </span>

                    <div className="saved-toggle">
                        <button
                            className={!showSaved ? "active" : ""}
                            onClick={() => setShowSaved(false)}
                        >
                            All Jobs
                        </button>

                        <button
                            className={showSaved ? "active" : ""}
                            onClick={() => setShowSaved(true)}
                        >
                            ♡ Saved
                            {savedJobs.length > 0 && (
                                <span className="saved-count">
                                    {savedJobs.length}
                                </span>
                            )}
                        </button>
                    </div>
                </div>


                <section className="job-list">

                    {filteredJobs.map((job) => (

                        <article className="job-card" key={job.id}>
                            <div className="company-logo">
                                {job.company_logo ? (
                                    <img
                                        src={job.company_logo}
                                        alt={`${job.company} logo`}
                                    />
                                ) : (
                                    <span>
                                        {job.company?.charAt(0)}
                                    </span>
                                )}
                            </div>

                            <div className="job-content">
                                <div className="job-main">
                                    <h2>{formatJobTitle(job)}</h2>

                                    <div className="company">
                                        {job.company}
                                    </div>

                                    <div className="job-meta">
                                        {job.location && (
                                            <span>{job.location}</span>
                                        )}

                                        {job.remote_type && (
                                            <span className="tag remote">
                                                {job.remote_type}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <div className="job-right">
                                    <span
                                        className={`posted-badge posted-${formatPostedTime(job.posted_at).type}`}
                                    >
                                        {formatPostedTime(job.posted_at).text}
                                    </span>

                                    {job.salary_min && (
                                        <div className="salary">
                                            {job.salary_period ? (
                                                <>
                                                    {job.salary_period === "annually"
                                                        ? `$${Math.round(job.salary_min / 1000)}k`
                                                        : `$${job.salary_min.toLocaleString()}`
                                                    }

                                                    {job.salary_max &&
                                                        (
                                                            job.salary_period === "annually"
                                                                ? ` – $${Math.round(
                                                                    job.salary_max / 1000
                                                                )}k`
                                                                : ` – $${job.salary_max.toLocaleString()}`
                                                        )
                                                    }

                                                    {" / "}

                                                    {job.salary_period === "hourly" && "hr"}
                                                    {job.salary_period === "daily" && "day"}
                                                    {job.salary_period === "monthly" && "mo"}
                                                    {job.salary_period === "annually" && "yr"}
                                                </>
                                            ) : (
                                                <>
                                                    ${Math.round(job.salary_min / 1000)}k
                                                    {job.salary_max &&
                                                        ` – $${Math.round(
                                                            job.salary_max / 1000
                                                        )}k`
                                                    }
                                                </>
                                            )}
                                        </div>
                                    )}

                                    <span className="source">
                                        {job.source}
                                    </span>
                                </div>
                            </div>

                            <button
                                className={`save-job ${
                                    isJobSaved(job.id) ? "saved" : ""
                                }`}
                                onClick={() => toggleSaved(job.id)}
                                aria-label={
                                    isJobSaved(job.id)
                                        ? "Remove saved job"
                                        : "Save job"
                                }
                            >
                                <span className="save-icon">
                                    {isJobSaved(job.id) ? "♥" : "♡"}
                                </span>

                                <span className="save-text">
                                    {isJobSaved(job.id) ? "Saved" : "Save"}
                                </span>
                            </button>

                            <a
                                className="view-job"
                                href={job.url}
                                target="_blank"
                                rel="noreferrer"
                            >
                                <span>View Job</span>
                                <span className="view-arrow">→</span>
                            </a>
                        </article>
                    ))}

                </section>

            </main>

        </div>
    );
}


export default Dashboard;