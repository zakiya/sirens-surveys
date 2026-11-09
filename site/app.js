// Sirens survey results. Renders site/data/surveys.json (built by
// scripts/build_site.py) into one page per year. All data text is inserted
// with textContent, never innerHTML.

const ROLE_ORDER = ["neg2", "neg1", "neutral", "pos1", "pos2"];
const main = document.getElementById("main");
const tip = document.querySelector(".tip");
let DATA = null;

// ---------- small DOM helpers ----------

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k === "style") {
      for (const [prop, val] of Object.entries(v)) {
        if (prop.startsWith("--")) node.style.setProperty(prop, val);
        else node.style[prop] = val;
      }
    }
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

const pct = (part, whole) => (whole ? Math.round((100 * part) / whole) : 0);
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function luminance(color) {
  const ctx = luminance.ctx || (luminance.ctx = document.createElement("canvas").getContext("2d"));
  ctx.fillStyle = color;
  const hex = ctx.fillStyle; // normalized to #rrggbb
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
const labelInk = (fill) => (luminance(fill) > 0.35 ? cssVar("--on-light-fill") : cssVar("--on-dark-fill"));

function textWidth(text, font) {
  const ctx = textWidth.ctx || (textWidth.ctx = document.createElement("canvas").getContext("2d"));
  ctx.font = font;
  return ctx.measureText(text).width;
}

// ---------- tooltip ----------

function showTip(target, value, label, color, event) {
  tip.replaceChildren(
    el("div", { class: "tip-value", text: value }),
    el("div", { class: "tip-label" }, el("span", { class: "key", style: { background: color } }), el("span", { text: label })),
  );
  tip.hidden = false;
  placeTip(target, event);
}

function placeTip(target, event) {
  const r = target.getBoundingClientRect();
  const x = event && event.clientX ? event.clientX : r.left + r.width / 2;
  const y = event && event.clientY ? event.clientY : r.top;
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = `${Math.min(Math.max(8, x - w / 2), window.innerWidth - w - 8)}px`;
  tip.style.top = `${y - h - 12 < 8 ? y + 20 : y - h - 12}px`;
}

function hideTip() { tip.hidden = true; }

function withTip(node, value, label, color) {
  node.addEventListener("pointerenter", (e) => showTip(node, value(), label, color(), e));
  node.addEventListener("pointermove", (e) => placeTip(node, e));
  node.addEventListener("pointerleave", hideTip);
  node.addEventListener("focus", () => showTip(node, value(), label, color()));
  node.addEventListener("blur", hideTip);
}

// ---------- charts ----------

function legend(categories) {
  return el("ul", { class: "legend", "aria-label": "Legend" },
    categories.map((c) => el("li", {}, el("span", { class: "swatch", style: { background: `var(--${c.role})` } }), c.label)));
}

function divergingChart(block) {
  const cats = [...block.categories].sort((a, b) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role));
  const side = (row, which) => cats.reduce((sum, c) => {
    const share = (row.counts[c.key] || 0) / row.n;
    if (c.role === "neutral") return sum + share / 2;
    return sum + (c.role.startsWith(which) ? share : 0);
  }, 0);
  const maxL = Math.max(...block.rows.map((r) => side(r, "neg")), 0.0001);
  const maxR = Math.max(...block.rows.map((r) => side(r, "pos")), 0.0001);
  const span = maxL + maxR;

  const chart = el("div", { class: "div-chart" });
  for (const row of block.rows) {
    const left = side(row, "neg");
    const bar = el("div", {
      class: "div-bar",
      style: { left: `${((maxL - left) / span) * 100}%`, width: `${((left + side(row, "pos")) / span) * 100}%` },
    });
    for (const c of cats) {
      const count = row.counts[c.key] || 0;
      const seg = el("div", {
        class: count ? "seg" : "seg empty",
        tabindex: count ? "0" : null,
        role: "img",
        "aria-label": `${row.label}: ${c.label}, ${pct(count, row.n)}% (${count} of ${row.n})`,
        "data-role": c.role,
        "data-pct": `${pct(count, row.n)}%`,
        style: { flex: `${count} 1 0`, background: `var(--${c.role})` },
      });
      if (count) withTip(seg, () => `${pct(count, row.n)}%  ·  ${count} of ${row.n}`, `${c.label}`, () => cssVar(`--${c.role}`));
      bar.append(seg);
    }
    const sub = row.excluded && row.excluded.count
      ? `${row.n} answered · ${row.excluded.count} left out`
      : `${row.n} answered`;
    chart.append(el("div", { class: "div-row" },
      el("div", { class: "row-label" }, row.label, el("small", { text: sub })),
      el("div", { class: "div-track", style: { "--center": `${(maxL / span) * 100}%` } }, bar)));
  }
  requestAnimationFrame(() => labelSegments(chart));
  return chart;
}

// Print a share inside a segment only when it fits with padding.
function labelSegments(root) {
  const font = `600 12.5px ${getComputedStyle(document.body).fontFamily}`;
  root.querySelectorAll(".seg:not(.empty)").forEach((seg) => {
    const text = seg.dataset.pct;
    const fits = seg.getBoundingClientRect().width >= textWidth(text, font) + 12;
    seg.textContent = fits ? text : "";
    seg.style.color = labelInk(cssVar(`--${seg.dataset.role}`));
  });
}

function barChart(block) {
  const max = Math.max(...block.items.map((i) => i.count), 1);
  const chart = el("div", { class: "bar-chart" });
  for (const item of block.items) {
    const share = pct(item.count, block.denominator);
    const row = el("div", {
      class: "bar-row", tabindex: "0", role: "img",
      "aria-label": `${item.label}: ${share}% (${item.count} of ${block.denominator})`,
    },
      el("div", { class: "row-label", text: item.label }),
      el("div", { class: "bar-line" },
        el("div", { class: "bar-fill", style: { width: `calc((100% - 6.5em) * ${item.count / max})` } }),
        el("span", { class: "bar-value" }, el("b", { text: `${share}%` }), `  ${item.count}`)));
    withTip(row, () => `${share}%  ·  ${item.count} of ${block.denominator}`, item.label, () => cssVar("--bar"));
    chart.append(row);
  }
  return chart;
}

function tableView(block) {
  let table;
  if (block.type === "diverging") {
    const cats = [...block.categories].sort((a, b) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role));
    const hasExcluded = block.rows.some((r) => r.excluded);
    table = el("table", { class: "data" },
      el("caption", { text: "Number of people, with share of those who answered" }),
      el("thead", {}, el("tr", {}, el("th", { text: "Question" }),
        cats.map((c) => el("th", { class: "num", text: c.label })),
        el("th", { class: "num", text: "Answered" }),
        hasExcluded ? el("th", { class: "num", text: "Left out" }) : null)),
      el("tbody", {}, block.rows.map((r) => el("tr", {},
        el("td", { text: r.question || r.label }),
        cats.map((c) => el("td", { class: "num", text: `${r.counts[c.key] || 0} (${pct(r.counts[c.key] || 0, r.n)}%)` })),
        el("td", { class: "num", text: r.n }),
        hasExcluded ? el("td", { class: "num", text: r.excluded ? r.excluded.count : "" }) : null))));
  } else {
    table = el("table", { class: "data" },
      el("caption", { text: `Share of ${block.denominator}` }),
      el("thead", {}, el("tr", {}, el("th", { text: "Answer" }), el("th", { class: "num", text: "People" }), el("th", { class: "num", text: "Share" }))),
      el("tbody", {}, block.items.map((i) => el("tr", {},
        el("td", { text: i.label }), el("td", { class: "num", text: i.count }), el("td", { class: "num", text: `${pct(i.count, block.denominator)}%` })))));
  }
  return el("details", {}, el("summary", { text: "Show the numbers" }), el("div", { class: "table-scroll" }, table));
}

function writeIns(block) {
  const items = block.type === "diverging"
    ? block.rows.flatMap((r) => r.writeIns.map((t) => ({ tag: r.label, text: t })))
    : (block.writeIns || []).map((t) => ({ tag: null, text: t }));
  if (!items.length) return null;
  return el("details", {},
    el("summary", { text: `Read the ${plural(items.length, "write-in answer", "write-in answers")}` }),
    el("ul", { class: "quotes" }, items.map((i) => el("li", {}, i.tag ? el("span", { class: "row-tag", text: i.tag }) : null, i.text))));
}

function renderBlock(block) {
  const wrap = el("div", { class: "block" }, el("h3", { text: block.title }));
  if (block.type === "comments") {
    wrap.append(el("p", { class: "comment-q", text: `“${block.question}”` }));
    if (!block.items.length) return wrap;
    wrap.append(el("details", {},
      el("summary", { text: `Read all ${plural(block.items.length, "comment", "comments")}` }),
      el("ul", { class: "quotes" }, block.items.map((t) => el("li", { text: t })))));
    return wrap;
  }
  if (block.subtitle) wrap.append(el("p", { class: "sub", text: block.subtitle }));
  if (block.type === "diverging") wrap.append(legend(block.categories), divergingChart(block));
  if (block.type === "bars") wrap.append(barChart(block));
  if (block.note) wrap.append(el("p", { class: "note", text: block.note }));
  wrap.append(tableView(block));
  const w = writeIns(block);
  if (w) wrap.append(w);
  return wrap;
}

function statTiles(stats) {
  return el("div", { class: "stats" }, stats.map((s) => el("div", { class: "stat" },
    el("div", { class: "label", text: s.label }),
    el("div", { class: "value", text: s.value }),
    el("div", { class: "detail", text: s.detail }))));
}

// ---------- pages ----------

function yearPage(y) {
  const intro = el("section", { class: "intro" }, el("div", { class: "wrap" },
    el("h1", { text: y.title }),
    el("ul", { class: "facts" },
      el("li", {}, el("b", { text: "When: " }), y.when),
      el("li", {}, el("b", { text: "How: " }), y.platform),
      el("li", {}, el("b", { text: "Who: " }), y.who)),
    statTiles(y.stats)));
  const body = el("div", { class: "wrap" },
    el("section", { class: "takeaways" }, el("h2", { text: "Key takeaways" }),
      el("ul", {}, y.takeaways.map((t) => el("li", { text: t })))),
    y.sections.map((s) => el("section", { class: "section" }, el("h2", { text: s.title }), s.blocks.map(renderBlock))),
    el("p", { class: "block note" }, "Download the full ",
      el("a", { href: `data/sirens_survey_${y.year}.csv`, text: `${y.year} responses (CSV)` }),
      ". Text in square brackets was written by the Sirens to remove names or identifying details."));
  return [intro, body];
}

function overviewPage() {
  const years = DATA.years;
  const total = years.reduce((s, y) => s + y.responses, 0);
  const a = DATA.across;
  const intro = el("section", { class: "intro" }, el("div", { class: "wrap" },
    el("h1", { text: "What Sirens told us, 2023–2025" }),
    el("p", { class: "lede", text: "Every year the Sirens survey supporters, mostly members, about game day, the Wave front office and the Sirens themselves. Here's what they said, with charts, summaries and the full anonymized responses." }),
    statTiles([
      { label: "Responses", value: String(total), detail: "Across three surveys" },
      ...years.slice().reverse().map((y) => ({ label: `${y.year} survey`, value: String(y.responses), detail: `${y.platform}, ${y.when}` })),
    ])));

  const cols = el("div", { class: "col-chart", role: "img", "aria-label": a.rep.items.map((i) => `${i.label}: ${i.value}% (${i.detail})`).join("; ") },
    a.rep.items.map((i) => el("div", { class: "col" },
      el("div", { class: "cap" }, `${i.value}%`, el("small", { text: i.detail })),
      el("div", { class: "fill", style: { height: `calc((100% - 3.2em) * ${i.value / 100})` } }))));
  const colLabels = el("div", { class: "col-labels", "aria-hidden": "true" }, a.rep.items.map((i) => el("span", { text: i.label })));

  const t = a.table;
  const table = el("div", { class: "table-scroll" }, el("table", { class: "data measure-table" },
    el("thead", {}, el("tr", {}, el("th", { text: "Measure" }), t.columns.map((c) => el("th", { text: c })))),
    el("tbody", {}, t.rows.map((r) => el("tr", {}, el("td", { text: r.label }),
      r.cells.map((c) => el("td", { class: c.value ? "" : "na" }, c.value, c.detail ? el("span", { class: "detail", text: c.detail }) : null)))))));

  const cards = years.slice().reverse().map((y) => el("div", { class: "block" },
    el("h3", {}, el("a", { href: `#${y.year}`, text: y.title })),
    el("ul", { class: "takeaways-short" }, y.takeaways.slice(0, 3).map((x) => el("li", { text: x })))));

  const body = el("div", { class: "wrap" },
    el("section", { class: "section" }, el("h2", { text: "Across the years" }),
      el("div", { class: "block" }, el("h3", { text: t.title }), table, el("p", { class: "note", text: t.note })),
      el("div", { class: "block" }, el("h3", { text: a.rep.title }), el("p", { class: "sub", text: a.rep.subtitle }), cols, colLabels)),
    el("section", { class: "section" }, el("h2", { text: "Each year at a glance" }), cards));
  return [intro, body];
}

function aboutPage() {
  const intro = el("section", { class: "intro" }, el("div", { class: "wrap" },
    el("h1", { text: "About the data" }),
    el("p", { class: "lede", text: "How the surveys were run, how responses were prepared for publication, and where to download them." })));
  const p = (t) => el("p", { text: t });
  const body = el("div", { class: "wrap prose" },
    el("h2", { text: "Download" }),
    el("ul", { class: "downloads" }, DATA.years.slice().reverse().map((y) =>
      el("li", {}, el("a", { href: `data/sirens_survey_${y.year}.csv`, download: true, text: `${y.year} responses · ${y.responses} rows (CSV)` })))),
    p("Each file has one row per response and one column per question, headed with the question as people saw it. Response IDs were made up for this release."),
    el("h2", { text: "The surveys" }),
    el("ul", {}, DATA.years.map((y) => el("li", {}, el("b", { text: `${y.year}: ` }), `${y.platform}, ${y.when}. ${y.who}. ${y.responses} responses.`))),
    p("2023 informed the Independent Supporters Council's front office ratings. 2025 dropped those rating questions and focused on the Sirens, watch parties and membership, so some trends only cover 2023 and 2024."),
    el("h2", { text: "How responses were prepared" }),
    el("ul", {},
      el("li", { text: "Only questions that were actually asked are included." }),
      el("li", { text: "Timestamps and platform IDs were removed, and rows were shuffled, so the order doesn't show when anyone responded." }),
      el("li", { text: "Every written answer was read before release. Names of Wave staff, Sirens officers, volunteers and other private people were replaced with a role in square brackets, like [ticket rep]. A few details that could identify a respondent were generalized the same way." }),
      el("li", { text: "Players, coaches and club executives are public figures, and their names are kept. Everything else is published as written." })),
    el("h2", { text: "Reading the charts" }),
    el("ul", {},
      el("li", { text: "Percentages are of the people who answered that question, which is shown under each label." }),
      el("li", { text: "Write-in answers to yes-or-no questions are counted as “Not sure or other”, and you can read them under each chart." }),
      el("li", { text: "Every chart has a “Show the numbers” table with the exact counts." })),
    el("h2", { text: "Something wrong?" }),
    el("p", {}, "If you see something that identifies you or someone else, email ",
      el("a", { href: "mailto:contact@sandiegosirens.com", text: "contact@sandiegosirens.com" }), " and it will be removed."));
  return [intro, body];
}

// ---------- routing ----------

function route() {
  hideTip();
  const hash = (location.hash || "#overview").slice(1);
  const year = DATA.years.find((y) => y.year === hash);
  const page = year ? yearPage(year) : hash === "about" ? aboutPage() : overviewPage();
  main.replaceChildren(...page);
  const current = year ? hash : hash === "about" ? "about" : "overview";
  document.querySelectorAll(".tabs a").forEach((a) => {
    if (a.getAttribute("href") === `#${current}`) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  document.title = year ? `${year.title} · Sirens Survey Results` : hash === "about" ? "About the data · Sirens Survey Results" : "Sirens Survey Results";
  window.scrollTo(0, 0);
}

let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => labelSegments(main), 120);
});
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => labelSegments(main));
window.addEventListener("hashchange", () => { route(); main.focus({ preventScroll: true }); });

fetch("data/surveys.json")
  .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then((d) => { DATA = d; route(); })
  .catch(() => main.replaceChildren(el("p", { class: "wrap error", text: "The survey results couldn't be loaded. Try refreshing the page." })));
