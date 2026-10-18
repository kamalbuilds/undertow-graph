import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

const $ = (id) => document.getElementById(id);
const usd = (n) => {
  n = Number(n) || 0;
  const a = Math.abs(n);
  if (a >= 1e9) return "$" + (n / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return "$" + (n / 1e6).toFixed(1) + "M";
  if (a >= 1e3) return "$" + (n / 1e3).toFixed(0) + "K";
  return "$" + n.toFixed(0);
};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function api(path, body) {
  const opt = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const r = await fetch(path, opt);
  let j = null;
  try { j = await r.json(); } catch { /* non-json body */ }
  if (!r.ok) throw new Error((j && (j.error || j.detail)) || `${path} returned HTTP ${r.status}`);
  return j;
}

const state = { assets: [], sel: null, shock: null, sim: null, nodes: [], links: [], hitBySym: new Map() };

// stats
api("/api/stats").then((s) => {
  $("stats").textContent = `${s.markets.toLocaleString()} markets · ${s.vaults.toLocaleString()} vaults · ${usd(s.tvl_usd)} TVL`;
}).catch((e) => { $("stats").textContent = "Stats unavailable: " + e.message; $("stats").classList.add("err"); });

// assets
function renderAssets() {
  const q = $("search").value.trim().toLowerCase();
  const list = state.assets.filter((a) => a.symbol.toLowerCase().includes(q));
  const ul = $("assets");
  if (!list.length) { ul.innerHTML = `<li class="muted">No asset matches "${esc(q)}".</li>`; return; }
  ul.innerHTML = list.map((a) => `
    <li tabindex="0" role="option" data-sym="${esc(a.symbol)}" class="${a.symbol === state.sel ? "sel" : ""}" aria-selected="${a.symbol === state.sel}">
      <div class="row"><span class="sym">${esc(a.symbol)}</span><span class="num mono">${usd(a.collateral_usd)}</span></div>
      ${a.wrapped_by?.length ? `<div class="chips"><span class="num">wrapped by</span>${a.wrapped_by.slice(0, 4).map((w) => `<span class="chip">${esc(w)}</span>`).join("")}${a.wrapped_by.length > 4 ? `<span class="chip">+${a.wrapped_by.length - 4}</span>` : ""}</div>` : ""}
    </li>`).join("");
}
api("/api/assets").then((a) => {
  state.assets = a;
  if (!a.length) { $("assets").innerHTML = `<li class="muted">The graph holds no shockable assets yet.</li>`; return; }
  renderAssets();
}).catch((e) => { $("assets").innerHTML = `<li class="err">Assets failed: ${esc(e.message)}</li>`; });
$("search").addEventListener("input", renderAssets);
function pick(li) {
  if (!li?.dataset.sym) return;
  state.sel = li.dataset.sym;
  $("run").disabled = false;
  $("run-state").textContent = `${state.sel} selected.`;
  renderAssets();
  loadGraph(state.sel);
}
$("assets").addEventListener("click", (e) => pick(e.target.closest("li")));
$("assets").addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(e.target.closest("li")); } });
$("haircut").addEventListener("input", (e) => { $("hc-out").textContent = e.target.value + "%"; });

// graph
const svg = d3.select("#graph");
const colors = { Asset: "#3ee0c5", Market: "#6aa5c9", Vault: "#e6f1f5", Curator: "#b69cff" };
const lossScale = d3.scaleLinear().range(["#f4a259", "#e4572e"]).clamp(true);

async function loadGraph(sym) {
  $("graph-msg").hidden = false;
  $("graph-msg").className = "muted graph-msg";
  $("graph-msg").textContent = `Loading graph for ${sym}...`;
  svg.selectAll("*").remove();
  state.node = null; state.loading = true;
  if (state.shock && state.shock.asset !== sym) state.shock = null;
  try {
    const g = await api("/api/subgraph?symbol=" + encodeURIComponent(sym));
    if (state.sel !== sym) return;
    state.loading = false;
    if (!g.nodes.length) { $("graph-msg").textContent = `${sym} has no vault exposure in the graph.`; return; }
    $("graph-msg").hidden = true;
    drawGraph(g);
    if (state.shock && state.shock.asset === sym) colorHits(state.shock);
  } catch (e) {
    state.loading = false;
    $("graph-msg").className = "err graph-msg";
    $("graph-msg").textContent = "Graph failed: " + e.message;
  }
}

function drawGraph(g) {
  svg.selectAll("*").remove();
  const box = $("graph").getBoundingClientRect();
  const W = box.width || 800, H = box.height || 560;
  svg.attr("viewBox", `0 0 ${W} ${H}`);
  const nodes = g.nodes.map((n) => ({ ...n }));
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const links = g.edges.filter((e) => byId.has(e.source) && byId.has(e.target)).map((e) => ({ ...e }));
  state.nodes = nodes; state.links = links;
  const wmax = d3.max(links, (l) => l.usd) || 1;
  const w = d3.scaleSqrt().domain([0, wmax]).range([0.8, 7]);
  const rmax = d3.max(nodes, (n) => n.usd) || 1;
  const r = d3.scaleSqrt().domain([0, rmax]).range([5, 18]);
  const root = svg.append("g");
  svg.call(d3.zoom().scaleExtent([0.3, 4]).on("zoom", (ev) => root.attr("transform", ev.transform)));
  const link = root.append("g").selectAll("line").data(links).join("line")
    .attr("stroke", "#2a5a70").attr("stroke-opacity", 0.7).attr("stroke-width", (d) => w(d.usd || 0));
  const node = root.append("g").selectAll("g").data(nodes).join("g").style("cursor", "pointer");
  node.each(function (d) {
    const s = d3.select(this), rr = r(d.usd || 0);
    if (d.label === "Asset") s.append("circle").attr("r", rr);
    else if (d.label === "Market") s.append("rect").attr("x", -rr).attr("y", -rr * 0.7).attr("width", rr * 2).attr("height", rr * 1.4);
    else if (d.label === "Vault") s.append("path").attr("d", `M0,${-rr * 1.2}L${rr * 1.2},0L0,${rr * 1.2}L${-rr * 1.2},0Z`);
    else s.append("rect").attr("x", -6).attr("y", -6).attr("width", 12).attr("height", 12).attr("rx", 3);
    s.select("*").attr("fill", colors[d.label] || "#7f9aa6").attr("stroke", "#07131a").attr("stroke-width", 1.5);
  });
  node.append("title").text((d) => `${d.label}: ${d.name} ${d.usd ? usd(d.usd) : ""}`);
  node.filter((d) => d.label === "Asset" || d.label === "Curator").append("text")
    .text((d) => d.name).attr("x", 10).attr("y", 4).attr("fill", "#e6f1f5").attr("font-size", 11).attr("pointer-events", "none");
  node.on("click", (ev, d) => { if (d.label === "Vault") showPath(d.name); });
  const pulses = root.append("g");
  const sim = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id((d) => d.id).distance(60).strength(0.5))
    .force("charge", d3.forceManyBody().strength(-120))
    .force("center", d3.forceCenter(W / 2, H / 2))
    .force("collide", d3.forceCollide(14))
    .on("tick", () => {
      link.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });
  node.call(d3.drag()
    .on("start", (ev, d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
    .on("end", (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));
  state.sim = sim; state.link = link; state.node = node; state.pulses = pulses;
}

function colorHits(s) {
  if (!state.node) return;
  const max = d3.max(s.hits, (h) => h.loss_usd) || 1;
  lossScale.domain([0, max]);
  state.hitBySym = new Map(s.hits.map((h) => [h.symbol, h]));
  state.node.select("path")
    .attr("fill", (d) => { const h = state.hitBySym.get(d.name); return h ? lossScale(h.loss_usd) : "#2b4a58"; });
  // pulse outward: BFS hop distance from shocked asset(s), delay = hop*400ms
  state.pulses.selectAll("*").remove();
  const adj = new Map();
  state.links.forEach((l) => {
    const a = l.source.id, b = l.target.id;
    (adj.get(a) || adj.set(a, []).get(a)).push([l, b]);
    (adj.get(b) || adj.set(b, []).get(b)).push([l, a]);
  });
  const start = state.nodes.filter((n) => n.label === "Asset" && n.name === s.asset).map((n) => n.id);
  const dist = new Map(start.map((i) => [i, 0]));
  const q = [...start]; const edgeHop = new Map();
  while (q.length) {
    const u = q.shift();
    for (const [l, v] of adj.get(u) || []) {
      if (!dist.has(v)) { dist.set(v, dist.get(u) + 1); edgeHop.set(l, dist.get(u)); q.push(v); }
    }
  }
  edgeHop.forEach((hop, l) => {
    const c = state.pulses.append("circle").attr("r", 4).attr("fill", "#f4a259").attr("opacity", 0)
      .attr("cx", l.source.x).attr("cy", l.source.y);
    const from = dist.get(l.source.id) < dist.get(l.target.id) ? l.source : l.target;
    const to = from === l.source ? l.target : l.source;
    c.attr("cx", from.x).attr("cy", from.y)
      .transition().delay(hop * 400).duration(0).attr("opacity", 1)
      .transition().duration(450).ease(d3.easeLinear).attr("cx", () => to.x).attr("cy", () => to.y)
      .transition().duration(200).attr("opacity", 0).remove();
  });
}

async function showPath(name) {
  const h = state.hitBySym.get(name);
  if (!h || !state.shock) return;
  document.querySelectorAll(".hits li").forEach((li) => li.classList.toggle("act", li.dataset.v === h.vault));
  try {
    const { paths } = await api(`/api/path?vault=${encodeURIComponent(h.vault)}&asset=${encodeURIComponent(state.shock.asset)}`);
    const names = new Set(paths.flat().map((p) => `${p.label}:${p.name}`));
    state.node.select("*").attr("stroke", (d) => names.has(`${d.label}:${d.name}`) ? "#3ee0c5" : "#07131a")
      .attr("stroke-width", (d) => names.has(`${d.label}:${d.name}`) ? 3 : 1.5);
    state.link.attr("stroke", (l) => names.has(`${l.source.label}:${l.source.name}`) && names.has(`${l.target.label}:${l.target.name}`) ? "#3ee0c5" : "#2a5a70");
  } catch (e) { $("run-state").textContent = "Path failed: " + e.message; $("run-state").className = "err"; }
}

// shock
$("run").addEventListener("click", async () => {
  if (!state.sel) return;
  const btn = $("run"), st = $("run-state");
  btn.disabled = true; st.className = "muted"; st.textContent = "Running shock...";
  try {
    const s = await api("/api/shock", { symbol: state.sel, haircut: Number($("haircut").value) / 100 });
    state.shock = s;
    st.textContent = `Scenario ${s.scenario_id} saved.`;
    renderHeadline(s); renderHits(s); loadScenarios();
    if (state.node) colorHits(s); else if (!state.loading) await loadGraph(state.sel);
  } catch (e) { st.className = "err"; st.textContent = "Shock failed: " + e.message; }
  btn.disabled = false;
});

function renderHeadline(s) {
  $("headline").innerHTML = `
    <div class="big d"><div class="lab">Direct collateral alert</div><div class="val">${usd(s.direct.loss_usd)}</div><div class="cnt">${s.direct.vaults} vaults</div></div>
    <div class="big g"><div class="lab">Through the graph</div><div class="val">${usd(s.graph.loss_usd)}</div><div class="cnt">${s.graph.vaults} vaults</div></div>
    <p class="sub muted">${esc(s.asset)} at a ${Math.round(s.haircut * 100)}% haircut. The direct view only sees markets whose collateral is ${esc(s.asset)}. The graph follows every wrapper and vault-of-vaults.</p>`;
  $("cypher-wrap").hidden = !(s.cypher && s.cypher.length);
  $("cypher").textContent = (s.cypher || []).join("\n\n");
}

function renderHits(s) {
  const ol = $("hits");
  if (!s.hits.length) { ol.innerHTML = `<li class="muted">${esc(s.asset)} reaches no vaults at this haircut.</li>`; return; }
  ol.innerHTML = s.hits.map((h) => `
    <li data-v="${esc(h.vault)}" data-s="${esc(h.symbol)}" tabindex="0">
      <div class="r1"><strong>${esc(h.symbol)}</strong><span class="loss">${usd(h.loss_usd)}</span></div>
      <div class="meta">${esc(h.curator || "no curator")} · ${h.hops} hop${h.hops === 1 ? "" : "s"} · TVL ${usd(h.tvl_usd)}</div>
      <div class="path">${(h.path || []).map(esc).join(" → ")}</div>
    </li>`).join("");
}
$("hits").addEventListener("click", (e) => { const li = e.target.closest("li[data-s]"); if (li) showPath(li.dataset.s); });

// scenarios
async function loadScenarios() {
  try {
    const sc = await api("/api/scenarios");
    $("scenarios").innerHTML = sc.length ? sc.map((x) => `
      <li><strong>${esc(x.asset)}</strong> at ${Math.round(x.haircut * 100)}% · <span class="mono">${usd(x.total_loss_usd)}</span>
      <div class="muted">${x.direct_vaults} direct vs ${x.graph_vaults} through graph${x.top_vaults?.length ? " · " + x.top_vaults.map(esc).join(", ") : ""}</div></li>`).join("")
      : `<li class="muted">No scenarios saved yet. Each shock you run is stored here.</li>`;
  } catch (e) { $("scenarios").innerHTML = `<li class="err">Scenarios failed: ${esc(e.message)}</li>`; }
}
loadScenarios();

// agent
const sid = localStorage.getItem("undertow_sid") || (crypto.randomUUID?.() || String(Date.now()));
localStorage.setItem("undertow_sid", sid);
$("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("chat-in"), msg = input.value.trim();
  if (!msg) return;
  const chat = $("chat");
  if (chat.querySelector("p.muted")) chat.innerHTML = "";
  chat.insertAdjacentHTML("beforeend", `<div class="msg u">${esc(msg)}</div>`);
  const out = document.createElement("div"); out.className = "msg"; out.textContent = "Thinking...";
  chat.appendChild(out); chat.scrollTop = chat.scrollHeight;
  input.value = ""; $("chat-send").disabled = true;
  try {
    const r = await api("/api/agent", { message: msg, session_id: sid });
    out.innerHTML = esc(r.reply) +
      (r.tool_calls?.length ? `<small>Tools: ${r.tool_calls.map((t) => esc(t.name)).join(", ")}</small>` : "") +
      (r.cypher?.length ? `<details><summary>Cypher the agent ran</summary><pre class="mono">${esc(r.cypher.join("\n\n"))}</pre></details>` : "");
  } catch (err) { out.className = "msg err"; out.textContent = "Agent failed: " + err.message; }
  $("chat-send").disabled = false; chat.scrollTop = chat.scrollHeight;
});
