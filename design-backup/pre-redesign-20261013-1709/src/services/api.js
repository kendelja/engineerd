const API_URL = "http://localhost:8000";


export async function getJobs() {

    const response = await fetch(
        `${API_URL}/jobs/`
    );

    if (!response.ok) {
        throw new Error("Failed to fetch jobs.");
    }

    return response.json();
}