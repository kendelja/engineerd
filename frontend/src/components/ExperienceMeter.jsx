import { yearsTone } from "../lib/jobs";


const SCALE_MAX = 10;

// A 0-10 year bar. The fill shows what the posting asks for, so the
// requirement reads at a glance instead of as a number to decode.
export default function ExperienceMeter({ years }) {
    const tone = yearsTone(years);

    if (tone === "unknown") {
        return (
            <div className="meter meter-unknown">
                <span className="meter-track" />
                <span className="meter-label">Years not stated</span>
            </div>
        );
    }

    const fill = Math.min(years, SCALE_MAX) / SCALE_MAX * 100;

    const label =
        years === 0
            ? "No experience required"
            : `Asks ${years} yrs`;

    return (
        <div className={`meter meter-${tone}`} title={label}>
            <span className="meter-track">
                <span className="meter-fill" style={{ width: `${Math.max(fill, 4)}%` }} />
            </span>
            <span className="meter-label">{label}</span>
        </div>
    );
}
