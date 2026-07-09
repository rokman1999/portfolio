import { useEffect, useState } from "react";
import { profile } from "../data/profile";
import ArrowIcon from "./ArrowIcon";

const navigation = [
  ["About", "about"],
  ["Why Hyundai", "why-hyundai"],
  ["Fit", "fit"],
  ["Works", "works"],
  ["Process", "process"],
  ["Contact", "contact"],
];

export default function Header() {
  const [active, setActive] = useState("about");
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const sections = navigation
      .map(([, id]) => document.getElementById(id))
      .filter(Boolean);
    const observer = new IntersectionObserver(
      (entries) => {
        const current = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (current) setActive(current.target.id);
      },
      { rootMargin: "-30% 0px -60% 0px", threshold: [0, 0.25, 0.5] },
    );
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <a className="wordmark" href="#top" aria-label="페이지 맨 위로">
          <span className="wordmark__mark">HYR</span>
          <span className="wordmark__text">
            Brand Experience
            <br />
            Designer
          </span>
        </a>

        <button
          className="menu-toggle"
          type="button"
          aria-expanded={menuOpen}
          aria-controls="primary-navigation"
          onClick={() => setMenuOpen((value) => !value)}
        >
          <span>{menuOpen ? "Close" : "Menu"}</span>
          <span className="menu-toggle__lines" aria-hidden="true" />
        </button>

        <nav
          id="primary-navigation"
          className={`site-nav ${menuOpen ? "is-open" : ""}`}
          aria-label="주요 메뉴"
        >
          {navigation.map(([label, id]) => (
            <a
              key={id}
              className={active === id ? "is-active" : ""}
              href={`#${id}`}
              onClick={() => setMenuOpen(false)}
            >
              {label}
            </a>
          ))}
        </nav>

        <a
          className="header-download"
          href={profile.portfolioPath}
          download
        >
          <span>Portfolio PDF</span>
          <ArrowIcon diagonal />
        </a>
      </div>
    </header>
  );
}
