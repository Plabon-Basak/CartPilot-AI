import { apiFetch } from "./client";

export interface PayPalOrderCreateRequest {
  amount: string;
}

export interface PayPalOrderCreateResponse {
  id: string;
  status: string;
  approval_url: string;
}

export interface PayPalOrderAmount {
  currency_code: string;
  value: string;
}

export interface PayPalOrderStatusResponse {
  id: string;
  status: string;
  intent: string;
  amount: PayPalOrderAmount;
}

export interface PayPalApprovalVerificationResponse {
  id: string;
  status: string;
  approved: boolean;
}

export interface PayPalCaptureResponse {
  id: string;
  status: string;
}

export async function createPayPalOrder(amount: string): Promise<PayPalOrderCreateResponse> {
  return apiFetch<PayPalOrderCreateResponse>("/paypal/orders", {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export async function getPayPalOrder(orderId: string): Promise<PayPalOrderStatusResponse> {
  return apiFetch<PayPalOrderStatusResponse>(`/paypal/orders/${encodeURIComponent(orderId)}`, {
    method: "GET",
  });
}

export async function verifyPayPalApproval(orderId: string): Promise<PayPalApprovalVerificationResponse> {
  return apiFetch<PayPalApprovalVerificationResponse>(
    `/paypal/orders/${encodeURIComponent(orderId)}/approval`,
    {
      method: "GET",
    }
  );
}

export async function capturePayPalOrder(orderId: string): Promise<PayPalCaptureResponse> {
  return apiFetch<PayPalCaptureResponse>(`/paypal/orders/${encodeURIComponent(orderId)}/capture`, {
    method: "POST",
  });
}
