/* 结构分析表征 — 页面渲染逻辑（配合 data.js 使用，支持中英文切换 / 暗色模式） */
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

    /* ---------- 搜索归一化：全角->半角、小写；查询按空白拆多词(AND) ---------- */
  function norm(s) {
    s = String(s || "").toLowerCase();
    var full = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ";
    var half = "0123456789abcdefghijklmnopqrstuvwxyz";
    var out = "";
    for (var i = 0; i < s.length; i++) {
      var k = full.indexOf(s.charAt(i));
      out += k >= 0 ? half.charAt(k) : s.charAt(i);
    }
    return out;
  }
  function qTerms(q) {
    return norm(q).split(/\s+/).filter(Boolean);
  }
  function hayHit(hay, ts) {
    hay = norm(hay);
    for (var i = 0; i < ts.length; i++) if (hay.indexOf(ts[i]) < 0) return false;
    return true;
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

  /* ---------- 暗色模式 ---------- */
  function readTheme() {
    try { return localStorage.getItem("fxbz_theme") || "light"; } catch (e) { return "light"; }
  }
  function applyTheme() {
    document.documentElement.setAttribute("data-theme", readTheme());
    var b = document.getElementById("theme-btn");
    if (b) b.textContent = readTheme() === "dark" ? "☀️" : "🌙";
  }
  function toggleTheme() {
    var next = readTheme() === "dark" ? "light" : "dark";
    try { localStorage.setItem("fxbz_theme", next); } catch (e) {}
    applyTheme();
  }
  applyTheme();

  /* ---------- 汉堡菜单 ---------- */
  function initHamburger() {
    var hb = document.getElementById("hamburger-btn");
    var nav = document.querySelector("header nav");
    if (!hb || !nav) return;
    hb.addEventListener("click", function () {
      nav.classList.toggle("nav-open");
    });
  }
  initHamburger();

  /* 明暗色切换按钮 */
  var themeBtn = document.getElementById("theme-btn");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () { toggleTheme(); });
  }

  /* ---------- 相关视频映射（图文+视频互链）：标题归一后按共同关键词匹配 ---------- */
  var vidTitleIndex = videos.map(function (v) { return { b: v.b, t: v.t, low: (v.t || "").toLowerCase() }; });
  function relatedVideos(a) {
    var t = (a.t || "").toLowerCase();
    var words = t.replace(/[^a-z0-9\u4e00-\u9fa5]+/g, " ").split(" ").filter(function (w) { return w.length >= 2; });
    if (!words.length) return [];
    var scored = [];
    vidTitleIndex.forEach(function (v) {
      var hit = 0;
      words.forEach(function (w) { if (v.low.indexOf(w) >= 0) hit++; });
      if (hit >= Math.min(2, words.length)) scored.push({ b: v.b, t: v.t, hit: hit });
    });
    scored.sort(function (x, y) { return y.hit - x.hit; });
    return scored.slice(0, 2);
  }

  function vCard(v, hot) {
    var picUrl = v.p ? (v.p.indexOf("hdslb.com") >= 0 ? v.p + "@480w_270h_1c.webp" : v.p) : "";
    var pic = picUrl ? '<img class="v-thumb" src="' + esc(picUrl) + '" alt="" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">' : "";
    var fire = (v.v || 0) >= 1000 ? '<span class="hot-badge">🔥 热门</span>' : "";
    return '<div class="v-card" data-bvid="' + esc(v.b) + '" data-title="' + esc(v.t) + '">' +
      pic +
      '<p class="v-title">' + esc(v.t) + "</p>" + fire +
      '<div class="v-meta">' +
      '<span class="v-tag ' + v.y + '">' + esc(t("type." + v.y)) + "</span>" +
      '<span class="v-src">B站</span>' +
      "<span>📅 " + esc(v.d) + "</span>" +
      "<span>⏱ " + esc(v.s) + "</span>" +
      "<span>▶ " + viewsTxt(v.v) + "</span>" +
      "</div></div>";
  }

  function aCard(a, withRelated) {
    var dig = a.g ? '<p class="v-digest">' + esc(String(a.g).slice(0, 70)) + "</p>" : "";
    var pic = a.p ? '<img class="v-thumb" loading="lazy" src="' + esc(a.p) + '" alt="" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">' : "";
    var srcCls = a.s === "光电子能谱分部" ? " src-xps" : a.s === "单晶多晶衍射分部" ? " src-xrd" : " src-main";
    var rel = "";
    if (withRelated && a.rel) {
      var rels = relatedVideos(a);
      if (rels.length) {
        rel = '<div class="v-rel">' + esc(lang === "en" ? "▶ Related videos" : "▶ 相关视频") + "：";
        rels.forEach(function (rv) {
          rel += '<a href="https://www.bilibili.com/video/' + esc(rv.b) + '" target="_blank" rel="noopener">' + esc(rv.t.slice(0, 28)) + "</a> ";
        });
        rel += "</div>";
      }
    }
    return '<a class="v-card a-card" href="' + esc(a.l) + '" target="_blank" rel="noopener">' + pic +
      '<p class="v-title">' + esc(a.t) + " ↗</p>" + dig + rel +
      '<div class="v-meta">' +
      '<span class="v-tag ' + a.y + '">' + esc(t("type." + a.y)) + "</span>" +
      '<span class="v-src' + srcCls + '">' + esc(a.s) + "</span>" +
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

  /* ---------- 首页：最新更新（视频 + 文章混合流 + 筛选） ---------- */
  var latest = document.getElementById("latest-grid");
  var rerenderLatest = function () {};
  if (latest) {
    var latestMode = "all";
    var latestChips = document.getElementById("latest-chips");
    rerenderLatest = function () {
      var items = [];
      if (latestMode !== "art") videos.forEach(function (v) { items.push({ d: v.d, h: vCard(v) }); });
      if (latestMode !== "vid") (D.articles || []).forEach(function (a) { items.push({ d: a.d, h: aCard(a, true) }); });
      items.sort(function (x, y) { return x.d < y.d ? 1 : -1; });
      latest.innerHTML = items.slice(0, 10).map(function (it) { return it.h; }).join("");
    };
    if (latestChips) {
      latestChips.addEventListener("click", function (e) {
        var chip = e.target.closest(".chip");
        if (!chip) return;
        latestChips.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        latestMode = chip.getAttribute("data-lt") || "all";
        rerenderLatest();
      });
    }
  }

  /* ---------- 首页搜索框：回车跳搜索页 ---------- */
  var homeQ = document.getElementById("home-q");
  if (homeQ) {
    var goSearch = function () {
      var kw = homeQ.value.trim();
      if (!kw) return;
      var prefix = document.body.getAttribute("data-page") === "home" ? "" : "../";
      location.href = prefix + "search/index.html?q=" + encodeURIComponent(kw);
    };
    homeQ.addEventListener("keydown", function (e) { if (e.key === "Enter") goSearch(); });
    var hb = document.getElementById("home-q-go");
    if (hb) hb.addEventListener("click", goSearch);
  }

  var page = document.body.getAttribute("data-page");

  /* ---------- 板块页：视频 + 软件卡（含热门排序） ---------- */
  var grid = document.getElementById("video-grid");
  var rerenderCat = function () {};
  if (grid && D.software && D.software[page]) {
    var catVideos = videos.filter(function (v) { return v.c === page; });
    var state = { type: "all", q: "", shown: PER_PAGE, sort: "new" };
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
      var list = catVideos.filter(function (v) {
        if (state.type !== "all" && v.y !== state.type) return false;
        if (state.q && !hayHit(norm(v.t) + " " + norm(v.g || ""), qTerms(state.q))) return false;
        return true;
      });
      if (state.sort === "hot") list = list.slice().sort(function (x, y) { return (y.v || 0) - (x.v || 0); });
      else if (state.sort === "old") list = list.slice().sort(function (x, y) { return String(x.d || "").localeCompare(String(y.d || "")); });
      else list = list.slice().sort(function (x, y) { return String(y.d || "").localeCompare(String(x.d || "")); });
      return list;
    }

    function render() {
      var list = filtered();
      document.getElementById("v-count").textContent = t("videos.count").replace("{n}", list.length);
      grid.innerHTML = list.slice(0, state.shown).map(function (v) { return vCard(v, true); }).join("") ||
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
    var sortChips = document.getElementById("sort-chips");
    if (sortChips) {
      sortChips.addEventListener("click", function (e) {
        var chip = e.target.closest(".chip");
        if (!chip) return;
        sortChips.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        state.sort = chip.getAttribute("data-sort") || "new";
        state.shown = PER_PAGE;
        render();
      });
    }
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

  /* ---------- 站内搜索页（结果分面：视频组 / 图文组） ---------- */
  var siteQ = document.getElementById("site-q");
  var rerenderSearch = function () {};
  if (siteQ && document.getElementById("search-grid")) {
    var sGrid = document.getElementById("search-grid");
    var sCount = document.getElementById("s-count");
    var sCap = 60;
    function renderSearch() {
      var ts = qTerms(siteQ.value);
      if (!ts.length) {
        sCount.textContent = "";
        sGrid.innerHTML = "";
        vShown = aShown = 0;
        var m0 = document.getElementById("smore");
        if (m0) m0.hidden = true;
        return;
      }
      var vRes = videos.filter(function (v) { return hayHit(norm(v.t) + " " + norm(v.g || ""), ts); });
      var aRes = (D.articles || []).filter(function (a) { return hayHit(norm(a.t) + " " + norm(a.g || ""), ts); });
      vRes.sort(function (x, y) { return x.d < y.d ? 1 : -1; });
      aRes.sort(function (x, y) { return x.d < y.d ? 1 : -1; });
      sCount.textContent = t("search.results").replace("{n}", vRes.length + aRes.length);
      if (vShown === undefined || window.__lastQ !== ts.join(" ")) {
        vShown = 30; aShown = 40; window.__lastQ = ts.join(" ");
      }
      var html = "";
      if (vRes.length) {
        html += '<p class="facet-head">▶ ' + esc(lang === "en" ? "Videos" : "视频") + "（" + vRes.length + "）</p>";
        html += vRes.slice(0, vShown).map(function (v) { return vCard(v, true); }).join("");
      }
      if (aRes.length) {
        html += '<p class="facet-head">📄 ' + esc(lang === "en" ? "WeChat articles" : "公众号图文") + "（" + aRes.length + "）</p>";
        html += aRes.slice(0, aShown).map(function (a) { return aCard(a, true); }).join("");
      }
      sGrid.innerHTML = html ||
        '<p class="muted" style="grid-column:1/-1;padding:20px 4px">' + esc(t("empty")) + "</p>";
      var moreBtn = document.getElementById("smore");
      if (moreBtn) moreBtn.hidden = !(vRes.length > vShown || aRes.length > aShown);
    }
    var vShown = 30, aShown = 40;
    var sTimer = null;
    siteQ.addEventListener("input", function () {
      clearTimeout(sTimer);
      sTimer = setTimeout(renderSearch, 200);
    });
    try {
      var q0 = new URLSearchParams(location.search).get("q");
      if (q0) {
        siteQ.value = q0;
        setTimeout(renderSearch, 0);
      }
    } catch (e) {}
    var smoreBtn = document.getElementById("smore");
    if (smoreBtn) {
      smoreBtn.addEventListener("click", function () {
        vShown += 30; aShown += 40;
        renderSearch();
        var g = document.getElementById("search-grid");
        if (g) g.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
    rerenderSearch = renderSearch;
  }

  /* ---------- 公众号图文栏目（过滤框 + 二级分类 + 年份分组 + 系列视图 + 来源筛选） ---------- */
  var aGrid = document.getElementById("article-grid");
  var rerenderArticles = function () {};
  if (aGrid && D.articles) {
    var isLitPage = page === "literature";
    var catArticles = D.articles.filter(function (a) {
      return isLitPage ? (a.y === "lit" || a.c === "general") : a.c === page;
    });

    /* 二级分类规则（按标题关键词自动聚类） */
    var SUB_RULES = [
      ["PeakForge", /peakforge/i],
      ["Avantage", /avantage|thermo/i],
      ["CasaXPS", /casaxps/i],
      ["Multipak", /multipak/i],
      ["转换 / 导出", /vgd|vms|转换|导出|excel|spe\b/i],
      ["UPS / 价带 / 功函数", /ups|价带|功函数|d带|p带|\bdos\b/i],
      ["深度 / 刻蚀", /深度|depth|刻蚀/i],
      ["结合能 / 校准", /结合能|校准|荷电/i],
      ["数据查询 / 元素", /元素|周期表|查询|数据库/i],
      ["书籍 / 出版", /入门到精通|出版|新书/i],
      ["文献解析", /文献|论文解读/i]
    ];
    function subOf(a) {
      if (page !== "xps") return "";
      for (var i = 0; i < SUB_RULES.length; i++) {
        if (SUB_RULES[i][1].test(a.t || "")) return SUB_RULES[i][0];
      }
      return lang === "en" ? "Other" : "其他";
    }
    function seriesKey(t) {
      var t2 = (t || "").replace(/\s+/g, "");
      t2 = t2.replace(/[-–—]?\d+$/, "");
      t2 = t2.replace(/（[^）]*）$/, "");
      t2 = t2.replace(/截至\d{4}[.\d]*/, "");
      return t2.slice(0, 18);
    }

    var aType = "all", aShown = 18, aSrc = "all", aSub = "all", aYear = "all", aView = "list", aKw = "", aSort = "new";
    /* 文章排序 chips（最新在前 / 最早在前） */
    var asortChipsEl = document.getElementById("asort-chips");
    if (asortChipsEl) {
      asortChipsEl.addEventListener("click", function (e) {
        var chip = e.target.closest(".chip");
        if (!chip) return;
        asortChipsEl.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        aSort = chip.getAttribute("data-asort") || "new";
        aShown = 18;
        renderArticles();
      });
    }

    /* 来源筛选 chips */
    var srcChipsEl = document.getElementById("asrc-chips");
    var srcs = [];
    catArticles.forEach(function (a) { if (a.s && srcs.indexOf(a.s) < 0) srcs.push(a.s); });
    function srcShort(s) {
      var m = { "结构分析表征": { zh: "主号", en: "Main" }, "光电子能谱分部": { zh: "XPS分部", en: "XPS" }, "单晶多晶衍射分部": { zh: "衍射分部", en: "XRD" } };
      var o = m[s];
      return o ? (lang === "en" ? o.en : o.zh) : s;
    }
    function buildSrcChips() {
      if (!srcChipsEl) return;
      if (srcs.length > 1) {
        var html = '<button class="chip active" data-asrc="all">' + t("chip.srcAll") + '</button>';
        srcs.forEach(function (sname) {
          html += '<button class="chip" data-asrc="' + esc(sname) + '">' + esc(srcShort(sname)) + "</button>";
        });
        srcChipsEl.innerHTML = html;
        srcChipsEl.style.display = "";
        srcChipsEl.onclick = function (e) {
          var chip = e.target.closest(".chip");
          if (!chip) return;
          srcChipsEl.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
          chip.classList.add("active");
          aSrc = chip.getAttribute("data-asrc") || "all";
          aShown = 18;
          renderArticles();
        };
      } else {
        srcChipsEl.style.display = "none";
      }
    }
    buildSrcChips();
    try {
      var qsrc = new URLSearchParams(location.search).get("src");
      if (qsrc && srcs.indexOf(qsrc) >= 0) {
        aSrc = qsrc;
        if (srcChipsEl) srcChipsEl.querySelectorAll(".chip").forEach(function (c) {
          c.classList.toggle("active", (c.getAttribute("data-asrc") || "all") === qsrc);
        });
      }
    } catch (e) {}

    /* 二级分类 chips（按板块标题聚类，仅 xps 启用） */
    var subChipsEl = document.getElementById("asub-chips");
    var subs = [];
    if (page === "xps") {
      var subCnt = {};
      catArticles.forEach(function (a) { var s = subOf(a); subCnt[s] = (subCnt[s] || 0) + 1; });
      subs = Object.keys(subCnt).filter(function (k) { return subCnt[k] >= 8; })
        .sort(function (x, y) { return subCnt[y] - subCnt[x]; });
    }
    function buildSubChips() {
      if (!subChipsEl) return;
      if (!subs.length) { subChipsEl.style.display = "none"; return; }
      var html = '<button class="chip active" data-asub="all">' + t("chip.subAll") + '</button>';
      subs.forEach(function (sname) {
        html += '<button class="chip" data-asub="' + esc(sname) + '">' + esc(sname) + "（" + subCnt[sname] + "）</button>";
      });
      subChipsEl.innerHTML = html;
      subChipsEl.style.display = "";
    }
    buildSubChips();
    if (subChipsEl && subs.length) {
      subChipsEl.addEventListener("click", function (e) {
        var chip = e.target.closest(".chip");
        if (!chip) return;
        subChipsEl.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        aSub = chip.getAttribute("data-asub") || "all";
        aShown = 18;
        renderArticles();
      });
    }

    /* 视图切换（列表 / 系列） */
    var viewChipsEl = document.getElementById("aview-chips");
    if (viewChipsEl) {
      viewChipsEl.addEventListener("click", function (e) {
        var chip = e.target.closest(".chip");
        if (!chip) return;
        viewChipsEl.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        aView = chip.getAttribute("data-aview") || "list";
        aShown = 18;
        renderArticles();
      });
    }

    /* 栏目内过滤框 */
    var catFilter = document.getElementById("cat-filter");
    if (catFilter) {
      var cfTimer = null;
      catFilter.addEventListener("input", function () {
        clearTimeout(cfTimer);
        cfTimer = setTimeout(function () {
          aKw = catFilter.value.trim().toLowerCase();
          aShown = 18;
          renderArticles();
        }, 180);
      });
    }

    var seriesOf = {};
    catArticles.forEach(function (a) {
      var k = seriesKey(a.t);
      if (!k) return;
      (seriesOf[k] = seriesOf[k] || []).push(a);
    });
    var seriesList = Object.keys(seriesOf).filter(function (k) { return seriesOf[k].length >= 4; })
      .sort(function (x, y) { return seriesOf[y].length - seriesOf[x].length; });

    function renderArticles() {
      try {
        window.__dbg = { aType: aType, aSrc: aSrc, aSub: aSub, aSort: aSort, aKw: aKw, aView: aView,
          catLen: catArticles.length, listLen: 0 };
      } catch (e) { window.__dbg = { err: e.message }; }
      var list = catArticles.filter(function (a) {
        if (!((aType === "all" || a.y === aType) && (aSrc === "all" || a.s === aSrc))) return false;
        if (aSub !== "all" && subOf(a) !== aSub) return false;
        if (aKw && a.t.toLowerCase().indexOf(aKw) < 0) return false;
        return true;
      });
      window.__dbg.listLen = list.length;
      if (aSort === "old") list = list.slice().reverse();
      document.getElementById("a-count").textContent = t("articles.count").replace("{n}", list.length);
      if (aView === "series" && seriesList.length) {
        /* 系列视图 */
        var html = '<p class="muted" style="grid-column:1/-1">' +
          (lang === "en" ? "Series with 4+ articles, click to view:" : "同一系列的教程已聚在一起，点击系列卡查看全部：") + "</p>";
        seriesList.forEach(function (k) {
          var g = seriesOf[k].slice().sort(function (x, y) { return x.d < y.d ? 1 : -1; });
          html += '<div class="series-block"><div class="series-head">' + esc(k) +
            ' <span class="count-badge">' + g.length + '</span></div><div class="series-items">';
          html += g.map(function (a) { return aCard(a, false); }).join("");
          html += "</div></div>";
        });
        aGrid.classList.add("series-mode");
        aGrid.innerHTML = html;
        var moreBtn = document.getElementById("amore");
        if (moreBtn) moreBtn.hidden = true;
        return;
      }
      aGrid.classList.remove("series-mode");
      /* 列表视图：年份分组 */
      var html = "";
      var lastYear = null;
      list.slice(0, aShown).forEach(function (a) {
        var y = (a.d || "").slice(0, 4);
        if (y && y !== lastYear) {
          html += '<div class="year-sep">' + y + "</div>";
          lastYear = y;
        }
        html += aCard(a, true);
      });
      aGrid.innerHTML = html ||
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
        aShown = 18;
        renderArticles();
      });
    }
    var moreBtn2 = document.getElementById("amore");
    if (moreBtn2) {
      moreBtn2.addEventListener("click", function () {
        aShown += 18;
        renderArticles();
      });
    }
    rerenderArticles = renderArticles;
  }

  function rerenderDynamic() {
    rerenderLatest();
    rerenderCat();
    if (typeof buildSrcChips === "function") buildSrcChips();
    if (typeof buildSubChips === "function") buildSubChips();
    rerenderArticles();
    rerenderSearch();
  }

  applyLang();
  rerenderDynamic();
})();
