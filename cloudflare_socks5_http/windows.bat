@echo off

set client_ip=127.0.0.1:30000
set dns=dns.alidns.com/dns-query
set token=服务端密钥
set cf_domain=workers域名/pages域名/自定义域名:13个CF端口
set cf_cdnip=优选IP/域名
set enable_ech=y开启ECH，n关闭ECH
set cnrule=y开启国内外分流分理，n开启全局代理
set pyip=填写proxyip，留空表示使用服务端的proxyip，多个用,隔开

windows-amd64.exe client_ip=%client_ip% cf_domain=%cf_domain% cf_cdnip=%cf_cdnip% token=%token% enable_ech=%enable_ech% dns=%dns% cnrule=%cnrule% pyip=%pyip%
pause

