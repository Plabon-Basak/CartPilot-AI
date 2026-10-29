import { useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import AssistantPanel from "./components/AssistantPanel";
import ProductDiscovery from "./components/ProductDiscovery";
import ShoppingCart from "./components/ShoppingCart";
import PayPalReturn from "./components/PayPalReturn";
import PayPalCancel from "./components/PayPalCancel";
import "./App.css";

function App() {
  const [view, setView] = useState<"dashboard" | "paypal-return" | "paypal-cancel">("dashboard");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("paypal") === "return") {
      setView("paypal-return");
    } else if (params.get("paypal") === "cancel") {
      setView("paypal-cancel");
    }
  }, []);

  if (view === "paypal-return") {
    return <PayPalReturn />;
  }

  if (view === "paypal-cancel") {
    return <PayPalCancel />;
  }

  return (
    <div className="app">
      <Navbar />
      <main>
        <Hero />
        <AssistantPanel />
        <ProductDiscovery />
        <ShoppingCart />
      </main>
    </div>
  );
}

export default App;
