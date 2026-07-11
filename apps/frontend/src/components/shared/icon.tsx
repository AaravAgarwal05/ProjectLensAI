/**
 * Material Symbols icon wrapper.
 * Usage: <Icon>search</Icon> or <Icon fill>home</Icon>
 */
export function Icon({
  children,
  fill,
  className = '',
  size,
}: {
  children: string
  fill?: boolean
  className?: string
  size?: string
}) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={{
        fontVariationSettings: `'FILL' ${fill ? 1 : 0}, 'wght' 300, 'GRAD' 0, 'opsz' 24`,
        fontSize: size ?? '20px',
      }}
    >
      {children}
    </span>
  )
}
