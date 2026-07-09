import { profile } from "../data/profile";
import Button from "./Button";

export default function PortfolioDownload() {
  return (
    <section className="download-section" aria-labelledby="download-title">
      <div className="container download-section__inner" data-reveal>
        <div>
          <p className="eyebrow">07 · Full Portfolio</p>
          <h2 id="download-title">
            See the full
            <br />
            <em>design process.</em>
          </h2>
        </div>
        <div className="download-section__action">
          <p>
            더 자세한 프로젝트 과정과 결과물은
            <br />
            PDF 포트폴리오에서 확인하실 수 있습니다.
          </p>
          <Button href={profile.portfolioPath} download diagonal>
            Download Portfolio PDF
          </Button>
          <span>PDF · HAN YOUNGROK · SELECTED WORKS</span>
        </div>
      </div>
    </section>
  );
}
