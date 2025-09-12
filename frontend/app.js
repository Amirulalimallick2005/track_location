// Replace this with your public backend URL
const BACKEND_URL = "https://track-location-4.onrender.com"; 
const CHECK_ENDPOINT = `${BACKEND_URL}/api/check_safety`;
const GET_USER_ENDPOINT = `${BACKEND_URL}/api/get_user_location/`;

// DOM Elements
const enableBtn = document.getElementById("enableBtn");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const coordsEl = document.getElementById("coords");
const safetyIndicator = document.getElementById("safetyIndicator");
const scoreEl = document.getElementById("score");
const trackFriendBtn = document.getElementById("trackFriendBtn");
const friendUsernameInput = document.getElementById("friendUsername");

// Initialize Map
let map = L.map('map').setView([26.5, 91.5], 10);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

// Variables
let userMarker = null;
let pathPolyline = L.polyline([], { color: 'blue' }).addTo(map);
let watchId = null;

// Get current logged-in username from localStorage
const username = localStorage.getItem("username");

// Function to update status on dashboard
function setStatus(status, score){
  safetyIndicator.textContent = `Status: ${status}`;
  safetyIndicator.className = status === "safe" ? "safe" : (status === "caution" ? "caution" : "danger");
  scoreEl.textContent = `Score: ${score}`;
}

// Activate Location button
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

// Start Tracking button
startBtn.addEventListener("click", () => {
  if (watchId) return;

  watchId = navigator.geolocation.watchPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    coordsEl.textContent = `Lat: ${latitude.toFixed(6)}, Lon: ${longitude.toFixed(6)}`;

    if(!userMarker) userMarker = L.marker([latitude, longitude]).addTo(map);
    else userMarker.setLatLng([latitude, longitude]);
    pathPolyline.addLatLng([latitude, longitude]);
    map.panTo([latitude, longitude], { animate: false });

    // Send location to backend
    try{
      const res = await fetch(CHECK_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, latitude, longitude })
      });
      if(res.ok){
        const data = await res.json();
        setStatus(data.status, data.safety_score);
      }
    } catch(e){ console.error(e); }

  }, (err) => console.error(err), { enableHighAccuracy:true, maximumAge:1000, timeout:5000 });

  startBtn.disabled = true;
  stopBtn.disabled = false;
});

// Stop Tracking button
stopBtn.addEventListener("click", () => {
  if(watchId){
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
});

// Track Friend button
trackFriendBtn.addEventListener("click", async () => {
  const friendUsername = friendUsernameInput.value.trim();
  if(!friendUsername) return alert("Enter friend username");

  try{
    const res = await fetch(`${GET_USER_ENDPOINT}${friendUsername}`);
    if(res.ok){
      const loc = await res.json();
      L.marker([loc.lat, loc.lon], {color:'red'}).addTo(map).bindPopup(friendUsername);
      map.panTo([loc.lat, loc.lon]);
    } else alert("Friend not found or not logged in.");
  } catch(e){ console.error(e); }
});
