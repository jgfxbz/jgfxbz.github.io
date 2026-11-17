# -*- coding: utf-8 -*-
"""轻量数据更新：只更新 data.js 的 videos / articles / 统计数字，不动 HTML 页面。
数据源：tools/videos_raw.json（fetch_bilibili.py 抓取）+ tools/articles-*.json（后台采集导出）
用法: python tools/update_data.py
"""
import json, sys, re, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
DATA = ROOT / 'assets' / 'js' / 'data.js'

def classify_article(title):
    t = (title or '').lower()
    if re.search(r'抽奖|中奖|荐购|快递|集运|维修|马到功成|分享图片|招生|招聘|审核制|直播|福利|节日|新年|中秋|国庆|^群$|^1$|群发测试', t):
        return 'noise'
    rules = [
        ('scxrd', r'单晶|olex|shelx|ccdc|绝对构型|晶体解析|晶体结构|孪晶|cif下载'),
        ('hrms', r'质谱|hrms|mass|xcalibur|masshunter|masslynx|peakview|sciex|sicex|代谢|mol文件'),
        ('xps', r'xps|ups|光电子|能谱|avantage|casa|xpspeak|peakforge|俄歇|功函数|结合能|灵敏度因子|多组分拟合|vgd|multipak|深度剖析'),
        ('xrd-powder', r'xrd|衍射|jade|highscore|gsas|rietveld|精修|粉末|多晶|物相|match!|profex|eva|endeavour|结晶度|靶材|cif|cod'),
        ('dataplot', r'origin|绘图|作图|python|脚本|红外|ir数据|pdf|物理地址|带隙|紫外|uv-vis|小工具|转换器|excel|git lfs|github 上传'),
    ]
    for cat, pat in rules:
        if re.search(pat, t):
            return cat
    return None

def classify_type(title):
    t = (title or '').lower()
    if re.search(r'文献|解读|lit\b', t): return 'lit'
    if re.search(r'原理|科普|什么是|的概念|概念与区别', t): return 'p'
    if re.search(r'安装|入门|初识|基本操作|简介|介绍|下载|开放下载|基本功能|常用功能', t): return 's'
    return 'a'

def main():
    m = re.search(r'window\.SITE_DATA = (\{.*\});?\s*$', DATA.read_text(encoding='utf-8'), re.S)
    data = json.loads(m.group(1))

    # 1. 视频：videos_raw.json → data.js videos
    raw_v = TOOLS / 'videos_raw.json'
    if raw_v.exists():
        vids = json.loads(raw_v.read_text(encoding='utf-8'))
        if isinstance(vids, dict):
            vids = vids.get('videos') or vids.get('list') or []
        old_map = {v['b']: v for v in data.get('videos', [])}
        new_vids = []
        for v in vids:
            b = v.get('bvid')
            old = old_map.get(b) or {}
            pub = v.get('pubdate') or 0
            dd = time.strftime('%Y-%m-%d', time.localtime(pub)) if pub else old.get('d', '')
            length = v.get('length') or 0
            s_txt = f"{length // 60}:{length % 60:02d}" if length else old.get('s', '')
            new_vids.append({'b': b, 't': v.get('title') or old.get('t', ''),
                             'c': v.get('category') or old.get('c', 'xps'),
                             'y': old.get('y', 'a'), 'd': dd,
                             's': old.get('s', ''), 'v': v.get('view') if v.get('view') is not None else old.get('v', 0),
                             'p': v.get('pic') or old.get('p', ''), 'g': old.get('g', '')})
        new_vids.sort(key=lambda x: x['d'], reverse=True)
        print(f"视频: {len(data.get('videos', []))} → {len(new_vids)}")
        data['videos'] = new_vids
        data['stats']['videos'] = len(new_vids)

    # 2. 文章：tools/articles-*.json（含预分类 c/y）→ data.js articles
    art_map = {}
    for fp in sorted(TOOLS.glob('articles-*.json')):
        try:
            batch = json.loads(fp.read_text(encoding='utf-8'))
        except Exception as e:
            print('skip article file:', fp.name, e); continue
        src = batch.get('account') or '公众号'
        for a in batch.get('articles') or []:
            link = a.get('link')
            title = (a.get('title') or '').strip()
            if not link or not title or link in art_map: continue
            ct = a.get('create_time') or 0
            dd = time.strftime('%Y-%m-%d', time.localtime(ct)) if ct else (a.get('d') or '')
            cat = a.get('c') or classify_article(title)
            if not cat or cat == 'noise': continue
            atype = a.get('y') or classify_type(title)
            art_map[link] = {'t': title, 'l': link, 'c': cat, 'y': atype,
                             'p': a.get('cover', ''), 'd': dd, 's': src,
                             'g': a.get('g', '')}
    old_cnt = len(data.get('articles', []))
    articles = sorted(art_map.values(), key=lambda x: x['d'], reverse=True)
    # 保留失效标记 g（手工核验的结果不被源文件覆盖）
    gmap = {a['l']: a['g'] for a in data.get('articles', []) if a.get('g')}
    for a in articles:
        if a['l'] in gmap and not a.get('g'): a['g'] = gmap[a['l']]
    print(f"文章: {old_cnt} → {len(articles)}")
    data['articles'] = articles
    data['stats']['articles'] = len(articles)

    data['generated'] = time.strftime('%Y-%m-%d %H:%M')
    new_js = ('<!-- 数据由 tools/update_data.py 自动更新，页面 HTML 不受影响 -->\n'
              if False else
              '// 自动生成于 %s（tools/update_data.py 数据更新），请勿手工编辑\n' % data['generated']) + \
             'window.SITE_DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n'
    DATA.write_text(new_js, encoding='utf-8')
    print('data.js 已更新（HTML 页面未动）:', len(new_js) // 1024, 'KB')

if __name__ == '__main__':
    main()
