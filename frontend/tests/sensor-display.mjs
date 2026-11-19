import assert from "node:assert/strict";
import { chromium } from "playwright";

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  const stamp = Date.now() - 60000; // Windows and Mac clocks need not agree.
  const readings = {temperature: 22.875, current: 0.123456, rpm: 118.375, vibration: 0.00004127};
  const frame = {
    server_time_ms: stamp, asset_id: "MOTOR_01", history: [], alerts: [],
    snapshot: {asset_id: "MOTOR_01", health_state: "UNKNOWN", is_fresh: false,
      metrics: {}, message: "Fixture", source: "PHYSICAL", health_score: null},
    sensors: Object.fromEntries(Object.entries(readings).map(([sensor, value]) =>
      [sensor, {quality: "VALID", source: "PHYSICAL", sequence: 41, last_updated_ms: stamp, is_fresh: true, value}])),
  };
  await page.route("**/api/dashboard", route => route.fulfill({json: frame}));
  let socket;
  await page.routeWebSocket("**/ws", connection => { socket = connection; });
  await page.goto("http://127.0.0.1:5173");
  const values = page.locator(".metric-card .metric-value");
  async function verify(expected) {
    await page.waitForFunction(wanted => {
      const actual = [...document.querySelectorAll(".metric-card .metric-value")].map(e => e.textContent.trim());
      return JSON.stringify(actual) === JSON.stringify(wanted);
    }, expected);
    assert.deepEqual((await values.allTextContents()).map(s => s.trim()), expected);
  }
  await verify(["22.875 °C", "0.123456 A", "118.375 RPM", "0.00004127 g"]);
  frame.sensors.temperature.value = 23.25;
  frame.sensors.current.quality = "CALIBRATION_REQUIRED";
  frame.sensors.rpm.value = 0;
  frame.sensors.vibration.is_fresh = false;
  socket.send(JSON.stringify(frame));
  await verify(["23.25 °C", "— A", "0 RPM", "— g"]);
  console.log("PASS rendered all four readings, WebSocket update, zero and unavailable states");
} finally {
  await browser.close();
}
