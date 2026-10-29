import { useEffect, useRef, useState } from "react";
import { useCart } from "../context/useCart";
import "./Navbar.css";

const NAVBAR_OFFSET = 90;
const TARGET_TOLERANCE = 2;
const CLICK_TOLERANCE = 1;
const SECTION_ORDER = ["assistant", "discover", "shopping"];
const DEFAULT_SECTION = "discover";

const isAtPageBottom = () =>
  window.scrollY > 0 &&
  window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;

const getSectionScrollTop = (section: HTMLElement) => {
  const maxScrollTop = Math.max(
    0,
    document.documentElement.scrollHeight - window.innerHeight,
  );
  const sectionTop = section.getBoundingClientRect().top + window.scrollY;
  return Math.min(Math.max(sectionTop - NAVBAR_OFFSET, 0), maxScrollTop);
};

const isSectionAtOffset = (section: HTMLElement, tolerance: number) =>
  Math.abs(section.getBoundingClientRect().top - NAVBAR_OFFSET) <= tolerance;

const getActiveSection = () => {
  if (isAtPageBottom()) {
    return "shopping";
  }

  let current = DEFAULT_SECTION;
  for (const id of SECTION_ORDER) {
    const section = document.getElementById(id);
    if (
      section &&
      section.getBoundingClientRect().top <= NAVBAR_OFFSET + TARGET_TOLERANCE
    ) {
      current = id;
    }
  }
  return current;
};

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
  const [activeSection, setActiveSection] = useState<string>(DEFAULT_SECTION);
  const pendingSectionRef = useRef<string | null>(null);
  const pendingScrollStartedRef = useRef(false);

  useEffect(() => {
    let frameId = 0;

    const finishPendingSection = () => {
      const pendingSection = pendingSectionRef.current;
      if (!pendingSection || !pendingScrollStartedRef.current) {
        return;
      }

      const target = document.getElementById(pendingSection);
      const targetReached =
        target !== null &&
        (isSectionAtOffset(target, TARGET_TOLERANCE) ||
          (pendingSection === "shopping" && isAtPageBottom()));

      pendingSectionRef.current = null;
      pendingScrollStartedRef.current = false;
      setActiveSection(targetReached ? pendingSection : getActiveSection());
    };

    const updateActiveSection = () => {
      const pendingSection = pendingSectionRef.current;
      if (pendingSection) {
        setActiveSection(pendingSection);
        return;
      }

      setActiveSection(getActiveSection());
    };

    const handleScroll = () => {
      if (pendingSectionRef.current) {
        pendingScrollStartedRef.current = true;
      }
      if (frameId !== 0) {
        return;
      }
      frameId = window.requestAnimationFrame(() => {
        frameId = 0;
        updateActiveSection();
      });
    };

    const cancelPendingSection = () => {
      pendingSectionRef.current = null;
      pendingScrollStartedRef.current = false;
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        event.key === "ArrowUp" ||
        event.key === "ArrowDown" ||
        event.key === "PageUp" ||
        event.key === "PageDown" ||
        event.key === "Home" ||
        event.key === "End" ||
        event.key === " "
      ) {
        cancelPendingSection();
      }
    };

    const handleScrollEnd = () => {
      finishPendingSection();
    };

    updateActiveSection();
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleScroll);
    window.addEventListener("wheel", cancelPendingSection, { passive: true });
    window.addEventListener("touchmove", cancelPendingSection, { passive: true });
    window.addEventListener("pointerdown", cancelPendingSection, { passive: true });
    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("scrollend", handleScrollEnd);

    return () => {
      if (frameId !== 0) {
        window.cancelAnimationFrame(frameId);
      }
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
      window.removeEventListener("wheel", cancelPendingSection);
      window.removeEventListener("touchmove", cancelPendingSection);
      window.removeEventListener("pointerdown", cancelPendingSection);
      window.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("scrollend", handleScrollEnd);
    };
  }, []);

  const handleNavClick = (sectionId: string) => {
    const target = document.getElementById(sectionId);
    if (!target) {
      return;
    }

    pendingSectionRef.current = sectionId;
    pendingScrollStartedRef.current = false;
    setActiveSection(sectionId);

    const alreadyAtTarget =
      Math.abs(window.scrollY - getSectionScrollTop(target)) < CLICK_TOLERANCE;
    if (alreadyAtTarget) {
      pendingSectionRef.current = null;
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <span className="navbar-logo">🛒</span>
          <span className="navbar-brand-text">CartPilot AI</span>
        </div>

        <div className="navbar-links">
          <a href="#discover" className={`navbar-link ${activeSection === "discover" ? "navbar-link-active" : ""}`} aria-current={activeSection === "discover" ? "page" : undefined} onClick={() => handleNavClick("discover")}>Discover</a>
          <a href="#assistant" className={`navbar-link ${activeSection === "assistant" ? "navbar-link-active" : ""}`} aria-current={activeSection === "assistant" ? "page" : undefined} onClick={() => handleNavClick("assistant")}>Assistant</a>
          <a href="#shopping" className={`navbar-link ${activeSection === "shopping" ? "navbar-link-active" : ""}`} aria-current={activeSection === "shopping" ? "page" : undefined} onClick={() => handleNavClick("shopping")}>My Shopping</a>
        </div>

        <div className="navbar-actions">
          <a href="#shopping" className="navbar-icon-btn" aria-label="Shopping bag" onClick={() => handleNavClick("shopping")}>
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
