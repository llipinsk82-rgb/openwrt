const assert = require('assert');
const fs = require('fs');
const path = require('path');
const normalize = require('../../luci-app-archer-dashboard/htdocs/luci-static/resources/archer-dashboard/normalize.js');
function fixture(name){return JSON.parse(fs.readFileSync(path.join(__dirname,'../fixtures/dashboard',name),'utf8'));}
{
  const s=normalize.normalizeSnapshot(fixture('normal.json'));
  assert.strictEqual(s.internet.status,'online');
  assert.strictEqual(s.internet.ipv4,'100.103.5.121');
  assert.strictEqual(s.internet.ipv6,'2a02:1234::1');
  assert.strictEqual(s.wifi.clients,3);
  assert.strictEqual(s.devices.total,4,'wifi+unique wired, duplicate MAC counted once');
  assert.strictEqual(s.vpn.status,'connected');
  assert.strictEqual(s.storage.mountpoint,'/mnt/usb');
  assert.strictEqual(s.system.model,'TP-Link Archer C7 v5');
  assert.ok(!JSON.stringify(s.vpn).toLowerCase().includes('private'));
}
{
  const s=normalize.normalizeSnapshot(fixture('missing_optional.json'));
  assert.strictEqual(s.internet.ipv6,'Not available');
  assert.strictEqual(s.vpn.status,'inactive');
  assert.strictEqual(s.storage.status,'not-mounted');
  assert.strictEqual(s.system.temperature,'Not available');
}
{
  const s=normalize.normalizeSnapshot(fixture('wifi_edge.json'));
  assert.strictEqual(s.wifi.clients,2,'same client on multiple SSIDs is deduplicated');
  assert.strictEqual(s.wifi.radios.filter(r=>r.active).length,2);
  assert.strictEqual(s.devices.total,3);
}
console.log('normalize fixtures: PASS');
