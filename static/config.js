const API_URL = "https://qulaypinn.wisp.uno";

function apiUrl(path) {
  return path.startsWith("/api/") ? `${API_URL}${path}` : path;
}
