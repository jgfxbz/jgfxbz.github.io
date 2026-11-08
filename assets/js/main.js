/* 结构分析表征 — 页面渲染逻辑（配合 data.js 使用） */
(function () {
  "use strict";
  var D = window.SITE_DATA || {};
  var videos = D.videos || [];
  var TYPE_NAME = { a: "数据分析", s: "软件介绍", p: "原理科普" };
  var PER_PAGE = 24;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function viewsTxt(n) {
    if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, "") + "万";
    return String(n);
  }

  function vCard(v) {
    return '<div class="v-card" data-bvid="' + esc(v.b) + '" data-title="' + esc(v.t) + '">' +
      '<p class="v-title">' + esc(v.t) + "</p>" +
      '<div class="v-meta">' +
      '<span class="v-tag ' + v.y + '">' + TYPE_NAME[v.y] + "</span>" +
      "<span>📅 " + esc(v.d) + "</span>" +
      "<span>⏱ " + esc(v.s) + "</span>" +
      "<span>▶ " + viewsTxt(v.v) + "</span>" +
      "</div></div>";
  }

  /* ---------- 视频弹窗播放 ---------- */
  var modal = document.getElementById("modal");
  var modalFrame = document.getElementById("modal-frame");
  var modalTitle = document.getElementById("modal-title");
  var modalLink = document.getElementById("modal-link");

  function openModal(bvid, title) {
    if (!modal) return;
    modalTitle.textContent = title;
    modalFrame.src = "https://player.bilibili.com/player.html?bvid=" + encodeURIComponent(bvid) +
      "&high_quality=1&danmaku=0&autoplay=0";
    modalLink.href = "https://www.bilibili.com/video/" + bvid;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }
  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    modalFrame.src = "";
    document.body.style.overflow = "";
  }
  document.addEventListener("click", function (e) {
    var card = e.target.closest(".v-card");
    if (card) { openModal(card.getAttribute("data-bvid"), card.getAttribute("data-title")); return; }
    if (e.target.closest("[data-close]")) closeModal();
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeModal(); });

  /* ---------- 首页：最新更新 ---------- */
  var latest = document.getElementById("latest-grid");
  if (latest) {
    var byDate = videos.slice().sort(function (a, b) { return b.d < a.d ? -1 : 1; }).slice(0, 8);
    latest.innerHTML = byDate.map(vCard).join("");
  }

  /* ---------- 仪器分类页 ---------- */
  var page = document.body.getAttribute("data-page");
  var grid = document.getElementById("video-grid");
  if (!grid || !D.software || !D.software[page]) return;

  var catVideos = videos.filter(function (v) { return v.c === page; });
  var state = { type: "all", q: "", shown: PER_PAGE };

  var swGrid = document.getElementById("sw-grid");
  swGrid.innerHTML = D.software[page].map(function (sw, i) {
    var n = catVideos.filter(function (v) {
      var t = v.t.toLowerCase();
      return sw.kw.some(function (k) { return t.indexOf(k.toLowerCase()) >= 0; });
    }).length;
    return '<div class="sw-card" data-kw="' + esc(sw.kw[0]) + '" data-idx="' + i + '">' +
      "<h3>" + esc(sw.name) + '<span class="vendor">' + esc(sw.vendor) + "</span></h3>" +
      "<p>" + esc(sw.desc) + "</p>" +
      '<span class="sw-n">' + (n ? n + " 个相关视频 →" : "相关视频整理中") + "</span></div>";
  }).join("");
  swGrid.addEventListener("click", function (e) {
    var card = e.target.closest(".sw-card");
    if (!card) return;
    var kw = card.getAttribute("data-kw");
    searchBox.value = kw;
    state.q = kw.toLowerCase();
    state.shown = PER_PAGE;
    render();
    document.getElementById("type-chips").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  var chips = document.getElementById("type-chips");
  chips.addEventListener("click", function (e) {
    var chip = e.target.closest(".chip");
    if (!chip) return;
    chips.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
    chip.classList.add("active");
    state.type = chip.getAttribute("data-type");
    state.shown = PER_PAGE;
    render();
  });

  var searchBox = document.getElementById("search");
  var timer = null;
  searchBox.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () {
      state.q = searchBox.value.trim().toLowerCase();
      state.shown = PER_PAGE;
      render();
    }, 150);
  });

  function filtered() {
    return catVideos.filter(function (v) {
      if (state.type !== "all" && v.y !== state.type) return false;
      if (state.q && v.t.toLowerCase().indexOf(state.q) < 0) return false;
      return true;
    });
  }

  function render() {
    var list = filtered();
    document.getElementById("v-count").textContent = "共 " + list.length + " 个";
    grid.innerHTML = list.slice(0, state.shown).map(vCard).join("") ||
      '<p class="muted" style="grid-column:1/-1;padding:20px 4px">没有匹配的视频，换个关键词试试（如：拟合 / 精修 / jade / avantage）。</p>';
    document.getElementById("more").hidden = list.length <= state.shown;
  }

  document.getElementById("more").addEventListener("click", function () {
    state.shown += PER_PAGE;
    render();
  });

  render();
})();
