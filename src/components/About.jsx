import { profile } from "../data/profile";
import SectionTitle from "./SectionTitle";

export default function About() {
  return (
    <section className="section about" id="about">
      <div className="container" data-reveal>
        <SectionTitle
          eyebrow="01 · About"
          title={
            <>
              좋은 디자인은 결과물에 머물지 않고,
              <br />
              <em className="korean-emphasis">운영 가능한 구조</em>가 됩니다.
            </>
          }
        />
        <div className="about__body">
          <div className="about__index" aria-hidden="true">
            <span>5+</span>
            <p>
              Years in-house
              <br />
              brand experience
            </p>
          </div>
          <div className="about__copy">
            <p className="lead">
              저는 브랜드의 정체성을 감각적인 결과물로 끝내지 않고, 조직
              안에서 반복 사용 가능한 디자인 시스템으로 정리하는 BX
              디자이너입니다.
            </p>
            <p>
              5년 이상 인하우스 환경에서 브랜드 아이덴티티, 캠페인, 공간,
              패키지, 온드미디어 콘텐츠까지 다양한 접점을 설계해 왔습니다.
              브랜드 메시지가 여러 채널에서 일관되게 전달될 수 있도록 비주얼
              시스템과 운영 구조를 함께 고민합니다.
            </p>
          </div>
        </div>
        <div className="keyword-list" aria-label="핵심 역량">
          {profile.keywords.map((keyword, index) => (
            <span key={keyword}>
              <b>{String(index + 1).padStart(2, "0")}</b>
              {keyword}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
