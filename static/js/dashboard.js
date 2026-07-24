(() => {
  "use strict";

  const els = {
    form: document.getElementById("track-form"),
    inputName: document.getElementById("input-name"),
    inputTicker: document.getElementById("input-ticker"),
    trackBtn: document.getElementById("track-btn"),
    statusLine: document.getElementById("track-status"),
    companyList: document.getElementById("company-list"),
    emptyState: document.getElementById("empty-state"),
    dashboard: document.getElementById("dashboard"),
    heroTicker: document.getElementById("hero-ticker"),
    heroName: document.getElementById("hero-name"),
    heroSource: document.getElementById("hero-source"),
    heroStamp: document.getElementById("hero-stamp"),
    heroStampLabel: document.getElementById("hero-stamp-label"),
    heroScore: document.getElementById("hero-score"),
    refreshBtn: document.getElementById("refresh-btn"),
    tickerTape: document.getElementById("ticker-tape-inner"),
    headlineFeed: document.getElementById("headline-feed"),
    signalStamp: document.getElementById("signal-stamp"),
    signalStampLabel: document.getElementById("signal-stamp-label"),
    confidenceFill: document.getElementById("confidence-fill"),
    confidenceValue: document.getElementById("confidence-value"),
    signalReasoning: document.getElementById("signal-reasoning"),
  };

  let activeTicker = null;
  let trendChart = null;
  let donutChart = null;

  const TONE_COLORS = {
    positive: "#3FB68B",
    neutral: "#C9A227",
    negative: "#E0637A",
  };

  function setStatus(msg, state) {
    els.statusLine.textContent = msg;
    if (state) els.statusLine.setAttribute("data-state", state);
    else els.statusLine.removeAttribute("data-state");
  }

  async function apiGet(url) {
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  }

  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  }

  async function loadCompanies() {
    const companies = await apiGet("/api/companies");
    els.companyList.innerHTML = "";
    if (companies.length === 0) {
      els.companyList.innerHTML = '<li class="empty-note">Nothing tracked yet.</li>';
      return;
    }
    companies.forEach((c) => {
      const li = document.createElement("li");
      li.className = "company-item" + (c.ticker === activeTicker ? " active" : "");
      li.innerHTML = `<span><span class="ci-ticker">${escapeHtml(c.ticker)}</span><span class="ci-name">${escapeHtml(c.name)}</span></span>`;
      li.addEventListener("click", () => selectCompany(c.ticker));
      els.companyList.appendChild(li);
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str ?? "";
    return div.innerHTML;
  }

  async function selectCompany(ticker) {
    activeTicker = ticker;
    await loadCompanies();
    await renderSentiment(ticker);
  }

  function toneFromScore(score) {
    if (score >= 0.05) return "positive";
    if (score <= -0.05) return "negative";
    return "neutral";
  }

  async function renderSentiment(ticker) {
    const data = await apiGet(`/api/sentiment/${encodeURIComponent(ticker)}`);
    els.emptyState.classList.add("hidden");
    els.dashboard.classList.remove("hidden");

    els.heroTicker.textContent = data.company.ticker;
    els.heroName.textContent = data.company.name;
    els.heroSource.textContent = `${data.headlines.length} headline${data.headlines.length === 1 ? "" : "s"} logged`;
    els.heroScore.textContent = data.overall_score.toFixed(2);

    const tone = toneFromScore(data.overall_score);
    els.heroStamp.setAttribute("data-tone", tone);
    els.heroStampLabel.textContent = tone.toUpperCase();

    const summary = data.summary;
    const pct = data.summary_pct;
    document.getElementById("count-positive").textContent = summary.positive;
    document.getElementById("count-neutral").textContent = summary.neutral;
    document.getElementById("count-negative").textContent = summary.negative;
    document.getElementById("pct-positive").textContent = `${pct.positive ?? 0}%`;
    document.getElementById("pct-neutral").textContent = `${pct.neutral ?? 0}%`;
    document.getElementById("pct-negative").textContent = `${pct.negative ?? 0}%`;

    renderTrendChart(data.trend);
    renderDonutChart(summary);
    renderHeadlines(data.headlines);
    renderTickerTape(data);
    renderSignal(data.signal);
  }

  function renderSignal(signal) {
    const tone = signal.signal.toLowerCase(); // buy | sell | hold
    els.signalStamp.setAttribute("data-tone", tone);
    els.signalStampLabel.textContent = signal.signal;

    const pct = Math.round(signal.confidence * 100);
    els.confidenceFill.style.width = `${pct}%`;
    els.confidenceValue.textContent = `${pct}%`;
    els.confidenceFill.style.background = TONE_COLORS[
      tone === "buy" ? "positive" : tone === "sell" ? "negative" : "neutral"
    ];

    els.signalReasoning.innerHTML = "";
    signal.reasoning.forEach((line) => {
      const li = document.createElement("li");
      li.textContent = line;
      els.signalReasoning.appendChild(li);
    });
  }

  function renderTrendChart(trend) {
    const ctx = document.getElementById("trend-chart");
    const labels = trend.map((t) => t.day);
    const scores = trend.map((t) => t.avg_score);

    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Avg. sentiment (compound)",
          data: scores,
          borderColor: "#6C8CFF",
          backgroundColor: "rgba(108,140,255,0.12)",
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointBackgroundColor: "#6C8CFF",
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            min: -1, max: 1,
            grid: { color: "#263352" },
            ticks: { color: "#8892A6" },
          },
          x: {
            grid: { color: "#1A2338" },
            ticks: { color: "#8892A6" },
          },
        },
      },
    });
  }

  function renderDonutChart(summary) {
    const ctx = document.getElementById("donut-chart");
    if (donutChart) donutChart.destroy();
    donutChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [{
          data: [summary.positive, summary.neutral, summary.negative],
          backgroundColor: [TONE_COLORS.positive, TONE_COLORS.neutral, TONE_COLORS.negative],
          borderColor: "#121A2C",
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom", labels: { color: "#8892A6", boxWidth: 12, padding: 14 } },
        },
      },
    });
  }

  function renderHeadlines(headlines) {
    els.headlineFeed.innerHTML = "";
    if (headlines.length === 0) {
      els.headlineFeed.innerHTML = '<li class="empty-note">No headlines yet.</li>';
      return;
    }
    headlines.forEach((h) => {
      const li = document.createElement("li");
      li.className = "headline-row";
      const dateStr = h.published_at ? h.published_at.substring(0, 10) : "—";
      const textHtml = h.url
        ? `<a href="${escapeHtml(h.url)}" target="_blank" rel="noopener">${escapeHtml(h.headline)}</a>`
        : escapeHtml(h.headline);
      li.innerHTML = `
        <span class="hr-tag" data-tone="${h.sentiment_label}">${h.sentiment_label.toUpperCase()}</span>
        <span class="hr-text">${textHtml}<span class="hr-meta">${escapeHtml(h.source || "")} · ${dateStr}</span></span>
        <span class="hr-score">${h.compound_score.toFixed(2)}</span>
      `;
      els.headlineFeed.appendChild(li);
    });
  }

  function renderTickerTape(data) {
    const tone = toneFromScore(data.overall_score);
    const arrow = tone === "positive" ? "▲" : tone === "negative" ? "▼" : "▬";
    els.tickerTape.textContent =
      `${data.company.ticker} ${arrow} ${data.overall_score.toFixed(2)}  |  ` +
      `POS ${data.summary.positive}  NEU ${data.summary.neutral}  NEG ${data.summary.negative}  |  ` +
      `${data.headlines.length} headlines tracked`;
  }

  els.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = els.inputName.value.trim();
    const ticker = els.inputTicker.value.trim().toUpperCase();
    if (!name || !ticker) return;

    els.trackBtn.disabled = true;
    setStatus("Fetching headlines and scoring sentiment…");
    try {
      const result = await apiPost("/api/track", { name, ticker });
      setStatus(
        result.live_source_used
          ? "Done — pulled live headlines."
          : "Done — live source unavailable, used sample data for demo.",
        "ok"
      );
      els.form.reset();
      await selectCompany(result.ticker);
    } catch (err) {
      setStatus(err.message, "error");
    } finally {
      els.trackBtn.disabled = false;
    }
  });

  els.refreshBtn.addEventListener("click", async () => {
    if (!activeTicker) return;
    els.refreshBtn.disabled = true;
    els.refreshBtn.textContent = "Refreshing…";
    try {
      await apiGet(`/api/refresh/${encodeURIComponent(activeTicker)}`);
      await renderSentiment(activeTicker);
    } catch (err) {
      setStatus(err.message, "error");
    } finally {
      els.refreshBtn.disabled = false;
      els.refreshBtn.textContent = "Refresh";
    }
  });

  loadCompanies();
})();
