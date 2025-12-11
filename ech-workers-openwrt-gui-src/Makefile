# Copyright (C) 2024
# This is free software, licensed under the GNU General Public License v3.

include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI support for ECH Workers Proxy
LUCI_DESCRIPTION:=LuCI configuration interface for ECH Workers - Encrypted Client Hello proxy client
LUCI_DEPENDS:=+curl +ca-certificates
LUCI_PKGARCH:=all

PKG_NAME:=luci-app-ech-workers
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

PKG_MAINTAINER:=ECH Workers Team
PKG_LICENSE:=GPL-3.0-or-later

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildance Buildsystem
$(eval $(call BuildPackage,$(PKG_NAME)))
