import { experiences, strengths } from "../data/profile";
import SectionTitle from "./SectionTitle";

export default function ResumeSnapshot() {
  return (
    <section className="section resume" id="resume">
      <div className="container" data-reveal>
        <SectionTitle
          eyebrow="06 · Resume Snapshot"
          title="Experience, briefly."
        />
        <div className="resume__grid">
          <div className="resume__profile">
            <div className="resume-monogram" aria-hidden="true">
              H<br />Y<br />R
            </div>
            <div>
              <h3>HAN YOUNGROK</h3>
              <p>Brand / Content / BX Designer</p>
              <span>Seoul, KR · 5+ Years</span>
            </div>
          </div>
          <div className="timeline">
            <h3>Experience</h3>
            {experiences.map((experience) => (
              <article key={experience.company}>
                <div className="timeline__heading">
                  <div>
                    <strong>{experience.company}</strong>
                    <span>{experience.role}</span>
                  </div>
                  <time>{experience.period}</time>
                </div>
                <p>{experience.description}</p>
              </article>
            ))}
          </div>
          <div className="strengths">
            <h3>Core Strength</h3>
            <ol>
              {strengths.map((strength, index) => (
                <li key={strength}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  {strength}
                </li>
              ))}
            </ol>
            <div className="award-note">
              <span>Selected Award</span>
              <strong>2024 iF Design Award</strong>
              <p>Communication / Package</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
