import { IconGitHub, IconLinkedIn } from "./Icons";


export const REPO_URL = "https://github.com/kendelja/engineerd";
export const LINKEDIN_URL = "https://www.linkedin.com/in/jacekendel/";


export default function SiteFooter() {
    return (
        <footer className="site-footer">

            <p>
                Created by <strong>Jace Kendel</strong> · 2026
            </p>

            <div className="footer-badges">
                <a
                    className="badge badge-linkedin"
                    href={LINKEDIN_URL}
                    target="_blank"
                    rel="noreferrer"
                >
                    <IconLinkedIn />
                    LinkedIn
                </a>

                <a
                    className="badge badge-github"
                    href={REPO_URL}
                    target="_blank"
                    rel="noreferrer"
                >
                    <IconGitHub />
                    GitHub
                </a>
            </div>

        </footer>
    );
}
