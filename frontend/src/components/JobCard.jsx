import ExperienceMeter from "./ExperienceMeter";
import FitBadge from "./FitBadge";
import { IconArrow, IconHeart, IconPin } from "./Icons";
import {
    fitReason,
    formatJobTitle,
    formatPostedTime,
    formatSalary,
} from "../lib/jobs";


const MAX_SKILLS = 5;

export default function JobCard({ job, saved, onToggleSave }) {
    const posted = formatPostedTime(job.posted_at);
    const salary = formatSalary(job);
    const reason = fitReason(job);
    const skills = job.skills ?? [];
    const hiddenSkills = skills.slice(MAX_SKILLS);

    return (
        <article className={`job-card spine-${job.fit_label ?? "none"}`}>

            <header className="job-top">

                <div className="company-mark">
                    {job.company_logo ? (
                        <img
                            src={job.company_logo}
                            alt=""
                            loading="lazy"
                        />
                    ) : (
                        <span>{job.company?.charAt(0)}</span>
                    )}
                </div>

                <div className="job-company">
                    <span className="company-name">{job.company}</span>
                    <span className="source-chip">{job.source}</span>
                </div>

                <button
                    className={`save-button ${saved ? "saved" : ""}`}
                    onClick={() => onToggleSave(job.id)}
                    aria-pressed={saved}
                    aria-label={saved ? "Remove from saved" : "Save job"}
                    title={saved ? "Saved" : "Save"}
                >
                    <IconHeart filled={saved} />
                </button>

            </header>

            <div className="job-main">

                <h2 className="job-title">{formatJobTitle(job)}</h2>

                <div className="job-meta">

                    {job.location && (
                        <span className="meta-item">
                            <IconPin />
                            {job.location}
                        </span>
                    )}

                    {job.work_model && (
                        <span
                            className={`work-chip ${
                                job.work_model === "Remote" ? "remote" : ""
                            }`}
                        >
                            {job.work_model}
                        </span>
                    )}

                </div>

            </div>

            <div className="job-signals">

                <FitBadge label={job.fit_label} />

                {job.years_required !== null && job.years_required !== undefined ? (
                    <ExperienceMeter years={job.years_required} />
                ) : (
                    job.fit_label && job.fit_label !== "unclear" && (
                        <ExperienceMeter years={null} />
                    )
                )}

                {reason && <p className="fit-reason">{reason}</p>}

            </div>

            {skills.length > 0 && (
                <ul className="skill-list" aria-label="Skills mentioned">
                    {skills.slice(0, MAX_SKILLS).map((skill) => (
                        <li key={skill} className="skill">{skill}</li>
                    ))}
                    {hiddenSkills.length > 0 && (
                        <li
                            className="skill skill-more"
                            title={hiddenSkills.join(", ")}
                        >
                            +{hiddenSkills.length}
                        </li>
                    )}
                </ul>
            )}

            <footer className="job-footer">

                <div className="job-facts">
                    {salary && <span className="salary">{salary}</span>}
                    <span className={`posted posted-${posted.type}`}>
                        {posted.text}
                    </span>
                </div>

                <a
                    className="view-link"
                    href={job.url}
                    target="_blank"
                    rel="noreferrer"
                >
                    View job
                    <IconArrow />
                </a>

            </footer>

        </article>
    );
}
