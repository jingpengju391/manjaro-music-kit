# Manjaro 桌面音乐迁移包

适用于 Manjaro / Arch、XFCE、X11。其他桌面环境的窗口定位、透明效果及快捷键未验证；Wayland 不支持这套窗口管理方式。

把整个文件夹复制到新电脑，在该文件夹打开终端，执行：

```bash
bash install.sh
```

安装器会按需通过 pacman 安装官方仓库依赖（可能要求 sudo 密码），备份同名配置，安装播放器与服务，设置快捷键并显示界面开始播放。不要用 sudo 运行整个安装器。需要联网安装缺少的依赖；须在已登录的桌面会话内运行。

只检查迁移文件和 Python 语法、不修改系统：

```bash
bash install.sh --dry-run
```

## 包含内容

- MPD 本地播放和 ncmpcpp 完整界面。
- 右上角半透明圆角歌单，长标题省略、时间独立对齐。
- 奶茶绿当前歌曲高亮、加粗粉色进度线。
- 30 根、3.8 像素宽的粉色频谱；自动定位笔记本屏幕或第一个显示器。
- 自动监听音乐库更新并补充队列。
- 安装时创建 `~/Music` 作为音乐库；自行放入歌曲后自动扫描。

不包含歌曲、MPD 数据库、历史队列、旧备份、OpenList、网盘 Cookie、账号或浏览器配置。频谱使用新机器官方仓库的 CAVA，不携带本机提取的二进制库。

## 使用

| 命令/快捷键 | 功能 |
|---|---|
| `~/.local/bin/music` / Ctrl+Alt+M | 扫描并补全队列，显示窗口并播放 |
| `~/.local/bin/music toggle` / Ctrl+Alt+P | 播放/暂停 |
| `~/.local/bin/music prev` / Ctrl+Alt+, | 上一首 |
| `~/.local/bin/music next` / Ctrl+Alt+. | 下一首 |
| `~/.local/bin/music hide` / Ctrl+Alt+H | 隐藏窗口，继续播放 |
| `~/.local/bin/music stop` | 暂停并隐藏 |

如果 `~/.local/bin` 已在 PATH 中，可直接输入 `music`。应用菜单也有“桌面音乐”。服务随登录启动，但以后登录不会自动打开窗口或开始播放。

歌单窗口内：上下方向键选歌、回车播放、空格暂停，`d` 仅从队列移除歌曲（不会删除文件），`u` 更新数据库，`2` 打开 ncmpcpp 音乐库；完整补回队列用 Ctrl+Alt+M。

旧配置和被覆盖快捷键记录保存在 `~/.local/state/manjaro-music-kit/backups/时间戳/`。安装会重启 MPD，因此运行中的音乐会短暂中断。现有音乐文件不删除。

## 传输与版本管理

迁移包只含播放器程序、配置和安装脚本，可以直接使用 Git 管理和迁移。新机器的歌曲自行放到 `~/Music`。

可在上级目录打包后复制到新电脑：

```bash
tar -czf manjaro-music-kit.tar.gz manjaro-music-kit
```

若 pacman 提示依赖版本冲突，请先完成系统更新，再重新运行安装器。安装器不会自动执行系统升级。
