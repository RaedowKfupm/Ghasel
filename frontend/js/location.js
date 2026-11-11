// Where the user is searching from: browser geolocation, a city preset, or typed coordinates.

const STORAGE_KEY = "ghasel.location";

// City-centre reference points, offered as shortcuts when geolocation is unavailable.
export const CITY_PRESETS = [
  { label: "Dhahran", latitude: 26.2886, longitude: 50.114 },
  { label: "Al Khobar", latitude: 26.2172, longitude: 50.1971 },
  { label: "Dammam", latitude: 26.4207, longitude: 50.0888 },
  { label: "Riyadh", latitude: 24.7136, longitude: 46.6753 },
  { label: "Jeddah", latitude: 21.4858, longitude: 39.1925 },
];

export function isValidCoordinate(latitude, longitude) {
  return Number.isFinite(latitude) && Number.isFinite(longitude) && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180;
}

export function savedLocation() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return value && isValidCoordinate(value.latitude, value.longitude) ? value : null;
  } catch {
    return null;
  }
}

export function saveLocation(location) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(location));
  } catch {
    /* non-essential convenience */
  }
}

export function currentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Your browser does not support location access. Choose a city or enter coordinates."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ label: "Your current location", latitude: coords.latitude, longitude: coords.longitude }),
      (error) =>
        reject(
          new Error(
            error.code === error.PERMISSION_DENIED
              ? "Location permission was denied. Choose a city or enter coordinates instead."
              : "Couldn't determine your location. Choose a city or enter coordinates instead.",
          ),
        ),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  });
}
