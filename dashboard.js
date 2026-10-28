const statusDisplay = document.getElementById("connection-status");
const tempDisplay = document.getElementById("live-temp");
const humDisplay = document.getElementById("live-hum");
const setpointInput = document.getElementById("temp-setpoint");
const intervalInput = document.getElementById("log-interval-input");
const relayStatusText = document.getElementById("relay-status-text");
const logBody = document.getElementById("long-body");
const canvas = document.getElementById("telemetryChart");
const ctx = canvas.getContext("2d");

let currentRelaystate = false;
let tempHistory = [];
let rawLogText = "";
let intervalInputInitialized = false;

function syncEsp32HardwareClock() {
  const localEpochSeconds = Math.floor(Date.now() / 1000);
  fetch("/api/sync-time", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ epoch: localEpochSeconds }),
  }).catch((err) => console.error("Time synchronization offline:", err));
}

function addRecordToLogTable(timeStr, temp, hum) {
  const row = `<tr><td>${timeStr}</td><td>${temp}</td><td>${hum}</td></tr>`;
  logBody.insertAdjacentHTML("afterbegin", row);
}

function drawChart() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (tempHistory.length < 2) return;
  const padding = 25,
    graphWidth = canvas.width - padding * 2,
    graphHeight = canvas.height - padding * 2;
  let maxTemp = Math.max(...tempHistory),
    minTemp = Math.min(...tempHistory);
  if (maxTemp === minTemp) {
    maxTemp += 2;
    minTemp -= 2;
  } else {
    maxTemp += 1;
    minTemp -= 1;
  }
  const tempRange = maxTemp - minTemp;

  ctx.strokeStyle = "dimgray";
  ctx.lineWidth = 1;
  for (let i = 1; i <= 3; i++) {
    let y = padding + (graphHeight / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(canvas.width - padding, y);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.strokeStyle = "yellow";
  ctx.lineWidth = 2;
  for (let i = 0; i < tempHistory.length; i++) {
    const x = padding + (i / (tempHistory.length - 1)) * graphWidth;
    const y =
      padding +
      graphHeight -
      ((tempHistory[i] - minTemp) / tempRange) * graphHeight;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  ctx.fillStyle = "white";
  ctx.font = "10px Arial";
  ctx.fillText(maxTemp.toFixed(1) + "°C", 2, padding);
  ctx.fillText(minTemp.toFixed(1) + "°C", 2, canvas.height - padding + 5);
  ctx.fillText("Samples: " + tempHistory.length, padding, canvas.height - 4);
}

function getLiveSensorData() {
  fetch("/api/sensors")
    .then((response) => {
      if (!response.ok) throw new Error("Network fault");
      return response.json();
    })
    .then((data) => {
      statusDisplay.innerText = "ESP32 . Connected";
      statusDisplay.style.color = "lightgreen";
      tempDisplay.innerText = data.temperature;
      humDisplay.innerText = data.humidity;

      if (!intervalInputInitialized && data.currentInterval) {
        intervalInput.value = data.currentInterval;
        intervalInputInitialized = true;
      }

      const currentTemp = parseFloat(data.temperature) || 0;
      const targetSetpoint = parseFloat(setpointInput.value) || 25;
      if (currentTemp > targetSetpoint) {
        updateAutomationState(true);
      } else {
        updateAutomationState(false);
      }
    })
    .catch((error) => {
      statusDisplay.innerText = "ESP32 . Offline";
      statusDisplay.style.color = "red";
      tempDisplay.innerText = "--";
      humDisplay.innerText = "--";
    });
}

function fetchHistoricalLogs() {
  fetch("/api/history")
    .then((res) => res.text())
    .then((text) => {
      rawLogText = text;
      const rows = text.trim().split("\n");
      logBody.innerHTML = "";
      tempHistory = [];

      rows.forEach((row) => {
        if (!row) return;
        const cols = row.split(",");
        if (cols.length < 3) return;

        addRecordToLogTable(cols[0], cols[1], cols[2]);
        tempHistory.push(parseFloat(cols[1]));
      });
      drawChart();
    });
}

function updateLoggingIntervalTime() {
  const newSec = parseInt(intervalInput.value) || 60;
  fetch("/api/interval", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ interval: newSec }),
  })
    .then((res) => {
      if (!res.ok) alert("Failed to save new timing channel.");
    })
    .catch((err) => console.error(err));
}

function updateAutomationState(shouldBeOn) {
  if (shouldBeOn == currentRelaystate) return;
  currentRelaystate = shouldBeOn;
  if (shouldBeOn) {
    relayStatusText.innerText = "ON";
    relayStatusText.style.color = "lightgreen";
  } else {
    relayStatusText.innerText = "OFF";
    relayStatusText.style.color = "crimson";
  }

  fetch("/api/relay", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ relayState: shouldBeOn }),
  })
    .then((res) => {
      if (!res.ok) console.error("Hardware register sync failure.");
    })
    .catch((err) => console.error("Failed to connect to relay API:", err));
}

function copyLogsToClipboard() {
  if (!rawLogText.trim()) {
    alert("No logs available to copy!");
    return;
  }
  navigator.clipboard
    .writeText(rawLogText)
    .then(() => alert("All logs copied to system clipboard!"))
    .catch(() => alert("Failed to copy logs."));
}

function clearDeviceLogs() {
  if (confirm("Are you sure you want to delete all logs from the ESP32?")) {
    fetch("/api/clear", { method: "POST" }).then(() => {
      alert("Device storage wiped!");
      fetchHistoricalLogs();
    });
  }
}

syncEsp32HardwareClock();
getLiveSensorData();
fetchHistoricalLogs();

setInterval(getLiveSensorData, 4000);
setInterval(fetchHistoricalLogs, 15000);
