import { IconMoon, IconSun } from "./Icons";


// Shows the mode you will switch to: the sun in dark mode, the moon in light.
export default function ThemeToggle({ isDark, onToggle }) {
    return (
        <button
            className="theme-toggle"
            onClick={onToggle}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            title={isDark ? "Light mode" : "Dark mode"}
        >
            {isDark ? <IconSun /> : <IconMoon />}
        </button>
    );
}
