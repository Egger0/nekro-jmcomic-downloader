# JMComic 下载器

基于 [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python) 的 [Nekro Agent](https://nekro.ai) 插件，提供 JMComic 本子的搜索、查询与下载功能，支持自动打包并通过 QQ 发送。

## 功能

| 方法 | 说明 |
|------|------|
| `download_album(album_id)` | 下载本子并打包发送（群聊 PDF / 私聊 zip） |
| `get_album_info(album_id)` | 查询本子详细信息（标题、作者、页数、标签等） |
| `search_album(keyword)` | 按关键词搜索本子 |

### 打包与发送

- **群聊**：图片压缩后生成 PDF 直接发送，体积小
- **私聊**：PDF 套一层 zip（QQ NT 内核限制），自动分卷避免超时
- 下载完成后 **30 秒自动清理**本地文件

## 安装

### 1. 安装依赖

```bash
pip install jmcomic pyyaml Pillow
```

### 2. 安装插件

将 `jmcomic_downloader` 目录复制到 Nekro Agent 的 `plugins/workdir/` 下：

```
plugins/workdir/jmcomic_downloader/
├── __init__.py
├── plugin.py
└── README.md
```

重启 Nekro Agent 或通过 WebUI 重载插件。

## 配置

在 Nekro Agent WebUI「插件配置」页面设置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| 代理地址 (HTTP) | 访问 JMComic 的 HTTP 代理 | 留空 |
| 代理地址 (HTTPS) | 访问 JMComic 的 HTTPS 代理 | 留空 |
| 下载目录 | 本子保存路径 | `./jmcomic_downloads` |
| 图片解码 | 是否自动解密图片 | 开启 |
| 图片后缀 | 保存格式 | `.png` |
| 图片下载线程 | 并发下载图片数 | 30 |
| 章节下载线程 | 并发下载章节数 | 20 |
| 启用缓存 | 跳过已下载的文件 | 开启 |
| 重试次数 | 请求失败重试 | 5 |
| 每卷页数上限 | 分卷时每卷最多页数（超过则拆多卷） | 60 |
| 客户端实现 | api / mobile / html | api |
| 自定义域名 | 手动指定禁漫域名，留空自动探测 | 留空 |

## 使用

对话中直接说即可：

```
下载本子 123456
查一下本子 350235
搜索关键词 xxx
```

或通过 `/exec` 调用：

```
/exec download_album(album_id=123456)
/exec get_album_info(album_id=123456)
/exec search_album(keyword="关键词")
```

## 注意事项

- 请合理使用，遵守相关法律法规
- 下载大本子可能需要几分钟，请耐心等待
- 如遇图片被替换为占位图，尝试切换「客户端实现」为 mobile 或 html
- 推荐将下载目录设为 Nekro Agent 的挂载路径以便本地访问
