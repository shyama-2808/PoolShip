export type UserRole = "SHIPPER" | "TRANSPORTER" | "ADMIN";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  company_name?: string;
  phone?: string;
  gst_number?: string;
  is_verified: boolean;
  rating: number;
}

export type ShipmentStatus =
  | "POSTED"
  | "MATCHED"
  | "POOLED"
  | "IN_TRANSIT"
  | "DELIVERED"
  | "CANCELLED";

export interface Shipment {
  id: number;
  shipper_id: number;
  pool_id?: number;
  title: string;
  goods_type: string;
  weight_kg: number;
  volume_cbm?: number;
  origin_address: string;
  origin_lat: number;
  origin_lng: number;
  destination_address: string;
  dest_lat: number;
  dest_lng: number;
  status: ShipmentStatus;
  allocated_cost?: number;
  is_perishable: boolean;
  is_hazardous: boolean;
  is_fragile: boolean;
  created_at: string;
}

export interface Truck {
  id: number;
  transporter_id: number;
  truck_type: string;
  registration_number: string;
  max_weight_kg: number;
  max_volume_cbm: number;
  origin_city: string;
  origin_lat: number;
  origin_lng: number;
  destination_city: string;
  dest_lat: number;
  dest_lng: number;
  available_date: string;
  rate_per_km: number;
  is_active: boolean;
}

export interface Pool {
  id: number;
  truck_id: number;
  status: string;
  total_distance_km: number;
  total_cost: number;
  current_weight_kg: number;
  current_volume_cbm: number;
  utilization_percentage: number;
  co2_saved_kg: number;
  diesel_saved_litres: number;
  shipments?: Shipment[];
  truck?: Truck;
}

export interface TrackingEvent {
  id: number;
  pool_id: number;
  status: string;
  location_name: string;
  latitude: number;
  longitude: number;
  note?: string;
  proof_photo_url?: string;
  delivery_otp?: string;
  timestamp: string;
}
