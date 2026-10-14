import { API_URL, JOB_LIMIT } from "./jobs";


// How often the page checks whether a scheduled refresh has landed.
export const STATUS_POLL_MS = 60000;


export async function fetchJobs(market) {
    const response = await fetch(
        `${API_URL}/jobs/?limit=${JOB_LIMIT}&market=${market}`
    );

    if (!response.ok) {
        throw new Error("Failed to fetch jobs");
    }

    return response.json();
}

// Chart and skills are extras: if they fail, the list still works.
export async function fetchSummary(market) {
    try {
        const [activity, topSkills] = await Promise.all([
            fetch(`${API_URL}/jobs/activity?days=14&market=${market}`).then((r) => (r.ok ? r.json() : [])),
            fetch(`${API_URL}/jobs/top-skills?limit=500&market=${market}`).then((r) => (r.ok ? r.json() : [])),
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

const ADMIN_TOKEN_KEY = "engineerd-admin-token";

// Kept for this browser session only; closing the tab forgets it.
export function readAdminToken() {
    try {
        return sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
    } catch {
        return "";
    }
}

export function storeAdminToken(token) {
    try {
        if (token) {
            sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
        } else {
            sessionStorage.removeItem(ADMIN_TOKEN_KEY);
        }
    } catch {
        // Blocked storage: the token is asked for again next time.
    }
}

// Resolves with the HTTP status so the caller can tell "busy" from "failed".
export async function startIngest(market, token) {
    const response = await fetch(
        `${API_URL}/jobs/ingest?market=${market}`,
        { method: "POST", headers: { "X-Admin-Token": token } }
    );

    return { ok: response.ok, status: response.status };
}
