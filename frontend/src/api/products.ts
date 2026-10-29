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

export interface ProductsListResponse {
  source: string;
  count: number;
  products: Product[];
}

export interface ProductsSearchResponse {
  source: string;
  query: string;
  count: number;
  products: Product[];
}

export interface ProductDetailResponse {
  source: string;
  product: Product;
}

export async function getProducts(category?: string): Promise<ProductsListResponse> {
  const params = new URLSearchParams();
  if (category !== undefined && category !== null && category.trim() !== "") {
    params.set("category", category.trim());
  }

  const queryString = params.toString();
  const path = queryString ? `/products?${queryString}` : "/products";

  return apiFetch<ProductsListResponse>(path, {
    method: "GET",
  });
}

export async function searchProducts(
  query: string,
  category?: string,
  maxResults?: number
): Promise<ProductsSearchResponse> {
  const params = new URLSearchParams();
  params.set("q", query);

  if (category !== undefined && category !== null && category.trim() !== "") {
    params.set("category", category.trim());
  }

  if (maxResults !== undefined && maxResults !== null) {
    params.set("max_results", String(maxResults));
  }

  const queryString = params.toString();
  const path = `/products/search?${queryString}`;

  return apiFetch<ProductsSearchResponse>(path, {
    method: "GET",
  });
}

export async function getProductById(productId: string): Promise<ProductDetailResponse> {
  return apiFetch<ProductDetailResponse>(`/products/${encodeURIComponent(productId)}`, {
    method: "GET",
  });
}
