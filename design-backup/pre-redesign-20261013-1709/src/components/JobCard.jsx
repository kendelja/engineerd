function JobCard({ job }) {

    return (
        <article className="job-card">

            <div className="job-header">

                <div>
                    <h2>{job.title}</h2>

                    <p className="company">
                        {job.company}
                    </p>
                </div>

                {job.experience_level && (
                    <span className="experience">
                        {job.experience_level}
                    </span>
                )}

            </div>

            <p>
                {job.location || "Location not specified"}
            </p>

            {job.remote_type && (
                <p>
                    {job.remote_type}
                </p>
            )}

            <div className="job-footer">

                <span>
                    {job.source}
                </span>

                <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    View Posting →
                </a>

            </div>

        </article>
    );
}

export default JobCard;