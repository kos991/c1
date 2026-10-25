# de_GWD 双端运行链路

本文记录配置产生者、进程/端口和依赖方向，而非部署验收结果。`客户端`是 DNS/透明代理/管理 UI 所在设备，`服务端`是提供 WS+TLS 节点及 DoH 的 VPS。客户端 DDNS、WireGuard、应用管理模块在本次移除；Pi-hole/Docker、核心 FWD/Rproxy 和证书保留，服务端 WARP 保留。已有应用或 WireGuard 的服务、数据、配置不自动卸载或删除；以下端口仅为脚本默认或配置项，不表示公网已开放。

## 1. 安装与控制面

- 双端均从 Debian 12/13 APT 初始化，并配置 signed-by keyring；客户端准备 Docker 仓库、原生 PHP 与网络工具，服务端另安装 Unbound（`client:18-89,103-184`；`server:18-89,95-139`；`@init:2-75`）。客户端仓库 ZIP、Nginx/配置包及服务端 DoH 二进制按相应 SHA256 文件决定替换（`client:197-269`；`server:174-215`）；下载校验不等于运行服务兼容性已验收。
- 客户端 `/opt/de_GWD/0conf` 保存仍保留的节点、DNS、转发设置；Nginx 管理页 `/var/www/html` + PHP-FPM Unix socket，后台 helper 在 `/opt/de_GWD/ui-*`（`client:2202-2245`、`resource/client/ui-web/{auth,login,index,forward,nodes,update,terminal-auth}.php`）。旧 `app.php`、`ddns.php` 及客户端 WireGuard 页面/helper 已从管理面移除。服务端由 `server` 交互菜单驱动，配置 `/opt/de_GWD/vtrui/config.json` 与 `/etc/nginx/conf.d/default.conf`（`server:1295-1404,1408-1461,2201-2345`）。

## 2. DNS：客户端与服务端不能混淆

### 客户端 DNS/DoH/DoG 链

```text
LAN/本机 DNS :53 (Pi-hole FTL, Docker --net=host)
  └─ Pi-hole upstream 127.0.0.1:5341 (mosdns, UDP+TCP)
      ├─ 国内/指定白名单 → SmartDNS 127.0.0.1:5331 (国内上游)
      └─ 全球/黑名单/节点/回退 → SmartDNS 127.0.0.1:5332 (DNS_global)
          ├─ 配置中的远端 DoH HTTPS 上游（证书/主机名验证）
          └─ 可选 CoreDNS 127.0.0.1:5333 → 远端 DoG/gRPC+TLS
可选对外 DoGs: CoreDNS grpc://.:<用户设置端口> + /var/www/ssl/de_GWD.{cer,key} → 127.0.0.1:53。
```

- `client:2274-2375` 将按架构选择的 Pi-hole 镜像作为 host-network Docker 容器，持久化 `/opt/de_GWD/pihole`、`/etc/dnsmasq.d`；安装暂设 DNS `5399`，后置恢复 `53` 并重启；管理 Web 端口 `127.0.0.1:8053`，上游 `127.0.0.1#5341`，禁用容器 NTP 和 IPv6 解析；管理页 `/admin/`、`/api/` 由 Nginx 代理（`client:2123-2143`）。
- mosdns `forwarders.yaml` 分别转发 SmartDNS `:5331`/`:5332`（`resource/client/ui-script/ui-DNSsplit:18-35`）；`config.yaml` 在 `127.0.0.1:5341` 监听 UDP/TCP，hosts、domains_listB/W、节点域名、国内域名及 IPchnroute 参与 `fallback`/`global_sequence`（同文件 `71-145`）。安装阶段 SmartDNS 曾配置 `:53/:5331/:5332`（`client:1124-1131`），运行期 helper 则仅绑定 `127.0.0.1:5331/:5332`（`resource/client/ui-script/ui-smartDNS:55-81`）；最终监听须以部署后的生成配置和服务日志确认。`/etc/resolv.conf` 指向本地（`client:1172-1187`）。
- DoH/DoG 上游先经国内 DNS 端口 `:5331` 解析 IP；安装阶段仅引导解析，已不再写入旧 `-no-check-certificate` SmartDNS 上游（`client:1195-1239`）。后置 helper 生成 `-host-name/-http-host/-tls-host-verify`、保留系统 CA 验证（`resource/client/ui-script/ui-dns-lib:29-55`、`resource/client/ui-script/ui-smartDNS:96-104`），CoreDNS gRPC 上游配置 `tls` 与 `tls_servername`（`resource/client/ui-script/ui-smartDNS:20-45`）；可选 DoGs server 使用共享证书（`resource/client/ui-script/ui-DoGsSave`）。首装和原位升级的 TLS/故障路径仍待实际验收。
- hosts 同时写 mosdns 与 Pi-hole（`resource/client/ui-script/ui-DNSsplit:40-93`）；`ui_4am` 取得 geoip/geosite、CHN 路由和 DNS 域名列表并按 hash 更新，复制至 Xray、nftables、dnsmasq（`resource/client/ui-script/ui_4am:21-138`）。DNS 防外流 block53 控制由 `resource/client/ui-script/ui-block53on`、`ui-block53off`、`ui-block53ctl` 按专属 `inet de_GWD_dns_guard` 表管理，不应冲掉其它 nftables 表；FWD/Rproxy 修改也不应清空 Pi-hole/DNS 守卫。

### 服务端 DNS/DoH 链

```text
/etc/resolv.conf → Unbound 127.0.0.1:53 UDP/TCP → 1.1.1.1/1.0.0.1/8.8.8.8/8.8.4.4/9.9.9.9/208.67.222.222
HTTPS https://<服务端域名>/dq → Nginx → doh-server 127.0.0.1:9853/dq → Unbound 127.0.0.1:53
Xray 的 dnsflow → tcp+local://127.0.0.1:53
```

- Unbound 配置/服务启动 `server:495-554`；`doh-server.conf` 的监听、路径、上游和 systemd 单元 `server:1004-1058`；Nginx 的 `/dq` 代理 `server:1354-1373`，Xray DNS 见 `server:1416-1420`。服务端旧版 Pi-hole/AdGuardHome 是迁移清理对象，不是当前 DNS 链（`server:232-260`）。

## 3. Xray + nftables + 路由

- 客户端 Xray 二进制名 `vtrui`，主透明入口 `127.0.0.1:9896`，`dokodemo-door` TCP/UDP + TPROXY `mark:255`；安装阶段 DNS 指向 `tcp+local://127.0.0.1:5332`（`client:1296-1332`），UI 重新生成的 `ui-NodeOne` 将 DNS 指向本机 :53 并开启嗅探 (`resource/client/ui-script/ui-NodeOne`)。默认 VMess 节点有 TCP 直连或 WS+TLS 两型，direct outbound 使用 `freedom` 和 mark 255 避免透明代理自循环（`client:1334-1439`）。`ui-NodeOne`、`ui-NodeSM`、`ui-NodeDT`、`ui-NodeCU`/`ui-node-lib` 根据 `0conf` 切换节点与规则；`ui-V2routingDomain`、`ui-V2routingIP`、`ui-V2routingSip`、`ui-V2outbound` 控制 Xray 路由/出口，命中顺序以生成的 `config.json` 为准。
- 客户端 nftables `de_GWD` 表维护 `GlobalDNS`、`V2NODE`、`CHNROUTE`、黑白名单等集合，读取 `/opt/de_GWD/nftables/*` 与 CHN route 更新（`client:1448-1539`、`resource/client/ui-script/ui_4am:121-138`）。系统启用 IPv4 forwarding、`nf_conntrack`/`ifb`/`sch_cake` 和 BBR/cake 调优（`client:860-996`）；独立 DNS 守卫见上一节。不能以透明代理覆盖已有防火墙/SSH 规则。
- 服务端 Nginx `$port` 的 TLS+QUIC 虚拟主机按 `$path` 检查 `Upgrade: websocket`，代理至 Xray `127.0.0.1:9890` VMess WS 入口；本机 Xray DNS 是 Unbound :53（`server:1327-1404,1408-1461`）。客户端 WS+TLS 的 Host/serverName/path 必须与服务端域名、证书及路径一致；服务端 UUID 可在菜单更改并同时重建 Nginx/Xray（`server:1659-1681`）。

## 4. 管理站点、证书、终端与历史应用资产

- 客户端 Nginx `$webUIport`（缺省 443）提供 PHP 管理页、Pi-hole `/admin/`/`/api/`、`ttyd` WebSocket `/ttyd` 和 `/update-terminal`；PHP 使用与 Debian suite 匹配的 FPM Unix socket（`client:2027-2195`）。终端路径由 Nginx `auth_request /terminal-auth.php` 调用内部 FastCGI 授权（`client:2109-2119,2160-2186`，`resource/client/ui-web/terminal-auth.php`）；后端端口 `3000`/`3001`，更新终端服务见 `client:2247-2263`。实际认证/权限、路径和回显需端到端核验。
- 双端证书使用 `/var/www/ssl/de_GWD.cer` 与 `.key`，Nginx `.ssl_certs` 引用；服务端 HTTP-01/DNS-01 通过 acme.sh 签发并验证证书/私钥/域名后安装（`server:1174-1255`），443 时保留 HTTP 80 ACME challenge（`server:1265-1279`），每日 `Qday` 用 acme.sh 续期（`server:1529-1536`）。客户端证书 helper `resource/client/ui-script/ui-installCER` 仍保留 Cloudflare DNS challenge；`resource/client/ui-script/ui_4am:141-148` 处理续期。核对证书链、密钥权限、过期与 reload，不把命令成功等同 TLS 已验收。
- 客户端当前保留 Pi-hole/Docker 基础服务，管理 UI 和 PHP-FPM 服务仍是核心链路。旧应用管理模块曾提供 Vaultwarden、Jellyfin、MariaDB、FileRun、NFS 安装与管理，旧 DDNS 模块曾提供 Cloudflare/3322 地址更新，旧 WireGuard 模块曾管理 `wg0` 和客户端配置；这些入口、helper 与调用链本次删除，**不再作为可选功能验收**。删除管理面不意味着迁移或自动卸载已有容器、数据库、FileRun 网站/许可证、NFS 配置、WireGuard 服务/密钥。旧组件来源仅供历史资产盘点，见 `COMPONENT-BASELINE.md` 的“已移除的客户端管理模块”。证书申请/续期与核心 FWD/Rproxy 则继续保留。

## 5. FWD / Rproxy / 服务端 WARP

- 客户端前端 `resource/client/ui-web/forward.php` 将选项保存在 `0conf`；FWD0 使用主 Xray 的新增入站，FWD1 用独立 `vtrui1` 服务转发至所选上游节点（`resource/client/ui-script/ui-FWD0save`、`ui-FWD1save`、`ui-route-config:175-195`）。Rproxy 两端由 `ui-RproxyCsave`/`ui-RproxySsave` 生成桥接/门户及独立 `RproxyC`/`RproxyS` 服务（`ui-route-config:198-249`）；客户端私网映射将 extPort+协议限定到固定 intIP:intPort，通过 Xray `freedom.settings.finalRules` 精确 allow 后 block，未匹配桥接请求 blackhole，directOut 拦截保留/私网地址（`ui-route-config:216-228`）。
- `resource/client/ui-script/ui-route-lib` 用独占锁串行重配、复制 Xray 二进制并仅重启指定 systemd 单元；`resource/client/ui-script/ui-route-config:17-174,175-249` 验证端口/主机/节点 UUID、占用冲突并原子写 FWD/Rproxy 配置。客户端 WireGuard 生命周期/helper 已切除，不再生成 `wg0` 或客户端配置/二维码；既有服务及密钥不自动停止、卸载或删除。
- 服务端可选 WARP 使用 wgcf 注册 Cloudflare WireGuard upstream 并由 `wg-quick@wgcf` 控制（`server:1691-1825`）；独立 HAProxy TCP 转发入口及局部 DNS resolver 在 `server:1829-1931`。WARP 是**服务端**功能，与已移除的客户端 WireGuard 管理模块不同。

## 6. 更新、定时任务和内核

- 客户端初装/更新重新应用仓库下载、依赖、Nginx/PHP、Web UI、SmartDNS/CoreDNS/mosdns、Xray/nftables、Pi-hole 和后置 helper（`client:2689-2770`），不再部署 DDNS/WireGuard/应用管理模块，也不自动清理已有应用或 WireGuard 数据。服务端初装/更新见 `server:1979-2111`；`version.php:1` 是产品版本，客户端 `resource/client/ui-script/ui-autoUpdateHour` 比较远端版本并按 cron 调用可信下载/更新 helper，服务端 `server:2114-2179` 有对应自动更新。每次更新应记录前备份/实装版本/重启状态，动态依赖不等于可复现发布。
- 客户端 `resource/client/ui-script/ui_4am:21-150` 每日校验域名/路由/Geo 数据并续期，`ui_4h`/`ui_2h` 做周期辅助；`ui-updateSave` 调整 ttyd 更新端口。服务端 `Qday` 调用 acme.sh 续期（`server:1529-1536`）。
- 双端菜单调用 `resource/kernel/installkernel`（`client:2487-2489`、`server:1613-1616`）；仅 Debian 12/13 amd64 使用 XanMod x64v CPU 分级和 signed-by APT 源（`resource/kernel/installkernel:17-53,126-164,192-245`）。保留 Debian 回退内核并检查引导/GRUB，不自动删除旧内核或重启；恢复/移除按 `--restore`/`--remove`，且移除前须先从 Debian 回退内核启动（同文件 `247-305`）。BBR v3 必须手动重启后观察模块/运行内核和 qdisc（同文件 `108-123,243-244`）。

## 待执行的真实验证矩阵

| 链路 | 应核验的观测结果 | 状态 |
| --- | --- | --- |
| 两端 DNS | Pi-hole → mosdns → SmartDNS/DoH/DoG；Unbound → DoH `/dq`；TCP/UDP、AAAA、阻断和上游失效回退 | 待验证 |
| 数据与代理 | DNS/IP/geosite/geoip 数据 SHA256、nft set、Xray 透明 TPROXY + mark 不循环、VMess WS/TLS 握手 | 待验证 |
| 管理/TLS | Nginx 配置/证书校验、Pi-hole API、PHP-FPM 页、终端双路径授权与 WebSocket、acme.sh 续期 | 待验证 |
| 保留的转发/服务端 WARP | FWD0/FWD1、Rproxy 两端与默认拒绝、服务端 `wgcf`、HAProxy；确认旧客户端 WG/应用数据不被更新流程自动删除 | 待验证 |
| 升级/内核 | Debian 12/13 与双架构升级、镜像 digest/二进制版本、安全公告、旧应用/WG 数据保留、XanMod 回退及重启后 BBR；不验收已移除应用/WG/DDNS 功能 | 待验证 |
