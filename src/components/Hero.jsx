import { useEffect, useState } from "react";
import { profile } from "../data/profile";
import Button from "./Button";

export default function Hero() {
  const [isCardFlipped, setIsCardFlipped] = useState(false);

  useEffect(() => {
    let ticking = false;

    const updateCardFlip = () => {
      if (ticking) return;

      ticking = true;
      window.requestAnimationFrame(() => {
        setIsCardFlipped(window.scrollY > 24);
        ticking = false;
      });
    };

    updateCardFlip();
    window.addEventListener("scroll", updateCardFlip, { passive: true });

    return () => window.removeEventListener("scroll", updateCardFlip);
  }, []);

  return (
    <section className="hero" id="top">
      <button
        className={`hero-card ${isCardFlipped ? "is-flipped" : "is-front"}`}
        type="button"
        aria-label="명함 앞뒤 뒤집기"
        aria-pressed={isCardFlipped}
        onClick={() => setIsCardFlipped((value) => !value)}
      >
        <span className="hero-card__inner">
          <span className="hero-card__face hero-card__face--front">
            <img src="assets/card-front.png" alt="" draggable="false" />
          </span>
          <span className="hero-card__face hero-card__face--back">
            <img src="assets/card-back.png" alt="" draggable="false" />
          </span>
        </span>
      </button>
      <div className="hero__grid container">
        <div className="hero__content">
          <div className="hero__title-wrap">
            <h1>
              Designing Trust
              <br />
              into <em>Brand Experience.</em>
            </h1>
          </div>
          <p className="hero__intro">
            브랜드의 신뢰를 시각 언어로 설계하고, 온·오프라인 접점에서 일관된 경험으로 확장합니다.
          </p>
        </div>
      </div>
      <div className="hero__actions">
        <Button href={profile.portfolioPath} download diagonal>
          Portfolio PDF
        </Button>
        <Button href="#fit" variant="secondary">
          View Hyundai Fit
        </Button>
      </div>
      <div className="hero__footer container" aria-hidden="true">
        <span>01 — Introduction</span>
        <span>Scroll to explore</span>
      </div>
    </section>
  );
}
