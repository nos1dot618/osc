const state = { data: null, type: "all", query: "" };

const $ = (s) => document.querySelector(s);
const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[c]));

function formatDate(iso) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short", day: "numeric", year: "numeric"
  }).format(new Date(iso));
}
function formatTime(iso) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit", minute: "2-digit"
  }).format(new Date(iso));
}
function dayKey(iso) {
  return new Date(iso).toISOString().slice(0, 10);
}
function kindLabel(type) {
  return ({ pr: "Pull request", review: "Code review", issue: "Issue", commit: "Commit" })[type] || type;
}
function matches(e) {
  const typeOK = state.type === "all" || e.type === state.type;
  const q = state.query.trim().toLowerCase();
  const text = [e.title, e.repo, e.owner, e.message, e.state].join(" ").toLowerCase();
  return typeOK && (!q || text.includes(q));
}

function render() {
  if (!state.data) return;
  const events = state.data.events
    .filter(matches)
    .sort((a, b) => new Date(b.occurredAt) - new Date(a.occurredAt));

  $("#empty").hidden = events.length !== 0;
  const groups = new Map();
  for (const e of events) {
    const key = dayKey(e.occurredAt);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(e);
  }

  $("#timeline").innerHTML = [...groups.entries()].map(([day, items]) => `
    <section class="day">
      <h2 class="day-label">${escapeHtml(formatDate(day))}</h2>
      ${items.map(e => `
        <article class="event">
          <div class="event-top">
            <span class="kind ${escapeHtml(e.type)}">${escapeHtml(kindLabel(e.type))}</span>
            <time class="when">${escapeHtml(formatTime(e.occurredAt))}</time>
          </div>
          <div class="title">
            <a href="${escapeHtml(e.url)}" target="_blank" rel="noreferrer">${escapeHtml(e.title)}</a>
          </div>
          <div class="meta">
            <span class="repo">${escapeHtml(e.repo)}</span>
            ${e.owner ? `<span>@${escapeHtml(e.owner)}</span>` : ""}
            ${e.state ? `<span class="badge">${escapeHtml(e.state)}</span>` : ""}
            ${e.commitCount > 1 ? `<span class="badge">${e.commitCount} commits that day</span>` : ""}
          </div>
        </article>
      `).join("")}
    </section>
  `).join("");
}

function renderStats() {
  const events = state.data.events;
  const repos = new Set(events.map(e => e.repo));
  const owners = new Set(events.map(e => e.owner).filter(Boolean));

  $("#count-total").textContent = events.length.toLocaleString();
  $("#count-repos").textContent = repos.size.toLocaleString();
  $("#count-orgs").textContent = owners.size.toLocaleString();
  $("#updated").textContent = state.data.generatedAt ? formatDate(state.data.generatedAt) : "—";
  $("#footer-updated").textContent = state.data.generatedAt
    ? `Updated ${formatDate(state.data.generatedAt)}`
    : "";

  // This is intentionally factual and minimal: the site is a filtered contribution view.
  const excluded = state.data.policy?.excludedOwner;
  $("#integrity-text").textContent = excluded
    ? `Public contribution history · ${events.length.toLocaleString()} contributions · ${excluded} repositories excluded`
    : `Public contribution history · ${events.length.toLocaleString()} contributions`;
}

async function init() {
  try {
    const res = await fetch("./data.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.data = await res.json();
    renderStats();
    render();
  } catch (err) {
    $("#integrity-text").textContent = "Contribution data is not available yet.";
    $("#timeline").innerHTML = `<p class="empty">Run the collector workflow first.</p>`;
    console.error(err);
  }
}

document.querySelectorAll(".filter").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter").forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    state.type = btn.dataset.type;
    render();
  });
});
$("#search").addEventListener("input", e => {
  state.query = e.target.value;
  render();
});
init();
