import { fitMatrix } from "../data/fitMatrix";
import SectionTitle from "./SectionTitle";

export default function FitMatrix() {
  return (
    <section className="section fit" id="fit">
      <div className="container" data-reveal>
        <SectionTitle
          eyebrow="03 · Role Fit"
          title="The right experience, matched."
        />
        <div className="fit-table" role="table" aria-label="현대해상 직무 적합성">
          <div className="fit-table__head" role="row">
            <span role="columnheader">Hyundai’s Needs</span>
            <span role="columnheader">My Experience</span>
          </div>
          {fitMatrix.map((item, index) => (
            <div className="fit-row" role="row" key={item.requirement}>
              <div role="cell">
                <span className="fit-row__number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <strong>{item.requirement}</strong>
              </div>
              <p role="cell">{item.experience}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
