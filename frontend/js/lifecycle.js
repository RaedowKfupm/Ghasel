// Display metadata for order statuses. The rules themselves live in the API:
// the backend validates every transition and tells us each order's next_status.

export const ORDER_STEPS = ["pending", "accepted", "picked_up", "cleaning", "ready", "delivering", "completed"];

export const STATUS = {
  pending: { label: "Requested", tone: "gold", description: "Waiting for a laundry to accept" },
  accepted: { label: "Accepted", tone: "blue", description: "A laundry has accepted the order" },
  picked_up: { label: "Picked up", tone: "blue", description: "Laundry collected from your address" },
  cleaning: { label: "Cleaning", tone: "violet", description: "Being washed and pressed" },
  ready: { label: "Ready", tone: "violet", description: "Clean and packed" },
  delivering: { label: "Out for delivery", tone: "violet", description: "On the way back to you" },
  completed: { label: "Delivered", tone: "green", description: "Order complete" },
  cancelled: { label: "Cancelled", tone: "red", description: "This order was cancelled" },
};

// What a branch manager's primary button says for each next status.
export const ADVANCE_LABEL = {
  picked_up: "Mark picked up",
  cleaning: "Start cleaning",
  ready: "Mark ready",
  delivering: "Out for delivery",
  completed: "Mark delivered",
};

export const ACTIVE_STATUSES = new Set(["pending", "accepted", "picked_up", "cleaning", "ready", "delivering"]);

export const customerCanCancel = (order) => order.status === "pending" || order.status === "accepted";
export const branchCanCancel = (order) => order.status === "accepted";
