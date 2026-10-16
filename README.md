# Manjaro Music Kit · 桌面音乐迁移包

**克隆后运行 `bash install.sh`，安装器自动判断桌面和显示会话，无需自己选择 KDE、Xfce 或 GNOME。**

提供 MPD 本地音乐播放、歌单、粉色频谱、自动扫描音乐库及应用菜单入口。不包含歌曲、账号、网盘 Cookie 或旧机器的播放历史。

## 一、新电脑安装

在已登录的 Manjaro 图形桌面打开终端：

```bash
git clone https://github.com/jingpengju391/manjaro-music-kit.git
cd manjaro-music-kit
bash install.sh
```

如果没有 Git，先安装：

```bash
sudo pacman -Syu --needed git
```

安装器会依次执行：

1. 识别桌面及 X11 / Wayland，选择对应界面和依赖。
2. 缺少依赖时调用 `sudo pacman -Syu --needed`，按提示输入密码并确认。这个步骤包含系统完整升级，取消后会停止，不写音乐配置。
3. 检查 Python、GTK、用户服务和音频服务是否可用。
4. 修改前备份原文件、受影响快捷键及 MPD 服务的启用/运行状态。
5. 安装用户配置、创建“桌面音乐”应用菜单入口、启用音乐库同步服务。
6. 默认打开播放器；有歌曲时开始播放，空音乐库也可以打开。

**不要执行 `sudo bash install.sh`。** 配置属于当前用户。安装会重启用户 MPD，正在播放的音乐会短暂中断。请保留安装输出中的备份路径。

把自己的歌曲放入 `~/Music`。应用菜单中打开 **桌面音乐**，或运行 `~/.local/bin/music`。

只想安装、暂时不打开窗口或播放：

```bash
bash install.sh --no-launch
```

## 二、支持的桌面与效果差异

| 环境 | 自动选择的界面 | 窗口效果 | 快捷键 |
| --- | --- | --- | --- |
| Xfce + X11 | 原来的两个桌面小组件 | 歌单、半透明圆角频谱，自动定位屏幕右上角并置底 | 自动配置；已占用的键保留 |
| KDE Plasma + Wayland | GTK Layer Shell 桌面组件 | 右上角、透明圆角、底层、不可拖拽；无标题栏和工具栏 | 歌单键盘操作及应用菜单；全局键在 KDE 设置中分配 |
| KDE Plasma + X11 | GTK / VTE 兼容播放器 | 歌单与频谱同窗，可移动缩放 | 应用菜单及控制按钮 |
| GNOME + X11 / Wayland | GTK / VTE 兼容播放器 | 歌单与粉色频谱同窗，可以移动、缩放 | 检测到 GNOME 快捷键接口时自动配置；锁定或冲突时跳过 |
| Xfce + Wayland / 其他图形桌面 | GTK / VTE 兼容播放器 | 普通可移动窗口 | 以应用菜单和窗口按钮为准 |

Wayland 模式不调用 `xdotool`、`xrandr` 或 `xprop`，也不要求安装 XFCE Terminal。**不会承诺在 Wayland 下强制置底、固定右上角、隐藏边框或复制 Xfce 的透明效果。**

本包使用目标电脑官方仓库的 MPD、CAVA、GTK/VTE，不携带本机编译的二进制程序。适用于依赖仍能从仓库安装的 Manjaro/Arch 系统，不承诺任意历史版本可直接运行；旧系统需要先完成更新。

音频需要已正常运行的 PulseAudio，或提供 PulseAudio 兼容接口的 PipeWire。安装器不会擅自替换桌面的音频系统。不同桌面之间切换后，重新运行安装命令即可补齐所需界面依赖。

## 三、使用与快捷键

| 命令 | 功能 | Xfce/X11、支持的 GNOME 默认快捷键 |
| --- | --- | --- |
| `~/.local/bin/music` | 扫描并补全队列，显示窗口，有歌曲时播放 | `Ctrl+Alt+M` |
| `~/.local/bin/music toggle` | 播放 / 暂停 | `Ctrl+Alt+P` |
| `~/.local/bin/music prev` | 上一首 | `Ctrl+Alt+,` |
| `~/.local/bin/music next` | 下一首 | `Ctrl+Alt+.` |
| `~/.local/bin/music hide` | 关闭播放器窗口，继续播放 | `Ctrl+Alt+H` |
| `~/.local/bin/music stop` | 暂停并关闭窗口 | — |

如果 `~/.local/bin` 已加入 PATH，可以直接使用 `music`。服务随登录启动，以后登录不会自动弹出窗口或主动开始播放。

KDE 不会写入 XFCE 快捷键设置，也不会直接改写 KGlobalAccel 的私有配置。可以先使用窗口上的控制按钮；如需全局快捷键，在 **系统设置 → 键盘 → 快捷键** 中添加上述命令（具体菜单名称随 Plasma 版本变化）。应用菜单还提供播放暂停、上一首、下一首及隐藏操作。

### 歌单内操作

| 按键 | 功能 |
| --- | --- |
| 上下方向键 | 选择歌曲 |
| 回车 | 播放所选歌曲 |
| 空格 | 播放 / 暂停 |
| `d` | 仅从播放队列移除，不删除文件 |
| `u` | 更新音乐库 |
| `2` | 打开 ncmpcpp 音乐库界面 |
| `q` | 退出当前歌单界面 |

再次执行 `music` 会补回音乐库中尚未进入队列的歌曲。

## 四、更新

在原来克隆的目录执行：

```bash
git pull --ff-only && bash install.sh
```

`git pull` 只更新仓库；后面的安装命令才会应用配置，每次都会生成新备份。已有个人 MPD/ncmpcpp 配置会被备份后替换，不会自动合并；歌曲、数据库和队列文件不主动删除，但重新扫描/播放可能改变当前队列和播放状态。

如果 Git 提示有未提交修改，先保存自己的更改，不要强制重置。

## 五、检查与恢复

只读检查，不安装软件、不修改配置、不启动服务：

```bash
bash install.sh --check
```

旧参数 `--dry-run` 仍可使用，但现在也会检查桌面和依赖；若缺少依赖，运行正常安装命令自动补齐。

查看新版可恢复备份：

```bash
bash install.sh --list-backups
```

恢复最近一次安装前的配置：

```bash
bash install.sh --restore
```

恢复指定备份：

```bash
bash install.sh --restore ~/.local/state/manjaro-music-kit/backups/实际时间戳
```

也可以直接运行安装时打印的备份目录中的脚本，不依赖仓库是否保留：

```bash
python3 /完整备份目录/restore.py
```

恢复前先关闭播放器窗口。恢复会覆盖安装后对这些文件的修改；会恢复原有配置、符号链接、被修改的快捷键以及两个用户服务的启用/运行状态。原来不存在的文件会移除。不会卸载系统包、撤销系统升级、删除歌曲，或精确还原播放进度和队列。重复安装后的最新备份是“最近一次安装之前”，最初状态要找第一次的备份。

旧版本只保存原文件和 `shortcuts.json` 的备份没有新恢复清单，仍需手动还原；不会假装能一键恢复它们。

## 六、配置位置与排错

| 路径 | 内容 |
| --- | --- |
| `~/.local/bin/music` | 跨桌面启动与播放控制 |
| `~/.config/mpd/mpd.conf` | MPD 音乐库和音频输出 |
| `~/.config/ncmpcpp/` | 歌单、频谱、兼容窗口、同步脚本 |
| `~/.config/systemd/user/music-library-sync.service` | 音乐库同步服务 |
| `~/.config/systemd/user/mpd.service.d/music-kit.conf` | 为 MPD 指定配置路径 |
| `~/.local/share/applications/manjaro-music-kit.desktop` | 应用菜单入口 |
| `~/.local/state/manjaro-music-kit/backups/` | 修改前备份 |
| `~/.local/state/manjaro-music-kit/player.log` | 兼容播放器日志 |

配置和应用入口支持 `XDG_CONFIG_HOME` / `XDG_DATA_HOME`。标准安装仍使用上表路径。

- **Python 报 GLIBC 版本错误**：先完整升级系统，`sudo pacman -Syu glibc python`，重启后重试；不要手动复制其他电脑的系统库。
- **音频检查失败**：先确认桌面上的其他应用能发声，运行 `pactl info` 查看 PipeWire/PulseAudio 是否工作。
- **服务启动失败**：查看 `systemctl --user status mpd music-library-sync` 以及 `journalctl --user -u mpd -u music-library-sync -n 60`。已有其他 MPD 占用 6600 端口时需先处理冲突。
- **兼容播放器未出现**：查看上表的 `player.log`；确认使用已登录的图形桌面，不是 SSH 或 TTY。
- **快捷键无反应**：检查桌面冲突；KDE 使用窗口控制按钮或自行绑定全局键。
- **没有歌曲**：将支持的本地音频放入 `~/Music`，再运行 `music`。新电脑不会带来旧机器的音乐。

## 七、验证范围

自动化测试覆盖桌面/会话分流、依赖选择、只读检查、取消安装、文件和快捷键备份、KDE 安装恢复。GTK/VTE 窗口在当前 Xfce/X11 上通过隔离图形冒烟测试：窗口、歌单子进程、模拟频谱帧及进程清理。**真实 KDE/GNOME/Wayland 的窗口效果和音频播放尚未现场验收**。

开发检查：

```bash
python3 -m unittest discover -s tests -v
# 需要图形会话和 GTK/VTE；使用模拟歌单/频谱，不操作当前 MPD
dbus-run-session -- python3 tests/smoke_player.py
```

兼容窗口使用 [GTK/VTE 的进程启动接口](https://gnome.pages.gitlab.gnome.org/vte/gtk3/method.Terminal.spawn_async.html) 和 [GApplication 单实例命令分发](https://docs.gtk.org/gio/flags.ApplicationFlags.html)。

### KDE Wayland 外观更新

旧版本的带按钮兼容窗口与 XFCE 桌面外观不同。更新后，KDE Wayland 使用 gtk-layer-shell 固定到右上角，以桌面底层显示；安装器自动补齐依赖。执行 `git pull --ff-only` 后运行 `bash install.sh`。需要原生 Wayland GTK 后端，勿设置 `GDK_BACKEND=x11`。KDE X11 和 GNOME 仍使用兼容窗口。此分支尚需真实 KDE Wayland 验收，缩放比例及字体可能影响实际尺寸。
