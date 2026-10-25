# de_GWD 组件基线与核验记录

> 范围：Debian 12/13、amd64/arm64 的客户端与服务端安装路径及客户端 UI helper。以下“旧基线”版本来自任务输入，不等于当前主机实测版本；候选版本均**未发布、待验证，不能称为已修复**。客户端 DDNS、WireGuard、应用管理模块在本次切除；Pi-hole/Docker 仍为核心组件，服务端 WARP 保留。现有应用或 WireGuard 数据不会因管理模块删除而自动卸载/删除。产品版本 `v2.1.0` 见 `version.php:1`，与组件版本无关。

## 核心组件清单

| 组件 / 运行侧 | 旧基线（任务输入） | 候选（未发布） | 分发、配置和版本来源 | 漏洞状态 / 下一步 |
| --- | --- | --- | --- | --- |
| Xray（客户端、服务端，进程名 `vtrui`） | 26.10.21 | 未指定 | `de_GWD_{amd64,arm64}.zip` 内 `xray`，客户端安装至 `/opt/de_GWD/vtrui/vtrui`（`client:1040-1065`），服务端同路径（`server:1065-1105`）；运行配置见 `client:1296-1439`、`server:1408-1461`。上游核验：[Xray releases](https://github.com/XTLS/Xray-core/releases)。 | **待验证**：双架构二进制版本、上游公告、协议与路由回归。 |
| mosdns（客户端） | 5.3.3 | 5.3.4 | 同上 ZIP 内 `mosdns`；服务 `mosdns start --as-service -d /opt/de_GWD/mosdns`（`client:1040-1118`）；配置由 `resource/client/ui-script/ui-DNSsplit:18-35,71-145` 生成。上游核验：[mosdns releases](https://github.com/IrineSistiana/mosdns/releases)。 | **待验证**：候选版本、插件配置、双协议 5341 与回退语义。 |
| CoreDNS（客户端，按需） | 1.11.3 | 1.15.0 | 同上 ZIP 内 `coredns`；服务和 `corefile` 路径 `client:1040-1094`；DoG/DoGs 按需监听 `resource/client/ui-script/ui-smartDNS:20-53`、`resource/client/ui-script/ui-DoGsSave`。上游核验：[CoreDNS releases](https://github.com/coredns/coredns/releases)。 | **待验证**：候选与 `grpc` 插件/`template`/TLS 配置兼容性。 |
| SmartDNS（客户端） | Release 46-23 | 48.4 | 同上 ZIP 内 `smartdns`；安装阶段配置 `:53/:5331/:5332` 见 `client:1122-1239`，运行期 `ui-smartDNS:55-136` 将国内/全球分组绑定到 `127.0.0.1:5331/:5332`。上游核验：[SmartDNS releases](https://github.com/pymumu/smartdns/releases)。 | **待验证**：候选可用性、DNS 分组/DoH 和重启后的解析链；部署后以最终生成的配置为准。 |
| yq（客户端 YAML 工具） | 4.23.1 | 4.54.1 | 同上 ZIP 内 `yq` → `/usr/bin/yq`（`client:1054-1065`），DNS helper 调用见 `resource/client/ui-script/ui-DNSsplit:46-53`。上游核验：[yq releases](https://github.com/mikefarah/yq/releases)。 | **待验证**：候选语法与 YAML 改写兼容性。 |
| Nginx + OpenSSL（双端） | Nginx 1.29.0 / OpenSSL 3.1.7 | Nginx 1.30.6；OpenSSL 未指定 | 架构二进制 `resource/nginx/nginx_amd64` / `resource/nginx/nginx_arm64`，SHA256 对照文件及配置包 `resource/nginx/nginxConf.zip`；下载/替换见 `client:228-246`、`server:174-207`；服务配置 `client:1959-2014`、`server:1112-1165`。上游核验：[Nginx security advisories](https://nginx.org/en/security_advisories.html)、[OpenSSL advisories](https://www.openssl.org/news/vulnerabilities.html)。 | **待验证**：实际编译依赖、TLS/HTTP/WS/QUIC；Nginx 更新不等于 OpenSSL 已更新。 |
| PHP-FPM / CLI（客户端管理 UI） | PHP 7.4，Sury backport | Debian 13: 8.4；Debian 12: 8.2 | 旧代码曾校验 Sury PHP 7.4 包安全修订；当前按 Debian suite 选择本机 PHP（`client:168-184`）；FPM/Nginx socket 见 `client:2109-2119,2146-2157`，以最终安装脚本及实机为准。上游核验：[PHP supported versions](https://www.php.net/supported-versions.php)、Debian Security Tracker（在 Debian 官方安全跟踪器按 suite 和 PHP 源包查询）。 | **待验证**：实装 PHP、模块、FPM socket、Web UI 与发行版安全公告；旧 Sury 回补不能推断 PHP 7.4 无漏洞。 |
| Pi-hole（客户端 Docker） | 旧 `latest`，无可复现固定版本 | 2026.10.0 | 客户端 `pullpihole` 依据架构选择 `pihole/pihole:2026.10.0@sha256:…`（`client:2274-2282`），host 网络/挂载/TOML 见 `client:2286-2375`。上游核验：[Pi-hole Docker releases](https://github.com/pi-hole/docker-pi-hole/releases)、[Pi-hole releases](https://github.com/pi-hole/pi-hole/releases)。 | **待验证**：候选 digest 的来源、架构、实际 FTL/TOML 兼容与服务端口；脚本选择候选不代表已发布验证。 |
| ttyd（客户端更新终端） | 1.7.3 | 1.7.7 | 下载 GitHub release 中按 `uname -m` 命名的二进制（`client:15,248-252`），`updateGWD` 本地服务见 `client:2247-2263`。上游核验：[ttyd releases](https://github.com/tsl0922/ttyd/releases)。 | **待验证**：候选下载、架构、WebSocket/终端服务和来源可信性。 |
| DoH server（服务端） | 未给出 | 未指定 | `resource/doh/doh_s_{amd64,arm64}` 与 SHA256 文件；下载/替换 `server:176-186`，监听 `127.0.0.1:9853/dq` 并转发 Unbound `:53`（`server:1004-1058`）。 | **待验证**：仓库二进制来源、构建版本及自身公告；不能误记为客户端 CoreDNS 或浏览器 DoH。 |
| Unbound（服务端） | Debian APT 版本，未固定 | 未指定 | `server:95-137` 安装 `unbound`；本机 127.0.0.1:53 上游和 systemd 见 `server:495-554`。上游核验：[Unbound releases](https://nlnetlabs.nl/projects/unbound/about/)。 | **待验证**：Debian 实装版本、解析可用性及公告。 |

### 分发、系统依赖与历史应用资产

- 底座与信任链：Debian 12/13 suite、APT keyring/signed-by（`client:18-89`、`server:18-89`、`@init:2-75`）；客户端 Docker 官方 Debian 仓库与 `docker-ce`（`client:146-165`）；Nginx amd64 的 `libmimalloc.so.2` 兼容处理（`server:141-158`、`client:203-232`），arm64 的 `google-perftools`（`client:103-112,164`、`server:135`）。实际 apt 版本由运行主机仓库确定。
- 客户端基础包：`sudo wget curl git locales netcat-openbsd lsof bind9-dnsutils net-tools resolvconf nftables ca-certificates apt-transport-https gnupg2 unzip zstd jq bc moreutils rng-tools-debian chrony cron irqbalance`（`client:103-143`）；第二批 `python3-toml psmisc dns-root-data idn2 ethtool tmux socat zip docker-ce sqlite3 libbrotli1 libcrypt1`（`client:146-165`），原生 PHP 包见 `client:177-184`。服务端另有 `screen qrencode unbound` 等（`server:95-137`）。
- 动态规则数据：`IPchnroute`（`client:197-222`）、`geosite.dat`、`geoip.dat`、`Domains.chn.txt`、`Domains.apple.txt`、`Domains.games.txt`、bogus-nxdomain 文件按校验和更新并用于 Xray、mosdns、nftables、Pi-hole（`resource/client/ui-script/ui_4am:21-138`）；版本需以 hash 记录。服务端 DoH、Nginx、站点样例和 de_GWD ZIP 亦分别校验（`server:174-215`）。
- 客户端前端由 `resource/client/Archive.zip` 分发至 `/opt/de_GWD` 和 `/var/www/html`（`client:2202-2245`）；当前页面为 `resource/client/ui-web/{auth,login,index,forward,nodes,update,terminal-auth}.php`。静态 vendor 包含 jQuery 3.6.4（`resource/client/ui-web/vendor/jquery/jquery.min.js:1`）、Bootstrap 4.2.1（`resource/client/ui-web/vendor/bootstrap/js/bootstrap.bundle.min.js:1-5`）、Font Awesome Free 5.11.2（`resource/client/ui-web/vendor/fontawesome-free/css/all.min.css:1-4`）及 jQuery Easing（`resource/client/ui-web/vendor/jquery-easing/jquery.easing.min.js:1`，未见显式版本），其漏洞状态亦待上游公告与实际资源核验。
- Docker/Compose 与 Pi-hole **保留为基础设施**：Docker 官方 Debian 仓库及 `docker-ce`（`client:146-165`）；`resource/client/ui-script/ui-installDocker` 仍在仓库，用于基础设施维护，**Web 应用安装入口 `act/installDocker` 已删除**。Pi-hole 依赖 Docker 引擎（`client:2274-2375`），Compose 版本取决于该 helper 的下载规则；镜像 digest 而非仅 tag 应作为发布基线。
- **已移除的客户端应用管理模块，仅盘点历史资产**：旧版曾安装 Vaultwarden (`vaultwarden/server:latest`；旧 `resource/client/ui-script/ui-installBitwarden:55-78`)、Jellyfin (`nyanmisaka/jellyfin:latest`；旧 `ui-installJellyfin:72-100`)、`mariadb-server`（旧 `ui-installMariaDB:13-59`）、授权 FileRun ZIP + ionCube/PHP 扩展及 `imagemagick pngquant ffmpeg`（旧 `ui-installFileRun:20-106`）、NFS 的 `autofs nfs-common`（旧 `ui-installNFS:13-35`）。**上述安装与 Bitwarden/Jellyfin 还原脚本均已从当前仓库删除，引用行号仅指删除前历史文件**。当前客户端不再提供应用安装、更新、启停、卸载、备份/还原或状态 UI；已有容器、数据库、站点、NFS/许可证资料**不自动删除或卸载**；其版本和漏洞**不属于当前基线验收**。
- **已移除的客户端 DDNS/WireGuard 管理功能**：Cloudflare/3322 DDNS helpers、`ui-installWG`/`ui-WG*`/`wg-quick@wg0`、相关前端/API 和调用链均不再作为当前功能分发或核验；既存 `wireguard-tools`、配置/密钥、服务**不自动卸载或删除**。服务端可选 WARP (`wgcf` + `wireguard-tools`) 和 HAProxy TCP 转发仍保留（`server:1691-1825,1829-1931`）；Cloudflare DNS-01 ACME 证书、核心 FWD/Rproxy 仍保留（`server:1196-1255`、`resource/client/ui-script/ui-installCER`）。
- 内核：amd64 Debian 12/13 从 XanMod signed-by APT 源选择匹配 CPU x64v 的 metapackage，保留 Debian 回退内核（`resource/kernel/installkernel:126-164,192-245`）；arm64 没有 XanMod 安装路径。双端入口见 `client:2487-2489`、`server:1613-1616`；`resource/kernel/zabbly` 不应混同当前 XanMod 主入口。BBR v3 需手动重启后实测（`resource/kernel/installkernel:108-123,224-245`）。

## 漏洞状态与证据边界

- 此文档**没有宣称任何候选版本已修复特定漏洞**。任务提供的版本号是待发布升级目标；实际修复状态只能由项目上游 release/security advisory、Debian Security Tracker/Sury changelog、供应商镜像 digest/构建信息及部署主机确认。上表“待验证”不是“安全”或“无漏洞”。
- PHP 7.4 的安全修订属于旧安装代码提出的 Sury 回补要求，不能直接外推到新 Debian 原生 PHP；以 `apt-cache policy`、已安装包和 PHP/发行版公告为准。Nginx 嵌入 OpenSSL 的版本与 Debian `openssl` 包可能不同，以 `nginx -V`、依赖检查和发布二进制构建记录为准。
- 为避免虚构 CVE，本基线不新增未经供应商安全公告核实的 CVE 编号。组件来源为上表仓库路径/行号与各上游链接；本任务没有取得部署主机的包版本、镜像 digest、二进制扫描或公告比对结果。

## 发布前验证矩阵（目前全部待验证）

| 场景 | 证据/判定条件 | 状态 |
| --- | --- | --- |
| amd64/arm64 产物 | 核对 ZIP 和单独二进制的 SHA256、解包文件名/可执行权限、`--version`/镜像 digest，记录构建源与发布 tag | 待验证 |
| Debian 12/13 全新与原位升级 | APT signed-by、PHP 8.2/8.4/FPM socket、Nginx 加载库；验证管理模块移除但既存应用和 WireGuard 配置/服务不被自动删除或卸载 | 待验证 |
| 客户端 DNS | Pi-hole :53 → mosdns :5341 → SmartDNS :5331/:5332 → 国内 DNS/DoH/DoG :5333；UDP/TCP、域名/hosts、拦截、备用路径及断网恢复 | 待验证 |
| 服务端 DNS/DoH | Unbound 127.0.0.1:53、DoH 127.0.0.1:9853/dq、Nginx HTTPS `/dq`、证书与上游故障 | 待验证 |
| 代理与转发 | Xray 客户端 TPROXY、nftables/geoip/geosite、服务端 VMess WS+TLS，FWD0/FWD1、Rproxy 双端、服务端 WARP、重启持久性；客户端 DDNS/WireGuard/应用入口已移除 | 待验证 |
| 管理与证书 | PHP 页面认证、ttyd 更新服务、Nginx TLS、核心证书续期和备份还原；不验收已移除应用模块功能 | 待验证 |
| 更新与内核 | 自动/手动更新与规则同步、候选安全公告、XanMod 安装/恢复/移除、手动重启后的运行内核与 BBR 证据 | 待验证 |
