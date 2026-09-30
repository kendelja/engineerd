import { useEffect, useState } from "react";

function Dashboard() {
    const [jobs, setJobs] = useState([]);

    const [search, setSearch] = useState("");
    const [remoteFilter, setRemoteFilter] = useState("all");
    const [sourceFilter, setSourceFilter] = useState("all");
    const [isRefreshing, setIsRefreshing] = useState(false);

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
                "http://localhost:8000/jobs/ingest",
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

        const sameDay =
            postedDate.getFullYear() === now.getFullYear() &&
            postedDate.getMonth() === now.getMonth() &&
            postedDate.getDate() === now.getDate();

        if (sameDay) {
            return {
                text: "Today",
                type: "today"
            };
        }

        const seconds = Math.floor((now - postedDate) / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days === 1) {
            return {
                text: "Yesterday",
                type: "yesterday"
            };
        }

        if (days >= 2 && days <= 6) {
            return {
                text: `${days} days ago`,
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

        return matchesSearch && matchesRemote && matchesSource;
    });


    return (
        <div className="app">

            <header className="topbar">
                <img
                    src="/JobLensLogo.svg"
                    alt="JobLens"
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
                        JobLens brings job postings from across the web into one searchable dashboard.
                    </p>
                </section>


                <section className="filters">

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
                        <option value="all">
                            All locations
                        </option>

                        <option value="remote">
                            Remote
                        </option>

                        <option value="remote only">
                            Remote only
                        </option>

                        <option value="on-site">
                            On-site
                        </option>
                    </select>

                    <select
                        value={sourceFilter}
                        onChange={(e) => setSourceFilter(e.target.value)}
                    >
                        <option value="all">
                            All sources
                        </option>

                        <option value="builtin">
                            Built In
                        </option>

                        <option value="wellfound">
                            Wellfound
                        </option>
                    </select>

                    <button
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

                </section>


                <div className="results-header">
                    <span>
                        {filteredJobs.length} matching jobs
                    </span>
                </div>


                <section className="job-list">

                    {filteredJobs.map((job) => (

                        <article
                            className="job-card"
                            key={job.id}
                        >

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

                                    <h2>{job.title}</h2>

                                    <div className="company">
                                        {job.company}
                                    </div>

                                    <div className="job-meta">
                                        {job.location && (
                                            <span>
                                                {job.location}
                                            </span>
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

                                            ${Math.round(
                                                job.salary_min / 1000
                                            )}k

                                            {job.salary_max &&
                                                ` – $${Math.round(
                                                    job.salary_max / 1000
                                                )}k`
                                            }

                                        </div>
                                    )}

                                    <span className="source">
                                        {job.source}
                                    </span>

                                </div>

                            </div>


                            <a
                                className="view-job"
                                href={job.url}
                                target="_blank"
                                rel="noreferrer"
                            >
                                →
                            </a>

                        </article>

                    ))}

                </section>

            </main>

        </div>
    );
}


export default Dashboard;