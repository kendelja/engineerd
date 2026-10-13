import { FIT_INFO } from "../lib/jobs";


export default function FitBadge({ label }) {
    const info = FIT_INFO[label];

    if (!info) {
        return null;
    }

    return (
        <span
            className={`fit-badge fit-${label}`}
            title={info.help}
        >
            <span className="fit-dot" aria-hidden="true" />
            {info.label}
        </span>
    );
}
