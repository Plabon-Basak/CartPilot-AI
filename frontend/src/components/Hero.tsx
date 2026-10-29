import "./Hero.css";

const SparkleIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
  </svg>
);

function Hero() {
  return (
    <section className="hero">
      <div className="hero-container">
        <div className="hero-content">
          <div className="hero-badge">
            <SparkleIcon />
            <span>AI-Powered Shopping</span>
          </div>
          <h1 className="hero-title">Shopping, made smarter.</h1>
          <p className="hero-description">
            Discover products tailored to your needs with CartPilot AI. Get intelligent 
            recommendations and streamline your shopping experience with our personal 
            autonomous shopping agent.
          </p>
        </div>
      </div>
    </section>
  );
}

export default Hero;
