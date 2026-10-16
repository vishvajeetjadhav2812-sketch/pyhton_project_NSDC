const $ = (s) => document.querySelector(s);
const money = (n) => "₹" + Number(n).toFixed(2);
const cart = {}; // { itemId: {name, price, qty} }

async function post(url, payload) {
  const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  return res.json();
}
function show(el, text, ok) { el.textContent = text; el.className = "msg " + (ok ? "ok" : "err"); }
function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

/* ---------- Menu quantity selectors ---------- */
document.querySelectorAll(".card").forEach((card) => {
  const id = card.dataset.id, price = +card.dataset.price, name = card.querySelector("h4").textContent;
  const count = card.querySelector(".count");
  const set = (q) => {
    q = Math.max(0, Math.min(50, q));
    count.textContent = q;
    card.classList.toggle("active", q > 0);
    q ? (cart[id] = { name, price, qty: q }) : delete cart[id];
    renderCart();
  };
  card.querySelector(".plus").onclick = () => set((cart[id]?.qty || 0) + 1);
  card.querySelector(".minus").onclick = () => set((cart[id]?.qty || 0) - 1);
});

function renderCart() {
  const items = Object.values(cart);
  const n = items.reduce((a, i) => a + i.qty, 0);
  const sub = items.reduce((a, i) => a + i.qty * i.price, 0);
  $("#cartSummary").textContent = n ? `${n} item(s) · Subtotal ${money(sub)} (tax added at billing)` : "No items added yet.";
}

/* ---------- Order + digital bill ---------- */
$("#orderForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const items = Object.fromEntries(Object.entries(cart).map(([id, i]) => [id, i.qty]));
  const data = await post("/api/order", { name: $("#oName").value, phone: $("#oPhone").value, items });
  if (!data.ok) return show($("#orderMsg"), data.error, false);
  show($("#orderMsg"), "Order placed successfully!", true);
  renderBill(data.bill);
});

function renderBill(b) {
  const rows = b.lines.map((l) => `<tr><td>${esc(l.name)}</td><td>${l.qty} × ${l.price}</td><td>${money(l.amount)}</td></tr>`).join("");
  const el = $("#bill");
  el.hidden = false;
  el.innerHTML = `
    <h3>🌶️ SPICE DELIGHT</h3>
    <div class="center">Order #${b.order_id} · ${b.time}<br>${esc(b.name)} · ${esc(b.phone)}</div>
    <table><thead><tr><th>Item</th><th>Qty × Rate</th><th>Amount</th></tr></thead><tbody>${rows}</tbody></table>
    <div class="tot"><span>Subtotal</span><span>${money(b.subtotal)}</span></div>
    <div class="tot"><span>GST (${b.tax_rate}%)</span><span>${money(b.tax)}</span></div>
    <div class="tot grand"><span>Grand Total</span><span>${money(b.total)}</span></div>
    <p class="center" style="margin-top:12px">Thank you for dining with us!</p>
    <button class="btn" onclick="window.print()">🖨️ Print Bill</button>`;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ---------- Table booking ---------- */
$("#bookForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = await post("/api/book", { name: $("#bName").value, date: $("#bDate").value, time: $("#bTime").value, guests: $("#bGuests").value });
  if (!data.ok) return show($("#bookMsg"), data.error, false);
  const b = data.booking;
  show($("#bookMsg"), `✅ Table booked! ID ${b.booking_id} — ${b.guests} guest(s) on ${b.date} at ${b.time}. See you soon, ${b.name}!`, true);
  e.target.reset();
});

/* ---------- Feedback ---------- */
let rating = 0;
document.querySelectorAll("#stars button").forEach((btn) => {
  btn.onclick = () => {
    rating = +btn.dataset.v;
    document.querySelectorAll("#stars button").forEach((b) => b.classList.toggle("on", +b.dataset.v <= rating));
  };
});
$("#fbForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = await post("/api/feedback", { name: $("#fName").value, rating, message: $("#fMsg").value });
  if (!data.ok) return show($("#fbMsg"), data.error, false);
  show($("#fbMsg"), "💛 Thank you for your feedback!", true);
  e.target.reset();
  rating = 0;
  document.querySelectorAll("#stars button").forEach((b) => b.classList.remove("on"));
});
