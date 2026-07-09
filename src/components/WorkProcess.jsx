import { process } from "../data/process";
import SectionTitle from "./SectionTitle";

export default function WorkProcess() {
  return (
    <section className="section process" id="process">
      <div className="container" data-reveal>
        <SectionTitle
          eyebrow="05 · How I Work"
          title="From intent to governance."
          description="목적을 이해하고, 시스템화하고, 확장한 뒤 일관성을 관리합니다."
          invert
        />
        <ol className="process-list">
          {process.map((item, index) => (
            <li key={item.step}>
              <div className="process-list__top">
                <span>{item.step}</span>
                <span aria-hidden="true">
                  {index < process.length - 1 ? "↘" : "●"}
                </span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
