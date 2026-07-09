import { profile } from "../data/profile";
import ArrowIcon from "./ArrowIcon";

export default function Contact() {
  return (
    <footer className="contact" id="contact">
      <div className="container" data-reveal>
        <p className="eyebrow">08 · Contact</p>
        <div className="contact__heading">
          <h2>
            Let’s design trust,
            <br />
            <em>consistently.</em>
          </h2>
          <p>
            브랜드의 신뢰가 더 많은 접점에서 일관되게 전달될 수 있도록,
            디자인 시스템과 경험을 함께 설계하겠습니다.
          </p>
        </div>
        <div className="contact__links">
          <a href={`mailto:${profile.email}`}>
            <span>Email</span>
            <strong>{profile.email}</strong>
            <ArrowIcon diagonal />
          </a>
          <a href={profile.phoneHref}>
            <span>Phone</span>
            <strong>{profile.phone}</strong>
            <ArrowIcon diagonal />
          </a>
          <div>
            <span>Location</span>
            <strong>{profile.location}</strong>
          </div>
        </div>
        <div className="contact__footer">
          <span>© 2026 HAN YOUNGROK</span>
          <span>BRAND EXPERIENCE DESIGNER</span>
          <a href="#top">Back to top ↑</a>
        </div>
      </div>
    </footer>
  );
}
