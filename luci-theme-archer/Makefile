# SPDX-License-Identifier: Apache-2.0
include $(TOPDIR)/rules.mk

PKG_NAME:=luci-theme-archer
PKG_VERSION:=1.0.0
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0
PKGARCH:=all

include $(INCLUDE_DIR)/package.mk

define Package/luci-theme-archer
  SECTION:=luci
  CATEGORY:=LuCI
  SUBMENU:=4. Themes
  TITLE:=Archer C7 Theme
  EXTRA_DEPENDS:=luci-base (>=26.180.75667~128a781)
  PKGARCH:=all
endef

define Package/luci-theme-archer/description
  Lightweight Archer C7 LuCI theme for OpenWrt 25.12.
endef

define Build/Compile
endef

define Package/luci-theme-archer/install
	$(INSTALL_DIR) $(1)/www
	$(CP) ./htdocs/* $(1)/www/
	$(INSTALL_DIR) $(1)/usr/share/ucode/luci/template/themes
	$(CP) ./ucode/template/themes/archer $(1)/usr/share/ucode/luci/template/themes/
	$(CP) ./root/* $(1)/
endef

$(eval $(call BuildPackage,luci-theme-archer))
