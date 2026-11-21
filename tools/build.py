# -*- coding: utf-8 -*-
"""构建静态站点 jgfxbz.github.io：
1. 读取 tools/videos_raw.json（由 fetch_bilibili.py 生成）
2. 读取可选的 tools/articles.json（公众号图文，手工维护）
3. 生成 assets/js/data.js（含视频数据 + 中英文案）和全部 HTML 页面
用法: python tools/build.py
"""
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # 修复: 工具链入库后, 仓库根即站点根(原多写的 /jgfxbz.github.io 使构建写进嵌套目录)
RAW = Path(__file__).resolve().parent / "videos_raw.json"

EMAIL = "jgfxbz@gmail.com"
BILI = "https://space.bilibili.com/386282560"

# ---------------- 中英文案 ----------------
I18N = {
    # 导航 / 页面标题
    "nav.home": {"zh": "首页", "en": "Home"},
    "nav.xps": {"zh": "XPS / UPS", "en": "XPS / UPS"},
    "nav.xrd": {"zh": "粉末衍射", "en": "Powder XRD"},
    "nav.scxrd": {"zh": "单晶衍射", "en": "SC-XRD"},
    "nav.hrms": {"zh": "高分辨质谱", "en": "HRMS"},
    "nav.dataplot": {"zh": "数据与绘图", "en": "Data & Plotting"},
    "nav.coop": {"zh": "商务合作", "en": "Business"},
    "nav.about": {"zh": "关于", "en": "About"},
    "title.index": {"zh": "结构分析表征 · XPS/XRD/HRMS 数据分析教程导航 — 结构分析表征",
                    "en": "结构分析表征 · XPS/XRD/HRMS Data-Analysis Tutorials"},
    "title.xps": {"zh": "XPS / UPS 光电子能谱教程 — 结构分析表征",
                  "en": "XPS / UPS Tutorials — 结构分析表征"},
    "title.xrd-powder": {"zh": "粉末衍射教程 — 结构分析表征",
                         "en": "Powder XRD Tutorials — 结构分析表征"},
    "title.scxrd": {"zh": "单晶衍射教程 — 结构分析表征",
                    "en": "Single-Crystal XRD Tutorials — 结构分析表征"},
    "title.hrms": {"zh": "高分辨质谱教程 — 结构分析表征",
                   "en": "HRMS Tutorials — 结构分析表征"},
    "title.dataplot": {"zh": "数据处理与绘图教程 — 结构分析表征",
                       "en": "Data Processing & Plotting Tutorials — 结构分析表征"},
    "title.coop": {"zh": "商务合作 — 结构分析表征", "en": "Business — 结构分析表征"},
    "title.about": {"zh": "关于 — 结构分析表征", "en": "About — 结构分析表征"},
    # 首页
    "hero.sub": {"zh": "XPS · UPS · XRD · HRMS 的数据分析教程合集 —— 把每一个谱图讲明白",
                 "en": "Data-analysis tutorials for XPS · UPS · XRD · HRMS — making every spectrum make sense."},
    "stat.videos": {"zh": "视频教程", "en": "Video tutorials"},
    "stat.cats": {"zh": "仪器类别", "en": "Instrument categories"},
    "stat.accounts": {"zh": "公众号矩阵", "en": "WeChat accounts"},
    "stat.views": {"zh": "累计播放", "en": "Total views"},
    "cta.bili": {"zh": "B 站主页 ↗", "en": "Bilibili ↗"},
    "cta.coop": {"zh": "商务合作", "en": "Business"},
    "home.cats": {"zh": "按仪器类别浏览", "en": "Browse by Instrument"},
    "home.latest": {"zh": "最新更新", "en": "Latest Updates"},
    "home.accounts": {"zh": "账号矩阵", "en": "Our Accounts"},
    "acc1.t": {"zh": "结构分析表征", "en": "结构分析表征"},
    "acc1.tag": {"zh": "主号", "en": "Main"},
    "acc1.desc": {"zh": "总号：XPS、UPS、HRMS、PXRD、SXRD 等表征数据分析教程汇总。",
                  "en": "Main account: tutorials for characterization data analysis covering XPS, UPS, HRMS, PXRD, SXRD, etc."},
    "acc2.t": {"zh": "光电子能谱分部", "en": "光电子能谱分部"},
    "acc2.tag": {"zh": "XPS 专号", "en": "XPS"},
    "acc2.desc": {"zh": "XPS / UPS 数据分析深度图文，配套出版《光电子能谱数据分析从入门到精通》。",
                  "en": "In-depth XPS / UPS articles; companion book Photoelectron Spectroscopy Data Analysis (PKU Press)."},
    "acc3.t": {"zh": "单晶多晶衍射分部", "en": "单晶多晶衍射分部"},
    "acc3.tag": {"zh": "XRD 专号", "en": "XRD"},
    "acc3.desc": {"zh": "单晶 / 粉末衍射的软件实操、解析与精修图文教程。",
                  "en": "Single-crystal & powder diffraction software tutorials and articles."},
    "acc4.t": {"zh": "B 站 · 结构分析表征", "en": "Bilibili · 结构分析表征"},
    "acc4.tag": {"zh": "视频", "en": "Video"},
    "acc4.desc": {"zh": "全部视频教程在此发布，点击站内视频卡片可直接播放。",
                  "en": "All video tutorials live here — click any video card to play on-site."},
    # 分类页通用
    "sec.software": {"zh": "软件介绍", "en": "Software Guide"},
    "sec.software.sub": {"zh": "点击软件卡片可筛选该软件的相关视频",
                         "en": "Click a software card to filter its videos"},
    "sec.videos": {"zh": "视频教程", "en": "Video Tutorials"},
    "videos.count": {"zh": "共 {n} 个", "en": "{n} in total"},
    "chip.all": {"zh": "全部", "en": "All"},
    "chip.a": {"zh": "数据分析", "en": "Data Analysis"},
    "chip.s": {"zh": "软件介绍", "en": "Software Guide"},
    "chip.p": {"zh": "原理科普", "en": "Principles"},
    "chip.lit": {"zh": "文献解读", "en": "Literature"},
    "type.a": {"zh": "数据分析", "en": "Data Analysis"},
    "type.s": {"zh": "软件介绍", "en": "Software Guide"},
    "type.p": {"zh": "原理科普", "en": "Principles"},
    "type.lit": {"zh": "文献解读", "en": "Literature"},
    "articles.count": {"zh": "共 {n} 篇", "en": "{n} in total"},
    "articles.source": {"zh": "来源", "en": "Source"},
    "nav.scripts": {"zh": "脚本工具", "en": "Scripts"},
    "title.scripts": {"zh": "脚本工具 — 结构分析表征", "en": "Scripts & Tools — 结构分析表征"},
    "nav.search": {"zh": "搜索", "en": "Search"},
    "title.search": {"zh": "站内搜索 — 结构分析表征", "en": "Search — 结构分析表征"},
    "search.desc": {"zh": "全站搜索：一次检索全部视频教程与公众号图文。",
                    "en": "Search all video tutorials and WeChat articles at once."},
    "search.ph2": {"zh": "输入关键词，如：拟合 / 结晶度 / 代谢 / 精修 …",
                   "en": "Type a keyword, e.g. fitting / crystallinity / metabolite …"},
    "search.results": {"zh": "共 {n} 条结果", "en": "{n} results"},
    "footer.updated": {"zh": "更新于", "en": "Updated"},
    "nav.literature": {"zh": "文献解读", "en": "Literature"},
    "title.literature": {"zh": "文献解读 — 结构分析表征", "en": "Literature Reading — 结构分析表征"},
    "literature.desc": {"zh": "文献精读与科研资讯：团队与同行的趣味文献解读、领域前沿速览，持续更新。",
                        "en": "Paper reading and research news: literature interpretations and frontier overviews, updated regularly."},
    "scripts.desc": {"zh": "团队自研的免费小工具与脚本，全部开源在 GitHub，配套 B 站视频教程。欢迎按需取用。",
                     "en": "Free in-house tools and scripts, all open-source on GitHub with Bilibili video tutorials."},
    "scripts.github": {"zh": "GitHub 仓库 ↗", "en": "GitHub repo ↗"},
    "scripts.video": {"zh": "▶ 视频教程", "en": "▶ Video tutorial"},
    "scripts.note": {"zh": "工具持续更新中，使用问题欢迎通过公众号或邮件反馈。",
                     "en": "Tools are updated regularly. Feedback welcome via WeChat or email."},
    "scripts.s1.t": {"zh": "XPS 深度剖析数据转 Excel", "en": "XPS Depth Profile → Excel"},
    "scripts.s1.d": {"zh": "将 Thermo Fisher XPS 深度剖析（depth profile）数据一键转换为 Excel 表格，方便后续作图与定量分析。",
                     "en": "Convert Thermo Fisher XPS depth-profile data to Excel in one click for plotting and quantification."},
    "scripts.s1.tag": {"zh": "XPS", "en": "XPS"},
    "scripts.s2.t": {"zh": "HRMS Metabolite Explorer", "en": "HRMS Metabolite Explorer"},
    "scripts.s2.d": {"zh": "高分辨质谱代谢产物分析软件（v2.9）：母体信息查找、批量提取分子式与代谢产物筛查，开放试用。",
                     "en": "HRMS metabolite analysis software (v2.9): parent-ion lookup, batch formula extraction and screening. Free trial."},
    "scripts.s2.tag": {"zh": "质谱", "en": "HRMS"},
    "scripts.s3.t": {"zh": "Metabolic-Analysis", "en": "Metabolic-Analysis"},
    "scripts.s3.d": {"zh": "高分辨质谱代谢产物分析软件，配合 vgd-excel 数据转换使用。",
                     "en": "HRMS metabolic analysis suite, works together with the vgd-excel converter."},
    "scripts.s3.tag": {"zh": "质谱", "en": "HRMS"},
    "scripts.s4.t": {"zh": "d 带 / p 带态密度计算脚本", "en": "d/p-band DOS Calculator"},
    "scripts.s4.d": {"zh": "基于价带（UPS）数据计算 d 带 / p 带中心与态密度（DOS），用于催化与电子结构分析。",
                     "en": "Compute d/p-band centers and DOS from valence-band (UPS) data for catalysis and electronic-structure studies."},
    "scripts.s4.tag": {"zh": "UPS", "en": "UPS"},
    "scripts.s5.t": {"zh": "粉末衍射精修工具手册 v8.1.1", "en": "Powder Diffraction Refinement Manual v8.1.1"},
    "scripts.s5.d": {"zh": "粉末衍射精修工具的用户手册与说明文档。",
                     "en": "User manual and documentation for the powder-diffraction refinement tool."},
    "scripts.s5.tag": {"zh": "XRD", "en": "XRD"},
    "scripts.s6.t": {"zh": "化合物 mol 文件批量下载", "en": "mol-file Batch Downloader"},
    "scripts.s6.d": {"zh": "按化合物名批量下载 mol 文件，配合质谱与代谢产物分析流程使用。",
                     "en": "Batch-download mol files by compound name; handy for MS and metabolite workflows."},
    "scripts.s6.tag": {"zh": "工具", "en": "Utility"},
    "scripts.s7.t": {"zh": "PDF 页面删除工具", "en": "PDF Page Splitter"},
    "scripts.s7.d": {"zh": "删除 PDF 中指定页面的轻量小工具（如去除材料中的无关页）。",
                     "en": "Lightweight tool to remove selected pages from a PDF."},
    "scripts.s7.tag": {"zh": "工具", "en": "Utility"},
    "coop.more": {"zh": "查看完整商务合作页 →", "en": "View full business page →"},
    "search.ph": {"zh": "搜索视频标题，如：拟合 / jade / 精修 …",
                  "en": "Search video titles, e.g. fitting / jade / refine …"},
    "sw.n": {"zh": "{n} 个相关视频 →", "en": "{n} related videos →"},
    "sw.none": {"zh": "相关视频整理中", "en": "Related videos coming soon"},
    "load.more": {"zh": "加载更多", "en": "Load more"},
    "empty": {"zh": "没有匹配的视频，换个关键词试试（如：拟合 / 精修 / jade / avantage）。",
              "en": "No matching videos — try another keyword (e.g. fitting / refine / jade / avantage)."},
    "sec.articles": {"zh": "图文教程 · 公众号", "en": "Articles · WeChat"},
    "cat.art2": {"zh": "现有图文请先移步微信公众号阅读；站点维护者把文章链接按 tools/articles.json 的格式填好后重新构建即可自动展示。",
                 "en": "Articles are currently on WeChat. Maintainers: add links to tools/articles.json and rebuild to display them here."},
    "bili.more1": {"zh": "以上只是本站收录的合集内容，", "en": "The above lists curated collections — "},
    "bili.more2": {"zh": "全部视频（含未分组）请移步 B 站主页", "en": "for ALL videos please visit the Bilibili homepage"},
    "modal.open": {"zh": "在 B 站打开（点赞投币收藏）↗", "en": "Open on Bilibili (like, coin, favourite) ↗"},
    "footer.bili": {"zh": "B站主页", "en": "Bilibili"},
    # 商务合作
    "coop.desc": {"zh": "欢迎高校课题组、测试平台、仪器厂商与软件厂商洽谈合作。",
                  "en": "Welcome inquiries from research groups, testing platforms, instrument and software vendors."},
    "coop.c1.t": {"zh": "数据分析服务", "en": "Data-Analysis Service"},
    "coop.c1.d": {"zh": "XPS / XRD / HRMS 等谱图的数据分析、分峰拟合与结果解读。",
                  "en": "Data analysis, peak fitting and interpretation for XPS / XRD / HRMS spectra."},
    "coop.c2.t": {"zh": "课程与培训", "en": "Courses & Training"},
    "coop.c2.d": {"zh": "仪器分析软件实操培训、线上课程定制（B 站已有 61 课时付费专栏）。",
                  "en": "Hands-on software training and custom online courses (61 paid lessons on Bilibili)."},
    "coop.c3.t": {"zh": "内容合作", "en": "Content Collaboration"},
    "coop.c3.d": {"zh": "仪器 / 软件 / 测试平台的内容推广、测评与合作视频。",
                  "en": "Promotion, reviews and co-produced videos for instruments, software and testing platforms."},
    "coop.c4.t": {"zh": "图文定制", "en": "Writing & Customization"},
    "coop.c4.d": {"zh": "公众号矩阵（主号 + 两个分部）的科普图文与软文合作。",
                  "en": "Science articles and sponsored posts across our WeChat account matrix."},
    "contact.h2": {"zh": "联系方式", "en": "Contact"},
    "contact.p1": {"zh": "商务合作请邮件联系：", "en": "For business inquiries, email: "},
    "contact.wechat": {"zh": "微信号：", "en": "WeChat: "},
    "contact.p2": {"zh": "合作意向请说明：合作类型 + 需求描述 + 联系方式，收到后会尽快回复。",
                   "en": "Please include: cooperation type + requirements + your contact info. We reply as soon as possible."},
    "qr.main": {"zh": "公众号 · 结构分析表征", "en": "WeChat · 结构分析表征"},
    "qr.xps": {"zh": "公众号 · 光电子能谱分部", "en": "WeChat · 光电子能谱分部"},
    "qr.xrd": {"zh": "公众号 · 单晶多晶衍射分部", "en": "WeChat · 单晶多晶衍射分部"},
    "qr.bili": {"zh": "B站 · 结构分析表征", "en": "Bilibili · 结构分析表征"},
    # 关于
    "about.p1": {"zh": "「结构分析表征」是一个聚焦材料结构分析表征数据处理的科普团队，运营三个微信公众号与同名 B 站账号，长期输出 XPS / UPS / XRD / HRMS 等表征技术的数据分析与软件实操教程。",
                 "en": "结构分析表征 is a science-communication team focused on data processing for materials characterization, running three WeChat accounts and a Bilibili channel with long-running tutorials on XPS / UPS / XRD / HRMS data analysis and software."},
    "about.h2a": {"zh": "我们是谁", "en": "Who We Are"},
    "about.li1": {"zh": "公众号「结构分析表征」：主号，覆盖各表征技术的数据分析教程；",
                  "en": "WeChat 结构分析表征: the main account, covering data-analysis tutorials across techniques;"},
    "about.li2": {"zh": "公众号「光电子能谱分部」：XPS / UPS 深度图文；",
                  "en": "WeChat 光电子能谱分部: in-depth XPS / UPS articles;"},
    "about.li3": {"zh": "公众号「单晶多晶衍射分部」：单晶与粉末衍射教程；",
                  "en": "WeChat 单晶多晶衍射分部: single-crystal & powder diffraction tutorials;"},
    "about.li4": {"zh": "B 站「结构分析表征」：视频教程（含 61 课时付费专栏《光电子能谱多种软件使用》）。",
                  "en": "Bilibili 结构分析表征: video tutorials (incl. the 61-lesson paid course on photoelectron-spectroscopy software)."},
    "about.h2b": {"zh": "出版物", "en": "Publications"},
    "about.pub": {"zh": "《光电子能谱数据分析从入门到精通》—— 李焕勇 著，北京大学出版社（ISBN 9787301366752）。",
                  "en": "Photoelectron Spectroscopy Data Analysis: From Beginner to Expert (《光电子能谱数据分析从入门到精通》) — by Li Huanyong, Peking University Press (ISBN 9787301366752)."},
    "about.h2c": {"zh": "关于本站", "en": "About This Site"},
    "about.site": {"zh": "本站是四个平台内容的导航目录：视频直接内嵌 B 站播放器，图文教程以公众号原文链接收录。分类为仪器类别 →（软件介绍 / 数据分析 / 原理科普 / 图文教程）两级结构，欢迎收藏使用。",
                   "en": "This site is a navigation hub for the four platforms: videos are embedded from Bilibili, articles link back to WeChat. Content is organized in two levels: instrument category → (software guide / data analysis / principles / articles)."},
}

# ---------------- 站点分类定义 ----------------
CATS = {
    "xps": {
        "nav": "nav.xps", "title_key": "title.xps",
        "title": "XPS / UPS 光电子能谱", "en": "Photoelectron Spectroscopy",
        "desc": "X 射线光电子能谱 / 紫外光电子能谱的数据分析、分峰拟合与软件实操教程，覆盖 Avantage、CasaXPS、XPSPEAK、PeakForge 等主流软件。",
        "desc_en": "Data-analysis and peak-fitting tutorials for X-ray / UV photoelectron spectroscopy, covering Avantage, CasaXPS, XPSPEAK, PeakForge and more.",
        "snip_en": "Data-analysis and peak-fitting tutorials for XPS / UPS.",
        "journals": "《光电子能谱分部》《结构分析表征》",
        "journals_en": "光电子能谱分部 & 结构分析表征",
        "software": [
            {"name": "Avantage", "name_en": "Avantage", "vendor": "Thermo Fisher 原厂", "vendor_en": "Thermo Fisher",
             "desc": "峰拟合、元素半定量、俄歇参数与功函数校正等全流程操作。",
             "desc_en": "Peak fitting, semi-quantification, Auger parameter and work-function correction — the full workflow.", "kw": ["avantage"]},
            {"name": "CasaXPS", "name_en": "CasaXPS", "vendor": "Case Software", "vendor_en": "Case Software",
             "desc": "国际通用的 XPS 数据处理软件，深度序列处理与定量。",
             "desc_en": "The internationally standard XPS processing package for deep batch processing and quantification.", "kw": ["casaxps"]},
            {"name": "XPSPEAK", "name_en": "XPSPEAK", "vendor": "免费经典", "vendor_en": "Free classic",
             "desc": "经典的免费分峰拟合软件，上手简单。",
             "desc_en": "Classic free peak-fitting software, easy to start.", "kw": ["xpspeak", "xps peak"]},
            {"name": "PeakForge", "name_en": "PeakForge", "vendor": "新一代拟合工具", "vendor_en": "Modern fitting tool",
             "desc": "内置拟合参数的多组分拟合软件，降低拟合门槛。",
             "desc_en": "Multi-component fitting with built-in start parameters — lowers the barrier.", "kw": ["peakforge"]},
        ],
    },
    "xrd-powder": {
        "nav": "nav.xrd", "title_key": "title.xrd-powder",
        "title": "粉末 / 多晶 X 射线衍射", "en": "Powder XRD",
        "desc": "粉末 XRD 从数据导入、物相检索到 Rietveld 精修的全流程：Jade、HighScore、Match!、GSAS-II、Profex 等软件实操，以及 CIF 文件获取系列。",
        "desc_en": "The full powder-XRD workflow from data import and phase ID to Rietveld refinement: Jade, HighScore, Match!, GSAS-II, Profex, plus the CIF-download series.",
        "snip_en": "The full powder-XRD workflow: phase ID to Rietveld refinement.",
        "journals": "《单晶多晶衍射分部》《结构分析表征》",
        "journals_en": "单晶多晶衍射分部 & 结构分析表征",
        "software": [
            {"name": "Jade", "name_en": "Jade", "vendor": "MDI", "vendor_en": "MDI",
             "desc": "物相检索、基线调平、结晶度计算、2θ 校正、靶材转换。",
             "desc_en": "Phase ID, baseline leveling, crystallinity, 2θ correction, target conversion.", "kw": ["jade"]},
            {"name": "HighScore (Plus)", "name_en": "HighScore (Plus)", "vendor": "Malvern Panalytical", "vendor_en": "Malvern Panalytical",
             "desc": "物相鉴定与全谱拟合分析。", "desc_en": "Phase identification and whole-powder-pattern fitting.", "kw": ["highscore"]},
            {"name": "GSAS-II", "name_en": "GSAS-II", "vendor": "开源", "vendor_en": "Open source",
             "desc": "开源 Rietveld 精修软件的基本操作。", "desc_en": "Open-source Rietveld refinement — the basics.", "kw": ["gsas"]},
            {"name": "Profex", "name_en": "Profex", "vendor": "开源 (BGMN)", "vendor_en": "Open source (BGMN)",
             "desc": "带图形界面的 Rietveld 精修软件。", "desc_en": "GUI front-end for BGMN Rietveld refinement.", "kw": ["profex"]},
            {"name": "Match!", "name_en": "Match!", "vendor": "Crystal Impact", "vendor_en": "Crystal Impact",
             "desc": "物相鉴定与相分析。", "desc_en": "Search-match phase identification.", "kw": ["match!"]},
            {"name": "DIFFRAC.EVA", "name_en": "DIFFRAC.EVA", "vendor": "Bruker", "vendor_en": "Bruker",
             "desc": "文本 XRD 数据的打开与分析。", "desc_en": "Open and analyze ASCII XRD data.", "kw": ["eva"]},
            {"name": "Endeavour", "name_en": "Endeavour", "vendor": "Crystal Impact", "vendor_en": "Crystal Impact",
             "desc": "由粉末衍射数据解析晶体结构。", "desc_en": "Solve crystal structures from powder data.", "kw": ["endeavour"]},
            {"name": "CIF 文件获取", "name_en": "CIF Files", "vendor": "数据库系列", "vendor_en": "Databases",
             "desc": "Materials Project / COD / CCDC / FindIt 下载晶体文件。",
             "desc_en": "Download crystal structures from Materials Project / COD / CCDC / FindIt.", "kw": ["cif"]},
        ],
    },
    "scxrd": {
        "nav": "nav.scxrd", "title_key": "title.scxrd",
        "title": "单晶 X 射线衍射", "en": "Single Crystal XRD",
        "desc": "单晶结构解析与精修：Olex2 解析实例、CCDC 晶体数据库、CIF 文件下载、绝对构型判定、衍射中心确认与堆积图绘制。",
        "desc_en": "Single-crystal structure solution and refinement: Olex2 worked examples, CCDC database, CIF downloads, absolute configuration, cell checks and stacking plots.",
        "snip_en": "Structure solution & refinement with Olex2, CCDC and more.",
        "journals": "《单晶多晶衍射分部》《结构分析表征》",
        "journals_en": "单晶多晶衍射分部 & 结构分析表征",
        "software": [
            {"name": "Olex2", "name_en": "Olex2", "vendor": "OlexSys", "vendor_en": "OlexSys",
             "desc": "结构解析与精修图形界面：解析实例、孔洞率计算、π-π 堆积图绘制。",
             "desc_en": "GUI for structure solution & refinement: worked examples, void calculation, π–π stacking plots.", "kw": ["olex2"]},
            {"name": "SHELX", "name_en": "SHELX", "vendor": "配合 Olex2 使用", "vendor_en": "Used with Olex2",
             "desc": "经典的晶体结构解析 / 精修引擎。", "desc_en": "The classic crystallographic solution / refinement engine.", "kw": ["shelx", "shelxt", "shelxl"]},
            {"name": "CCDC / Mercury", "name_en": "CCDC / Mercury", "vendor": "CCDC", "vendor_en": "CCDC",
             "desc": "晶体数据库检索、客户端使用与更新包安装。", "desc_en": "CSD database access, client usage and update installation.", "kw": ["ccdc", "mercury"]},
            {"name": "CIF 与实用脚本", "name_en": "CIF & Utilities", "vendor": "实用系列", "vendor_en": "Utility series",
             "desc": "文献 CIF 下载、衍射中心确认脚本、绝对构型判定。",
             "desc_en": "Download CIFs from papers, cell-check scripts, absolute configuration.", "kw": ["cif", "衍射中心", "绝对构型"]},
        ],
    },
    "hrms": {
        "nav": "nav.hrms", "title_key": "title.hrms",
        "title": "高分辨质谱 (HRMS)", "en": "High-Resolution Mass Spectrometry",
        "desc": "高分辨质谱数据处理：精确分子量与质荷比计算、二级碎片模拟、定量分析与未知物筛查，覆盖 Thermo / Agilent / Waters / SCIEX 各家软件。",
        "desc_en": "HRMS data processing: accurate mass, MS/MS fragment simulation, quantification and unknown screening across Thermo / Agilent / Waters / SCIEX software.",
        "snip_en": "Accurate mass, MS/MS simulation, quantification and screening.",
        "journals": "《结构分析表征》",
        "journals_en": "结构分析表征",
        "software": [
            {"name": "Xcalibur", "name_en": "Xcalibur", "vendor": "Thermo Fisher", "vendor_en": "Thermo Fisher",
             "desc": "标准质谱图导出与数据处理。", "desc_en": "Export standard MS spectra and process data.", "kw": ["xcalibur"]},
            {"name": "MassHunter", "name_en": "MassHunter", "vendor": "Agilent", "vendor_en": "Agilent",
             "desc": "精确分子量与质荷比计算。", "desc_en": "Accurate mass and m/z calculations.", "kw": ["masshunter"]},
            {"name": "MassLynx", "name_en": "MassLynx", "vendor": "Waters", "vendor_en": "Waters",
             "desc": "安装与基本操作。", "desc_en": "Installation and basic operations.", "kw": ["masslynx"]},
            {"name": "PeakView", "name_en": "PeakView", "vendor": "SCIEX", "vendor_en": "SCIEX",
             "desc": "二级碎片模拟、信噪比与积分面积计算。", "desc_en": "MS/MS fragment simulation, S/N and area integration.", "kw": ["peakview"]},
            {"name": "SCIEX OS", "name_en": "SCIEX OS", "vendor": "SCIEX", "vendor_en": "SCIEX",
             "desc": "定量分析与未知物筛查、常用功能与使用技巧。", "desc_en": "Quantification and unknown screening, tips & tricks.", "kw": ["sciex os", "sicex os"]},
            {"name": "TIC / XIC / BPC", "name_en": "TIC / XIC / BPC", "vendor": "概念科普", "vendor_en": "Concepts",
             "desc": "质谱分析中三种色谱峰的概念与区别。", "desc_en": "TIC vs XIC vs BPC — concepts and differences.", "kw": ["tic", "xic", "bpc"]},
        ],
    },
    "dataplot": {
        "nav": "nav.dataplot", "title_key": "title.dataplot",
        "title": "数据处理与绘图", "en": "Data Processing & Plotting",
        "desc": "Origin 作图与数据处理的常见问题（断点、曲线填充、峰拟合、微分、版本转换），以及自研 Python 小脚本：CIF 下载、红外基线校正、mol 文件批量下载等。",
        "desc_en": "Common Origin plotting / data issues (breaks, filling, peak fitting, derivatives, version conversion), plus in-house Python scripts: CIF download, IR baseline correction, mol-file batch download and more.",
        "snip_en": "Origin plotting fixes and in-house Python scripts.",
        "journals": "《结构分析表征》",
        "journals_en": "结构分析表征",
        "software": [
            {"name": "Origin", "name_en": "Origin", "vendor": "OriginLab", "vendor_en": "OriginLab",
             "desc": "断点、填充谱图、单峰/双峰拟合、微分、高低版本转换。",
             "desc_en": "Breakpoints, curve filling, single/doublet peak fitting, derivatives, version conversion.", "kw": ["origin"]},
            {"name": "Python 脚本", "name_en": "Python Scripts", "vendor": "自研工具", "vendor_en": "In-house tools",
             "desc": "CIF 下载、红外基线校正等效率脚本（相关脚本分布在各仪器分类页）。",
             "desc_en": "Efficiency scripts: CIF download, IR baseline correction, etc. (scripts live in each instrument section).", "kw": ["脚本", "python"]},
            {"name": "PeakForge", "name_en": "PeakForge", "vendor": "谱图拟合", "vendor_en": "Spectral fitting",
             "desc": "碳谱等多组分谱图拟合实操。", "desc_en": "Multi-component fitting for NMR carbon spectra and more.", "kw": ["peakforge"]},
            {"name": "实用小技巧", "name_en": "Handy Tips", "vendor": "科研日常", "vendor_en": "Daily research",
             "desc": "PDF 页面删除等科研中的实用小操作。", "desc_en": "Practical everyday tips (e.g. removing PDF pages).", "kw": ["pdf", "物理地址"]},
        ],
    },
}

NAV_ORDER = ["index", "xps", "xrd-powder", "scxrd", "hrms", "dataplot", "scripts", "search", "cooperation", "about"]
NAV_I18N = {"index": "nav.home", "xrd-powder": "nav.xrd", "cooperation": "nav.coop", "about": "nav.about"}
NAV_LABEL = {"index": "首页", "cooperation": "商务合作", "about": "关于"}

FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%230b6e99'/%3E%3Ctext x='50' y='62' font-size='34' text-anchor='middle' fill='white' font-family='sans-serif' font-weight='bold'%3E%E8%A1%A8%3C/text%3E%3C/svg%3E"

# 静态资源版本号（每次构建更新，防访客浏览器缓存旧文件）
VERSION = time.strftime("%Y%m%d%H%M")
UPD_DATE = time.strftime("%Y-%m-%d")


def nav_html(active, prefix):
    items = []
    for key in NAV_ORDER:
        href = "index.html" if key == "index" else key + "/index.html"
        cls = ' class="active"' if key == active else ""
        i18n_key = NAV_I18N.get(key, "nav." + key)
        label = I18N[i18n_key]["zh"]
        items.append('<li><a href="%s%s"%s data-i18n="%s">%s</a></li>' % (prefix, href, cls, i18n_key, label))
    return "\n".join(items)


def layout(active, title, desc, body, prefix=""):
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title data-i18n="title.%(active)s">%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="icon" href="%(favicon)s">
<link rel="stylesheet" href="%(prefix)sassets/css/style.css?v=%(ver)s">
</head>
<body data-page="%(active)s">
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="%(prefix)sindex.html">
      <span class="logo-badge">表</span>
      <span class="logo-text"><strong>结构分析表征</strong><small>Structure Analysis &amp; Characterization</small></span>
    </a>
    <nav><ul>%(nav)s</ul></nav>
    <button id="lang-toggle" class="lang-toggle" type="button" aria-label="切换语言 / Switch language">EN</button>
  </div>
</header>
<main>
%(body)s
</main>
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div>© 2026 结构分析表征 · 光电子能谱分部 · 单晶多晶衍射分部 · <span data-i18n="footer.updated">更新于</span> %(upd)s</div>
    <div class="footer-links">
      <span class="bz">👁 <span id="busuanzi_value_site_pv"></span> · 👤 <span id="busuanzi_value_site_uv"></span></span>
      <a href="%(bili)s" target="_blank" rel="noopener" data-i18n="footer.bili">B站主页</a>
      <a href="mailto:%(email)s">%(email)s</a>
    </div>
  </div>
</footer>
<div id="modal" class="modal" hidden>
  <div class="modal-mask" data-close></div>
  <div class="modal-body">
    <div class="modal-bar"><span id="modal-title"></span><button class="modal-close" data-close>✕</button></div>
    <div class="modal-player"><iframe id="modal-frame" src="" allowfullscreen scrolling="no" frameborder="0"></iframe></div>
    <div class="modal-foot"><a id="modal-link" href="#" target="_blank" rel="noopener" data-i18n="modal.open">在 B 站打开（点赞投币收藏）↗</a></div>
  </div>
</div>
<script src="%(prefix)sassets/js/data.js?v=%(ver)s"></script>
<script src="%(prefix)sassets/js/main.js?v=%(ver)s"></script>
<script async src="https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js"></script>
</body>
</html>""" % {"active": active, "title": title, "desc": desc, "favicon": FAVICON,
             "prefix": prefix, "nav": nav_html(active, prefix), "body": body,
             "bili": BILI, "email": EMAIL, "ver": VERSION, "upd": UPD_DATE}


# 公众号文章分类（关键词 → 仪器分类；按顺序匹配，先命中先归类）
ARTICLE_CATEGORY_RULES = [
    ("scxrd", r"单晶|olex|shelx|ccdc|绝对构型|晶体解析|晶体结构|孪晶|cif下载"),
    ("hrms", r"质谱|hrms|mass|xcalibur|masshunter|masslynx|peakview|sciex|sicex|代谢|mol文件"),
    ("xps", r"xps|ups|光电子|能谱|avantage|casa|xpspeak|peakforge|俄歇|功函数|结合能|灵敏度因子|多组分拟合|vgd|multipak|深度剖析"),
    ("xrd-powder", r"xrd|衍射|jade|highscore|gsas|rietveld|精修|粉末|多晶|物相|match!|profex|eva|endeavour|结晶度|靶材|cif|cod"),
    ("dataplot", r"origin|绘图|作图|python|脚本|红外|ir数据|pdf|物理地址|带隙|紫外|uv-vis|小工具|转换器|excel|git lfs|github 上传"),
]

# 明确剔除的杂讯（抽奖/生活类/通知）
ARTICLE_NOISE = r"抽奖|中奖|荐购|快递|集运|维修|马到功成|分享图片|招生|招聘|审核制|直播|福利|节日|新年|中秋|国庆|^群$|^1$|群发测试"


def classify_article(title):
    t = title.lower()
    if re.search(ARTICLE_NOISE, t):
        return "noise"
    for cat, pattern in ARTICLE_CATEGORY_RULES:
        if re.search(pattern, t):
            return cat
    return None


def classify_article_type(title):
    t = title.lower()
    if re.search(r"文献|解读|lit\b", t):
        return "lit"
    if re.search(r"原理|科普|什么是|的概念|概念与区别", t):
        return "p"
    if re.search(r"安装|入门|初识|基本操作|简介|介绍|下载|开放下载|基本功能|常用功能", t):
        return "s"
    return "a"


# ---------------- GitHub 脚本仓库（scripts 页） ----------------
SCRIPTS = [
    {"key": "s1", "repo": "thermo-xps-depth-data-to-excel-converter", "video": None},
    {"key": "s2", "repo": "HRMS-Metabolite-Explorer", "video": "代谢产物分析软件HRMS Metabolite Explorer v2.9开放试用和购买"},
    {"key": "s3", "repo": "Metabolic-Analysis", "video": "vgd-excel和Metabolic-Analysis开放下载"},
    {"key": "s4", "repo": "d-or-p-band-DOS-based-on-Valence-or-UPS", "video": "d带和P带计算的脚本"},
    {"key": "s5", "repo": "-v8.1.1-User-Manual-for-Powder-Diffraction-Refinement-Tool-v8.1.1", "video": None},
    {"key": "s6", "repo": "mol-downloader", "video": "化合物mol文件下载脚本"},
    {"key": "s7", "repo": "PDF-Page-Splitter", "video": "如何删除pdf中指定的页面"},
]

# 每个分类的文章数量（main() 填充，构建期使用）
ART_COUNT = {}

HTML_404 = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>404 — 结构分析表征</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%230b6e99'/%3E%3Ctext x='50' y='62' font-size='34' text-anchor='middle' fill='white' font-family='sans-serif' font-weight='bold'%3E%E8%A1%A8%3C/text%3E%3C/svg%3E">
<style>
body{margin:0;font-family:system-ui,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f3f7fa;color:#1c2b36;
display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center}
.box{padding:40px}
h1{font-size:72px;margin:0;color:#0b6e99}
p{color:#64748b;margin:8px 0 24px}
a{display:inline-block;margin:0 8px;padding:10px 22px;border-radius:10px;text-decoration:none;font-size:15px}
a.pri{background:#0b6e99;color:#fff}
a.gho{border:1px solid #0b6e99;color:#0b6e99}
</style>
</head>
<body>
<div class="box">
  <h1>404</h1>
  <p>页面不存在 / Page not found</p>
  <a class="pri" href="/">返回首页 ←</a>
  <a class="gho" href="https://space.bilibili.com/386282560" target="_blank" rel="noopener">B 站主页 ↗</a>
</div>
</body>
</html>
"""

# 构建期数据引用（main() 填充，用于静态预渲染 SEO）
VIDEOS = []
ARTICLES = []

TYPE_ZH = {"a": "数据分析", "s": "软件介绍", "p": "原理科普", "lit": "文献解读"}


def hesc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def py_vcard(v):
    """与 main.js vCard 输出一致的静态卡片（SEO 预渲染，中文默认）。"""
    pic = ('<img class="v-thumb" src="%s" alt="" referrerpolicy="no-referrer" onerror="this.style.display=%s">'
           % (hesc(v["pic"]) + "@480w_270h_1c.webp" if "hdslb.com" in v.get("pic", "") else hesc(v.get("pic", "")),
              "'none'")) if v.get("pic") else ""
    return ('<div class="v-card" data-bvid="%s" data-title="%s">%s'
            '<p class="v-title">%s</p><div class="v-meta">'
            '<span class="v-tag %s">%s</span><span class="v-src">B站</span>'
            '<span>📅 %s</span><span>⏱ %s</span><span>▶ %s</span></div></div>'
            % (hesc(v["b"]), hesc(v["t"]), pic, hesc(v["t"]), v["y"], TYPE_ZH[v["y"]],
               hesc(v["d"]), hesc(v["s"]), fmt_views_zh(v["v"])))


def py_acard(a):
    digest = ('<p class="v-digest">%s</p>' % hesc(a["g"][:70])) if a.get("g") else ""
    pic = ('<img class="v-thumb" loading="lazy" src="%s" alt="" referrerpolicy="no-referrer" onerror="this.style.display=%s">'
           % (hesc(a["p"]), "'none'")) if a.get("p") else ""
    return ('<a class="v-card a-card" href="%s" target="_blank" rel="noopener">%s'
            '<p class="v-title">%s ↗</p>%s<div class="v-meta">'
            '<span class="v-tag %s">%s</span><span class="v-src">%s</span>'
            '<span>📅 %s</span></div></a>'
            % (hesc(a["l"]), pic, hesc(a["t"]), digest, a["y"], TYPE_ZH[a["y"]],
               hesc(a["s"]), hesc(a["d"])))


def article_section_body(cat):
    if ART_COUNT.get(cat):
        cat_arts = [a for a in ARTICLES if a["c"] == cat]
        pre = "\n".join(py_acard(a) for a in cat_arts[:12])
        return """<div class="toolbar">
      <div class="chips" id="atype-chips">
        <button class="chip active" data-atype="all" data-i18n="chip.all">全部</button>
        <button class="chip" data-atype="a" data-i18n="chip.a">数据分析</button>
        <button class="chip" data-atype="s" data-i18n="chip.s">软件介绍</button>
        <button class="chip" data-atype="p" data-i18n="chip.p">原理科普</button>
        <button class="chip" data-atype="lit" data-i18n="chip.lit">文献解读</button>
      </div>
    </div>
    <div class="v-grid" id="article-grid">%s</div>
    <div class="more-row"><button id="amore" class="btn ghost" data-i18n="load.more">加载更多</button></div>
    <p class="muted" style="margin-top:14px" data-i18n="cat.art2">图文内容持续收录中；也可直接移步微信公众号阅读原文。</p>""" % pre
    return """<div class="note-panel" id="article-panel">
      <p><strong data-i18n="cat.%(slug)s.art1a">深度图文教程整理中。</strong><span data-i18n="cat.%(slug)s.art1b">%(journals)s 的图文内容将陆续收录到本栏目（按 数据分析 / 软件介绍 / 文献解读 分类展示）。</span></p>
      <p class="muted" data-i18n="cat.art2">现有图文请先移步微信公众号阅读；站点维护者把文章链接按 tools/articles.json 的格式填好后重新构建即可自动展示。</p>
    </div>""" % {"slug": cat, "journals": CATS[cat]["journals"]}


def page_search():
    body = """
<section class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="../index.html" data-i18n="nav.home">首页</a> / <span data-i18n="nav.search">搜索</span></p>
    <h1><span data-i18n="nav.search">搜索</span> <small>Search</small></h1>
    <p class="page-desc" data-i18n="search.desc">全站搜索：一次检索全部视频教程与公众号图文。</p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <input id="site-q" class="search site-search" type="search" data-i18n-ph="search.ph2" placeholder="输入关键词，如：拟合 / 结晶度 / 代谢 / 精修 …" autofocus>
    <p class="count-badge" id="s-count"></p>
    <div class="v-grid" id="search-grid"></div>
    <div class="more-row"><button id="smore" class="btn ghost" hidden data-i18n="load.more">加载更多</button></div>
  </div>
</section>"""
    return layout("search", I18N["title.search"]["zh"],
                  "全站搜索视频教程与公众号图文。", body, prefix="../")


def page_scripts(video_bvid):
    cards = []
    for sc in SCRIPTS:
        key = sc["key"]
        btns = ['<a class="btn small primary" href="https://github.com/jgfxbz/%s" target="_blank" rel="noopener" data-i18n="scripts.github">GitHub 仓库 ↗</a>' % sc["repo"]]
        if sc["video"] and sc["video"] in video_bvid:
            btns.append('<a class="btn small ghost" href="https://www.bilibili.com/video/%s" target="_blank" rel="noopener" data-i18n="scripts.video">▶ 视频教程</a>' % video_bvid[sc["video"]])
        cards.append("""
      <div class="acc-card script-card">
        <h3><span data-i18n="scripts.%s.t"></span> <span class="tag" data-i18n="scripts.%s.tag"></span></h3>
        <p data-i18n="scripts.%s.d"></p>
        <div class="btn-row">%s</div>
      </div>""" % (key, key, key, "".join(btns)))
    body = """
<section class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="../index.html" data-i18n="nav.home">首页</a> / <span data-i18n="nav.scripts">脚本工具</span></p>
    <h1><span data-i18n="nav.scripts">脚本工具</span> <small>Scripts &amp; Tools</small></h1>
    <p class="page-desc" data-i18n="scripts.desc">团队自研的免费小工具与脚本，全部开源在 GitHub，配套 B 站视频教程。欢迎按需取用。</p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="acc-grid">%s
    </div>
    <p class="muted" style="margin-top:18px" data-i18n="scripts.note">工具持续更新中，使用问题欢迎通过公众号或邮件反馈。</p>
  </div>
</section>""" % "\n".join(cards)
    return layout("scripts", I18N["title.scripts"]["zh"],
                  "结构分析表征团队自研的免费开源脚本与工具。", body, prefix="../")


def video_section(cat):
    cat_vids = [v for v in VIDEOS if v["c"] == cat]
    pre_vids = "\n".join(py_vcard(v) for v in cat_vids[:24])
    return """
<section class="section">
  <div class="wrap">
    <h2><span class="h-num">01</span><span data-i18n="sec.software">软件介绍</span></h2>
    <p class="section-sub" data-i18n="sec.software.sub">点击软件卡片可筛选该软件的相关视频</p>
    <div class="sw-grid" id="sw-grid">%s</div>
  </div>
</section>
<section class="section section-alt">
  <div class="wrap">
    <h2><span class="h-num">02</span><span data-i18n="sec.videos">视频教程</span> <span class="count-badge" id="v-count"></span></h2>
    <div class="toolbar">
      <div class="chips" id="type-chips">
        <button class="chip active" data-type="all" data-i18n="chip.all">全部</button>
        <button class="chip" data-type="a" data-i18n="chip.a">数据分析</button>
        <button class="chip" data-type="s" data-i18n="chip.s">软件介绍</button>
        <button class="chip" data-type="p" data-i18n="chip.p">原理科普</button>
      </div>
      <input id="search" class="search" type="search" data-i18n-ph="search.ph" placeholder="搜索视频标题，如：拟合 / jade / 精修 …">
    </div>
    <div class="v-grid" id="video-grid">%s</div>
    <div class="more-row"><button id="more" class="btn ghost" data-i18n="load.more">加载更多</button></div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2><span class="h-num">03</span><span data-i18n="sec.articles">图文教程 · 公众号</span> <span class="count-badge" id="a-count"></span></h2>
    %s
  </div>
</section>""" % (software_pre(cat), pre_vids, article_section_body(cat))


def software_pre(cat):
    return "\n".join(
        '<div class="sw-card" data-kw="%s"><h3>%s<span class="vendor">%s</span></h3>'
        '<p>%s</p></div>' % (hesc(sw["kw"][0]), hesc(sw["name"]), hesc(sw["vendor"]), hesc(sw["desc"]))
        for sw in CATS[cat]["software"])


def bili_note():
    return """
<section class="section section-alt" style="padding-top:0">
  <div class="wrap">
    <div class="note-panel">
      <p><span data-i18n="bili.more1">以上只是本站收录的合集内容，</span><strong data-i18n="bili.more2">全部视频（含未分组）请移步 B 站主页</strong>：
      <a href="%s" target="_blank" rel="noopener">space.bilibili.com/386282560 ↗</a></p>
    </div>
  </div>
</section>""" % BILI


def merged_latest(n=10):
    """首页最新更新：视频 + 文章按日期混排。"""
    items = []
    for v in VIDEOS:
        items.append({"kind": "v", "date": v["d"], "obj": v})
    for a in ARTICLES:
        items.append({"kind": "a", "date": a["d"], "obj": a})
    items.sort(key=lambda x: x["date"], reverse=True)
    return [py_vcard(x["obj"]) if x["kind"] == "v" else py_acard(x["obj"]) for x in items[:n]]


def page_index(stats):
    cards = []
    for slug, c in CATS.items():
        n = stats["cat_count"].get(slug, 0)
        cards.append("""
      <a class="cat-card" href="%s/index.html">
        <div class="cat-name"><span data-i18n="%s">%s</span><small>%s</small></div>
        <p data-i18n="cat.%s.snip">%s</p>
        <div class="cat-meta" data-i18n="cat.%s.count">%d 个视频 →</div>
      </a>""" % (slug, c["nav"], c["nav_zh"] if "nav_zh" in c else c["nav"], c["en"], slug,
                 c["desc"].split("，")[0].split("。")[0], slug, n))
    body = """
<section class="hero">
  <div class="wrap">
    <h1>结构分析表征</h1>
    <p class="hero-sub" data-i18n="hero.sub">XPS · UPS · XRD · HRMS 的数据分析教程合集 —— 把每一个谱图讲明白</p>
    <div class="hero-stats">
      <div><strong data-stat="videos">%d</strong><span data-i18n="stat.videos">视频教程</span></div>
      <div><strong data-stat="cats">%d</strong><span data-i18n="stat.cats">仪器类别</span></div>
      <div><strong data-stat="accounts">3</strong><span data-i18n="stat.accounts">公众号矩阵</span></div>
      <div><strong data-stat="views">%s</strong><span data-i18n="stat.views">累计播放</span></div>
    </div>
    <div class="hero-cta">
      <a class="btn primary" href="%s" target="_blank" rel="noopener" data-i18n="cta.bili">B 站主页 ↗</a>
      <a class="btn ghost" href="cooperation/index.html" data-i18n="cta.coop">商务合作</a>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2 data-i18n="home.cats">按仪器类别浏览</h2>
    <div class="cat-grid">%s
    </div>
  </div>
</section>
<section class="section section-alt">
  <div class="wrap">
    <h2 data-i18n="home.latest">最新更新</h2>
    <div class="v-grid" id="latest-grid">%s</div>
  </div>
</section>""" % (
        stats["total"], len(CATS), stats["views_txt"], BILI, "\n".join(cards),
        "\n".join(merged_latest(10))) + """
<section class="section">
  <div class="wrap">
    <h2 data-i18n="home.accounts">账号矩阵</h2>
    <div class="acc-grid">
      <div class="acc-card"><h3><span data-i18n="acc1.t">结构分析表征</span> <span class="tag main" data-i18n="acc1.tag">主号</span></h3><p data-i18n="acc1.desc">总号：XPS、UPS、HRMS、PXRD、SXRD 等表征数据分析教程汇总。</p></div>
      <div class="acc-card"><h3><span data-i18n="acc2.t">光电子能谱分部</span> <span class="tag" data-i18n="acc2.tag">XPS 专号</span></h3><p data-i18n="acc2.desc">XPS / UPS 数据分析深度图文，配套出版《光电子能谱数据分析从入门到精通》。</p></div>
      <div class="acc-card"><h3><span data-i18n="acc3.t">单晶多晶衍射分部</span> <span class="tag" data-i18n="acc3.tag">XRD 专号</span></h3><p data-i18n="acc3.desc">单晶 / 粉末衍射的软件实操、解析与精修图文教程。</p></div>
      <div class="acc-card"><h3><span data-i18n="acc4.t">B 站 · 结构分析表征</span> <span class="tag" data-i18n="acc4.tag">视频</span></h3><p data-i18n="acc4.desc">全部视频教程在此发布，点击站内视频卡片可直接播放。</p><p><a href="%s" target="_blank" rel="noopener">space.bilibili.com/386282560 ↗</a></p></div>
    </div>
  </div>
</section>
<section class="section section-alt">
  <div class="wrap">
    <h2 data-i18n="nav.coop">商务合作</h2>
    <div class="coop-band">
      <div class="coop-info">
        <div class="coop-types">
          <span>📊 <span data-i18n="coop.c1.t">数据分析服务</span></span>
          <span>🎓 <span data-i18n="coop.c2.t">课程与培训</span></span>
          <span>📣 <span data-i18n="coop.c3.t">内容合作</span></span>
          <span>✍️ <span data-i18n="coop.c4.t">图文定制</span></span>
        </div>
        <p class="coop-mail"><span data-i18n="contact.p1">商务合作请邮件联系：</span><a class="mail" href="mailto:%s">%s</a></p>
        <p class="coop-wechat"><span data-i18n="contact.wechat">微信号：</span><strong>FF-JGFXBZ</strong></p>
        <p class="muted" data-i18n="contact.p2">合作意向请说明：合作类型 + 需求描述 + 联系方式，收到后会尽快回复。</p>
        <a class="btn small ghost coop-more" href="cooperation/index.html" data-i18n="coop.more">查看完整商务合作页 →</a>
      </div>
      <div class="coop-qr">
        <img src="assets/img/qr-main.png" alt="结构分析表征" onerror="this.style.display='none'">
        <span class="qr-tip" data-i18n="qr.main">公众号 · 结构分析表征</span>
      </div>
    </div>
  </div>
</section>""" % (BILI, EMAIL, EMAIL)
    return layout("index", I18N["title.index"]["zh"],
                  "XPS、UPS、XRD、HRMS 数据分析与软件实操教程导航：视频教程、软件介绍、文献解读与商务合作。", body)


def page_cat(slug):
    c = CATS[slug]
    body = """
<section class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="../index.html" data-i18n="nav.home">首页</a> / <span data-i18n="%s">%s</span></p>
    <h1><span data-i18n="cat.%s.title">%s</span> <small>%s</small></h1>
    <p class="page-desc" data-i18n="cat.%s.desc">%s</p>
  </div>
</section>
%s
%s""" % (c["nav"], c["nav_zh"], slug, c["title"], c["en"], slug, c["desc"],
         video_section(slug), bili_note())
    return layout(slug, I18N[c["title_key"]]["zh"], c["desc"], body, prefix="../")


def page_cooperation():
    body = """
<section class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="../index.html" data-i18n="nav.home">首页</a> / <span data-i18n="nav.coop">商务合作</span></p>
    <h1><span data-i18n="nav.coop">商务合作</span> <small>Business</small></h1>
    <p class="page-desc" data-i18n="coop.desc">欢迎高校课题组、测试平台、仪器厂商与软件厂商洽谈合作。</p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="acc-grid">
      <div class="acc-card"><h3>📊 <span data-i18n="coop.c1.t">数据分析服务</span></h3><p data-i18n="coop.c1.d">XPS / XRD / HRMS 等谱图的数据分析、分峰拟合与结果解读。</p></div>
      <div class="acc-card"><h3>🎓 <span data-i18n="coop.c2.t">课程与培训</span></h3><p data-i18n="coop.c2.d">仪器分析软件实操培训、线上课程定制（B 站已有 61 课时付费专栏）。</p></div>
      <div class="acc-card"><h3>📣 <span data-i18n="coop.c3.t">内容合作</span></h3><p data-i18n="coop.c3.d">仪器 / 软件 / 测试平台的内容推广、测评与合作视频。</p></div>
      <div class="acc-card"><h3>✍️ <span data-i18n="coop.c4.t">图文定制</span></h3><p data-i18n="coop.c4.d">公众号矩阵（主号 + 两个分部）的科普图文与软文合作。</p></div>
    </div>
    <div class="contact-panel">
      <h2 data-i18n="contact.h2">联系方式</h2>
      <p><span data-i18n="contact.p1">商务合作请邮件联系：</span><a class="mail" href="mailto:%s">%s</a></p>
      <p class="wechat-line"><span data-i18n="contact.wechat">微信号：</span><strong>FF-JGFXBZ</strong></p>
      <p class="muted" data-i18n="contact.p2">合作意向请说明：合作类型 + 需求描述 + 联系方式，收到后会尽快回复。</p>
      <div class="qr-row">
        <div class="qr-box"><img src="../assets/img/qr-main.png" alt="结构分析表征" onerror="this.style.display='none'"><span class="qr-tip" data-i18n="qr.main">公众号 · 结构分析表征</span></div>
        <div class="qr-box"><img src="../assets/img/qr-xps.png" alt="光电子能谱分部" onerror="this.style.display='none'"><span class="qr-tip" data-i18n="qr.xps">公众号 · 光电子能谱分部</span></div>
        <div class="qr-box"><img src="../assets/img/qr-xrd.png" alt="单晶多晶衍射分部" onerror="this.style.display='none'"><span class="qr-tip" data-i18n="qr.xrd">公众号 · 单晶多晶衍射分部</span></div>
        <div class="qr-box"><a href="%s" target="_blank" rel="noopener"><img src="../assets/img/qr-bili.png" alt="B站 结构分析表征" onerror="this.style.display='none'"></a><span class="qr-tip" data-i18n="qr.bili">B站 · 结构分析表征</span></div>
      </div>
    </div>
  </div>
</section>""" % (EMAIL, EMAIL, BILI)
    return layout("cooperation", I18N["title.coop"]["zh"],
                  "数据分析服务、课程培训、内容合作与图文定制的商务合作页面。", body, prefix="../")


def page_about():
    body = """
<section class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="../index.html" data-i18n="nav.home">首页</a> / <span data-i18n="nav.about">关于</span></p>
    <h1><span data-i18n="nav.about">关于</span> <small>About</small></h1>
    <p class="page-desc">Analytical Characterization Methods about XPS, UPS, HRMS, PXRD, SXRD et al.</p>
  </div>
</section>
<section class="section">
  <div class="wrap about-body">
    <h2 data-i18n="about.h2a">我们是谁</h2>
    <p data-i18n="about.p1">「结构分析表征」是一个聚焦材料结构分析表征数据处理的科普团队，运营三个微信公众号与同名 B 站账号，长期输出 XPS / UPS / XRD / HRMS 等表征技术的数据分析与软件实操教程。</p>
    <ul>
      <li data-i18n="about.li1">公众号「结构分析表征」：主号，覆盖各表征技术的数据分析教程；</li>
      <li data-i18n="about.li2">公众号「光电子能谱分部」：XPS / UPS 深度图文；</li>
      <li data-i18n="about.li3">公众号「单晶多晶衍射分部」：单晶与粉末衍射教程；</li>
      <li data-i18n="about.li4">B 站「结构分析表征」：视频教程（含 61 课时付费专栏《光电子能谱多种软件使用》）。</li>
    </ul>
    <h2 data-i18n="about.h2b">出版物</h2>
    <p data-i18n="about.pub">《光电子能谱数据分析从入门到精通》—— 李焕勇 著，北京大学出版社（ISBN 9787301366752）。</p>
    <h2 data-i18n="about.h2c">关于本站</h2>
    <p data-i18n="about.site">本站是四个平台内容的导航目录：视频直接内嵌 B 站播放器，图文教程以公众号原文链接收录。分类为仪器类别 →（软件介绍 / 数据分析 / 原理科普 / 图文教程）两级结构，欢迎收藏使用。</p>
  </div>
</section>"""
    return layout("about", I18N["title.about"]["zh"], "结构分析表征账号矩阵与出版物的介绍页面。", body, prefix="../")


# ---------------- 数据处理 ----------------
def remap_category(v):
    cat, title, cols = v["category"], v["title"].lower(), v["collections"]
    if cat == "book":          # 多重分裂(元素化学态) → XPS
        return "xps"
    if "IRMS" in cols:         # 同位素质谱 → 质谱类
        return "hrms"
    if cat == "dataplot" and "xps" in title:   # PeakForge XPS 系列
        return "xps"
    if cat == "other":         # pdf删页 / 改物理地址 → 数据与绘图·实用技巧
        return "dataplot"
    return cat


def tag_type(title):
    if re.search(r"原理|什么是|概念", title):
        return "p"
    if re.search(r"基本操作|安装|入门|初识|简介|基本功能|常用功能|界面|基本介绍", title):
        return "s"
    return "a"


def fmt_views_zh(n):
    if n >= 10000:
        return ("%.1f万" % (n / 10000)).rstrip("0").rstrip(".").replace(".0万", "万")
    return str(n)


def fmt_dur(sec):
    sec = int(sec or 0)
    return "%d:%02d" % (sec // 60, sec % 60) if sec < 3600 else "%d:%02d:%02d" % (sec // 3600, sec % 3600 // 60, sec % 60)


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))

    videos = []
    for v in raw["videos"]:
        cat = remap_category(v)
        ts = v.get("pubdate") or 0
        videos.append({
            "b": v["bvid"], "t": v["title"], "c": cat, "y": tag_type(v["title"]),
            "d": time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else "",
            "s": fmt_dur(v.get("length")), "v": v.get("view", 0),
            "p": v.get("pic", ""),
        })

    cat_count = {}
    for v in videos:
        cat_count[v["c"]] = cat_count.get(v["c"], 0) + 1
    total_views = sum(v["v"] for v in videos)
    stats = {"total": len(videos), "cat_count": cat_count, "views_txt": fmt_views_zh(total_views)}

    # 构建期全局引用（预渲染用）
    VIDEOS.clear()
    VIDEOS.extend(videos)
    ARTICLES.clear()

    # 公众号文章（tools/articles-*.json，由后台采集导出）
    art_map = {}
    skipped = 0
    for fp in sorted(Path(__file__).resolve().parent.glob("articles-*.json")):
        try:
            batch = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print("skip article file:", fp.name, e)
            continue
        src = batch.get("account") or "公众号"
        for a in batch.get("articles") or []:
            link = a.get("link")
            title = (a.get("title") or "").strip()
            if not link or not title or link in art_map:
                continue
            cat = a.get("c") or classify_article(title)
            if not cat or cat == "noise":
                skipped += 1
                continue
            atype = a.get("y") or classify_article_type(title)
            art_map[link] = {"t": title, "l": link, "c": cat, "y": atype, "p": a.get("cover", ""),
                             "d": time.strftime("%Y-%m-%d", time.localtime(a.get("create_time") or 0)),
                             "s": src}
    articles_data = sorted(art_map.values(), key=lambda x: x["d"], reverse=True)
    ARTICLES.extend(articles_data)
    ART_COUNT.clear()
    for a in articles_data:
        if a["c"] in CATS:
            ART_COUNT[a["c"]] = ART_COUNT.get(a["c"], 0) + 1
    print("articles: ok=%d skipped=%d per-cat=%s" % (len(articles_data), skipped, ART_COUNT))

    # 标题 -> BV 映射（脚本页"视频教程"按钮用）
    video_bvid = {v["t"]: v["b"] for v in videos if v["t"]}

    # nav_zh 补充（cat 卡片与面包屑的中文 label）
    for slug, c in CATS.items():
        c["nav_zh"] = c["nav"]

    # per-cat 文案键（分类页图文说明 / 首页卡片）
    TITLE_EN = {
        "xps": "XPS / UPS Photoelectron Spectroscopy",
        "xrd-powder": "Powder / Polycrystalline XRD",
        "scxrd": "Single-Crystal XRD",
        "hrms": "High-Resolution Mass Spectrometry",
        "dataplot": "Data Processing & Plotting",
    }
    for slug, c in CATS.items():
        I18N["cat.%s.title" % slug] = {"zh": c["title"], "en": TITLE_EN[slug]}
        I18N["cat.%s.desc" % slug] = {"zh": c["desc"], "en": c["desc_en"]}
        I18N["cat.%s.snip" % slug] = {"zh": c["desc"].split("，")[0].split("。")[0], "en": c["snip_en"]}
        I18N["cat.%s.count" % slug] = {"zh": "%d 个视频 →" % cat_count.get(slug, 0),
                                       "en": "%d videos →" % cat_count.get(slug, 0)}
        I18N["cat.%s.art1a" % slug] = {"zh": "深度图文教程整理中。", "en": "In-depth article tutorials are being curated."}
        I18N["cat.%s.art1b" % slug] = {
            "zh": "%s 的图文内容将陆续收录到本栏目（按 数据分析 / 软件介绍 / 文献解读 分类展示）。" % c["journals"],
            "en": "Articles from %s will be collected here (grouped into Data Analysis / Software Guide / Literature Reading)." % c["journals_en"]}

    # nav_zh 映射（nav.* 的 zh 值即为中文导航名，已包含在 I18N）
    for slug, c in CATS.items():
        c["nav_zh"] = I18N[c["nav"]]["zh"]

    # data.js
    data_js = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "bili": BILI,
        "videos": videos,
        "software": {slug: c["software"] for slug, c in CATS.items()},
        "articles": articles_data,
        "i18n": I18N,
        "stats": {"videos": stats["total"], "cats": len(CATS), "accounts": 3, "views": total_views},
    }
    (ROOT / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets" / "js" / "data.js").write_text(
        "// 自动生成于 %s，请勿手工编辑（修改请改 tools/build.py 或 articles.json 后重新构建）\nwindow.SITE_DATA = %s;\n"
        % (data_js["generated"], json.dumps(data_js, ensure_ascii=False, separators=(",", ":"))),
        encoding="utf-8")

    # HTML 页面
    (ROOT / "index.html").write_text(page_index(stats), encoding="utf-8")
    for slug in CATS:
        (ROOT / slug).mkdir(exist_ok=True)
        (ROOT / slug / "index.html").write_text(page_cat(slug), encoding="utf-8")
    (ROOT / "cooperation" / "index.html").parent.mkdir(exist_ok=True)
    (ROOT / "cooperation" / "index.html").write_text(page_cooperation(), encoding="utf-8")
    (ROOT / "about" / "index.html").parent.mkdir(exist_ok=True)
    (ROOT / "about" / "index.html").write_text(page_about(), encoding="utf-8")
    (ROOT / "scripts" / "index.html").parent.mkdir(exist_ok=True)
    (ROOT / "scripts" / "index.html").write_text(page_scripts(video_bvid), encoding="utf-8")
    (ROOT / "search" / "index.html").parent.mkdir(exist_ok=True)
    (ROOT / "search" / "index.html").write_text(page_search(), encoding="utf-8")

    # SEO: sitemap / robots / 404
    pages = ["", "xps/", "xrd-powder/", "scxrd/", "hrms/", "dataplot/",
             "scripts/", "search/", "cooperation/", "about/"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        sm.append("  <url><loc>https://jgfxbz.github.io/%s</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq></url>"
                  % (p, UPD_DATE))
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    (ROOT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://jgfxbz.github.io/sitemap.xml\n",
                                     encoding="utf-8")
    (ROOT / "404.html").write_text(HTML_404, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")

    print("built OK: %d videos | views=%s | per-cat=%s | i18n keys=%d" %
          (stats["total"], stats["views_txt"], cat_count, len(I18N)))


if __name__ == "__main__":
    main()
