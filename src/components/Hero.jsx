import { profile } from "../data/profile";
import Button from "./Button";

export default function Hero() {
  return (
    <section className="hero" id="top">
      <div className="hero__grid container">
        <div className="hero__content">
          <h1>
            Designing Trust
            <br />
            into <em>Brand Experience.</em>
          </h1>
          <p className="hero__intro">
            브랜드의 신뢰를 시각 언어로 설계하고,
            <br />
            온·오프라인 접점에서 일관된 경험으로 확장합니다.
          </p>
          <div className="hero__actions">
            <Button href={profile.portfolioPath} download diagonal>
              Portfolio PDF
            </Button>
            <Button href="#fit" variant="secondary">
              View Hyundai Fit
            </Button>
          </div>
        </div>
      </div>
      <div className="hero__footer container" aria-hidden="true">
        <span>01 — Introduction</span>
        <span>Scroll to explore</span>
      </div>
    </section>
  );
}
