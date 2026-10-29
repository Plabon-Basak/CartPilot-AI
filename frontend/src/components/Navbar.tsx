import { useEffect, useState } from "react";
import { useCart } from "../context/useCart";
import "./Navbar.css";

const ShoppingBagIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
    <line x1="3" y1="6" x2="21" y2="6"></line>
    <path d="M16 10a4 4 0 0 1-8 0"></path>
  </svg>
);

const UserIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

function Navbar() {
  const { cartCount } = useCart();
  const [activeSection, setActiveSection] = useState<string>("discover");

  useEffect(() => {
    const sections = ["discover", "assistant", "shopping"];
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      {
        rootMargin: "-90px 0px -60% 0px",
        threshold: [0, 0.25, 0.5, 0.75, 1],
      }
    );

    sections.forEach((id) => {
      const element = document.getElementById(id);
      if (element) {
        observer.observe(element);
      }
    });

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <span className="navbar-logo">🛒</span>
          <span className="navbar-brand-text">CartPilot AI</span>
        </div>

        <div className="navbar-links">
          <a href="#discover" className={`navbar-link ${activeSection === "discover" ? "navbar-link-active" : ""}`} aria-current={activeSection === "discover" ? "page" : undefined}>Discover</a>
          <a href="#assistant" className={`navbar-link ${activeSection === "assistant" ? "navbar-link-active" : ""}`} aria-current={activeSection === "assistant" ? "page" : undefined}>Assistant</a>
          <a href="#shopping" className={`navbar-link ${activeSection === "shopping" ? "navbar-link-active" : ""}`} aria-current={activeSection === "shopping" ? "page" : undefined}>My Shopping</a>
        </div>

        <div className="navbar-actions">
          <a href="#shopping" className="navbar-icon-btn" aria-label="Shopping bag">
            <ShoppingBagIcon />
            {cartCount > 0 && <span className="navbar-cart-badge">{cartCount}</span>}
          </a>
          <div className="navbar-profile">
            <div className="navbar-avatar">
              <UserIcon />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
