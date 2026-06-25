# JMComic 下载器

基于 [jmcomic](https://github.com/tonquer/jmcomic) 的 Nekro Agent 插件，提供 JMComic 本子的搜索与下载功能。

## 功能

| 方法 | 说明 |
|------|------|
| `download_album(album_id)` | 根据本子 ID 下载全部图片到本地 |
| `get_album_info(album_id)` | 获取本子的标题、作者、页数等元信息 |
| `search_album(keyword)` | 按关键词搜索本子 |

## 安装

### 1. 安装依赖

确保 Nekro Agent 的 Python 环境中已安装 `jmcomic` 和 `pyyaml`：

```bash
pip install jmcomic pyyaml
```

### 2. 安装插件

将 `jmcomic_downloader` 目录复制到 Nekro Agent 的 `plugins/workdir/` 目录下：

```
plugins/workdir/jmcomic_downloader/
├── __init__.py
└── plugin.py
```

重启 Nekro Agent 或通过管理界面重新加载插件即可。

## 配置

在 Nekro Agent WebUI 的「插件配置」页面中设置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| 代理地址 (HTTP/HTTPS) | 访问 JMComic 所需的代理 | 留空 |
| 下载目录 | 本子保存路径 | `./jmcomic_downloads` |
| 图片解码 | 是否自动解密图片 | 开启 |
| 图片后缀 | 图片保存格式 | `.png` |
| 下载线程数 | 并发下载数 | 30/20 |
| 启用缓存 | 避免重复下载 | 开启 |
| 重试次数 | 请求失败重试 | 5 |

## 使用方法

在 Nekro Agent 对话中直接使用：

```
"帮我下载本子 ID 123456"
"查询本子 123456 的信息"
"搜索关键词 xxx 的本子"
```

或通过 `/exec` 指令直接调用：

```
/exec download_album(album_id=123456)
/exec get_album_info(album_id=123456)
/exec search_album(keyword="关键词")
```

## 注意事项

- 请合理使用，遵守相关法律法规
- 下载大本子（数百页）可能需要几分钟时间
- 如遇网络问题，请检查代理设置
# JMComic 下载器

基于 [# JMComic 下载器

基于 [jmcomic](https://github.com/hect0x7/JMComic-Crawler# JMComic 下载器

基于 [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python) 的 [Nekro Agent](https://nekro.ai) 插件，# JMComic 下载器

基于 [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python) 的 [Nekro Agent](https://nekro.ai) 插件，提供 JMComic 本子的搜索与下载功能，支持自动分卷打包并通过 QQ# JMComic 下载器

基于 [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python) 的 [Nekro Agent](https://nekro.ai) 插件，提供 JMComic 本子的搜索与下载功能，支持自动分卷打包并通过 QQ 发送。

## 功能

| 方法 | 说明 |
|------|------|
| `