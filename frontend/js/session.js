// The signed-in user and their token, persisted across reloads.

const TOKEN_KEY = "ghasel.token";
const listeners = new Set();

function read(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key, value) {
  try {
    value === null ? localStorage.removeItem(key) : localStorage.setItem(key, value);
  } catch {
    /* storage unavailable (private mode); the session lasts until reload */
  }
}

export const session = {
  token: read(TOKEN_KEY),
  user: null,

  start(token) {
    this.token = token;
    write(TOKEN_KEY, token);
  },

  setUser(user) {
    this.user = user;
  },

  end() {
    this.token = null;
    this.user = null;
    write(TOKEN_KEY, null);
    listeners.forEach((listener) => listener());
  },

  onEnd(listener) {
    listeners.add(listener);
  },
};
