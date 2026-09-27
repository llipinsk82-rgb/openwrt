'use strict';

const NOT_AVAILABLE = 'Not available';

function stripCidr(value) {
	return typeof value === 'string' ? value.split('/')[0] : value;
}

function uniqueMacs(items) {
	const seen = new Set();
	for (const item of items || []) {
		const mac = String(item?.mac || item?.macaddr || '').toUpperCase();
		if (mac) seen.add(mac);
	}
	return seen;
}

function formatBytes(bytes) {
	if (bytes == null || !Number.isFinite(Number(bytes))) return NOT_AVAILABLE;
	let value = Number(bytes), unit = 'B';
	for (const next of ['KiB', 'MiB', 'GiB', 'TiB']) {
		if (value < 1024) break;
		value /= 1024;
		unit = next;
	}
	return '%s %s'.replace('%s', value >= 10 || unit === 'B' ? value.toFixed(0) : value.toFixed(1)).replace('%s', unit);
}

function formatUptime(seconds) {
	seconds = Math.max(0, Number(seconds) || 0);
	const days = Math.floor(seconds / 86400); seconds %= 86400;
	const hours = Math.floor(seconds / 3600); seconds %= 3600;
	const mins = Math.floor(seconds / 60);
	return [days ? `${days}d` : '', hours || days ? `${hours}h` : '', `${mins}m`].filter(Boolean).join(' ');
}

function normalizeWan(raw) {
	if (!raw) return { up: false, name: NOT_AVAILABLE, device: NOT_AVAILABLE, proto: NOT_AVAILABLE, uptime: 0, addresses: [], gateway: NOT_AVAILABLE };
	return {
		up: raw.up === true,
		name: raw.name || NOT_AVAILABLE,
		device: raw.device || NOT_AVAILABLE,
		proto: raw.proto || NOT_AVAILABLE,
		uptime: Number(raw.uptime) || 0,
		addresses: (raw.addresses || []).map(stripCidr).filter(Boolean),
		gateway: raw.gateway || NOT_AVAILABLE
	};
}

function normalizeSnapshot(raw) {
	raw = raw || {};
	const wan4 = normalizeWan(raw.wan4);
	const wan6 = normalizeWan(raw.wan6);
	const activeWifi = (raw.wifi || []).filter(r => r && !r.disabled);
	const wifiMacs = new Set();
	const radios = (raw.wifi || []).map((r) => {
		const clients = uniqueMacs(r?.clients || []);
		if (!r?.disabled) clients.forEach(mac => wifiMacs.add(mac));
		const signals = (r?.clients || []).map(c => Number(c.signal)).filter(Number.isFinite);
		return {
			radio: r?.radio || NOT_AVAILABLE,
			band: r?.band || NOT_AVAILABLE,
			ssid: r?.ssid || NOT_AVAILABLE,
			channel: r?.channel ?? NOT_AVAILABLE,
			active: !r?.disabled,
			clients: r?.disabled ? 0 : clients.size,
			bestSignal: signals.length && !r?.disabled ? Math.max(...signals) : null
		};
	});
	const wiredMacs = uniqueMacs(raw.wired_clients || []);
	const allMacs = new Set([...wifiMacs, ...wiredMacs]);
	const wg = (raw.wireguard || [])[0] || null;
	const mount = (raw.mounts || []).find(m => m && m.mount === '/mnt/usb') || null;
	const board = raw.board || {};
	const sys = raw.system || {};
	const mem = sys.memory || {};
	const memTotal = Number(mem.total) || 0;
	const memFree = (Number(mem.free) || 0) + (Number(mem.buffered) || 0) + (Number(mem.cached) || 0);
	const memUsed = Math.max(0, memTotal - memFree);
	const load = (sys.load || []).map(v => Number(v) / 65536);

	return {
		internet: {
			status: wan4.up || wan6.up ? 'online' : 'offline',
			ipv4: wan4.addresses[0] || NOT_AVAILABLE,
			ipv6: wan6.addresses[0] || NOT_AVAILABLE,
			gateway: wan4.gateway !== NOT_AVAILABLE ? wan4.gateway : wan6.gateway,
			interface: wan4.device !== NOT_AVAILABLE ? wan4.device : wan6.device,
			protocol: wan4.proto !== NOT_AVAILABLE ? wan4.proto : wan6.proto,
			uptime: formatUptime(Math.max(wan4.uptime, wan6.uptime))
		},
		wifi: { status: activeWifi.length ? 'active' : 'inactive', networks: activeWifi.length, clients: wifiMacs.size, radios },
		vpn: wg ? {
			status: wg.up ? 'connected' : 'inactive',
			interface: wg.interface || NOT_AVAILABLE,
			endpoint: wg.endpoint || NOT_AVAILABLE,
			allowedIps: Array.isArray(wg.allowed_ips) && wg.allowed_ips.length ? wg.allowed_ips.join(', ') : NOT_AVAILABLE,
			latestHandshake: wg.latest_handshake || NOT_AVAILABLE,
			rx: formatBytes(wg.rx_bytes), tx: formatBytes(wg.tx_bytes)
		} : { status: 'inactive', interface: NOT_AVAILABLE, endpoint: NOT_AVAILABLE, allowedIps: NOT_AVAILABLE, latestHandshake: NOT_AVAILABLE, rx: NOT_AVAILABLE, tx: NOT_AVAILABLE },
		devices: { total: allMacs.size, wired: wiredMacs.size, wifi: wifiMacs.size },
		storage: mount ? {
			status: 'mounted', mountpoint: mount.mount, device: mount.device || NOT_AVAILABLE, filesystem: mount.fstype || NOT_AVAILABLE,
			total: formatBytes(mount.size), used: formatBytes(Number(mount.size || 0) - Number(mount.free || 0)), free: formatBytes(mount.free)
		} : { status: 'not-mounted', mountpoint: '/mnt/usb', device: NOT_AVAILABLE, filesystem: NOT_AVAILABLE, total: NOT_AVAILABLE, used: NOT_AVAILABLE, free: NOT_AVAILABLE },
		system: {
			model: board.model || NOT_AVAILABLE,
			architecture: board.system || NOT_AVAILABLE,
			firmware: board.release?.description || NOT_AVAILABLE,
			uptime: formatUptime(sys.uptime),
			load: load.length ? load.slice(0, 3).map(v => v.toFixed(2)).join(' / ') : NOT_AVAILABLE,
			memory: memTotal ? `${formatBytes(memUsed)} / ${formatBytes(memTotal)} (${Math.round(memUsed * 100 / memTotal)}%)` : NOT_AVAILABLE,
			temperature: raw.temperature != null ? `${raw.temperature}°C` : NOT_AVAILABLE
		}
	};
}

const api = { NOT_AVAILABLE, formatBytes, formatUptime, normalizeSnapshot };
if (typeof module !== 'undefined' && module.exports)
	module.exports = api;
else
	return api;
