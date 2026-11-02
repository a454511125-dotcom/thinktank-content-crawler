# CFR、PIIE 人工验证

需要访问验证时，用 Selenium 入口启动可见 Chrome 窗口：

```powershell
.\.venv\Scripts\python.exe main_selenium.py --tank cfr --pages 1
```

1. 在弹出的 Chrome 中查看网站提示，自行完成获准的验证或登录。
2. 确认页面已显示正常搜索结果。
3. 回到终端，按回车继续。

`piie` 使用相同方式。批量采集时遇到这两个站点也会暂停；无人值守任务可使用 `--skip cfr piie`。

验证会话仅供本次浏览器使用。不要上传 Cookie、登录凭据或浏览器用户目录。若网站仍拒绝访问，停止该站点的采集，核对其访问规则或联系站点取得授权。
