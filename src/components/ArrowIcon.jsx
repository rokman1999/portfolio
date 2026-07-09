export default function ArrowIcon({ diagonal = false }) {
  return (
    <svg
      aria-hidden="true"
      className="arrow-icon"
      viewBox="0 0 20 20"
      fill="none"
    >
      {diagonal ? (
        <path d="M5 15 15 5m0 0H7m8 0v8" />
      ) : (
        <path d="M3 10h14m-5-5 5 5-5 5" />
      )}
    </svg>
  );
}
