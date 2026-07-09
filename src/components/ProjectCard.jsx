import { profile } from "../data/profile";
import ArrowIcon from "./ArrowIcon";
import ProjectVisual from "./ProjectVisual";

export default function ProjectCard({ project }) {
  return (
    <article className="project-card">
      <ProjectVisual type={project.visual} />
      <div className="project-card__content">
        <div className="project-card__meta">
          <span>{project.number}</span>
          <span>{project.category}</span>
        </div>
        <h3>{project.title}</h3>
        <p>{project.description}</p>
        <dl>
          <div>
            <dt>Role</dt>
            <dd>{project.role}</dd>
          </div>
          <div>
            <dt>Related Skills</dt>
            <dd className="tag-row">
              {project.tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </dd>
          </div>
        </dl>
        <a href={profile.portfolioPath} download>
          <span>View in Portfolio PDF</span>
          <ArrowIcon diagonal />
        </a>
      </div>
    </article>
  );
}
