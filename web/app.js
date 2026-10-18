"use strict";
let apiKey = "";
let generation = 0;
const byId = (id) => document.getElementById(id);
const status = (message) => { byId("connection-status").textContent = message; };
function clearData() {
  for (const id of ["memory", "disk", "sessions"]) byId(id).textContent = "Unavailable";
  byId("users").replaceChildren();
  byId("audit-results").textContent = "No checks run.";
}
function disconnect(message = "Disconnected. No server data loaded.") {
  generation += 1;
  apiKey = "";
  byId("api-key").value = "";
  clearData();
  for (const id of ["refresh", "load-users", "audit"]) byId(id).disabled = true;
  status(message);
}
async function request(path) {
  const current = generation;
  const response = await fetch(`/api/v1/${path}`, {headers: {"X-API-Key": apiKey}, cache: "no-store", signal: AbortSignal.timeout(15000)});
  if (current !== generation) throw new Error("Connection changed. Please retry.");
  if (!response.ok) {
    if ([401, 503].includes(response.status)) disconnect("Authentication failed or server API key is not configured.");
    throw new Error(`Server request failed (${response.status}).`);
  }
  const data = await response.json();
  if (current !== generation) throw new Error("Connection changed. Please retry.");
  return data;
}
async function refresh() {
  clearData();
  const data = await request("status");
  byId("memory").textContent = `${data.mem_used_mb} / ${data.mem_total_mb} MB (${data.mem_percent}%)`;
  byId("disk").textContent = `${data.disk_used_gb} / ${data.disk_total_gb} GB (${data.disk_percent}%)`;
  byId("sessions").textContent = data.online_users;
  status(`Connected. Metrics updated at ${new Date().toLocaleTimeString()}.`);
}
byId("connect-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  generation += 1;
  apiKey = byId("api-key").value;
  byId("api-key").value = "";
  status("Connecting…");
  try {
    await refresh();
    for (const id of ["refresh", "load-users", "audit"]) byId(id).disabled = false;
  } catch (error) { disconnect(error.message); }
});
byId("disconnect").addEventListener("click", () => disconnect());
byId("refresh").addEventListener("click", () => refresh().catch((error) => status(error.message)));
byId("load-users").addEventListener("click", async () => {
  byId("users").replaceChildren();
  try {
    const users = await request("users");
    for (const user of users) {
      const item = document.createElement("li");
      item.textContent = `${user.username} — configured connection limit: ${user.limit}`;
      byId("users").append(item);
    }
    if (!users.length) byId("users").textContent = "No managed accounts.";
  } catch (error) { status(error.message); }
});
byId("audit").addEventListener("click", async () => {
  byId("audit-results").textContent = "Checking…";
  try { byId("audit-results").textContent = JSON.stringify(await request("security/audit"), null, 2); }
  catch (error) { byId("audit-results").textContent = error.message; }
});
