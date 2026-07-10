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
      </div>
    </article>
  );
}
