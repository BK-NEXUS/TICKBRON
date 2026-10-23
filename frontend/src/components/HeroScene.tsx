/** Decorative 3D backdrop of the home hero: three gold arches at different depths that turn with the pointer (CSS only). */
export function HeroScene() {
  return (
    <div className="hero-scene" aria-hidden="true">
      <div className="hero-scene-stage">
        <span className="hero-arch hero-arch--back" />
        <span className="hero-arch hero-arch--middle" />
        <span className="hero-arch hero-arch--front" />
      </div>
    </div>
  )
}
