import { useEffect, useState } from "react";
import { getProducts } from "../api/products";
import type { Product } from "../api/products";
import { useCart } from "../context/useCart";
import "./ProductDiscovery.css";

function ProductDiscovery() {
  const categories = ["All", "Electronics", "Computers and accessories", "Mobile phones", "Clothing", "Home and lifestyle"];

  const { addToCart } = useCart();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [addedProductId, setAddedProductId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError(null);
        const response =
          selectedCategory === "All"
            ? await getProducts()
            : await getProducts(selectedCategory);

        if (controller.signal.aborted) {
          return;
        }

        setProducts(response.products);
      } catch (err) {
        if (controller.signal.aborted || (err instanceof Error && err.name === "AbortError")) {
          return;
        }
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchProducts();

    return () => {
      controller.abort();
    };
  }, [selectedCategory]);

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

  return (
    <section id="discover" className="product-discovery">
      <div className="product-discovery-container">
        <div className="product-discovery-header">
          <h2 className="product-discovery-title">Explore products</h2>
        </div>

        <div className="product-discovery-filters">
          <div className="product-discovery-chips">
            {categories.map((category) => (
              <button
                key={category}
                className={`product-discovery-chip ${selectedCategory === category ? "product-discovery-chip-active" : ""}`}
                type="button"
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {loading && <p className="product-discovery-status">Loading products...</p>}
        {error && <p className="product-discovery-status product-discovery-status-error">Error: {error}</p>}
        {!loading && !error && products.length === 0 && (
          <p className="product-discovery-status">No products found.</p>
        )}
        {!loading && !error && products.length > 0 && (
          <div className="product-discovery-grid">
            {products.map((product) => (
              <article key={product.id} className="product-card">
                <div className="product-card-header">
                  <h3 className="product-card-name">{product.name}</h3>
                  <span className="product-card-price">{formatPrice(product.price, product.currency)}</span>
                </div>
                <div className="product-card-body">
                  <p className="product-card-meta">
                    <span className="product-card-label">Category:</span> {product.category}
                  </p>
                  <p className="product-card-meta">
                    <span className="product-card-label">Brand:</span> {product.brand}
                  </p>
                  <p className={`product-card-availability product-card-availability-${product.availability.replace("_", "-")}`}>
                    {product.availability === "in_stock" ? "In stock" : product.availability}
                  </p>
                  <button
                    className="product-card-add-btn"
                    type="button"
                    onClick={() => {
                      addToCart(product);
                      setAddedProductId(product.id);
                      setTimeout(() => setAddedProductId(null), 1200);
                    }}
                    disabled={addedProductId === product.id}
                  >
                    {addedProductId === product.id ? "Added to Cart" : "Add to Cart"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default ProductDiscovery;
