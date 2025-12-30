async function runMVP(scenario) {
  const briefEl = document.getElementById("brief");
  const summaryEl = document.getElementById("summary");
  const jsonEl = document.getElementById("json");
  const apiBaseEl = document.getElementById("apiBase");

  const brief = briefEl.value.trim();
  if (!brief) {
    alert("Paste a brief first.");
    return;
  }

  const apiBase = (apiBaseEl && apiBaseEl.value.trim())
    ? apiBaseEl.value.trim().replace(/\/+$/, "")
    : "";
  const base = window.location.protocol === "file:" ? apiBase : "";

  summaryEl.textContent = "Running...";
  jsonEl.textContent = "";

  try {
    const res = await fetch(`${base}/api/mvp/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, brief })
    });

    const data = await res.json();
    if (!res.ok) {
      summaryEl.textContent = "Error: " + (data?.detail || JSON.stringify(data));
      return;
    }

    summaryEl.textContent = data.summary || "";
    jsonEl.textContent = JSON.stringify(data.data || {}, null, 2);
  } catch (e) {
    summaryEl.textContent = "Request failed: " + e;
  }
}
