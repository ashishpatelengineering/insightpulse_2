import { NavLink } from "react-router-dom";
import { MODES } from "../modes/config.js";
import { ModeIcon } from "./Icons.jsx";

export default function Sidebar() {
  return (
    <nav className="sidebar" aria-label="Analysis modes">
      {MODES.map((mode) => (
        <NavLink
          key={mode.id}
          to={mode.path}
          className={({ isActive }) => `side-link${isActive ? " active" : ""}`}
          title={mode.title}
          aria-label={mode.title}
        >
          <ModeIcon name={mode.icon} />
          <span className="side-label">{mode.shortTitle}</span>
        </NavLink>
      ))}
    </nav>
  );
}
