import { API_URL, JOB_LIMIT } from "./jobs";


// How often the page checks whether a scheduled refresh has landed.
export const STATUS_POLL_MS = 60000;


export async function fetchJobs() {
    const response = await fetch(`${API_URL}/jobs/?limit=${JOB_LIMIT}`);

    if (!response.ok) {
        throw new Error("Failed to fetch jobs");
    }

    return response.json();
}

// Chart and skills are extras: if they fail, the list still works.
export async function fetchSummary() {
    try {
        const [activity, topSkills] = await Promise.all([
            fetch(`${API_URL}/jobs/activity?days=14`).then((r) => (r.ok ? r.json() : [])),
            fetch(`${API_URL}/jobs/top-skills?limit=500`).then((r) => (r.ok ? r.json() : [])),
        ]);

        return { activity, topSkills };
    } catch {
        return { activity: [], topSkills: [] };
    }
}

export async function fetchIngestStatus() {
    const response = await fetch(`${API_URL}/jobs/ingest/status`);

    if (!response.ok) {
        throw new Error("Failed to fetch refresh status");
    }

    return response.json();
}

// Resolves with the HTTP status so the caller can tell "busy" from "failed".
export async function startIngest(market) {
    const response = await fetch(
        `${API_URL}/jobs/ingest?market=${market}`,
        { method: "POST" }
    );

    return { ok: response.ok, status: response.status };
}
