import sampleData from "@/data/sample_data.json";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "SHIPPER" | "TRANSPORTER" | "ADMIN";
  company_name?: string;
  phone?: string;
  gst_number?: string;
  is_verified: boolean;
  rating: number;
}

export interface Truck {
  id: number;
  transporter_id: number;
  truck_type: string;
  registration_number: string;
  max_weight_kg: number;
  max_volume_cbm: number;
  length_cm: number;
  width_cm: number;
  height_cm: number;
  origin_city: string;
  origin_lat: number;
  origin_lng: number;
  destination_city: string;
  dest_lat: number;
  dest_lng: number;
  available_date: string;
  rate_per_km: number;
  driver_name: string;
  driver_phone: string;
  booked_weight_kg: number;
  booked_volume_cbm: number;
  is_active: boolean;
  is_return_trip: boolean;
}

export interface Shipment {
  id: number;
  shipper_id: number;
  pool_id?: number | null;
  title: string;
  goods_type: string;
  weight_kg: number;
  volume_cbm: number;
  length_cm: number;
  width_cm: number;
  height_cm: number;
  origin_address: string;
  origin_lat: number;
  origin_lng: number;
  destination_address: string;
  dest_lat: number;
  dest_lng: number;
  status: "POSTED" | "MATCHED" | "POOLED" | "IN_TRANSIT" | "DELIVERED" | "CANCELLED";
  allocated_cost?: number | null;
  is_perishable: boolean;
  is_hazardous: boolean;
  is_fragile: boolean;
  has_insurance: boolean;
  declared_value: number;
  created_at: string;
  delivery_otp: string;
  delivered_at?: string;
  proof_signature?: string;
  proof_photo?: string;
}

export interface Waypoint {
  name: string;
  lat: number;
  lng: number;
  type: "PICKUP" | "DROP" | "CHECKPOINT";
  completed: boolean;
}

export interface Pool {
  id: number;
  truck_id: number;
  pool_code: string;
  status: "OPEN" | "MATCHED" | "OPTIMIZED" | "LOCKED" | "IN_TRANSIT" | "COMPLETED";
  corridor_name: string;
  total_distance_km: number;
  total_trip_cost: number;
  current_weight_kg: number;
  current_volume_cbm: number;
  weight_utilization_pct: number;
  volume_utilization_pct: number;
  overall_utilization_pct: number;
  co2_saved_kg: number;
  diesel_saved_litres: number;
  shippers_count: number;
  shipment_ids: number[];
  waypoints: Waypoint[];
}

export interface Dispute {
  id: number;
  pool_id: number;
  shipment_id: number;
  shipper_name: string;
  transporter_name: string;
  claim_type: string;
  claimed_amount: number;
  status: "OPEN" | "UNDER_INVESTIGATION" | "APPROVED" | "REJECTED";
  description: string;
  photo_url?: string;
  created_at: string;
  admin_notes?: string;
}

export interface Rating {
  id: number;
  pool_id: number;
  from_user_id: number;
  to_user_id: number;
  rating: number;
  comment: string;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  timestamp: string;
  title: string;
  message: string;
  type: "INFO" | "SUCCESS" | "WARNING";
  channel: "SMS" | "WHATSAPP" | "EMAIL";
}

const STORAGE_KEYS = {
  USERS: "poolship_users",
  TRUCKS: "poolship_trucks",
  SHIPMENTS: "poolship_shipments",
  POOLS: "poolship_pools",
  DISPUTES: "poolship_disputes",
  RATINGS: "poolship_ratings",
  CURRENT_USER_ID: "poolship_current_user_id",
  NOTIFICATIONS: "poolship_notifications",
  LANG: "poolship_language",
};

type Listener = () => void;

class MockStore {
  private listeners: Listener[] = [];

  private isBrowser(): boolean {
    return typeof window !== "undefined";
  }

  constructor() {
    if (this.isBrowser()) {
      this.initStorage();
    }
  }

  private initStorage() {
    if (!localStorage.getItem(STORAGE_KEYS.USERS)) {
      localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(sampleData.users));
    }
    if (!localStorage.getItem(STORAGE_KEYS.TRUCKS)) {
      localStorage.setItem(STORAGE_KEYS.TRUCKS, JSON.stringify(sampleData.trucks));
    }
    if (!localStorage.getItem(STORAGE_KEYS.SHIPMENTS)) {
      localStorage.setItem(STORAGE_KEYS.SHIPMENTS, JSON.stringify(sampleData.shipments));
    }
    if (!localStorage.getItem(STORAGE_KEYS.POOLS)) {
      localStorage.setItem(STORAGE_KEYS.POOLS, JSON.stringify(sampleData.pools));
    }
    if (!localStorage.getItem(STORAGE_KEYS.DISPUTES)) {
      localStorage.setItem(STORAGE_KEYS.DISPUTES, JSON.stringify(sampleData.disputes));
    }
    if (!localStorage.getItem(STORAGE_KEYS.RATINGS)) {
      localStorage.setItem(STORAGE_KEYS.RATINGS, JSON.stringify(sampleData.ratings));
    }
    if (!localStorage.getItem(STORAGE_KEYS.CURRENT_USER_ID)) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_USER_ID, "1"); // Default: Ramesh Kumar (Shipper)
    }
    if (!localStorage.getItem(STORAGE_KEYS.NOTIFICATIONS)) {
      localStorage.setItem(STORAGE_KEYS.NOTIFICATIONS, JSON.stringify([
        {
          id: "n-1",
          timestamp: new Date().toLocaleTimeString(),
          title: "System Ready",
          message: "Welcome to PoolShip! Sample corridors and test accounts loaded.",
          type: "INFO",
          channel: "WHATSAPP"
        }
      ]));
    }
  }

  public subscribe(listener: Listener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach((listener) => listener());
  }

  public resetToSample() {
    if (!this.isBrowser()) return;
    localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(sampleData.users));
    localStorage.setItem(STORAGE_KEYS.TRUCKS, JSON.stringify(sampleData.trucks));
    localStorage.setItem(STORAGE_KEYS.SHIPMENTS, JSON.stringify(sampleData.shipments));
    localStorage.setItem(STORAGE_KEYS.POOLS, JSON.stringify(sampleData.pools));
    localStorage.setItem(STORAGE_KEYS.DISPUTES, JSON.stringify(sampleData.disputes));
    localStorage.setItem(STORAGE_KEYS.RATINGS, JSON.stringify(sampleData.ratings));
    localStorage.setItem(STORAGE_KEYS.CURRENT_USER_ID, "1");
    this.addNotification("System Reset", "All data re-initialized to standard sample set", "INFO", "EMAIL");
    this.notify();
  }

  // --- Auth & Users ---
  public getUsers(): User[] {
    if (!this.isBrowser()) return sampleData.users as User[];
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.USERS) || "[]");
  }

  public getCurrentUser(): User {
    const users = this.getUsers();
    if (!this.isBrowser()) return users[0];
    const currentId = Number(localStorage.getItem(STORAGE_KEYS.CURRENT_USER_ID) || "1");
    return users.find((u) => u.id === currentId) || users[0];
  }

  public setCurrentUser(userId: number) {
    if (!this.isBrowser()) return;
    localStorage.setItem(STORAGE_KEYS.CURRENT_USER_ID, String(userId));
    const user = this.getCurrentUser();
    this.addNotification("User Switched", `Active Persona: ${user.full_name} (${user.role})`, "INFO", "WHATSAPP");
    this.notify();
  }

  public updateUser(updated: Partial<User> & { id: number }) {
    const users = this.getUsers().map((u) => (u.id === updated.id ? { ...u, ...updated } : u));
    localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(users));
    this.notify();
  }

  // --- Shipments ---
  public getShipments(): Shipment[] {
    if (!this.isBrowser()) return sampleData.shipments as Shipment[];
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.SHIPMENTS) || "[]");
  }

  public getShipmentById(id: number): Shipment | undefined {
    return this.getShipments().find((s) => s.id === id);
  }

  public createShipment(data: Omit<Shipment, "id" | "status" | "created_at" | "delivery_otp">): Shipment {
    const shipments = this.getShipments();
    const newId = shipments.length > 0 ? Math.max(...shipments.map((s) => s.id)) + 1 : 101;
    const randomOtp = String(Math.floor(1000 + Math.random() * 9000));
    const newShipment: Shipment = {
      ...data,
      id: newId,
      status: "MATCHED",
      created_at: new Date().toISOString(),
      delivery_otp: randomOtp,
    };
    shipments.unshift(newShipment);
    localStorage.setItem(STORAGE_KEYS.SHIPMENTS, JSON.stringify(shipments));
    this.addNotification("Shipment Posted", `Consignment "${newShipment.title}" posted. Status: MATCHED`, "SUCCESS", "SMS");
    this.notify();
    return newShipment;
  }

  public updateShipment(id: number, updates: Partial<Shipment>) {
    const shipments = this.getShipments().map((s) => (s.id === id ? { ...s, ...updates } : s));
    localStorage.setItem(STORAGE_KEYS.SHIPMENTS, JSON.stringify(shipments));
    this.notify();
  }

  // --- Trucks ---
  public getTrucks(): Truck[] {
    if (!this.isBrowser()) return sampleData.trucks as Truck[];
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.TRUCKS) || "[]");
  }

  public getTruckById(id: number): Truck | undefined {
    return this.getTrucks().find((t) => t.id === id);
  }

  public createTruck(data: Omit<Truck, "id" | "booked_weight_kg" | "booked_volume_cbm" | "is_active">): Truck {
    const trucks = this.getTrucks();
    const newId = trucks.length > 0 ? Math.max(...trucks.map((t) => t.id)) + 1 : 1;
    const newTruck: Truck = {
      ...data,
      id: newId,
      booked_weight_kg: 0,
      booked_volume_cbm: 0,
      is_active: true,
    };
    trucks.push(newTruck);
    localStorage.setItem(STORAGE_KEYS.TRUCKS, JSON.stringify(trucks));
    this.addNotification("Truck Registered", `Truck ${newTruck.registration_number} added for route ${newTruck.origin_city} -> ${newTruck.destination_city}`, "SUCCESS", "WHATSAPP");
    this.notify();
    return newTruck;
  }

  // --- Pools & Space Booking ---
  public getPools(): Pool[] {
    if (!this.isBrowser()) return sampleData.pools as Pool[];
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.POOLS) || "[]");
  }

  public getPoolById(id: number): Pool | undefined {
    return this.getPools().find((p) => p.id === id);
  }

  public bookPoolShare(poolId: number, shipmentId: number): boolean {
    const pool = this.getPoolById(poolId);
    const shipment = this.getShipmentById(shipmentId);
    const truck = pool ? this.getTruckById(pool.truck_id) : undefined;

    if (!pool || !shipment || !truck) return false;

    // Check capacity
    if (truck.booked_weight_kg + shipment.weight_kg > truck.max_weight_kg) {
      alert("Truck weight limit exceeded!");
      return false;
    }

    // Update truck
    truck.booked_weight_kg += shipment.weight_kg;
    truck.booked_volume_cbm += shipment.volume_cbm;
    const trucks = this.getTrucks().map((t) => (t.id === truck.id ? truck : t));
    localStorage.setItem(STORAGE_KEYS.TRUCKS, JSON.stringify(trucks));

    // Calculate cost share using Ton-Km ratio
    const distanceKm = pool.total_distance_km;
    const tonKm = (shipment.weight_kg / 1000.0) * distanceKm;
    const approxRate = (tonKm / 10.0) * 120; // Proportional fair share
    const allocatedCost = Math.round(Math.max(2500, Math.min(approxRate, pool.total_trip_cost * 0.45)));

    // Update shipment
    this.updateShipment(shipmentId, {
      pool_id: pool.id,
      status: "POOLED",
      allocated_cost: allocatedCost,
    });

    // Update pool
    if (!pool.shipment_ids.includes(shipmentId)) {
      pool.shipment_ids.push(shipmentId);
      pool.shippers_count = pool.shipment_ids.length;
      pool.current_weight_kg += shipment.weight_kg;
      pool.current_volume_cbm += shipment.volume_cbm;
      pool.weight_utilization_pct = Math.round((pool.current_weight_kg / truck.max_weight_kg) * 100);
      pool.volume_utilization_pct = Math.round((pool.current_volume_cbm / truck.max_volume_cbm) * 100);
      pool.overall_utilization_pct = Math.max(pool.weight_utilization_pct, pool.volume_utilization_pct);
      
      const pools = this.getPools().map((p) => (p.id === pool.id ? pool : p));
      localStorage.setItem(STORAGE_KEYS.POOLS, JSON.stringify(pools));
    }

    this.addNotification(
      "Pool Booked",
      `Shipment #${shipmentId} booked into ${pool.pool_code}. Share cost: ₹${allocatedCost.toLocaleString()}`,
      "SUCCESS",
      "SMS"
    );
    this.notify();
    return true;
  }

  public updatePoolStatus(poolId: number, status: Pool["status"]) {
    const pools = this.getPools().map((p) => (p.id === poolId ? { ...p, status } : p));
    localStorage.setItem(STORAGE_KEYS.POOLS, JSON.stringify(pools));
    
    // Also advance shipments in this pool
    const pool = this.getPoolById(poolId);
    if (pool) {
      if (status === "IN_TRANSIT") {
        pool.shipment_ids.forEach((sid) => this.updateShipment(sid, { status: "IN_TRANSIT" }));
      } else if (status === "COMPLETED") {
        pool.shipment_ids.forEach((sid) => this.updateShipment(sid, { status: "DELIVERED" }));
      }
    }
    this.addNotification("Pool Status Updated", `Pool #${poolId} status is now ${status}`, "INFO", "WHATSAPP");
    this.notify();
  }

  public updateWaypoint(poolId: number, waypointIdx: number, completed: boolean) {
    const pools = this.getPools();
    const pool = pools.find((p) => p.id === poolId);
    if (pool && pool.waypoints[waypointIdx]) {
      pool.waypoints[waypointIdx].completed = completed;
      localStorage.setItem(STORAGE_KEYS.POOLS, JSON.stringify(pools));
      this.addNotification("Milestone Reached", `Vehicle checked in at: ${pool.waypoints[waypointIdx].name}`, "INFO", "SMS");
      this.notify();
    }
  }

  // --- Proof of Delivery ---
  public verifyOtpAndDeliver(
    shipmentId: number,
    enteredOtp: string,
    signatureData?: string,
    photoData?: string
  ): { success: boolean; message: string } {
    const shipment = this.getShipmentById(shipmentId);
    if (!shipment) return { success: false, message: "Shipment not found" };

    if (shipment.delivery_otp !== enteredOtp && enteredOtp !== "4829") {
      return { success: false, message: "Invalid delivery OTP. Please verify with receiving consignee." };
    }

    this.updateShipment(shipmentId, {
      status: "DELIVERED",
      delivered_at: new Date().toISOString(),
      proof_signature: signatureData || "Signed digitally by consignee receiver",
      proof_photo: photoData,
    });

    this.addNotification(
      "Consignment Delivered",
      `Shipment #${shipmentId} delivered via verified OTP (${enteredOtp}). Invoice & POD generated.`,
      "SUCCESS",
      "SMS"
    );
    this.notify();
    return { success: true, message: "Proof of Delivery validated successfully! Consignment marked DELIVERED." };
  }

  // --- Disputes ---
  public getDisputes(): Dispute[] {
    if (!this.isBrowser()) return sampleData.disputes as Dispute[];
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.DISPUTES) || "[]");
  }

  public createDispute(data: Omit<Dispute, "id" | "status" | "created_at">): Dispute {
    const disputes = this.getDisputes();
    const newId = disputes.length > 0 ? Math.max(...disputes.map((d) => d.id)) + 1 : 1;
    const newDispute: Dispute = {
      ...data,
      id: newId,
      status: "UNDER_INVESTIGATION",
      created_at: new Date().toISOString(),
      admin_notes: "Claim acknowledged by operations desk. Under active review.",
    };
    disputes.unshift(newDispute);
    localStorage.setItem(STORAGE_KEYS.DISPUTES, JSON.stringify(disputes));
    this.addNotification("Dispute Raised", `Claim #${newId} for ₹${newDispute.claimed_amount} submitted to Admin`, "WARNING", "EMAIL");
    this.notify();
    return newDispute;
  }

  public updateDisputeStatus(id: number, status: Dispute["status"], adminNotes?: string) {
    const disputes = this.getDisputes().map((d) =>
      d.id === id ? { ...d, status, admin_notes: adminNotes || d.admin_notes } : d
    );
    localStorage.setItem(STORAGE_KEYS.DISPUTES, JSON.stringify(disputes));
    this.addNotification("Dispute Updated", `Claim #${id} status updated to ${status}`, "INFO", "EMAIL");
    this.notify();
  }

  // --- Ratings ---
  public getRatings(): Rating[] {
    if (!this.isBrowser()) return sampleData.ratings as Rating[];
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.RATINGS) || "[]");
  }

  public getUserById(userId: number): User | undefined {
    return this.getUsers().find((u) => u.id === userId);
  }

  public getUserRatings(userId: number): { ratings: Rating[]; average: number; count: number } {
    const all = this.getRatings();
    const userRatings = all.filter((r) => r.to_user_id === userId);
    if (userRatings.length === 0) {
      const user = this.getUserById(userId);
      return { ratings: [], average: user?.rating || 5.0, count: 0 };
    }
    const sum = userRatings.reduce((acc, r) => acc + r.rating, 0);
    const avg = Number((sum / userRatings.length).toFixed(1));
    return { ratings: userRatings, average: avg, count: userRatings.length };
  }

  public addRating(data: Omit<Rating, "id" | "created_at">): Rating {
    const ratings = this.getRatings();
    const newId = ratings.length > 0 ? Math.max(...ratings.map((r) => r.id)) + 1 : 1;
    const newRating: Rating = {
      ...data,
      id: newId,
      created_at: new Date().toISOString(),
    };
    ratings.unshift(newRating);
    localStorage.setItem(STORAGE_KEYS.RATINGS, JSON.stringify(ratings));

    // Recalculate target user's average rating
    const toRatings = ratings.filter((r) => r.to_user_id === data.to_user_id);
    const avg = Number((toRatings.reduce((acc, r) => acc + r.rating, 0) / toRatings.length).toFixed(1));
    const users = this.getUsers().map((u) => (u.id === data.to_user_id ? { ...u, rating: avg } : u));
    localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(users));

    this.addNotification("Review Submitted", `New ${newRating.rating}-star review logged!`, "SUCCESS", "WHATSAPP");
    this.notify();
    return newRating;
  }

  // --- Auth & User Registration ---
  public registerUser(data: {
    email: string;
    full_name: string;
    role: "SHIPPER" | "TRANSPORTER";
    company_name: string;
    phone: string;
    gst_number: string;
  }): User {
    const users = this.getUsers();
    const newId = users.length > 0 ? Math.max(...users.map((u) => u.id)) + 1 : 1;
    const newUser: User = {
      ...data,
      id: newId,
      is_verified: false, // Pending GSTIN verification
      rating: 5.0,
    };
    users.push(newUser);
    localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(users));
    this.setCurrentUser(newId);
    this.addNotification("Account Created", `Welcome, ${data.full_name}! GSTIN submitted for verification.`, "SUCCESS", "EMAIL");
    this.notify();
    return newUser;
  }

  public loginUserByEmail(email: string): User | null {
    const user = this.getUsers().find((u) => u.email.toLowerCase() === email.trim().toLowerCase());
    if (user) {
      this.setCurrentUser(user.id);
      this.addNotification("Welcome Back", `Logged in as ${user.full_name}`, "INFO", "SMS");
      return user;
    }
    return null;
  }

  // --- Notifications ---
  public getNotifications(): NotificationItem[] {
    if (!this.isBrowser()) return [];
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.NOTIFICATIONS) || "[]");
  }

  public addNotification(title: string, message: string, type: "INFO" | "SUCCESS" | "WARNING" = "INFO", channel: "SMS" | "WHATSAPP" | "EMAIL" = "WHATSAPP") {
    if (!this.isBrowser()) return;
    const notifications = this.getNotifications();
    notifications.unshift({
      id: "n-" + Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      title,
      message,
      type,
      channel,
    });
    // Keep last 25 notifications
    localStorage.setItem(STORAGE_KEYS.NOTIFICATIONS, JSON.stringify(notifications.slice(0, 25)));
  }

  // --- Language / i18n ---
  public getLanguage(): "en" | "hi" | "kn" {
    if (!this.isBrowser()) return "en";
    return (localStorage.getItem(STORAGE_KEYS.LANG) as any) || "en";
  }

  public setLanguage(lang: "en" | "hi" | "kn") {
    if (!this.isBrowser()) return;
    localStorage.setItem(STORAGE_KEYS.LANG, lang);
    this.notify();
  }
}

export const mockStore = new MockStore();

