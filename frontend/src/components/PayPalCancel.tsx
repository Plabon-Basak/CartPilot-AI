import "./PayPalReturn.css";

function PayPalCancel() {
  const handleBackToShopping = () => {
    window.location.href = "/";
  };

  return (
    <div className="paypal-return">
      <div className="paypal-return-container">
        <h1 className="paypal-return-title">Checkout Cancelled</h1>
        <div className="paypal-return-card">
          <p className="paypal-return-message">Your PayPal Sandbox checkout was cancelled.</p>
          <p className="paypal-return-submessage">No payment was captured.</p>
          <button className="paypal-return-btn" onClick={handleBackToShopping}>
            Return to Shopping
          </button>
        </div>
      </div>
    </div>
  );
}

export default PayPalCancel;
