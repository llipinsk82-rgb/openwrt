# SPDX-License-Identifier: Apache-2.0
include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-archer-dashboard
PKG_VERSION:=1.0.0
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0
PKGARCH:=all

include $(INCLUDE_DIR)/package.mk

define Package/luci-app-archer-dashboard
  SECTION:=luci
  CATEGORY:=LuCI
  SUBMENU:=3. Applications
  TITLE:=Archer C7 Dashboard
  EXTRA_DEPENDS:=luci-base (>=26.180.75667~128a781)
  PKGARCH:=all
endef

define Package/luci-app-archer-dashboard/description
  Read-only lightweight status dashboard for Archer C7 on OpenWrt 25.12.
endef

define Build/Compile
endef

define Package/luci-app-archer-dashboard/install
	$(INSTALL_DIR) $(1)/www
	$(CP) ./htdocs/* $(1)/www/
	$(CP) ./root/* $(1)/
endef

$(eval $(call BuildPackage,luci-app-archer-dashboard))
