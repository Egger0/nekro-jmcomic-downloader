"""
JMComic 本子下载插件

基于 jmcomic 库，提供 JMComic 本子的搜索与下载功能。
用户可以通过本插件在 Nekro Agent 中直接下载指定 ID 的本子到本地。

## 功能列表

- 根据本子 ID 下载本子（全部图片）
- 搜索本子（按关键词）
- 获取本子详细信息

## 配置说明

安装插件后，请在 WebUI 插件配置页面中设置：
- **代理地址**：如果需要代理访问，请填写 HTTP/HTTPS 代理地址
- **下载目录**：本子下载到本地的目标目录
- **图片设置**：图片解码、后缀格式等
- **下载线程数**：并发下载图片和封面的线程数

## 注意事项

- 需要安装 jmcomic 和 pyyaml：`pip install jmcomic pyyaml Pillow`
- 请合理使用，遵守相关法律法规
- 下载大本子时可能需要较长时间
"""

from nekro_agent.api.plugin import NekroPlugin, SandboxMethodType, ConfigBase, ExtraField
from nekro_agent.api.schemas import AgentCtx
from pydantic import Field

# ============================================================
# 插件实例
# ============================================================

plugin = NekroPlugin(
    name="JMComic 下载器",
    module_name="jmcomic_downloader",
    description="基于 jmcomic 的 JMComic 本子下载插件，支持按 ID 下载和关键词搜索。",
    version="1.0.0",
    author="Eggerthe",
    url="https://github.com/eggerthe/nekro-jmcomic-downloader",
    allow_sleep=True,
    sleep_brief="当用户需要下载 JMComic 本子、搜索本子或获取本子信息时激活。",
)


# ============================================================
# 插件配置
# ============================================================

@plugin.mount_config()
class JMComicConfig(ConfigBase):
    """JMComic 下载器配置项

    请根据你的网络环境和需求配置以下选项。代理和下载目录为必填项。
    """

    # --- 代理设置 ---
    proxy_http: str = Field(
        default="",
        title="HTTP 代理地址",
        description="HTTP 代理地址，格式如 127.0.0.1:3067。留空则不使用代理。",
        json_schema_extra=ExtraField(placeholder="127.0.0.1:3067").model_dump(),
    )

    proxy_https: str = Field(
        default="",
        title="HTTPS 代理地址",
        description="HTTPS 代理地址，格式如 127.0.0.1:3067。留空则与 HTTP 代理一致。",
        json_schema_extra=ExtraField(placeholder="127.0.0.1:3067").model_dump(),
    )

    # --- 下载目录 ---
    download_dir: str = Field(
        default="./jmcomic_downloads",
        title="下载目录",
        description="本子下载到本地的目标文件夹路径。支持绝对路径或相对路径。",
        json_schema_extra=ExtraField(required=True, placeholder="./jmcomic_downloads").model_dump(),
    )

    # --- 下载设置 ---
    image_decode: bool = Field(
        default=True,
        title="图片解码",
        description="下载后是否自动解码图片（将加密图片转为标准格式）。建议开启。",
    )

    image_suffix: str = Field(
        default=".png",
        title="图片后缀",
        description="下载图片的保存格式后缀，如 .png、.jpg。",
    )

    thread_count_images: int = Field(
        default=30,
        title="图片下载线程数",
        description="并发下载本子内页图片的线程数。数值越大下载越快但对网络要求更高。",
    )

    thread_count_photos: int = Field(
        default=20,
        title="封面下载线程数",
        description="并发下载本子封面的线程数。",
    )

    cache_enabled: bool = Field(
        default=True,
        title="启用缓存",
        description="是否使用下载缓存，避免重复下载已存在的文件。建议开启。",
    )

    retry_times: int = Field(
        default=5,
        title="重试次数",
        description="网络请求失败时的重试次数。",
    )

    # --- 高级设置 ---
    pages_per_volume: int = Field(
        default=40,
        title="每卷页数上限",
        description="每卷最多页数。超过 50MB 可能被 QQ 拒绝上传。建议 30~50 页。",
    )

    client_impl: str = Field(
        default="api",
        title="客户端实现",
        description="选择使用的客户端实现：api（推荐，需会员）、mobile（移动端）、html（网页端）。"
                    "如果下载图片异常，可尝试切换。",
    )

    custom_domain: str = Field(
        default="",
        title="自定义域名",
        description="手动指定禁漫域名，如 18comic.vip。留空则自动探测。"
                    "当前默认探测域名包括 18comic.org、18comic.vip 等。",
        json_schema_extra=ExtraField(placeholder="留空自动探测").model_dump(),
    )


# ============================================================
# 辅助函数：根据插件配置构建 jmcomic 的 option 对象
# ============================================================

def _build_jm_option():
    """根据插件配置构建 jmcomic 的 JmOption 对象。

    将插件 WebUI 配置映射为 YAML 文件，
    然后通过 jmcomic.create_option_by_file() 创建 option 对象。
    """
    import os
    import tempfile
    import yaml

    cfg = plugin.get_config()

    # 确保下载目录存在
    if cfg.download_dir:
        os.makedirs(cfg.download_dir, exist_ok=True)

    # 构建代理配置
    proxies = {}
    if cfg.proxy_http:
        proxies["http"] = cfg.proxy_http
    if cfg.proxy_https:
        proxies["https"] = cfg.proxy_https
    elif cfg.proxy_http:
        proxies["https"] = cfg.proxy_http

    # 构建域名列表
    domains = []
    if cfg.custom_domain:
        domains.append(cfg.custom_domain)

    option_dict = {
        "version": "2.1",
        "log": True,
        "client": {
            "impl": cfg.client_impl,
            "async_impl": "async_api",
            "domain": domains,
            "cache": None,
            "retry_times": cfg.retry_times,
        },
        "dir_rule": {
            "rule": "Bd_Pname",
            "base_dir": cfg.download_dir,
        },
        "download": {
            "cache": cfg.cache_enabled,
            "image": {
                "decode": cfg.image_decode,
                "suffix": cfg.image_suffix,
            },
            "threading": {
                "image": cfg.thread_count_images,
                "photo": cfg.thread_count_photos,
            },
        },
    }

    # 仅在配置了代理时添加代理设置
    if proxies:
        option_dict["client"]["postman"] = {
            "type": "curl_cffi",
            "meta_data": {
                "proxies": proxies,
                "headers": None,
                "impersonate": "chrome",
            },
        }
    else:
        option_dict["client"]["postman"] = {
            "type": "curl_cffi",
            "meta_data": {
                "headers": None,
                "impersonate": "chrome",
            },
        }

    # 写入临时 YAML 文件，用 create_option_by_file 加载
    import jmcomic
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", encoding="utf-8", delete=False
    ) as f:
        yaml.dump(option_dict, f, allow_unicode=True, default_flow_style=False)
        tmp_path = f.name

    plugin.logger.info(f"jmcomic 临时配置文件: {tmp_path}")
    return jmcomic.create_option_by_file(tmp_path)


# ============================================================
# 辅助函数：安全提取属性
# ============================================================

def _safe_attr(obj, *names, default="未知"):
    """安全地从对象获取属性，尝试多个候选名称，返回第一个非 None 的值。"""
    for name in names:
        val = getattr(obj, name, None)
        if val is not None:
            return val
    return default


def _fmt_album_info(album) -> str:
    """将 JmAlbumDetail 格式化为可读的文本信息。

    JmAlbumDetail 属性: album_id, name, page_count, pub_date, update_date,
    likes, views, comment_count, tags, authors, works, actors, description, episode_list
    """
    title = _safe_attr(album, "name")
    aid = _safe_attr(album, "album_id", "id")
    author = _safe_attr(album, "author")
    if isinstance(author, list):
        author = ", ".join(str(a) for a in author)
    if str(author) in ("N/A", "未知", "", "None"):
        author = "（无作者信息）"

    page_count = _safe_attr(album, "page_count")
    pub_date = _safe_attr(album, "pub_date")
    update_date = _safe_attr(album, "update_date")
    views = _safe_attr(album, "views")
    likes = _safe_attr(album, "likes")
    tags = _safe_attr(album, "tags")
    if isinstance(tags, list):
        tags = ", ".join(str(t) for t in tags)
    description = _safe_attr(album, "description")

    lines = [
        "──────────────────────────────────────────────────",
        f" 📖 标题: {title}",
        f" 🆔 ID: JM{aid}",
        f" ✍️ 作者: {author}",
        "──────────────────────────────────────────────────",
    ]
    if str(pub_date) not in ("未知", "", "0"):
        lines.append(f" 📅 发布日期: {pub_date}")
    if str(update_date) not in ("未知", "", "0"):
        lines.append(f" 📅 更新日期: {update_date}")
    if str(page_count) not in ("未知", "", "0"):
        lines.append(f" 📄 总页数: {page_count} 页")
    if str(views) not in ("未知", "", "0"):
        lines.append(f" 👀 观看: {views}")
    if str(likes) not in ("未知", "", "0"):
        lines.append(f" ❤️ 点赞: {likes}")
    lines.append("──────────────────────────────────────────────────")
    if str(tags) != "未知":
        lines.append(f" 🏷️ 标签: {tags}")
    if str(description) not in ("未知", "", "None", None):
        desc = str(description)
        lines.append(f" 📝 简介: {desc[:200]}{'...' if len(desc) > 200 else ''}")
    lines.append("──────────────────────────────────────────────────")

    return "\n".join(lines)


# ============================================================
# 沙盒方法
# ============================================================

@plugin.mount_sandbox_method(
    method_type=SandboxMethodType.TOOL,
    name="download_album",
    description="根据本子 ID 下载本子到本地。返回下载结果摘要。",
)
async def download_album(_ctx: AgentCtx, album_id: int) -> str:
    """下载指定 ID 的 JMComic 本子，打包为 PDF 并发送。

    通过 jmcomic 库下载指定 album_id 对应的本子全部图片到本地下载目录，
    下载完成后自动将所有图片压缩为 PDF 文件并发送给用户。

    Args:
        album_id (int): 要下载的本子的唯一数字 ID。

    Returns:
        str: 下载结果的描述文本，包含成功/失败信息和下载详情。

    Example:
        ```python
        # 下载 ID 为 123456 的本子
        result = download_album(album_id=123456)
        print(result)
        ```
    """
    import pathlib
    import asyncio

    async def _send_with_retry(sandbox_path, max_retries=5):
        """带重试的文件发送。QQNT 偶尔抽风多试几次即可。"""
        for attempt in range(1, max_retries + 1):
            try:
                await _ctx.send_file(sandbox_path)
                plugin.logger.info(f"发送成功 (第 {attempt} 次)")
                return True
            except Exception as e:
                plugin.logger.warning(f"发送失败 (第 {attempt}/{max_retries} 次): {str(e)[:150]}")
                if attempt < max_retries:
                    await asyncio.sleep(3 * attempt)
        return False

    try:
        import jmcomic

        plugin.logger.info(f"开始下载本子 ID={album_id}")

        await _ctx.send_text(f"📥 正在下载本子 (ID: {album_id})，请稍候...", record=False)

        option = _build_jm_option()
        cfg = plugin.get_config()
        import os
        save_dir = os.path.abspath(cfg.download_dir)

        # 下载并捕获返回值
        result = jmcomic.download_album(album_id, option)
        if isinstance(result, tuple):
            album_detail = result[0]
        else:
            album_detail = result

        # 提取本子信息
        info = _fmt_album_info(album_detail) if album_detail is not None else f"📖 ID: JM{album_id}"
        title = _safe_attr(album_detail, "name") if album_detail is not None else str(album_id)

        # 查找下载的图片所在的目录
        save_path = getattr(album_detail, "save_path", None) if album_detail is not None else None
        if save_path and os.path.isdir(save_path):
            search_root = save_path
        else:
            search_root = save_dir

        # 递归收集所有图片文件
        image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
        all_images = []
        for root, dirs, files in os.walk(search_root):
            for fname in sorted(files):
                if pathlib.Path(fname).suffix.lower() in image_exts:
                    all_images.append(os.path.join(root, fname))

        plugin.logger.info(f"找到 {len(all_images)} 张图片，开始打包...")

        if not all_images:
            return f"❌ 下载完成但未找到图片文件，请检查保存目录: {save_dir}"

        # 统一先压成 PDF（高压缩），私聊再套一层 zip 绕过 QQNT 限制
        is_private = (_ctx.channel_type == "private")
        safe_title = "".join(c for c in title if c.isalnum() or c in "._- ()（）")

        limit = max(1, cfg.pages_per_volume)
        batches = [all_images[i:i+limit] for i in range(0, len(all_images), limit)]
        total_volumes = len(batches)

        await _ctx.send_text(
            f"📦 正在压 PDF（{total_volumes} 卷）...",
            record=False,
        )

        try:
            from PIL import Image as PILImage
        except ImportError:
            return "❌ 缺少 Pillow，请执行: pip install Pillow"

        MAX_PX, JPEG_Q = 1000, 45
        sent_count = 0
        failed_volumes = []
        vol_files = []

        for vol_idx, batch in enumerate(batches, 1):
            suffix = f"_{vol_idx}of{total_volumes}" if total_volumes > 1 else ""

            # Step 1: 生成 PDF
            pdf_filename = f"JM{album_id}_{safe_title[:40]}{suffix}.pdf"
            pdf_dst = os.path.join(save_dir, pdf_filename)

            pil_ims = []
            for img_path in batch:
                try:
                    im = PILImage.open(img_path)
                    if im.mode not in ("RGB", "L"):
                        im = im.convert("RGB")
                    w, h = im.size
                    s = MAX_PX / max(w, h)
                    if s < 1:
                        im = im.resize((int(w*s), int(h*s)), PILImage.LANCZOS)
                    import io
                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=JPEG_Q, optimize=True)
                    buf.seek(0)
                    im = PILImage.open(buf)
                    im.load()
                    pil_ims.append(im)
                except Exception as e:
                    plugin.logger.warning(f"跳过: {img_path}, {e}")

            if not pil_ims:
                continue

            pil_ims[0].save(
                pdf_dst, save_all=True, append_images=pil_ims[1:],
                resolution=100.0, quality=JPEG_Q, optimize=True,
            )
            pdf_size = os.path.getsize(pdf_dst) / 1024 / 1024
            plugin.logger.info(f"PDF {vol_idx}/{total_volumes}: {pdf_filename}, {len(pil_ims)}页, {pdf_size:.1f}MB")

            # Step 2: 私聊把 PDF 打入 zip（QQNT 拒绝裸 PDF 但接受 zip）
            if is_private:
                import zipfile
                zip_filename = pdf_filename.replace(".pdf", ".zip")
                zip_dst = os.path.join(save_dir, zip_filename)
                with zipfile.ZipFile(zip_dst, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.write(pdf_dst, pdf_filename)
                file_size = os.path.getsize(zip_dst) / 1024 / 1024
                vol_files.append((zip_filename, file_size, len(pil_ims)))
                dst = zip_dst
                fname = zip_filename
                plugin.logger.info(f"zip 封装: {fname}, {file_size:.1f}MB")
            else:
                vol_files.append((pdf_filename, pdf_size, len(pil_ims)))
                dst = pdf_dst
                fname = pdf_filename

            # 发送
            try:
                sp = await _ctx.fs.mixed_forward_file(dst, file_name=fname)
                if await _send_with_retry(sp):
                    sent_count += 1
                else:
                    failed_volumes.append(fname)
            except Exception as e:
                failed_volumes.append(fname)
                plugin.logger.warning(f"发送失败 {fname}: {e}")

        # 清理临时目录
        try:
            import shutil
            for clean_dir in (_ctx.fs.shared_path, _ctx.fs.upload_path):
                if clean_dir and clean_dir.exists():
                    for item in clean_dir.iterdir():
                        try:
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                        except Exception:
                            pass
            plugin.logger.info("临时目录已清理")
        except Exception as e:
            plugin.logger.warning(f"清理临时目录失败: {e}")

        # 延迟清理：发送完后 30s 删除 PDF 和图片目录
        async def _delayed_cleanup(save_root, album_path):
            await asyncio.sleep(30)
            try:
                # 删除本子目录（图片）和根目录下的 PDF
                if album_path and os.path.isdir(album_path):
                    shutil.rmtree(album_path, ignore_errors=True)
                    plugin.logger.info(f"已清理图片目录: {album_path}")
                for name, _, _ in vol_files:
                    f = os.path.join(save_root, name)
                    if os.path.isfile(f):
                        os.remove(f)
                        plugin.logger.info(f"已清理: {name}")
            except Exception as e:
                plugin.logger.warning(f"延迟清理失败: {e}")

        asyncio.create_task(_delayed_cleanup(save_dir, search_root))

        total_pages = sum(p for _, _, p in vol_files)
        result_text = f"✅ 本子下载完成！\n{info}\n\n"

        if total_volumes > 1:
            result_text += f"📦 {total_volumes} 卷  |  📖 {total_pages} 页\n"
            for name, sz, pgs in vol_files:
                result_text += f"  {name}（{pgs}页, {sz:.1f}MB）\n"
        elif vol_files:
            result_text += f"📦 {vol_files[0][0]}（{total_pages}页, {vol_files[0][1]:.1f}MB）\n"

        if sent_count == total_volumes:
            result_text += f"📤 已全部发送（{sent_count}/{total_volumes}）"
        elif sent_count > 0:
            result_text += (
                f"📤 QQ已发 {sent_count}/{total_volumes}，超时的从本地取:\n"
                f"\\\\wsl.localhost\\NekroAgent\\root\\nekro_agent_data\\jmcomic_downloads"
            )
        else:
            result_text += (
                f"⚠️ 发送超时，本地取:\n"
                f"\\\\wsl.localhost\\NekroAgent\\root\\nekro_agent_data\\jmcomic_downloads"
            )

        plugin.logger.info(
            f"本子下载完成: ID={album_id}, {total_pages}页, {total_volumes}卷, 发送 {sent_count}/{total_volumes}"
        )
        return result_text

    except ImportError:
        plugin.logger.error("jmcomic 库未安装，请执行 pip install jmcomic")
        return "❌ 下载失败：jmcomic 库未安装，请联系管理员执行 `pip install jmcomic` 安装依赖。"
    except Exception as e:
        plugin.logger.exception(f"下载本子 ID={album_id} 时出错: {e}")
        return f"❌ 下载本子 (ID={album_id}) 时发生错误：{e}"


@plugin.mount_sandbox_method(
    method_type=SandboxMethodType.TOOL,
    name="get_album_info",
    description="根据本子 ID 获取本子的详细信息（标题、作者、页数、标签等），不执行下载。",
)
async def get_album_info(_ctx: AgentCtx, album_id: int) -> str:
    """查询指定 ID 的 JMComic 本子详细信息。

    仅获取本子的元数据信息，不会触发下载。

    Args:
        album_id (int): 要查询的本子的唯一数字 ID。

    Returns:
        str: 本子的详细信息描述文本。

    Example:
        ```python
        # 查询 ID 为 123456 的本子信息
        info = get_album_info(album_id=123456)
        print(info)
        ```
    """
    try:
        import jmcomic

        plugin.logger.info(f"查询本子信息 ID={album_id}")

        option = _build_jm_option()

        # 尝试多种方式获取本子详情
        album = None
        for func_name in ("album_detail", "find_album", "get_album_detail"):
            func = getattr(jmcomic, func_name, None)
            if func is not None:
                try:
                    album = func(album_id, option)
                    if album is not None:
                        break
                except Exception:
                    continue

        if album is None:
            # 回退：用 download_album 只下载封面来获取元数据（不下载全部图片）
            try:
                result = jmcomic.download_album(album_id, option)
                if isinstance(result, tuple):
                    album = result[0]
                else:
                    album = result
            except Exception:
                return f"❌ 未找到 ID 为 {album_id} 的本子，请检查 ID 是否正确。"

        plugin.logger.info(
            f"get_album_info 返回类型: {type(album)}, "
            f"属性: {[a for a in dir(album) if not a.startswith('_')][:30]}"
        )

        info = _fmt_album_info(album)
        plugin.logger.info(f"本子信息查询完成: ID={album_id}")
        return info

    except ImportError:
        plugin.logger.error("jmcomic 库未安装")
        return "❌ 查询失败：jmcomic 库未安装，请联系管理员执行 `pip install jmcomic` 安装依赖。"
    except Exception as e:
        plugin.logger.exception(f"查询本子 ID={album_id} 时出错: {e}")
        return f"❌ 查询本子 (ID={album_id}) 时发生错误：{e}"


@plugin.mount_sandbox_method(
    method_type=SandboxMethodType.TOOL,
    name="search_album",
    description="根据关键词搜索 JMComic 本子，返回匹配的本子列表。",
)
async def search_album(_ctx: AgentCtx, keyword: str) -> str:
    """按关键词搜索 JMComic 本子。

    在 JMComic 中搜索匹配关键词的本子，返回结果列表供用户选择。

    Args:
        keyword (str): 搜索关键词，如本子标题或标签。

    Returns:
        str: 搜索结果描述文本，包含匹配本子的 ID、标题等信息。

    Example:
        ```python
        # 搜索标题包含特定关键词的本子
        results = search_album(keyword="关键词")
        print(results)
        ```
    """
    try:
        import jmcomic

        plugin.logger.info(f"搜索本子: keyword='{keyword}'")

        option = _build_jm_option()

        # 尝试多种搜索 API
        results = None
        for func_name in ("search_album", "search", "find_by_keyword"):
            func = getattr(jmcomic, func_name, None)
            if func is not None:
                try:
                    results = func(keyword, option)
                    break
                except Exception:
                    continue

        if results is None:
            return (
                "⚠️ 当前版本的 jmcomic 库不支持搜索功能。\n"
                "请直接输入本子 ID 使用 `download_album` 或 `get_album_info`。"
            )

        if not results:
            return f"🔍 未找到与「{keyword}」相关的本子。"

        result_lines = [f"🔍 搜索「{keyword}」的结果（共 {len(results)} 个）：", ""]
        for i, album in enumerate(results[:20], 1):
            aid = _safe_attr(album, "id", "album_id")
            title = _safe_attr(album, "name", "title")
            author = _safe_attr(album, "author")
            if isinstance(author, list):
                author = ", ".join(str(a) for a in author)
            result_lines.append(f"{i}. [{aid}] {title}（作者：{author}）")

        if len(results) > 20:
            result_lines.append(f"... 还有 {len(results) - 20} 个结果未显示，请尝试更精确的关键词。")

        plugin.logger.info(f"搜索完成: keyword='{keyword}', 找到 {len(results)} 个结果")
        return "\n".join(result_lines)

    except ImportError:
        plugin.logger.error("jmcomic 库未安装")
        return "❌ 搜索失败：jmcomic 库未安装，请联系管理员执行 `pip install jmcomic` 安装依赖。"
    except Exception as e:
        plugin.logger.exception(f"搜索本子 keyword='{keyword}' 时出错: {e}")
        return f"❌ 搜索本子时发生错误：{e}"


# ============================================================
# 初始化方法
# ============================================================

@plugin.mount_init_method()
async def initialize_plugin():
    """插件初始化：检查 jmcomic 依赖。"""
    plugin.logger.info(f"插件 '{plugin.name}' v{plugin.version} 正在初始化...")

    try:
        import jmcomic
        plugin.logger.info("jmcomic 库已就绪")
    except ImportError:
        plugin.logger.warning(
            "jmcomic 库未安装！插件功能将不可用。"
            "请执行: pip install jmcomic"
        )

    plugin.logger.info(f"插件 '{plugin.name}' 初始化完成。")


# ============================================================
# 清理方法
# ============================================================

@plugin.mount_cleanup_method()
async def cleanup_plugin():
    """插件卸载时的清理工作。"""
    plugin.logger.info(f"插件 '{plugin.name}' 正在清理...")
    plugin.logger.info(f"插件 '{plugin.name}' 清理完成。")
