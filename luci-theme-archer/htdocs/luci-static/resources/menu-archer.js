'use strict';
'require baseclass';
'require ui';

const STORAGE_KEY = 'archer-ui-mode';

return baseclass.extend({
	getMode() {
		try {
			const value = window.localStorage.getItem(STORAGE_KEY);
			return value === 'advanced' || value === 'simple' ? value : 'simple';
		}
		catch (e) {
			return 'simple';
		}
	},

	setMode(mode) {
		mode = mode === 'advanced' ? 'advanced' : 'simple';
		try { window.localStorage.setItem(STORAGE_KEY, mode); } catch (e) {}
		document.documentElement.setAttribute('data-archer-mode', mode);
		const toggle = document.querySelector('#archer-mode-toggle');
		if (toggle) {
			toggle.classList.toggle('is-advanced', mode === 'advanced');
			toggle.setAttribute('aria-pressed', mode === 'advanced' ? 'true' : 'false');
		}
		return mode;
	},

	__init__() {
		ui.menu.load().then((tree) => {
			this.render(tree);
			this.bindControls();
			this.setMode(this.getMode());
			document.documentElement.setAttribute('data-archer-ready', '1');
		});
	},

	bindControls() {
		const toggle = document.querySelector('#archer-mode-toggle');
		if (toggle)
			toggle.addEventListener('click', () => this.setMode(this.getMode() === 'simple' ? 'advanced' : 'simple'));
		document.querySelectorAll('[data-archer-action="advanced"]').forEach((node) => {
			node.addEventListener('click', () => this.setMode('advanced'));
		});
	},

	render(tree) {
		let node = tree;
		let url = '';
		this.renderModeMenu(tree);
		if (L.env.dispatchpath.length >= 3) {
			for (let i = 0; i < 3 && node; i++) {
				node = node.children[L.env.dispatchpath[i]];
				url += (url ? '/' : '') + L.env.dispatchpath[i];
			}
			if (node) this.renderTabMenu(node, url);
		}
	},

	renderTabMenu(tree, url, level) {
		const container = document.querySelector('#tabmenu');
		if (!container) return E([]);
		const ul = E('ul', { class: 'tabs' });
		const children = ui.menu.getChildren(tree);
		let activeNode = null;
		children.forEach((child) => {
			const active = L.env.dispatchpath[3 + (level || 0)] === child.name;
			ul.appendChild(E('li', { class: 'tabmenu-item-%s%s'.format(child.name, active ? ' active' : '') }, [E('a', { href: L.url(url, child.name) }, [_(child.title)])]));
			if (active) activeNode = child;
		});
		if (!ul.children.length) return E([]);
		container.appendChild(ul);
		if (activeNode) this.renderTabMenu(activeNode, url + '/' + activeNode.name, (level || 0) + 1);
		return ul;
	},

	renderMainMenu(tree, url, level) {
		const ul = level ? E('ul', { class: 'dropdown-menu' }) : document.querySelector('#topmenu');
		if (!ul) return E([]);
		const children = ui.menu.getChildren(tree);
		if (!children.length || level > 1) return E([]);
		children.forEach((child) => {
			const submenu = this.renderMainMenu(child, url + '/' + child.name, (level || 0) + 1);
			const hasChildren = !!submenu.firstElementChild;
			ul.appendChild(E('li', { class: !level && hasChildren ? 'dropdown' : '' }, [
				E('a', { class: !level && hasChildren ? 'menu' : '', href: hasChildren ? '#' : L.url(url, child.name) }, [_(child.title)]), submenu
			]));
		});
		return ul;
	},

	renderModeMenu(tree) {
		const ul = document.querySelector('#modemenu');
		const children = ui.menu.getChildren(tree);
		children.forEach((child, index) => {
			const active = L.env.requestpath.length ? child.name === L.env.requestpath[0] : index === 0;
			if (ul) ul.appendChild(E('li', { class: active ? 'active' : '' }, [E('a', { href: L.url(child.name) }, [_(child.title)])]));
			if (active) this.renderMainMenu(child, child.name);
		});
	}
});
