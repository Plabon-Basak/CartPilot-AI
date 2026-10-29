import { apiFetch } from "./client";

export interface Product {
  id: string;
  name: string;
  category: string;
  description: string;
  price: number;
  currency: string;
  brand: string;
  availability: string;
}

export interface Intent {
  category: string | null;
  keywords: string[];
  min_ram_gb: number | null;
  max_ram_gb: number | null;
  min_storage_gb: number | null;
  max_storage_gb: number | null;
  storage_type: string | null;
  max_price: number | null;
  min_price: number | null;
  brand: string | null;
  currency: string;
  use_case: string | null;
}

export interface Match {
  product: Product;
  score: number;
  reasons: string[];
}

export interface AssistantIntentResponse {
  source: string;
  query: string;
  intent: Intent;
  matches: Match[];
  count: number;
}

export async function submitShoppingIntent(query: string): Promise<AssistantIntentResponse> {
  return apiFetch<AssistantIntentResponse>("/assistant/intent", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
