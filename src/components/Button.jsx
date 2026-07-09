import ArrowIcon from "./ArrowIcon";

export default function Button({
  children,
  href,
  variant = "primary",
  download = false,
  diagonal = false,
  className = "",
}) {
  return (
    <a
      className={`button button--${variant} ${className}`.trim()}
      href={href}
      download={download || undefined}
    >
      <span>{children}</span>
      <ArrowIcon diagonal={diagonal} />
    </a>
  );
}
