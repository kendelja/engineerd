import { useState } from "react";

import { formatDayLabel } from "../lib/jobs";


// Jobs posted per day, oldest on the left. Hovering (or focusing) a bar
// shows that day's count in the readout; with nothing hovered the
// readout shows today.
export default function ActivityChart({ days }) {
    const [hovered, setHovered] = useState(null);

    if (days.length === 0) {
        return null;
    }

    const peak = Math.max(...days.map((day) => day.count), 1);
    const todayIndex = days.length - 1;
    const activeIndex = hovered ?? todayIndex;
    const active = days[activeIndex];

    return (
        <section className="activity" aria-label="Jobs posted per day">

            <div className="activity-readout" aria-live="polite">
                <span className="activity-value">{active.count}</span>
                <span className="activity-text">
                    {active.count === 1 ? "job" : "jobs"} posted{" "}
                    <strong>{formatDayLabel(active.date)}</strong>
                </span>
            </div>

            <div
                className="activity-bars"
                onMouseLeave={() => setHovered(null)}
            >
                {days.map((day, index) => {
                    const height = Math.max((day.count / peak) * 100, 4);

                    return (
                        <button
                            key={day.date}
                            type="button"
                            className={[
                                "activity-bar",
                                index === todayIndex ? "today" : "",
                                index === activeIndex ? "active" : "",
                            ].join(" ")}
                            style={{ height: `${height}%` }}
                            onMouseEnter={() => setHovered(index)}
                            onFocus={() => setHovered(index)}
                            onBlur={() => setHovered(null)}
                            aria-label={`${day.count} ${day.count === 1 ? "job" : "jobs"} posted ${formatDayLabel(day.date)}`}
                        />
                    );
                })}
            </div>

            <div className="activity-axis" aria-hidden="true">
                <span>{days.length - 1 ? `${days.length - 1} days ago` : ""}</span>
                <span>Today</span>
            </div>

        </section>
    );
}
