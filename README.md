# 寒月
* 具备流量整形加速的旁路网关
* 仅供学习与研究，不支持机场的双端自建方案

* 基于性能考量，尽量避免使用虚拟交换


[![Telegram](https://cdn.jsdelivr.net/gh/Patrolavia/telegram-badge@8fe3382b3fd3a1c533ba270e608035a27e430c2e/chat.svg)](https://t.me/de_GWD_DQ)  

## Debian 13 (trixie)

本地安装脚本已加入 Debian 13（amd64 / arm64）适配：

* `client`、`server` 和 `@init` 保留 Debian 13 当前的 APT 软件源，包括 DEB822 `.sources` 文件，不再将其改写为 bookworm；安装前应确保系统源已经正确指向 trixie。
* DNS 工具使用 `bind9-dnsutils`，显式安装自动更新所需的 `cron`，补齐预编译 Nginx 的 Brotli、crypt 和 arm64 profiler 运行库。
* amd64 Nginx 依赖 `libmimalloc.so.2`。安装器从 Debian 官方下载 `libmimalloc2.0_2.0.9+ds-2_amd64.deb` 并校验固定 SHA-256，不添加 bookworm 软件源；不能用 `libmimalloc3` 或将 `.so.3` 链接为 `.so.2` 替代。该兼容库随 Debian 12 包维护，后续更换 Nginx 构建时应同步更新此依赖。
* 客户端管理界面改用 Debian 13 的 PHP 8.4、Debian 12 的 PHP 8.2，安装器按系统版本选择 PHP CLI/FPM 与 Nginx FastCGI socket；不再将 Sury PHP 7.4 作为当前运行基线。迁移时须核对发行版实际包版本、扩展和 Web 页面行为。
* 通过 `/etc/sysctl.d/99-de-gwd.conf` 指向现有 `/etc/sysctl.conf`，使 Debian 13 的 systemd-sysctl 在启动时读取网关参数。客户端 WireGuard 管理模块已移除，不能把该 sysctl 链接解释为对客户端 WireGuard 功能的支持。
* 安装入口使用 LF 换行，并通过 `.gitattributes` 固定 Shell 脚本换行格式，避免 Windows 检出后的 CRLF 导致 Linux Bash 语法错误。

使用此修改版时，将本地 `client`（客户端另带对应架构的 `de_GWD_amd64.zip` 或 `de_GWD_arm64.zip`）或 `server` 上传到 Debian 13，在所在目录以 root 执行：

```bash
bash ./client
# 服务端执行：
bash ./server
```

仓库位于 `kos991/c1`；本地脚本、资源和更新入口应先核对来源、所选分支及摘要，再作为部署输入。原项目为 `jacyl4/de_GWD`，保留原作者署名与许可证；已有上游安装需手动执行本仓库脚本以切换更新来源。**本轮改动尚未发布并通过整机验收**，下文历史记录不等于当前候选版本或新版管理面的验证结果。

### 当前功能边界与升级保护

客户端继续保留 Pi-hole/Docker DNS 链、Xray/nftables、节点和 FWD/Rproxy 转发、证书、系统备份/还原及更新管理；服务端继续保留 WARP (`wgcf`)、HAProxy 转发、DoH、Nginx/证书与 Xray。客户端已经移除完整的 DDNS、WireGuard 和应用管理模块：不再提供 Cloudflare/3322 DDNS、`wg0`/客户端配置/二维码，以及 FileRun、MariaDB、Jellyfin、Vaultwarden、NFS 的安装、备份/还原和状态入口。**切除管理入口不自动停用或卸载既有应用与 WireGuard 服务，也不自动删除其数据、密钥、站点或许可证资料**；升级前应自行备份，并确认现有服务与 PHP 8.4/8.2 的兼容性。Docker 仍是 Pi-hole 基础依赖，证书的 Cloudflare DNS-01 流程不属于已移除的 DDNS 功能。

升级时会删除旧页面、`act` 接口和 `ui-*` 脚本，并清除 `ui-ddns*` 定时任务；旧的公开备份 `/var/www/html/restore/*` 迁入私有目录 `/var/lib/de_GWD/restore`（`root:www-data 0640`）。

网页更新和自动更新只执行 root 所有的 `/etc/de_GWD/update-source.json` 中固定的 HTTPS 地址和 SHA-256。**该文件不会自动生成**，未配置时网页更新和自动更新会直接报错退出。可以在命令行运行 `client` 更新，或以 root 写入 `{"url":"https://...","sha256":"..."}` 并设置 `root:root 0644`。

完整的组件旧基线、未发布候选和来源见 [COMPONENT-BASELINE.md](COMPONENT-BASELINE.md)；双端 DNS、代理、管理、更新与内核链路见 [RUNTIME-FLOWS.md](RUNTIME-FLOWS.md)。候选版本及镜像 digest 仍需在对应架构、Debian 发行版上核对上游公告、构建产物和实际运行结果，不应称为已修复漏洞或已通过生产验证。

### 验证状态

**本轮已执行（2026-10-25，Debian 13.7 amd64）**：客户端、服务端、初始化和所有 UI helper 通过 Shell/Python 语法检查；Web PHP 同时在 PHP 7.4 和 8.4.27 下通过语法检查。DoH 地址解析（含非法主机、端口、路径拒绝）、Pi-hole 上游写入和自动更新调用在 trixie 容器中实测通过。新版 `resource/client/Archive.zip` 完整性与摘要通过检查；隔离容器执行 `installWebUI`，确认旧 DDNS/WireGuard/应用页面和脚本删除、已有应用数据保留、旧备份迁至私有目录。独立 PHP 8.4 测试站点中，浏览器确认登录后菜单只剩概览、中转、节点管理、更新和 Pi-hole，已删除的 `act` 接口返回 404，未携带 CSRF token 的 POST 返回 403；旧 `app.php` 和 `ddns.php` 不在发布包内，但 PHP 内置服务器会把不存在的页面请求回退到首页（已部署 Nginx 的返回码尚未验收）。这些测试没有启动完整网关或真实 PHP-FPM。

**指定测试机整机验收（2026-10-25，Debian 13 amd64）**：在完成隔离检查后，经授权在 `192.168.0.111` 执行真实客户端安装。使用本地资源和现有可用 VMess WS/TLS 节点；PHP 8.4.27、Nginx、Pi-hole Docker、SmartDNS、mosdns、Xray、nftables 和 SSH 正常运行。浏览器通过实际 Nginx/PHP-FPM 登录，概览、节点、中转、更新页返回 200，旧 `app.php`、`ddns.php`、专属接口返回 404；缺少 CSRF token 返回 403，配置备份请求成功。国内/国外 DNS 查询及透明代理 HTTPS 请求通过；重建 DNS 配置并重启 nftables、相关服务后再次通过。25 项 POSIX 回归测试通过。原 `honk-core` 已停止并禁用自启动，原配置保留；定时网络回滚已取消，恢复备份保留在测试机 root 私有目录。

实测修复：首次安装补齐 DoH 上游配置；依赖、资源和固定镜像准备移到透明代理接管之前；Nginx 本地资源校验兼容 CRLF 并恢复 `libmimalloc.so.2` 依赖；Docker 公钥下载失败不再截断已有 keyring；不可变镜像可从本地缓存使用；空 nftables 集合不再输出非法 `elements = { }`，节点集合持久化改为冷启动可加载的声明，nft 加载失败向 systemd 返回错误。资源压缩包与摘要同步更新。

测速接口修复：节点 TCP、DoH 1/2、DoG 延迟与节点下载测速接口补齐 `auth.php` 初始化，修复调用未定义公共函数导致 HTTP 500、页面延迟留空的问题。目标机浏览器实际点击 `Ping (TCP)` 后节点及两个 DoH 延迟均显示数字；五个接口的未登录请求返回 401，缺少 CSRF token 返回 403，非法节点索引返回 400。这里显示的是 TCP 建连耗时，不代表完整 DoH 查询耗时。

更新角色判断修复：客户端以 `/opt/de_GWD/0conf` 为安装依据，不再因额外的 `/opt/de_GWD/version.php` 误判为服务端；服务端更新同时要求服务端版本文件存在且客户端配置不存在。错误角色返回非零并在修改系统前停止。新增六项角色边界回归测试，覆盖额外版本文件、正常双端安装和未安装主机。

更新重入实测：同一测试机执行客户端快速更新时，旧 Nginx 模板把 `/restore/` 与 `/terminal-auth.php` 重复拼接，导致服务失败却仍输出更新成功。现在每次生成完整配置并在重启前 `nginx -t`，已连续生成两次且只保留一份路由；失败通过更新入口返回非零并停止成功提示。修复缓存 ZIP、现有 DH 参数文件条件为假导致的误报失败；移除不存在的 `tcpTime` 调用。网卡 `clsact` 已存在时不再另加互斥 `ingress` qdisc，IFB 过滤器按 ingress hook 重建。在 111 上实际快速更新返回 0，Nginx/PHP/DNS/Xray/nftables/Docker/SSH 均 active，面板和透明代理 HTTPS 均返回 200；重跑 `/etc/rc_online.local` 无此前的 qdisc/RTNETLINK 报错。配置与服务层面的更新已验证，整机重启仍未验收。

**仍未验证**：整机重启、Debian 12 和 arm64 实机安装/升级、完整 LAN 客户端 UDP/透明代理、全部转发与反向代理操作、DoG、服务端完整安装、证书签发/续期、WARP。安装过程中实际升级了系统软件包及 Debian 回退内核，未重启当前 XanMod 内核；配置回滚不是系统软件包版本回滚。管理页使用安装器生成的自签名证书，浏览器需明确接受该测试证书。

**历史记录（2026-10-24，不适用于当前候选）**：此前 Debian 13.7 amd64 / Linux 6.12 环境中曾检查 APT 源处理、Nginx `libmimalloc.so.2` 兼容、旧 PHP 7.4 FastCGI/SQLite/XML/Intl、Docker `hello-world`、隔离网络的 nftables/TPROXY/策略路由和旧 ZIP 内二进制版本。旧 Sury PHP 7.4 的包版本/安全回补检查仅涉及旧部署，不能证明当前 Debian PHP 8.4/8.2 已修复特定漏洞；旧 PHP 7.4 的测试和安装函数已不作为当前安装方案。任何漏洞状态均以对应发行版/上游公告及实际安装包为准，不使用历史测试代替本轮验证。

### Nginx 证书和 APT 提示修复

服务端现在在签发证书前放行启用 UFW 时所需的 TCP 80、TCP 443 和 UDP 443；使用 HTTP-01 时，80 端口必须能从公网访问。ACME 失败、证书为空/过期、域名不匹配或证书与私钥不匹配都会中止安装，不再留下空证书后继续启用 Nginx。证书有效性通过 `openssl` 检查，Nginx 配置通过 `nginx -t` 后才重启。

Debian 13 的官方源会自动补上 Debian archive keyring 的 `Signed-By` 字段，已有第三方源保持不变，并使用 `.c1-before-signed-by.save` 备份源文件。该修复消除 APT 的 `Missing Signed-By` 提示，不改变镜像、套件或组件。

历史实机记录（2026-10-24）：`vm.jinfei.org` 当时因 UFW 仅放行 SSH 22 而无法公网访问 HTTP-01，放行 80/tcp、443/tcp、443/udp 后签发 Let's Encrypt 证书并验证外部 TLS 1.3/HTTPS 200。此记录不证明本轮候选 Nginx、PHP 或证书更新流程已通过测试。

### XanMod 内核安装入口

`resource/kernel/installkernel` 已替换为基于 `Eric86777/vps-tcp-tune` v5.4.19（参考提交 `7c2301cb3395ea8363ae7401719b416eb830714f`）的 XanMod-only 适配器。它只负责 Debian 12/13 amd64 的 XanMod 内核、Debian 回退内核、GRUB 和 initramfs，不引入原项目的 DNS、IPv6、代理或其他菜单功能。

安全行为：安装前检查系统、虚拟化、Secure Boot、DKMS、磁盘空间和可用 Debian 回退内核；不自动重启、不自动删除旧内核、不运行 `apt autoremove`。旧版 `rc_kernel.local` 自动备份到 `/opt/de_GWD/kernel-backup` 后停用，避免启动后删除当前或回退内核。安装、恢复和卸载均需显式输入 `YES`；卸载 XanMod 前必须先运行 Debian 内核。

客户端与服务端顶层菜单的第 2 项均为“管理 XanMod 内核（仅 amd64，手动重启）”，与内核子菜单一致：安装、恢复和卸载不会自动重启。内核脚本先下载到私有临时文件，验证下载非空且 Bash 语法有效，再进入菜单；下载失败会明确返回错误，避免执行空脚本却显示成功。服务端更新不再凭安装的 `linux-image` 包数量触发重启；客户端更新也不再把多内核并存误报为“Kernel updated”。

192.168.8.41 只读检查：当前运行 Debian `6.12.107+deb13-cloud-amd64`；已安装 XanMod `7.2.12-x64v2-xanmod1` 和 Debian `6.12.113+deb13-cloud-amd64` 回退内核，两者 boot/initrd 均存在。`GRUB_DEFAULT=0` 的主启动项指向已安装的 XanMod，但该机没有执行本轮重启；安装完成不等于运行内核已经切换。`--status`、`--check` 和 19 项隔离内核测试通过；未执行内核安装、卸载或重启。

历史记录（2026-10-24）：此前 Debian 13 amd64 测试机通过 `--help`、`--status`、`--check` 和 Bash 语法检查，未执行内核安装或重启；本轮内核路径仍待验收。

### C1 独立版本与 Xray 双端更新（当前 v2.0.0）

修改版从独立版本 **`v2.0.0`** 开始，当前发布版本号按维护者要求回退为 **`v2.0.0`**；项目名称保留 C1，版本号不带 `+C1` 后缀，与原版 `jacyl4/de_GWD` 的版本线独立。采用 `v主版本.功能小版本.BUG修复版本`：功能小版本和修复版本均从 0 开始；功能更新依次递增中间位并将修复位归零，修 BUG 则递增最后一位，不兼容更新递增主版本并将后两位归零。Xray 组件仍为 `26.10.21`，与产品版本号独立。

版本分类：Nginx、PHP、Xray、DNS 等组件的版本升级或组件安全更新，归入小版本更新，递增中间位并将末位归零（如 `v2.0.0 → v2.1.0`）；新增功能同样递增中间位。仅修复项目自身 BUG、未升级组件的改动递增末位（如 `v2.1.0 → v2.1.1`）。同次发布包含组件更新和 BUG 修复时，按小版本发布，不逐个组件累计版本号。

GPT/ChatGPT、Claude 独立分流及节点服务端版本“未检测”标识仍保留在代码中；本次**只回退发布版本号，不回退这些功能**。客户端与服务端脚本共用同一产品版本文件，但远端节点的实现及版本必须由节点自身可信地声明，不能从产品发布号推断。由于功能代码与旧 `v2.0.0` 共用版本号，已安装 `v2.0.0` 的用户不会因版本比较自动触发更新，须手动运行新版脚本。

客户端与服务端安装器均以同一份 `version.php` 的首行作为本地版本；手动上传本地安装资源时，须将该文件与 `client` / `server` 一起上传。面板“客户端 C1 版本”卡片比较的是本机 `/var/lib/de_GWD/version.php` 与 `kos991/c1/main/version.php`，**不代表下方代理节点的版本**。节点各自可能运行旧 de_GWD 或其他服务端；现有 VMess/WebSocket 接入不提供可信的版本声明，节点表的“服务端版本”因此标为“未检测”，不能把本机 `v2.0.0` 冒充 bwg 等节点版本。双端自动更新比较时兼容历史 `+C1` 后缀，仅远端语义版本真正更高才触发。

预定义 AI 分流新增 GPT/ChatGPT 和 Claude 的独立节点选项；保留原 OpenAI 规则和配置。GPT 覆盖 ChatGPT 网页、认证与静态资源域名，并排在范围较广的 `geosite:openai` 规则之前；`api.openai.com` 继续由 OpenAI 选择控制。未选择 GPT 时不写 GPT 专属规则，交集仍按原 OpenAI 选择或默认代理运行。Claude 覆盖 `claude.ai`、`claude.com`、`anthropic.com` 等官方域名及专用资源域名；未声明覆盖所有第三方 CDN。111 的隔离配置在 OpenAI 与 GPT 指向不同节点时，实测路由顺序为 GPT → OpenAI → Claude，Xray 配置检查通过；浏览器规则写入后保存和回显通过，随后恢复原配置。旧版 `geosite:apple-ads` 在当前数据文件中缺失，已从 Apple 默认规则移除，避免整个路由配置加载失败。


历史版本记录（2026-10-24）：双端 `de_GWD_amd64.zip`、`de_GWD_arm64.zip` 曾包含官方 [Xray v26.10.21](https://github.com/XTLS/Xray-core/releases/tag/v26.10.21)，当时校验过发布包 SHA-256；该记录不代表本轮所有候选组件已更新、已发布，或 `26.10.21` 仍为上游 Latest。以当前 ZIP 哈希、部署主机 `/opt/de_GWD/vtrui/vtrui version` 和 [COMPONENT-BASELINE.md](COMPONENT-BASELINE.md) 为准。

安装/更新时运行对应的 `server` 或 `client`；客户端离线安装须同时提供对应架构的 ZIP，避免旧本地包覆盖新资源。已有安装应先备份并确认旧应用与 WireGuard 数据不被自动清理；客户端 Web 更新和定时更新仅使用固定可信来源，不能把旧 `0conf` 中的更新 URL 当作可任意执行的脚本。

历史双端验证（2026-10-24）：当时现有服务端配置与客户端 TPROXY、VMess TCP、WS/TLS 配置通过 `run -test`，隔离网络中测试了新版双端 TCP、Nginx 终止 TLS 的 WS 转发及新旧客户端/服务端互通，TLS 测试使用临时 CA 未关闭证书验证。arm64 仅校验旧版二进制/打包内容，未作实机验证；这些结果不等于本轮候选的整机、DNS、UDP 或新管理面的验收。

兼容性变化：新版仍可使用 VMess 和 WebSocket，但会输出上游弃用提示，本次未迁移协议。新版默认拦截来自 VMess 等代理入站、经 freedom 出站访问回环或私网目标的连接；需要通过代理访问内网服务的用户应先评估此变化。本次保留官方默认规则，客户端 TPROXY 的配置检查不等于完整网关、UDP 和 DNS 分流验收。







## Server (amd64 & arm64) support kvm xen openvz lxc and so on:
```
apt install -y wget
bash <(wget --no-check-certificate -qO- https://raw.githubusercontent.com/kos991/c1/main/server)
```

![de_GWD 0](https://raw.githubusercontent.com/jacyl4/de_GWD/main/resource/screenshot/0.png)

## Client (amd64 & arm64):
```
apt install -y wget
bash <(wget --no-check-certificate -qO- https://raw.githubusercontent.com/kos991/c1/main/client)
```
或

手动上传client文件与de_GWD压缩包后
```
chmod +x client
./client
```

![de_GWD 1](https://raw.githubusercontent.com/jacyl4/de_GWD/main/resource/screenshot/1.png)
![de_GWD 2](https://raw.githubusercontent.com/jacyl4/de_GWD/main/resource/screenshot/2.png)
![de_GWD 3](https://raw.githubusercontent.com/jacyl4/de_GWD/main/resource/screenshot/3.png)
![de_GWD 4](https://raw.githubusercontent.com/jacyl4/de_GWD/main/resource/screenshot/4.png)
![de_GWD 5](https://raw.githubusercontent.com/jacyl4/de_GWD/main/resource/screenshot/5.png)

## Manual:
[Deepwiki 自动生成的文档](https://deepwiki.com/jacyl4/de_GWD)    

## Thanks to
* [ XTLS/Xray-core ](https://github.com/XTLS/Xray-core)
* [ coredns/coredns ](https://github.com/coredns/coredns)
* [ pymumu/smartdns ](https://github.com/pymumu/smartdns)
* [ IrineSistiana/mosdns ](https://github.com/IrineSistiana/mosdns)
* [ m13253/dns-over-https ](https://github.com/m13253/dns-over-https)
* [ pi-hole/docker-pi-hole ](https://github.com/pi-hole/docker-pi-hole)
* [ mmotti/pihole-regex ](https://github.com/mmotti/pihole-regex)
* [ Loyalsoldier/v2ray-rules-dat ](https://github.com/Loyalsoldier/v2ray-rules-dat)
* [ makotom/cfspeed ](https://github.com/makotom/cfspeed)
* [ mzz2017/lkl-haproxy ](https://github.com/mzz2017/lkl-haproxy)
* [ zabbly/linux ](https://github.com/zabbly/linux)
* [ xanmod/linux ](https://github.com/xanmod/linux)
* [ tsl0922/ttyd ](https://github.com/tsl0922/ttyd)
* [ mikefarah/yq ](https://github.com/mikefarah/yq)


## Stargazers over time
[![Stargazers over time](https://starchart.cc/jacyl4/de_GWD.svg)](https://starchart.cc/jacyl4/de_GWD)

[![Powered by DartNode](https://dartnode.com/branding/DN-Open-Source-sm.png)](https://dartnode.com "Powered by DartNode - Free VPS for Open Source")
