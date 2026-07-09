export default function ProjectVisual({ type }) {
  return (
    <div className={`project-visual project-visual--${type}`} aria-hidden="true">
      {type === "system" && (
        <>
          <div className="system-card system-card--one">
            <small>BRAND PRINCIPLE</small>
            <strong>Clear</strong>
            <span />
          </div>
          <div className="system-card system-card--two">
            <small>VISUAL LANGUAGE</small>
            <div className="mini-grid">
              <i />
              <i />
              <i />
              <i />
            </div>
          </div>
        </>
      )}
      {type === "offline" && (
        <>
          <div className="space-wall">
            <span>goorm</span>
          </div>
          <div className="space-sign">G</div>
          <div className="space-floor" />
        </>
      )}
      {type === "campaign" && (
        <>
          <p>MESSAGE</p>
          <div className="campaign-type">
            Make it
            <br />
            <span>clear.</span>
          </div>
          <div className="campaign-dot" />
        </>
      )}
      {type === "ai" && (
        <>
          <div className="ai-orbit ai-orbit--one" />
          <div className="ai-orbit ai-orbit--two" />
          <div className="ai-core">AI</div>
          <span className="ai-label">RESEARCH → EXPAND → GOVERN</span>
        </>
      )}
    </div>
  );
}
