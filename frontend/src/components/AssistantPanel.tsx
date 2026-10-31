import { useState } from "react";
import { submitShoppingIntent } from "../api/assistant";
import type { AssistantIntentResponse } from "../api/assistant";
import { useCart } from "../context/useCart";
import "./AssistantPanel.css";

const ArrowIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12"></line>
    <polyline points="12 5 19 12 12 19"></polyline>
  </svg>
);

function AssistantPanel() {
  const suggestions = [
    "Laptop for university",
    "Best earbuds under $100",
    "Wireless charger for my phone",
  ];

  const { addToCart } = useCart();
  const [query, setQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AssistantIntentResponse | null>(null);
  const [addedProductId, setAddedProductId] = useState<string | null>(null);

  const formatPrice = (price: number, currency: string) => {
    try {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: currency || "USD",
      }).format(price);
    } catch {
      return `${currency || "USD"} ${price.toFixed(2)}`;
    }
  };

  const formatScore = (score: number) => {
    if (typeof score !== "number" || isNaN(score)) {
      return "0%";
    }
    return `${Math.round(score)}%`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await submitShoppingIntent(trimmed);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChipClick = (suggestion: string) => {
    setQuery(suggestion);
  };

  return (
    <section id="assistant" className="assistant-panel">
      <div className="assistant-container">
        <div className="assistant-card">
          <h2 className="assistant-title">What are you looking for?</h2>
          <p className="assistant-subtitle">
            Tell me what you need and I'll help find the perfect products
          </p>

          <form className="assistant-form" onSubmit={handleSubmit}>
            <div className="assistant-input-group">
              <input
                type="text"
                className="assistant-input"
                placeholder="e.g., I need a laptop for gaming under $1000"
                aria-label="Shopping request"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="assistant-submit-btn"
                aria-label="Submit request"
                disabled={loading}
              >
                {loading ? "Finding products..." : <ArrowIcon />}
              </button>
            </div>
          </form>

          <div className="assistant-suggestions">
            <span className="assistant-suggestions-label">Suggested prompts:</span>
            <div className="assistant-suggestions-chips">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  className="assistant-chip"
                  type="button"
                  onClick={() => handleChipClick(suggestion)}
                  disabled={loading}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>

        {loading && <p className="assistant-status">Finding products...</p>}
        {error && <p className="assistant-status assistant-status-error">Error: {error}</p>}
        {!loading && !error && result && result.count === 0 && (
          <p className="assistant-status">No matching products found.</p>
        )}
        {!loading && !error && result && result.count > 0 && (
          <div className="assistant-results">
            <h3 className="assistant-results-title">Recommendations</h3>
            <div className="assistant-results-grid">
              {result.matches.map((match, index) => (
                <article key={`${match.product.id}-${index}`} className="assistant-result-card">
                  <div className="assistant-result-header">
                    <h4 className="assistant-result-name">{match.product.name}</h4>
                    <span className="assistant-result-price">
                      {formatPrice(match.product.price, match.product.currency)}
                    </span>
                  </div>
                  <div className="assistant-result-body">
                    <p className="assistant-result-meta">
                      <span className="assistant-result-label">Brand:</span> {match.product.brand}
                    </p>
                    <p className="assistant-result-meta">
                      <span className="assistant-result-label">Category:</span> {match.product.category}
                    </p>
                    <p className="assistant-result-meta">
                      <span className="assistant-result-label">Availability:</span> {match.product.availability === "in_stock" ? "In stock" : match.product.availability}
                    </p>
                    <p className="assistant-result-meta">
                      <span className="assistant-result-label">Match score:</span> {formatScore(match.score)}
                    </p>
                    {match.reasons && match.reasons.length > 0 && (
                      <div className="assistant-result-reasons">
                        <span className="assistant-result-label">Match reasons:</span>
                        <ul className="assistant-result-reasons-list">
                          {match.reasons.map((reason, reasonIndex) => (
                            <li key={reasonIndex}>{reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <button
                      className="assistant-result-add-btn"
                      type="button"
                      onClick={() => {
                        addToCart(match.product);
                        setAddedProductId(match.product.id);
                        setTimeout(() => setAddedProductId(null), 1200);
                      }}
                      disabled={addedProductId === match.product.id}
                    >
                      {addedProductId === match.product.id ? "Added to Cart" : "Add to Cart"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default AssistantPanel;
