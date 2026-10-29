import { useState } from "react";
import { useCart } from "../context/useCart";
import { createPayPalOrder } from "../api/paypal";
import "./ShoppingCart.css";

function ShoppingCart() {
  const { items, updateQuantity, removeFromCart, clearCart, cartTotal } = useCart();
  const [checkoutLoading, setCheckoutLoading] = useState<boolean>(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(price);
  };

  const handleClearCart = () => {
    if (items.length === 0) {
      return;
    }
    const confirmed = window.confirm("Clear all items from your cart?");
    if (confirmed) {
      clearCart();
    }
  };

  const handleCheckout = async () => {
    if (items.length === 0 || cartTotal <= 0 || checkoutLoading) {
      return;
    }

    setCheckoutLoading(true);
    setCheckoutError(null);

    try {
      const amount = cartTotal.toFixed(2);
      const response = await createPayPalOrder(amount);
      if (response.approval_url) {
        window.location.assign(response.approval_url);
      } else {
        setCheckoutError("Unable to start PayPal checkout. Please try again.");
      }
    } catch (error) {
      setCheckoutError(error instanceof Error ? error.message : "Failed to create PayPal order.");
    } finally {
      setCheckoutLoading(false);
    }
  };

  return (
    <section id="shopping" className="shopping-cart">
      <div className="shopping-cart-container">
        <div className="shopping-cart-header">
          <h2 className="shopping-cart-title">My Shopping</h2>
          {items.length > 0 && (
            <button className="shopping-cart-clear-btn" type="button" onClick={handleClearCart}>
              Clear Cart
            </button>
          )}
        </div>

        {items.length === 0 ? (
          <div className="shopping-cart-empty">
            <p className="shopping-cart-empty-text">Your cart is empty.</p>
          </div>
        ) : (
          <>
            <div className="shopping-cart-items">
              {items.map((item) => (
                <article key={item.product.id} className="shopping-cart-item">
                  <div className="shopping-cart-item-main">
                    <div className="shopping-cart-item-info">
                      <h3 className="shopping-cart-item-name">{item.product.name}</h3>
                      <p className="shopping-cart-item-meta">
                        <span className="shopping-cart-item-label">Brand:</span> {item.product.brand}
                      </p>
                      <p className="shopping-cart-item-meta">
                        <span className="shopping-cart-item-label">Category:</span> {item.product.category}
                      </p>
                      <p className="shopping-cart-item-meta">
                        <span className="shopping-cart-item-label">Unit price:</span> {formatPrice(item.product.price)}
                      </p>
                    </div>
                    <div className="shopping-cart-item-actions">
                      <div className="shopping-cart-quantity">
                        <button
                          className="shopping-cart-qty-btn"
                          type="button"
                          onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                          aria-label="Decrease quantity"
                        >
                          -
                        </button>
                        <span className="shopping-cart-qty-value">{item.quantity}</span>
                        <button
                          className="shopping-cart-qty-btn"
                          type="button"
                          onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                          aria-label="Increase quantity"
                        >
                          +
                        </button>
                      </div>
                      <button
                        className="shopping-cart-remove-btn"
                        type="button"
                        onClick={() => removeFromCart(item.product.id)}
                      >
                        Remove
                      </button>
                      <p className="shopping-cart-item-total">
                        <span className="shopping-cart-item-label">Line total:</span> {formatPrice(item.product.price * item.quantity)}
                      </p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
            <div className="shopping-cart-summary">
              <div className="shopping-cart-summary-row">
                <span className="shopping-cart-summary-label">Subtotal</span>
                <span className="shopping-cart-summary-value">{formatPrice(cartTotal)}</span>
              </div>
              <button
                className="shopping-cart-checkout-btn"
                type="button"
                onClick={handleCheckout}
                disabled={items.length === 0 || cartTotal <= 0 || checkoutLoading}
              >
                {checkoutLoading ? "Creating PayPal order..." : "Checkout with PayPal"}
              </button>
              {checkoutError && <p className="shopping-cart-checkout-error">{checkoutError}</p>}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default ShoppingCart;
