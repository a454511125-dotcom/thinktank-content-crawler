# 智库 TikTok 内容采集脚本

从 17 家美国智库网站检索 TikTok 相关文章，提取标题、链接、作者、日期、摘要和正文，并保存为 JSON。提供 HTTP 和 Selenium 两个入口，以及站点诊断脚本。

## 先采集一个站点

Windows PowerShell，Python 3.10 或以上；Selenium 入口还需要 Google Chrome。请在项目根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 只显示站点列表，不访问网络
.\.venv\Scripts\python.exe main.py --list

# HTTP 入口：先采集 CSIS 的一页
.\.venv\Scripts\python.exe main.py --tank csis --pages 1

# 动态页面：使用 Selenium（首次运行会下载 ChromeDriver）
.\.venv\Scripts\python.exe main_selenium.py --tank csis --pages 1
```

结果写入 `data/processed/csis_results.json`，日志写入 `logs/`；调试模式下 HTML 快照写入 `data/raw_html/`。

## 批量采集与合并

```powershell
# HTTP 入口：未指定 --tank 时逐个采集全部站点
.\.venv\Scripts\python.exe main.py --pages 2
.\.venv\Scripts\python.exe main.py --merge

# Selenium 入口：显式指定 --all；可跳过站点
.\.venv\Scripts\python.exe main_selenium.py --all --pages 2 --skip cfr piie
.\.venv\Scripts\python.exe main_selenium.py --merge
```

两个入口共用 `data/processed/{tank_id}_results.json`，同一站点再次采集会覆盖该文件。HTTP 合并结果为 `data/final/tiktok_reports.json`；Selenium 合并结果为 `data/processed/all_results.json`。合并按 URL 去重，并排除已有的 `all_results.json`，可重复执行。

Selenium 的 `--resume` 只按结果文件是否存在且大于 100 字节来跳过整个站点；它不能判断站点是否采集完整，也不是逐篇断点续传。需要补采的站点请单独运行 `--tank`，并先自行备份已有结果。

## 站点配置

`config.py` 保留以下 17 家智库的搜索地址、选择器和默认页数：

| ID | 智库 |
|---|---|
| `brookings` | Brookings Institution |
| `csis` | Center for Strategic and International Studies |
| `cfr` | Council on Foreign Relations |
| `rand` | RAND Corporation |
| `carnegie` | Carnegie Endowment for International Peace |
| `atlantic_council` | Atlantic Council |
| `cnas` | Center for a New American Security |
| `piie` | Peterson Institute for International Economics |
| `chicago_council` | Chicago Council on Global Affairs |
| `hoover` | Hoover Institution |
| `hudson` | Hudson Institute |
| `cato` | Cato Institute |
| `heritage` | The Heritage Foundation |
| `wilson` | Wilson Center |
| `aei` | American Enterprise Institute |
| `asia_society` | Asia Society |
| `cap` | Center for American Progress |

搜索地址和 CSS 选择器来自原项目。站点改版、动态搜索和访问验证会影响采集结果；本次整理未重新进行 17 个站点的在线采集验收。先用一页结果核对标题、正文和分页，再运行大批量任务。HTTP 200 或匹配到页面元素不能直接证明文章采集完整。

### Cookie 与人工验证

仓库不附带 Cookie 或登录状态。HTTP 入口可通过当前 PowerShell 会话的 `CFR_COOKIE`、`PIIE_COOKIE` 环境变量读取使用者自行获得且有权使用的 Cookie。不要把实际值写进代码或提交到 Git。

Selenium 入口访问 CFR、PIIE 时使用可见 Chrome 窗口，并暂停等待使用者自行完成网站验证；看到正常搜索结果后回到终端按回车。其他站点默认无头运行。详见 [人工验证说明](USAGE_MANUAL_AUTH.md)。

### Brookings 的可选 Algolia 路径

Selenium 入口在设置 `BROOKINGS_ALGOLIA_API_KEY` 后使用 Algolia 检索；未配置时明确提示并使用浏览器搜索页面。API Key 应由使用者通过获准渠道取得，仓库不提供实际值。

`BROOKINGS_ALGOLIA_APP_ID`、`BROOKINGS_ALGOLIA_INDEX` 可覆盖原项目保留的公开应用 ID 和索引名。API 只用于检索，文章正文仍从文章页面提取。

[.env.example](.env.example) 仅列出变量名，程序不会自动加载 `.env` 文件；请在当前 PowerShell 中设置所需环境变量。

## 输出字段与研究口径

主要字段：`think_tank`、`title`、`url`、`authors`、`publish_date`、`content_type`、`abstract`、`full_text`、`keywords`、`scraped_at`、`phase`、`is_paid_content`。

- `full_text` 保存页面提取的文本，仍可能包含导航或缺失动态内容，需要后续语料治理。Selenium 版已取消原脚本的 10,000 字符截断。
- `scraped_at` 沿用原脚本的本机时间格式，没有时区标记。
- `phase` 沿用原项目的四阶段配置：2017—2019、2020、2021—2022、2023—2026。日期无法识别或超出范围时为 `Unknown`；这属于项目预设，使用者应按研究设计调整。
- HTTP 版对 RAND 沿用“正文少于 200 字符”的 `is_paid_content` 启发式标记，并将这些记录另存 `data/final/rand_paid_reports.json`；短正文也可能来自提取失败，不能据此认定付费。其余 RAND 记录保留已提取正文。Selenium 版不做该判断，字段固定为 `false`。
- `keywords` 是固定的检索主题标签 `TikTok`，不是正文相关性检验结果。

## 文件与验证

- `main.py`、`scraper.py`：HTTP 采集及结果合并。
- `main_selenium.py`、`scraper_selenium.py`：动态页面、人工验证及可选 Algolia 检索。
- `config.py`：站点、时期和输出配置。
- `test_all_tanks.py`、`test_algolia_api.py`、`test_asia_society.py`、`final_verification.py`、`diagnose_problem_tanks.py`、`verify_user_urls.py`：原项目的联网诊断脚本。执行时会访问网站，部分会启动浏览器或下载驱动；它们不是离线单元测试。
- `tests/test_offline.py`：合成 HTML、时期标注、输出目录、合并去重及配置检查，不访问外网。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 来源与使用

本仓库整理自原 `thinktank_scraper` 项目，保留两个原有命令入口及全部 11 个 Python 脚本。发布副本将内嵌 Cookie、API Key 改为环境变量，并修复 JSON 路径被建成目录、Selenium 时期标注、合并重复及正文截断问题；不附带原始语料、运行日志、浏览器状态或历史测试报告。

原项目说明限定学术研究用途，未提供标准开源许可证；本次整理沿用该用途说明。采集内容的权利归原权利人所有。使用前核对各站点的访问规则和使用条款，保持适当请求间隔，不采集无权访问的内容。
