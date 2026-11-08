/* 结构分析表征 — 页面渲染逻辑（配合 data.js 使用，支持中英文切换） */
(function () {
  "use strict";
  var D = window.SITE_DATA || {};
  var videos = D.videos || [];
  var I18N = D.i18n || {};
  var lang = "zh";
  try { lang = localStorage.getItem("fxbz_lang") || "zh"; } catch (e) {}
  var PER_PAGE = 24;

  function t(key) {
    var item = I18N[key];
    if (!item) return key;
    return item[lang] || item.zh || key;
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function viewsTxt(n) {
    if (lang === "en") {
      if (n >= 1000000) return (n / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
      if (n >= 10000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "k";
      return String(n);
    }
    if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, "") + "万";
    return String(n);
  }

  function vCard(v) {
    return '<div class="v-card" data-bvid="' + esc(v.b) + '" data-title="' + esc(v.t) + '">' +
      '<p class="v-title">' + esc(v.t) + "</p>" +
      '<div class="v-meta">' +
      '<span class="v-tag ' + v.y + '">' + esc(t("type." + v.y)) + "</span>" +
      '<span class="v-src">B站</span>' +
      "<span>📅 " + esc(v.d) + "</span>" +
      "<span>⏱ " + esc(v.s) + "</span>" +
      "<span>▶ " + viewsTxt(v.v) + "</span>" +
      "</div></div>";
  }

  function aCard(a) {
    return '<a class="v-card a-card" href="' + esc(a.l) + '" target="_blank" rel="noopener">' +
      '<p class="v-title">' + esc(a.t) + " ↗</p>" +
      '<div class="v-meta">' +
      '<span class="v-tag ' + a.y + '">' + esc(t("type." + a.y)) + "</span>" +
      '<span class="v-src">' + esc(a.s) + "</span>" +
      "<span>📅 " + esc(a.d) + "</span>" +
      "</div></a>";
  }

  /* ---------- 静态文案切换 ---------- */
  function applyLang() {
    document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      if (el.dataset.zh === undefined) el.dataset.zh = el.textContent;
      var v = I18N[el.getAttribute("data-i18n")];
      if (v) el.textContent = lang === "en" ? (v.en || v.zh) : (el.dataset.zh || v.zh);
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      if (el.dataset.phZh === undefined) el.dataset.phZh = el.getAttribute("placeholder");
      var v = I18N[el.getAttribute("data-i18n-ph")];
      if (v) el.setAttribute("placeholder", lang === "en" ? (v.en || v.zh) : (el.dataset.phZh || v.zh));
    });
    document.querySelectorAll("[data-stat]").forEach(function (el) {
      var k = el.getAttribute("data-stat");
      var n = D.stats && D.stats[k];
      if (typeof n === "number") el.textContent = viewsTxt(n);
    });
    var btn = document.getElementById("lang-toggle");
    if (btn) btn.textContent = lang === "zh" ? "EN" : "中文";
  }

  var toggle = document.getElementById("lang-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      lang = lang === "zh" ? "en" : "zh";
      try { localStorage.setItem("fxbz_lang", lang); } catch (e) {}
      applyLang();
      rerenderDynamic();
    });
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

  /* ---------- 动态区块（语言切换后重渲染） ---------- */
  var latest = document.getElementById("latest-grid");
  var rerenderLatest = function () {};
  if (latest) {
    rerenderLatest = function () {
      var byDate = videos.slice().sort(function (a, b) { return b.d < a.d ? -1 : 1; }).slice(0, 8);
      latest.innerHTML = byDate.map(vCard).join("");
    };
  }

  var page = document.body.getAttribute("data-page");
  var grid = document.getElementById("video-grid");
  var rerenderCat = function () {};
  if (grid && D.software && D.software[page]) {
    var catVideos = videos.filter(function (v) { return v.c === page; });
    var state = { type: "all", q: "", shown: PER_PAGE };
    var swGrid = document.getElementById("sw-grid");
    var searchBox = document.getElementById("search");

    function renderSw() {
      swGrid.innerHTML = D.software[page].map(function (sw) {
        var n = catVideos.filter(function (v) {
          var tt = v.t.toLowerCase();
          return sw.kw.some(function (k) { return tt.indexOf(k.toLowerCase()) >= 0; });
        }).length;
        var name = lang === "en" ? (sw.name_en || sw.name) : sw.name;
        var vendor = lang === "en" ? (sw.vendor_en || sw.vendor) : sw.vendor;
        var desc = lang === "en" ? (sw.desc_en || sw.desc) : sw.desc;
        return '<div class="sw-card" data-kw="' + esc(sw.kw[0]) + '">' +
          "<h3>" + esc(name) + '<span class="vendor">' + esc(vendor) + "</span></h3>" +
          "<p>" + esc(desc) + "</p>" +
          '<span class="sw-n">' + esc(n ? t("sw.n").replace("{n}", n) : t("sw.none")) + "</span></div>";
      }).join("");
    }

    function filtered() {
      return catVideos.filter(function (v) {
        if (state.type !== "all" && v.y !== state.type) return false;
        if (state.q && v.t.toLowerCase().indexOf(state.q) < 0) return false;
        return true;
      });
    }

    function render() {
      var list = filtered();
      document.getElementById("v-count").textContent = t("videos.count").replace("{n}", list.length);
      grid.innerHTML = list.slice(0, state.shown).map(vCard).join("") ||
        '<p class="muted" style="grid-column:1/-1;padding:20px 4px">' + esc(t("empty")) + "</p>";
      document.getElementById("more").hidden = list.length <= state.shown;
    }

    swGrid.addEventListener("click", function (e) {
      var card = e.target.closest(".sw-card");
      if (!card) return;
      searchBox.value = card.getAttribute("data-kw");
      state.q = card.getAttribute("data-kw").toLowerCase();
      state.shown = PER_PAGE;
      render();
      document.getElementById("type-chips").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    document.getElementById("type-chips").addEventListener("click", function (e) {
      var chip = e.target.closest(".chip");
      if (!chip) return;
      document.querySelectorAll("#type-chips .chip").forEach(function (c) { c.classList.remove("active"); });
      chip.classList.add("active");
      state.type = chip.getAttribute("data-type");
      state.shown = PER_PAGE;
      render();
    });
    var timer = null;
    searchBox.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        state.q = searchBox.value.trim().toLowerCase();
        state.shown = PER_PAGE;
        render();
      }, 150);
    });
    document.getElementById("more").addEventListener("click", function () {
      state.shown += PER_PAGE;
      render();
    });

    rerenderCat = function () { renderSw(); render(); };
    renderSw();
    render();
  }

  /* ---------- 公众号图文栏目 ---------- */
  var aGrid = document.getElementById("article-grid");
  var rerenderArticles = function () {};
  if (aGrid && D.articles) {
    var isLitPage = page === "literature";
    var catArticles = D.articles.filter(function (a) {
      return isLitPage ? (a.y === "lit" || a.c === "general") : a.c === page;
    });
    var aType = "all", aShown = 12;
    function renderArticles() {
      var list = catArticles.filter(function (a) {
        return aType === "all" || a.y === aType;
      });
      document.getElementById("a-count").textContent = t("articles.count").replace("{n}", list.length);
      aGrid.innerHTML = list.slice(0, aShown).map(aCard).join("") ||
        '<p class="muted" style="grid-column:1/-1;padding:20px 4px">' + esc(t("empty")) + "</p>";
      var moreBtn = document.getElementById("amore");
      if (moreBtn) moreBtn.hidden = list.length <= aShown;
    }
    var chipsEl = document.getElementById("atype-chips");
    if (chipsEl) {
      chipsEl.addEventListener("click", function (e) {
        var chip = e.target.closest(".chip");
        if (!chip) return;
        chipsEl.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        aType = chip.getAttribute("data-atype");
        aShown = 12;
        renderArticles();
      });
    }
    var moreBtn2 = document.getElementById("amore");
    if (moreBtn2) {
      moreBtn2.addEventListener("click", function () {
        aShown += 12;
        renderArticles();
      });
    }
    rerenderArticles = renderArticles;
  }

  function rerenderDynamic() {
    rerenderLatest();
    rerenderCat();
    rerenderArticles();
  }

  applyLang();
  rerenderDynamic();
})();
