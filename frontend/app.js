
const BACKEND_URL = "https://track-location-5.onrender.com";
const CHECK_ENDPOINT = `${BACKEND_URL}/api/check_safety`;

const enableBtn = document.getElementById("enableBtn");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const coordsEl = document.getElementById("coords");
const safetyIndicator = document.getElementById("safetyIndicator");
const scoreEl = document.getElementById("score");

let map = L.map('map').setView([26.5, 91.5], 10);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

let userMarker = null;
let pathPolyline = L.polyline([], { color: 'blue' }).addTo(map);
let watchId = null;

function setStatus(status, score) {
  safetyIndicator.textContent = `Status: ${status}`;
  safetyIndicator.className = status === "safe" ? "safe" : (status === "caution" ? "caution" : "danger");
  scoreEl.textContent = `Score: ${score}`;
}

enableBtn.addEventListener("click", () => {
  if (!navigator.geolocation) return alert("Geolocation not supported.");

  navigator.geolocation.getCurrentPosition((pos) => {
    const { latitude, longitude } = pos.coords;
    coordsEl.textContent = `Lat: ${latitude.toFixed(6)}, Lon: ${longitude.toFixed(6)}`;
    map.setView([latitude, longitude], 15);
    if (!userMarker) userMarker = L.marker([latitude, longitude]).addTo(map);
    startBtn.disabled = false;
    enableBtn.disabled = true;
  }, (err) => alert("Could not get location permission."), { enableHighAccuracy: true, timeout: 5000 });
});

startBtn.addEventListener("click", () => {
  if (watchId) return;
  watchId = navigator.geolocation.watchPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    coordsEl.textContent = `Lat: ${latitude.toFixed(6)}, Lon: ${longitude.toFixed(6)}`;

    if (!userMarker) userMarker = L.marker([latitude, longitude]).addTo(map);
    else userMarker.setLatLng([latitude, longitude]);
    pathPolyline.addLatLng([latitude, longitude]);
    map.panTo([latitude, longitude], { animate: false });

    try {
      const res = await fetch(CHECK_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude, longitude })
      });
      if(res.ok){
        const data = await res.json();
        setStatus(data.status, data.safety_score);
      } else console.error("Server error", res.status);
    } catch (e) {
      console.error("Network error", e);
    }
  }, (err) => console.error("watchPosition error", err), { enableHighAccuracy: true, maximumAge: 1000, timeout: 5000 });

  startBtn.disabled = true;
  stopBtn.disabled = false;
});

stopBtn.addEventListener("click", () => {
  if (watchId) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
});
