import { fitMatrix } from "../data/fitMatrix";
import SectionTitle from "./SectionTitle";

export default function FitMatrix() {
  return (
    <section className="section fit" id="fit">
      <div className="container" data-reveal>
        <SectionTitle
          eyebrow="03 · Role Fit"
          title="The right experience, matched."
          description="공고의 요구를 제가 해온 일과 1:1로 연결했습니다."
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
        <p className="fit__statement">
          공고의 요구사항을 충족하는 것을 넘어, 브랜드 디자인을 조직 안에서
          <strong> 일관되게 운영 가능한 구조</strong>로 만드는 데 집중합니다.
        </p>
      </div>
    </section>
  );
}
