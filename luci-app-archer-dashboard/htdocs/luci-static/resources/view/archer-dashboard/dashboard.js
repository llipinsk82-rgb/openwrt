'use strict';
'require view';
'require archer-dashboard.data as dashboardData';

if (!document.querySelector('link[data-archer-dashboard-css]'))
	document.head.appendChild(E('link', { rel: 'stylesheet', href: L.resource('archer-dashboard/dashboard.css'), 'data-archer-dashboard-css': '1' }));

const REFRESH_MS = 10000;

function pill(text, kind) { return E('span', { class: `archer-pill ${kind || ''}` }, [String(text).toUpperCase()]); }
function row(label, value) { return E('div', { class: 'archer-kv' }, [E('span', {}, [label]), E('b', {}, [value == null ? 'Not available' : String(value)])]); }
function card(id, icon, title, subtitle, state, stateKind, rows, href, linkLabel) {
	return E('section', { class: 'archer-card', id }, [
		E('div', { class: 'archer-card-head' }, [E('span', { class: 'archer-card-icon' }, [icon]), E('div', { class: 'archer-card-title' }, [E('h2', {}, [title]), E('small', {}, [subtitle])]), pill(state, stateKind)]),
		E('div', { class: 'archer-card-body' }, rows),
		href ? E('a', { class: 'archer-card-link', href }, [linkLabel || _('Settings'), ' →']) : ''
	]);
}

return view.extend({
	load() { return dashboardData.loadSnapshot(); },
	renderCards(s) {
		return E('div', { class: 'archer-dashboard-grid' }, [
			card('internet', '◉', _('Internet'), s.internet.status === 'online' ? _('Connected') : _('Disconnected'), s.internet.status, s.internet.status === 'online' ? 'good' : 'muted', [row('IPv4 (WAN)', s.internet.ipv4), row('IPv6 (WAN)', s.internet.ipv6), row(_('Gateway'), s.internet.gateway), row(_('Interface'), s.internet.interface), row(_('Protocol'), s.internet.protocol), row(_('Uptime'), s.internet.uptime)], L.url('admin/network/network'), _('Internet Settings')),
			card('wifi', '⌁', _('Wi-Fi'), _('%d networks active').format(s.wifi.networks), s.wifi.status, s.wifi.status === 'active' ? 'info' : 'muted', s.wifi.radios.map(r => row(`${r.band} (${r.ssid})`, r.active ? `Ch ${r.channel} / ${r.clients} clients${r.bestSignal != null ? ` / ${r.bestSignal} dBm` : ''}` : _('Disabled'))).concat([row(_('Total clients'), s.wifi.clients)]), L.url('admin/network/wireless'), _('Wi-Fi Settings')),
			card('vpn', '⬡', _('VPN'), 'WireGuard', s.vpn.status, s.vpn.status === 'connected' ? 'good' : 'muted', [row(_('Interface'), s.vpn.interface), row(_('Endpoint'), s.vpn.endpoint), row(_('Allowed IPs'), s.vpn.allowedIps), row(_('Latest handshake'), s.vpn.latestHandshake), row(_('Transfer (↓ / ↑)'), `${s.vpn.rx} / ${s.vpn.tx}`)], L.url('admin/network/network'), _('VPN Settings')),
			card('devices', '▣', _('Devices'), _('%d connected clients').format(s.devices.total), 'active', 'info', [row(_('Wired clients'), s.devices.wired), row(_('Wi-Fi clients'), s.devices.wifi), row(_('Total unique'), s.devices.total)], L.url('admin/status/overview'), _('View Devices')),
			card('storage', '▭', _('Storage'), s.storage.status === 'mounted' ? _('USB storage detected') : _('No storage detected'), s.storage.status === 'mounted' ? 'mounted' : 'not mounted', s.storage.status === 'mounted' ? 'good' : 'muted', [row(_('Mount point'), s.storage.mountpoint), row(_('Device'), s.storage.device), row(_('Total space'), s.storage.total), row(_('Used space'), s.storage.used), row(_('Free space'), s.storage.free), row(_('Filesystem'), s.storage.filesystem)]),
			card('system', '⚙', _('System'), s.system.firmware, 'healthy', 'good', [row(_('Model'), s.system.model), row(_('Architecture'), s.system.architecture), row(_('CPU load (1 / 5 / 15)'), s.system.load), row(_('Memory'), s.system.memory), row(_('Temperature'), s.system.temperature), row(_('Uptime'), s.system.uptime)], L.url('admin/system/system'), _('System Settings'))
		]);
	},
	renderShell(snapshot) {
		return E('div', { class: 'archer-dashboard' }, [E('section', { class: 'archer-dashboard-hero' }, [E('div', {}, [E('h1', {}, [_('Dashboard')]), E('p', {}, [_('Overview of your router, network and system status')])]), E('div', { class: 'archer-dashboard-uptime' }, [_('Uptime'), ' ', E('b', {}, [snapshot.system.uptime])])]), this.renderCards(snapshot)]);
	},
	render(snapshot) {
		const shell = this.renderShell(snapshot);
		if (this._timer) window.clearInterval(this._timer);
		this._timer = window.setInterval(() => dashboardData.loadSnapshot().then((next) => { const fresh = this.renderShell(next); shell.replaceChildren(...fresh.childNodes); }).catch(() => {}), REFRESH_MS);
		window.addEventListener('beforeunload', () => { if (this._timer) window.clearInterval(this._timer); }, { once: true });
		return shell;
	},
	handleSaveApply: null,
	handleSave: null,
	handleReset: null
});
