# 结构分析表征 · 官网

「结构分析表征」四个平台（公众号主号 + 光电子能谱分部 + 单晶多晶衍射分部 + B站）的内容导航站。
纯静态、无后端、无依赖，GitHub Pages 直接托管。

**线上地址**：https://jgfxbz.github.io （部署后生效）

## 站点结构

```
index.html            首页（仪器分类入口 + 最新更新 + 账号矩阵）
xps/                  XPS / UPS（含软件介绍卡片 + 视频教程 + 公众号图文栏）
xrd-powder/           粉末衍射 XRD
scxrd/                单晶衍射 SCXRD
hrms/                 高分辨质谱 HRMS
dataplot/             数据处理与绘图（Origin / Python / 实用技巧）
cooperation/          商务合作（邮箱 + 公众号二维码）
about/                关于
assets/
  css/style.css       样式
  js/data.js          视频数据（build.py 自动生成，勿手改）
  js/main.js          渲染与交互逻辑
```

内容组织为两级：**仪器类别 →（软件介绍 / 数据分析 / 软件介绍视频 / 原理科普 / 公众号图文）**。

## 日常更新

### 1. 更新 B 站视频

```bash
python tools/fetch_bilibili.py   # 重新抓取 B 站合集数据 → tools/videos_raw.json
python tools/build.py            # 重新生成 data.js 和全部页面
```

需要 Python 3，无第三方依赖。

### 2. 添加公众号图文（数据分析 / 软件介绍 / 文献解读）

编辑 `tools/articles.json`（首次可从空模板开始）：

```json
{
  "xps": [
    { "title": "文章标题", "url": "https://mp.weixin.qq.com/s/xxxx",
      "date": "2026-10-01", "source": "光电子能谱分部", "type": "analysis" }
  ]
}
```

- 键名：`xps` / `xrd-powder` / `scxrd` / `hrms` / `dataplot`
- `type`：`analysis`(数据分析) / `software`(软件介绍) / `literature`(文献解读)
- 保存后运行 `python tools/build.py` 即在对应仪器页展示。

### 3. 更换公众号二维码

把二维码图片放到 `assets/img/` 下，命名 `qr-main.png`、`qr-xps.png`、`qr-xrd.png`（150×150 以上即可），商务合作页自动显示。

## 部署（GitHub Pages）

仓库已按 `jgfxbz.github.io` 命名，推送到 GitHub 后自动生效：

```bash
git init
git add -A
git commit -m "init: 结构分析表征官网"
git branch -M main
git remote add origin https://github.com/jgfxbz/jgfxbz.github.io.git
git push -u origin main
```

> 首次推送后，在 GitHub 仓库 Settings → Pages 确认 Source 为 `main` 分支（默认即是）。
