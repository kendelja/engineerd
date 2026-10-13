import { useRef, useState } from "react";

import { IconChevron } from "./Icons";


const ROW = 22;        // px per row
const WINDOW = 1.6;    // rows drawn either side of the centre


// An iPhone-style picker: drag with a mouse or finger, or use the arrow
// keys. Rows fade and tilt away from the centre, and it snaps to the
// nearest skill when you let go. The page still scrolls normally over it.
export default function SkillWheel({ skills }) {
    const [position, setPosition] = useState(0);
    const [dragging, setDragging] = useState(false);

    const drag = useRef(null);

    const last = Math.max(skills.length - 1, 0);
    const clamp = (value) => Math.min(Math.max(value, 0), last);
    const selected = Math.round(position);

    function snapToNearest() {
        setPosition((current) => clamp(Math.round(current)));
    }

    function onPointerDown(event) {
        event.currentTarget.setPointerCapture(event.pointerId);

        drag.current = { y: event.clientY, start: position };
        setDragging(true);
    }

    function onPointerMove(event) {
        if (!drag.current) {
            return;
        }

        const rows = (drag.current.y - event.clientY) / ROW;

        setPosition(clamp(drag.current.start + rows));
    }

    function onPointerUp() {
        drag.current = null;
        setDragging(false);
        snapToNearest();
    }

    function onKeyDown(event) {
        const moves = {
            ArrowDown: selected + 1,
            ArrowUp: selected - 1,
            PageDown: selected + 3,
            PageUp: selected - 3,
            Home: 0,
            End: last,
        };

        if (event.key in moves) {
            event.preventDefault();
            setPosition(clamp(moves[event.key]));
        }
    }

    if (skills.length === 0) {
        return <p className="wheel-empty">No skills yet</p>;
    }

    return (
        <div
            className={`wheel ${dragging ? "dragging" : ""}`}
            style={{ height: ROW * 3 }}
            title={`Drag to see all ${skills.length} skills`}
            tabIndex={0}
            role="listbox"
            aria-label={`Skills by number of postings, ${skills.length} in total. Drag or use the arrow keys.`}
            aria-activedescendant={`skill-${selected}`}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            onKeyDown={onKeyDown}
        >
            <div className="wheel-band" style={{ height: ROW }} aria-hidden="true" />

            <IconChevron className="wheel-chevron wheel-chevron-up" />
            <IconChevron className="wheel-chevron wheel-chevron-down" />

            {skills.map((item, index) => {
                const offset = index - position;

                if (Math.abs(offset) > WINDOW) {
                    return null;
                }

                const distance = Math.abs(offset);

                return (
                    <div
                        key={item.skill}
                        id={`skill-${index}`}
                        role="option"
                        aria-selected={index === selected}
                        className={`wheel-row ${index === selected ? "selected" : ""}`}
                        style={{
                            height: ROW,
                            transform: `translateY(${offset * ROW}px) rotateX(${-offset * 24}deg)`,
                            opacity: Math.max(0, 1 - distance * 0.4),
                        }}
                    >
                        <span>{item.skill}</span>
                        <span className="skill-count">{item.postings}</span>
                    </div>
                );
            })}
        </div>
    );
}
