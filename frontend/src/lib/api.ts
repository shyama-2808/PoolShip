const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

// --- Member 1 Logistics Engine API Clients ---

export interface EngineApi {
  getSampleData: () => Promise<any>;
  getCompatibilityRules: () => Promise<any>;
  getDemoPools: () => Promise<any>;
  getDemoStops: (truckId: number) => Promise<any>;
  getDemoReturn: (truckId: number) => Promise<any>;
  getDemoPrice: (shipmentId: number) => Promise<any>;
  getDemoEta: () => Promise<any>;
  getDemoRecurring: () => Promise<any>;
  getDemoHub: (shipmentId: number) => Promise<any>;
  planPool: (truckId: number) => Promise<any>;
}

export const engineApi: EngineApi = {
  getSampleData: () => fetchApi("/engine/sample-data"),
  getCompatibilityRules: () => fetchApi("/engine/compatibility/rules"),
  getDemoPools: () => fetchApi("/engine/demo-pools"),
  getDemoStops: (truckId: number) => fetchApi(`/engine/demo-stops/${truckId}`),
  getDemoReturn: (truckId: number) => fetchApi(`/engine/demo-return/${truckId}`),
  getDemoPrice: (shipmentId: number) => fetchApi(`/engine/demo-price/${shipmentId}`),
  getDemoEta: () => fetchApi("/engine/demo-eta"),
  getDemoRecurring: () => fetchApi("/engine/demo-recurring"),
  getDemoHub: (shipmentId: number) => fetchApi(`/engine/demo-hub/${shipmentId}`),
  planPool: (truckId: number) => fetchApi(`/engine/demo/${truckId}`),
};
