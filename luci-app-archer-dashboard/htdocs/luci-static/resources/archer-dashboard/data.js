'use strict';
'require rpc';
'require network';
'require archer-dashboard.normalize as normalize';

const callSystemBoard = rpc.declare({ object: 'system', method: 'board' });
const callSystemInfo = rpc.declare({ object: 'system', method: 'info' });
const callMountPoints = rpc.declare({ object: 'luci', method: 'getMountPoints', expect: { result: [] } });
const callDHCPLeases = rpc.declare({ object: 'luci-rpc', method: 'getDHCPLeases', expect: { '': {} } });

function pickWan(nets, v6) {
	if (!nets?.length) return null;
	const net = nets.slice().sort((a, b) => (a.getMetric?.() ?? 0) - (b.getMetric?.() ?? 0))[0];
	const addrs = v6 ? (net.getIP6Addrs?.() || []) : (net.getIPAddrs?.() || []);
	return {
		up: !!net.isUp?.(), name: net.getName?.(), device: net.getDevice?.()?.getName?.(), proto: net.getProtocol?.() || net.getI18n?.(),
		uptime: net.getUptime?.() || 0, addresses: addrs,
		gateway: v6 ? net.getGateway6Addr?.() : net.getGatewayAddr?.()
	};
}

async function collectWifi() {
	const networks = await L.resolveDefault(network.getWifiNetworks(), []);
	return Promise.all(networks.map(async (net) => {
		const clients = await L.resolveDefault(net.getAssocList?.(), []);
		const freq = Number(net.getFrequency?.());
		return {
			radio: net.getWifiDeviceName?.(),
			band: Number.isFinite(freq) ? (freq < 3 ? '2.4 GHz' : '5 GHz') : 'Wi-Fi',
			ssid: net.getActiveSSID?.() || net.getSSID?.() || 'Not available',
			disabled: !!net.isDisabled?.(), channel: net.getChannel?.() || null,
			clients: clients.map(c => ({ mac: c.mac, signal: c.signal }))
		};
	}));
}

async function collectWireGuard() {
	const nets = await L.resolveDefault(network.getNetworks(), []);
	return nets.filter(n => n.getProtocol?.() === 'wireguard').map((net) => {
		const dev = net.getDevice?.();
		return {
			interface: net.getName?.(), up: !!net.isUp?.(), endpoint: null, allowed_ips: [], latest_handshake: null,
			rx_bytes: dev?.getRXBytes?.() ?? null, tx_bytes: dev?.getTXBytes?.() ?? null
		};
	});
}

async function loadSnapshot() {
	const [board, system, wans4, wans6, wifi, wireguard, leases, mounts] = await Promise.all([
		L.resolveDefault(callSystemBoard(), {}), L.resolveDefault(callSystemInfo(), {}),
		L.resolveDefault(network.getWANNetworks(), []), L.resolveDefault(network.getWAN6Networks(), []),
		collectWifi(), collectWireGuard(), L.resolveDefault(callDHCPLeases(), {}), L.resolveDefault(callMountPoints(), [])
	]);
	const wired = (leases?.dhcp_leases || []).map(l => ({ mac: l.macaddr })).filter(x => x.mac);
	return normalize.normalizeSnapshot({ board, system, wan4: pickWan(wans4, false), wan6: pickWan(wans6, true), wifi, wireguard, wired_clients: wired, mounts });
}

return { loadSnapshot };
