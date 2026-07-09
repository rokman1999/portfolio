export default function SectionTitle({ eyebrow, title, description, invert = false }) {
  return (
    <header className={`section-title ${invert ? "section-title--invert" : ""}`}>
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {description && <p className="section-title__description">{description}</p>}
    </header>
  );
}
