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
* Web 界面继续使用 Sury 提供的 trixie PHP 7.4 包；PHP 7.4 上游已停止维护，本次适配未迁移 PHP 大版本。PHP 源使用独立 keyring 和 `signed-by`，不再调用 `apt-key`；Docker 公钥转为二进制 keyring 后使用。
* 通过 `/etc/sysctl.d/99-de-gwd.conf` 指向现有 `/etc/sysctl.conf`，使 Debian 13 的 systemd-sysctl 在启动时读取网关参数，并保持 WireGuard 和内核脚本对同一配置的修改生效。
* 安装入口使用 LF 换行，并通过 `.gitattributes` 固定 Shell 脚本换行格式，避免 Windows 检出后的 CRLF 导致 Linux Bash 语法错误。

使用此修改版时，将本地 `client`（客户端另带对应架构的 `de_GWD_amd64.zip` 或 `de_GWD_arm64.zip`）或 `server` 上传到 Debian 13，在所在目录以 root 执行：

```bash
bash ./client
# 服务端执行：
bash ./server
```

此修复版发布于 `kos991/c1`，在线安装、资源下载、Web 更新、自动更新和内核安装入口均指向该仓库的 `main` 分支。原项目为 `jacyl4/de_GWD`，保留原作者署名与许可证；已有上游安装需先手动执行本仓库脚本以切换更新来源。

验证范围：已执行 Debian 12/13 软件源处理场景、兼容库下载及摘要校验，并核对 Debian/Sury/Docker 的 trixie amd64、arm64 包索引。在 Debian 13.7 amd64、Linux 6.12 测试机上完成以下验证：

* 客户端、服务端、初始化和内核安装入口通过 Linux Bash 语法检查；客户端与服务端依赖集合通过 APT 模拟安装。
* 复现预编译 Nginx 缺少 `libmimalloc.so.2`，执行安装器中的兼容库函数后 Nginx 1.29.0 正常运行。
* 使用项目的 Nginx 基础配置、PHP-FPM pool 和 PHP ini 设置，在回环地址完成 Nginx → PHP 7.4.33 请求，SQLite、XML、Intl 验证通过；Web 压缩包中的 PHP 文件通过语法检查。
* PHP-FPM 和 Docker systemd 服务正常启动；Docker 29.9.2 成功拉取并运行 `hello-world` 容器。
* 使用有效测试节点与网段输入，在独立网络命名空间中实际加载项目 nftables、TPROXY、flowtable 和策略路由；在隔离挂载/网络命名空间中验证 `systemd-sysctl` 通过配置软链接加载 IPv4 转发参数。
* 压缩包内 Xray、mosdns、SmartDNS、CoreDNS 和 yq 均成功执行版本命令。

尚未验证：arm64 实机运行、完整交互安装、真实上游节点转发、域名证书签发、Web 管理操作及整机重启后的网关连通性。上述组件测试不等于完整部署验收；安装脚本会修改网络、DNS、防火墙和系统参数。

### PHP 安全修复：CVE-2026-109618 / CVE-2026-109619

这两项 PHP 核心漏洞需要包含修复补丁的运行时；关闭错误显示、限制上传或缩短 worker 生命周期不能替代补丁。上游公告：

* CVE-2026-109618：https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w
* CVE-2026-109619：https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp

本项目保留 Sury PHP 7.4 以兼容现有应用。Sury 的 Debian changelog 在 `1:7.4.33-31` 中明确记录从 PHP 8.2.35 回补两个 CVE；`php -v` 仍显示 `7.4.33`，必须以完整发行包版本及发行商补丁记录判断。此版本下限针对 Sury 包，不表示所有自行编译的 PHP 7.4.33 都已修复。

`client` 的 `installSecurePHP` 在依赖安装路径中检查 PHP common、CLI、FPM、CGI、核心扩展及已安装的同源 PHP 包，要求至少为 `1:7.4.33-31`。缺失或过旧时执行 APT 更新和安装，完成后再次检查版本；升级失败或仍低于下限时停止流程，验证通过后重启 FPM，替换旧 worker。PECL 扩展版本独立，不套用 PHP 核心包版本下限。

2026-10-24 实机核实：测试机已经安装 Sury `1:7.4.33-31+0~20261021.121+debian13~1.gbpe9c428`，其 `/usr/share/doc/php7.4-common/changelog.Debian.gz` 包含两个 CVE 的回补记录。本次执行安全检查并重启 FPM，确认运行中的可执行文件与已修补的安装包一致，包完整性检查和真实 FastCGI 请求通过。未执行攻击性漏洞利用测试，也未据此作入侵排查结论。

回归验证：在 Debian 执行 `python3 -m unittest discover -s tests -v`。五个场景覆盖旧包升级、缺失 FPM 安装、已修复版本、APT 成功但候选版本仍旧及 APT 失败；已在测试机通过。




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
* [ nyanmisaka/jellyfin ](https://hub.docker.com/r/nyanmisaka/jellyfin)
* [ dani-garcia/vaultwarden ](https://github.com/dani-garcia/vaultwarden)

## Stargazers over time
[![Stargazers over time](https://starchart.cc/jacyl4/de_GWD.svg)](https://starchart.cc/jacyl4/de_GWD)

[![Powered by DartNode](https://dartnode.com/branding/DN-Open-Source-sm.png)](https://dartnode.com "Powered by DartNode - Free VPS for Open Source")
