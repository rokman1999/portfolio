import { projects } from "../data/projects";
import ProjectCard from "./ProjectCard";
import SectionTitle from "./SectionTitle";

export default function SelectedWorks() {
  return (
    <section className="section works" id="works">
      <div className="container" data-reveal>
        <SectionTitle
          eyebrow="04 · Selected Works"
          title={
            <>
              Four ways I build
              <br />
              <em>consistent brands.</em>
            </>
          }
          description="현대해상 브랜드디자인 직무의 관점에서 작업을 네 가지 역량으로 재구성했습니다."
        />
        <div className="project-grid">
          {projects.map((project) => (
            <ProjectCard project={project} key={project.title} />
          ))}
        </div>
      </div>
    </section>
  );
}
