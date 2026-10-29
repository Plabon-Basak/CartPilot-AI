import { useEffect, useState } from "react";
import { verifyPayPalApproval, capturePayPalOrder } from "../api/paypal";
import { useCart } from "../context/useCart";
import "./PayPalReturn.css";

function PayPalReturn() {
  const { clearCart } = useCart();
  const [status, setStatus] = useState<"loading" | "approved" | "not-approved" | "error">("loading");
  const [orderId, setOrderId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [captureLoading, setCaptureLoading] = useState<boolean>(false);
  const [captureError, setCaptureError] = useState<string>("");
  const [captureSuccess, setCaptureSuccess] = useState<boolean>(false);
  const [captureStatus, setCaptureStatus] = useState<string>("");
  const [cartCleared, setCartCleared] = useState<boolean>(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    setOrderId(token);

    if (!token) {
      setStatus("error");
      setErrorMessage("No order token found in the return URL.");
      return;
    }

    const verify = async () => {
      try {
        const response = await verifyPayPalApproval(token);
        if (response.approved) {
          setStatus("approved");
        } else {
          setStatus("not-approved");
        }
      } catch (error) {
        setStatus("error");
        setErrorMessage(error instanceof Error ? error.message : "Failed to verify PayPal approval.");
      }
    };

    verify();
  }, []);

  const handleBackToShopping = () => {
    window.location.href = "/";
  };

  const handleConfirmPayment = async () => {
    if (!orderId || captureLoading || captureSuccess) {
      return;
    }

    setCaptureLoading(true);
    setCaptureError("");

    try {
      const response = await capturePayPalOrder(orderId);
      if (response.status === "COMPLETED") {
        setCaptureSuccess(true);
        setCaptureStatus(response.status);
        if (!cartCleared) {
          clearCart();
          setCartCleared(true);
        }
      } else {
        setCaptureSuccess(true);
        setCaptureStatus(response.status);
      }
    } catch (error) {
      setCaptureError(error instanceof Error ? error.message : "Failed to capture PayPal payment.");
    } finally {
      setCaptureLoading(false);
    }
  };

  return (
    <div className="paypal-return">
      <div className="paypal-return-container">
        <h1 className="paypal-return-title">PayPal Sandbox Return</h1>

        {status === "loading" && <p className="paypal-return-message">Verifying your PayPal approval...</p>}

        {status === "error" && (
          <div className="paypal-return-card">
            <p className="paypal-return-message paypal-return-message-error">{errorMessage}</p>
            <button className="paypal-return-btn" onClick={handleBackToShopping}>
              Return to Shopping
            </button>
          </div>
        )}

        {status === "not-approved" && (
          <div className="paypal-return-card">
            <p className="paypal-return-message">Order {orderId} is not approved yet.</p>
            <p className="paypal-return-submessage">Payment has not been confirmed. Please complete approval in PayPal Sandbox or try again.</p>
            <button className="paypal-return-btn" onClick={handleBackToShopping}>
              Return to Shopping
            </button>
          </div>
        )}

        {status === "approved" && (
          <div className="paypal-return-card">
            <p className="paypal-return-message paypal-return-message-success">Order {orderId} is approved.</p>
            <p className="paypal-return-submessage">Payment approval has been verified.</p>

            {captureSuccess ? (
              <div>
                <p className="paypal-return-message paypal-return-message-success">Payment captured successfully.</p>
                <p className="paypal-return-submessage">Capture status: {captureStatus}</p>
              </div>
            ) : (
              <>
                <button
                  className="paypal-return-btn"
                  onClick={handleConfirmPayment}
                  disabled={captureLoading}
                >
                  {captureLoading ? "Processing..." : "Confirm Payment"}
                </button>
                {captureError && (
                  <p className="paypal-return-message paypal-return-message-error">{captureError}</p>
                )}
              </>
            )}

            <button className="paypal-return-btn paypal-return-btn-secondary" onClick={handleBackToShopping}>
              Return to Shopping
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default PayPalReturn;
