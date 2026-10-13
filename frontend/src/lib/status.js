// "2026-10-13T17:42:00" -> "just now" | "12 min ago" | "3 h ago" | "2 days ago"
export function formatAgo(isoTimestamp, now = new Date()) {
    if (!isoTimestamp) {
        return null;
    }

    const minutes = Math.round((now - new Date(isoTimestamp)) / 60000);

    if (minutes < 2) return "just now";
    if (minutes < 60) return `${minutes} min ago`;

    const hours = Math.round(minutes / 60);

    if (hours < 24) return `${hours} h ago`;

    const days = Math.round(hours / 24);

    return `${days} ${days === 1 ? "day" : "days"} ago`;
}

// "2026-10-13T18:00:00-04:00" -> "6:00 p.m."
export function formatClock(isoTimestamp) {
    if (!isoTimestamp) {
        return null;
    }

    return new Date(isoTimestamp).toLocaleTimeString("en-CA", {
        hour: "numeric",
        minute: "2-digit",
    });
}
