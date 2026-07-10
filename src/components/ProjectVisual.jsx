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
            <div className="space-wall__meta">
              <span>BRAND SPACE</span>
              <span>SEOUL · 01</span>
            </div>
            <div className="space-wall__title">
              <strong>SPACE</strong>
              <span>SYSTEM</span>
            </div>
            <p>WORK / LEARN / CONNECT</p>
          </div>
          <div className="space-sign">
            <span>G</span>
            <small>
              WELCOME
              <br />
              LOUNGE
            </small>
          </div>
          <div className="space-wayfinding">
            <span>02</span>
            <strong>→</strong>
            <small>
              STUDIO
              <br />
              COMMUNITY
            </small>
          </div>
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
