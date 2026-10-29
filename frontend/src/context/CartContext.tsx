import { useEffect, useState, type ReactNode } from "react";
import type { Product } from "../api/products";
import { CartContext, type CartItem, type CartContextType } from "./cartContext";

export type { CartItem, CartContextType };

const STORAGE_KEY = "cartpilot_cart";
const STORAGE_VERSION = 1;

interface StoredCart {
  version: number;
  items: CartItem[];
}

function isValidProduct(product: unknown): product is Product {
  if (!product || typeof product !== "object") {
    return false;
  }
  const p = product as Record<string, unknown>;
  return (
    typeof p.id === "string" &&
    typeof p.name === "string" &&
    typeof p.category === "string" &&
    typeof p.description === "string" &&
    typeof p.price === "number" &&
    !isNaN(p.price) &&
    typeof p.currency === "string" &&
    typeof p.brand === "string" &&
    typeof p.availability === "string"
  );
}

function isValidCartItem(item: unknown): item is CartItem {
  if (!item || typeof item !== "object") {
    return false;
  }
  const i = item as Record<string, unknown>;
  if (!isValidProduct(i.product)) {
    return false;
  }
  if (typeof i.quantity !== "number" || !Number.isInteger(i.quantity)) {
    return false;
  }
  if (i.quantity < 1) {
    return false;
  }
  return true;
}

function loadCartFromStorage(): CartItem[] {
  try {
    if (typeof window === "undefined" || !window.localStorage) {
      return [];
    }
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }
    const parsed = JSON.parse(stored);
    if (!parsed || typeof parsed !== "object") {
      return [];
    }
    const storedCart = parsed as StoredCart;
    if (storedCart.version !== STORAGE_VERSION) {
      return [];
    }
    if (!Array.isArray(storedCart.items)) {
      return [];
    }
    const validItems = storedCart.items.filter(isValidCartItem);
    return validItems;
  } catch {
    return [];
  }
}

function saveCartToStorage(items: CartItem[]): void {
  try {
    if (typeof window === "undefined" || !window.localStorage) {
      return;
    }
    const storedCart: StoredCart = {
      version: STORAGE_VERSION,
      items,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(storedCart));
  } catch {
    // Ignore localStorage errors (quota, private mode, etc.)
  }
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(() => loadCartFromStorage());

  useEffect(() => {
    saveCartToStorage(items);
  }, [items]);

  const addToCart = (product: Product) => {
    if (!isValidProduct(product)) {
      return;
    }
    setItems((prevItems) => {
      const existingIndex = prevItems.findIndex((item) => item.product.id === product.id);
      if (existingIndex >= 0) {
        const updatedItems = [...prevItems];
        updatedItems[existingIndex] = {
          ...updatedItems[existingIndex],
          quantity: updatedItems[existingIndex].quantity + 1,
        };
        return updatedItems;
      }
      return [...prevItems, { product, quantity: 1 }];
    });
  };

  const removeFromCart = (productId: string) => {
    if (typeof productId !== "string") {
      return;
    }
    setItems((prevItems) => prevItems.filter((item) => item.product.id !== productId));
  };

  const updateQuantity = (productId: string, quantity: number) => {
    if (typeof productId !== "string") {
      return;
    }
    if (typeof quantity !== "number" || !Number.isInteger(quantity)) {
      return;
    }
    if (quantity < 1) {
      removeFromCart(productId);
      return;
    }
    setItems((prevItems) => {
      const index = prevItems.findIndex((item) => item.product.id === productId);
      if (index < 0) {
        return prevItems;
      }
      const updatedItems = [...prevItems];
      updatedItems[index] = {
        ...updatedItems[index],
        quantity,
      };
      return updatedItems;
    });
  };

  const clearCart = () => {
    setItems([]);
  };

  const cartCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);

  const value: CartContextType = {
    items,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    cartCount,
    cartTotal,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
