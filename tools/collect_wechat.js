/* 公众号文章采集脚本（在已登录 mp.weixin.qq.com 的浏览器控制台运行）
 * 用法：
 * 1. 浏览器登录公众号后台（勾选"允许切换登录我的其他公众号"，可免扫码切换账号）
 * 2. 打开控制台(F12)粘贴本脚本回车 → 自动翻页采集当前账号的"发表记录"
 * 3. 完成后控制台执行 copy(JSON.stringify(window.__wxData)) 或按提示下载
 * 4. 保存为 tools/articles-<账号名>.json，运行 python tools/build.py
 * 采集内容：标题/链接/发布时间/封面/摘要，自动排除已删除与被屏蔽文章
 */
(function () {
  if (window.__wxCollect) { console.log("已在运行"); return; }
  var S = window.__wxCollect = { running: true, done: false, err: null, pages: 0, total: null,
    items: {}, account: (wx.commonData.data.real_nick_name || wx.commonData.data.nick_name || "") };
  var token = wx.commonData.data.token;
  var begin = 0;
  function pick(a) {
    return a.pic_cdn_url_235_1 || a.pic_cdn_url_16_9 || a.cover || "";
  }
  async function step() {
    try {
      if (begin > 6000) { S.err = "cap"; S.done = true; S.running = false; return; }
      var r = await fetch("/cgi-bin/appmsgpublish?sub=list&begin=" + begin +
        "&count=10&query=&type=101_1_102_103&show_type=&free_publish_type=1_102_103&sub_action=list_ex&search_card=0&token=" +
        token + "&lang=zh_CN&f=json&ajax=1", { credentials: "include" });
      var j = await r.json();
      if (!j.publish_page) { S.err = "ret=" + (j.base_resp && j.base_resp.ret); S.done = true; S.running = false; return; }
      var pp = JSON.parse(j.publish_page);
      S.total = pp.total_count;
      var list = pp.publish_list || [];
      S.pages++;
      if (!list.length) { S.done = true; S.running = false; return; }
      for (var it of list) {
        try {
          var info = JSON.parse(it.publish_info);
          for (var a of (info.appmsgex || [])) {
            if (a.link && !S.items[a.link] && !a.is_deleted && !a.ban_flag) {
              S.items[a.link] = {
                title: a.title, link: a.link, create_time: a.create_time,
                cover: pick(a), digest: (a.digest || "").trim(),
                show_type: a.item_show_type
              };
            }
          }
        } catch (e) { }
      }
      begin += 10;
      setTimeout(step, 600);
    } catch (e) { S.err = String(e); S.done = true; S.running = false; }
  }
  step();
  var timer = setInterval(function () {
    console.log("进度: %d 页 / %d 篇 / done=%s", S.pages, Object.keys(S.items).length, S.done);
    if (S.done) {
      clearInterval(timer);
      var out = { account: S.account, count: Object.keys(S.items).length,
                  articles: Object.values(S.items).sort(function (a, b) { return b.create_time - a.create_time; }) };
      window.__wxData = out;
      console.log("完成！执行 copy(JSON.stringify(window.__wxData)) 复制，保存为 tools/articles-<账号名>.json");
    }
  }, 3000);
})();
