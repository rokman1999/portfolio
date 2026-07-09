import { useEffect } from "react";
import About from "./components/About";
import Contact from "./components/Contact";
import FitMatrix from "./components/FitMatrix";
import Header from "./components/Header";
import Hero from "./components/Hero";
import PortfolioDownload from "./components/PortfolioDownload";
import ResumeSnapshot from "./components/ResumeSnapshot";
import SelectedWorks from "./components/SelectedWorks";
import WhyHyundai from "./components/WhyHyundai";
import WorkProcess from "./components/WorkProcess";

export default function App() {
  useEffect(() => {
    const items = document.querySelectorAll("[data-reveal]");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 },
    );

    items.forEach((item) => observer.observe(item));
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <a className="skip-link" href="#main">
        본문으로 바로가기
      </a>
      <Header />
      <main id="main">
        <Hero />
        <About />
        <WhyHyundai />
        <FitMatrix />
        <SelectedWorks />
        <WorkProcess />
        <ResumeSnapshot />
        <PortfolioDownload />
        <Contact />
      </main>
    </>
  );
}
