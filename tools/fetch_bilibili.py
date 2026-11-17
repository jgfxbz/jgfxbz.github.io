# -*- coding: utf-8 -*-
"""抓取 B站 UP主「结构分析表征」(mid=386282560) 的全部视频数据。
输出: site/assets/data/videos_raw.json (原始数据)
"""
import json
import time
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path

MID = 386282560
OUT = Path(__file__).resolve().parent  # 原始数据存放在 tools/ 下，不随站点部署
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://space.bilibili.com/%d/" % MID,
    "Accept": "application/json",
}

# 合集名 -> 站点分类
CATEGORY_MAP = {
    "xps": "xps", "ups": "xps", "avantage": "xps", "xpspeak": "xps",
    "casaXPS": "xps", "XPS光电子能谱": "xps",
    "粉末衍射": "xrd-powder", "多晶衍射\\粉末衍射": "xrd-powder",
    "单晶衍射": "scxrd", "单晶解析": "scxrd", "microED": "scxrd",
    "高分辨质谱": "hrms",
    "origin": "dataplot", "绘图": "dataplot", "python": "dataplot",
    "book": "other", "IRMS": "other", "直播回放": "other", "其他": "other",
}


def api_get(url, params=None, retries=4, ok_codes=(0,)):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            if data.get("code") in ok_codes:
                return data["data"]
            last = data.get("code")
            # 风控/限流，指数退避重试
            time.sleep(min(3 * (2 ** i), 30))
        except Exception as e:
            last = repr(e)
            time.sleep(min(3 * (2 ** i), 30))
    raise RuntimeError("API failed (%s): %s" % (last, url))


# ---------- 合集 / 播放列表 ----------
def get_collections():
    d = api_get("https://api.bilibili.com/x/polymer/web-space/seasons_series_list",
                {"mid": MID, "page_num": 1, "page_size": 20})
    il = d.get("items_lists") or {}
    cols = []
    for s in il.get("seasons_list") or []:
        m = s.get("meta") or {}
        cols.append({"kind": "season", "id": m["season_id"], "name": m.get("title") or m.get("name", ""),
                     "total": m.get("total", 0)})
    for s in il.get("series_list") or []:
        m = s.get("meta") or {}
        cols.append({"kind": "series", "id": m["series_id"], "name": m.get("name", ""), "total": m.get("total", 0)})
    return cols


def get_season_videos(season_id):
    out, page = [], 1
    while True:
        d = api_get("https://api.bilibili.com/x/polymer/web-space/seasons_archives_list",
                    {"mid": MID, "season_id": season_id, "page_num": page, "page_size": 100})
        archs = d.get("archives") or []
        for a in archs:
            out.append({
                "bvid": a.get("bvid", ""),
                "title": (a.get("title") or "").strip(),
                "pubdate": a.get("pubdate") or a.get("ctime", 0),
                "length": a.get("duration", 0),
                "view": (a.get("stat") or {}).get("view", 0),
                "pic": (a.get("pic") or "").replace("http://", "https://"),
            })
        total = (d.get("page") or {}).get("total", 0)
        if len(out) >= total or not archs:
            break
        page += 1
        time.sleep(0.4)
    return out


def get_series_videos(series_id):
    out, pn = [], 1
    while True:
        d = api_get("https://api.bilibili.com/x/series/archives",
                    {"mid": MID, "series_id": series_id, "pn": pn, "ps": 100})
        archs = d.get("archives") or []
        for a in archs:
            out.append({
                "bvid": a.get("bvid", ""),
                "title": (a.get("title") or "").strip(),
                "pubdate": a.get("pubdate") or a.get("ctime", 0),
                "length": a.get("duration", 0),
                "view": (a.get("stat") or {}).get("view", 0),
                "pic": (a.get("pic") or "").replace("http://", "https://"),
            })
        total = d.get("total", 0)
        if len(out) >= total or not archs:
            break
        pn += 1
        time.sleep(0.4)
    return out


# ---------- 全部视频列表 (wbi 签名, 用于补齐未加入合集的视频) ----------
MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5,
             49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55,
             40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57,
             62, 11, 36, 20, 34, 44, 52]


def wbi_sign(params, img_key, sub_key):
    mixin = "".join((img_key + sub_key)[i] for i in MIXIN_TAB)[:32]
    p = dict(params)
    p["wts"] = int(time.time())
    p = {k: str(v).replace("!", "").replace("'", "").replace("(", "").replace(")", "").replace("*", "")
         for k, v in p.items()}
    q = urllib.parse.urlencode(dict(sorted(p.items())))
    p["w_rid"] = hashlib.md5((q + mixin).encode()).hexdigest()
    return p


def get_all_videos_wbi():
    # 未登录时 code=-101，但 data.wbi_img 仍然可用
    nav = api_get("https://api.bilibili.com/x/web-interface/nav", ok_codes=(0, -101))
    img = nav["wbi_img"]["img_url"].rsplit("/", 1)[1].split(".")[0]
    sub = nav["wbi_img"]["sub_url"].rsplit("/", 1)[1].split(".")[0]
    out, pn = [], 1
    while True:
        params = wbi_sign({"mid": MID, "order": "pubdate", "pn": pn, "ps": 50}, img, sub)
        d = api_get("https://api.bilibili.com/x/space/wbi/arc/search", params)
        vlist = (d.get("list") or {}).get("vlist") or []
        for a in vlist:
            out.append({
                "bvid": a.get("bvid", ""),
                "title": (a.get("title") or "").strip(),
                "pubdate": a.get("created", 0),
                "length": a.get("length", "0:00"),  # 字符串 mm:ss
                "view": a.get("play", 0),
            })
        vtotal = d.get("page", {}).get("count", 0)
        if len(out) >= vtotal or not vlist:
            break
        pn += 1
        time.sleep(0.5)
    return out, vtotal


def length_to_sec(s):
    if isinstance(s, (int, float)):
        return int(s)
    parts = [int(x) for x in str(s).split(":")]
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def main():
    cols = get_collections()
    print("collections:", [(c["name"], c["total"]) for c in cols])

    # 合并模式：以上次数据为基础，成功的合集覆盖更新，失败的保留旧数据
    fp = OUT / "videos_raw.json"
    base = {}
    if fp.exists():
        try:
            for v in json.loads(fp.read_text(encoding="utf-8"))["videos"]:
                base[v["bvid"]] = v
        except Exception as e:
            print("base load failed, 从零开始:", e)
    videos = base

    ok_cols, fail_cols = [], []
    for c in cols:
        try:
            items = get_season_videos(c["id"]) if c["kind"] == "season" else get_series_videos(c["id"])
        except Exception as e:
            print("SKIP(保留旧数据)", c["name"], str(e)[:80])
            fail_cols.append(c["name"])
            continue
        ok_cols.append(c["name"])
        print("  %-14s -> %d videos" % (c["name"], len(items)))
        cat = CATEGORY_MAP.get(c["name"], "other")
        for it in items:
            old = videos.get(it["bvid"], {})
            v = dict(old)
            v.update(it)
            v["category"] = cat
            v["collections"] = old.get("collections") or []
            if c["name"] not in v["collections"]:
                v["collections"].append(c["name"])
            videos[it["bvid"]] = v
        time.sleep(0.8)

    no_pic = sum(1 for v in videos.values() if not v.get("pic"))
    data = {
        "mid": MID,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_bilibili": len(videos),
        "videos": sorted(videos.values(), key=lambda x: -(x["pubdate"] or 0)),
    }
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved:", fp, "videos:", len(videos), "| no_pic:", no_pic)
    print("ok collections:", ok_cols)
    if fail_cols:
        print("FAILED collections (旧数据已保留，可稍后重跑):", fail_cols)
    # 打印未分组视频标题，便于人工归类
    others = [v for v in videos.values() if v["category"] == "other"]
    print("---- other/未分组 (%d) ----" % len(others))
    for v in others[:60]:
        print(" ", v["collections"], v["title"])


if __name__ == "__main__":
    main()
