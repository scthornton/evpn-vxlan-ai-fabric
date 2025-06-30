# EVPN-VxLAN Troubleshooting Guide
## Common Issues and Solutions for AI Data Center Fabrics

---

## 🔍 Troubleshooting Methodology

### 1. Follow the OSI Model (Bottom-Up)
```
Layer 1 (Physical) → Layer 2 (Switching) → Layer 3 (Routing) → Overlay (EVPN-VxLAN)
```

### 2. Verify in Order:
1. Physical connectivity
2. IP reachability (underlay)
3. BGP sessions
4. EVPN control plane
5. VxLAN data plane
6. End-to-end connectivity

---

## 🚨 Common Issues and Solutions

### Issue 1: BGP Sessions Not Establishing

**Symptoms:**
```bash
net show bgp summary
# Shows "Connect" or "Active" state instead of "Established"
```

**Troubleshooting Steps:**

1. **Check Physical Connectivity:**
```bash
net show interface swp1
# Look for "UP" state

# Test layer 3 connectivity
ping -I swp1 10.1.1.0
```

2. **Verify BGP Configuration:**
```bash
# Check local AS number
net show bgp
# Verify it matches what neighbors expect

# Check neighbor configuration
net show bgp neighbor 10.1.1.0
# Verify remote-as matches neighbor's local AS
```

3. **Common Fixes:**
```bash
# Fix: AS number mismatch
net del bgp neighbor 10.1.1.0
net add bgp neighbor 10.1.1.0 remote-as 65001  # Correct AS

# Fix: Wrong IP address
net del bgp neighbor 10.1.1.0
net add bgp neighbor 10.1.1.1 remote-as 65001  # Correct IP

# Fix: Interface not in BGP
net add bgp network 10.0.0.1/32  # Advertise loopback

net commit
```

**Debug Commands:**
```bash
# Enable BGP debugging
net add bgp debug neighbor-events
net add bgp debug updates
net commit

# View logs
sudo journalctl -u bgpd -f
```

### Issue 2: EVPN Routes Not Being Exchanged

**Symptoms:**
```bash
net show bgp l2vpn evpn summary
# Shows established but 0 prefixes received
```

**Troubleshooting Steps:**

1. **Verify EVPN is Activated:**
```bash
# On spine
net show bgp neighbor 10.0.0.11
# Look for "L2VPN EVPN: advertised and received"

# If missing, activate EVPN
net add bgp l2vpn evpn neighbor 10.0.0.11 activate
net commit
```

2. **Check VNI Advertisement:**
```bash
# On leaves
net show evpn vni
# Should show configured VNIs

# If empty, ensure advertise-all-vni
net add bgp l2vpn evpn advertise-all-vni
net commit
```

3. **Verify VTEP Configuration:**
```bash
# Check VTEP IP
net show vxlan vtep
# Should show local VTEP IP as loopback

# Fix if using wrong source
net del vxlan vni10 vxlan local-tunnelip
net add vxlan vni10 vxlan local-tunnelip 10.0.0.11
net commit
```

### Issue 3: MAC Addresses Not Being Learned

**Symptoms:**
```bash
net show evpn mac vni all
# Shows no remote MACs
```

**Troubleshooting Steps:**

1. **Verify Local MAC Learning:**
```bash
# Check bridge MAC table
bridge fdb show | grep -v permanent
# Should show local host MACs

# If empty, check host connectivity
net show interface swp10
# Ensure host interface is UP
```

2. **Check EVPN Route Types:**
```bash
# Look for Type-2 (MAC/IP) routes
net show bgp l2vpn evpn route type macip
# Should show local and remote MACs

# Look for Type-3 (IMET) routes
net show bgp l2vpn evpn route type multicast
# Should show one per VTEP per VNI
```

3. **Verify Route Import/Export:**
```bash
# Check route-targets
net show bgp l2vpn evpn vni
# Ensure RT values match across VTEPs
```

### Issue 4: VxLAN Tunnel Not Forming

**Symptoms:**
```bash
# No communication between hosts on different leaves
# Pings fail despite routes being present
```

**Troubleshooting Steps:**

1. **Check VTEP Reachability:**
```bash
# From Leaf1 to Leaf2
ping -I 10.0.0.11 10.0.0.12
# Must work for VxLAN to function
```

2. **Verify VxLAN Interface:**
```bash
net show interface vni10
# Check operational state

# Verify VLAN to VNI mapping
net show bridge vlan
# Ensure VLAN 10 maps to VNI 10
```

3. **Check MTU Issues:**
```bash
# VxLAN adds 50 bytes overhead
# Ensure underlay MTU is at least 1550

net show interface swp1
# Check MTU value

# Fix MTU if needed
net add interface swp1 mtu 9216
net commit
```

### Issue 5: Asymmetric Routing Issues

**Symptoms:**
- One-way traffic works
- Return traffic takes different path
- Intermittent connectivity

**Solution:**
```bash
# Enable symmetric routing
net add vxlan vni10 vxlan arp-nd-suppress on
net add bridge bridge arp-nd-suppress on
net commit
```

### Issue 6: Multi-tenancy Isolation Failure

**Symptoms:**
- Traffic leaking between VNIs
- Hosts in different VLANs can communicate

**Troubleshooting:**
```bash
# Verify VLAN isolation
net show bridge vlan

# Check VNI configuration
net show evpn vni detail

# Ensure unique L3VNI per tenant
net show vrf
```

---

## 🛠️ Advanced Debugging Techniques

### 1. Packet Capture
```bash
# Capture BGP traffic
sudo tcpdump -i swp1 -w bgp.pcap tcp port 179

# Capture VxLAN traffic
sudo tcpdump -i any -w vxlan.pcap udp port 4789

# Capture specific VNI
sudo tcpdump -i any -w vni10.pcap 'udp port 4789 and udp[8:2] = 0x0800 and udp[11:4] = 10'
```

### 2. Route Tracing
```bash
# Trace EVPN route propagation
net show bgp l2vpn evpn route detail

# Track specific MAC
net show bgp l2vpn evpn route mac 00:11:22:33:44:55
```

### 3. Performance Debugging
```bash
# Check for packet drops
net show counters port
net show counters port drops

# Monitor BGP update rate
net show bgp statistics
```

---

## 📊 Health Check Script

```bash
#!/bin/bash
# evpn-health-check.sh

echo "=== EVPN-VxLAN Health Check ==="
echo

echo "1. BGP Underlay Status:"
net show bgp summary | grep -E "Estab|Active|Connect"

echo -e "\n2. EVPN Control Plane:"
net show bgp l2vpn evpn summary | grep "Total number"

echo -e "\n3. VxLAN Data Plane:"
net show evpn vni | grep -E "VNI|Type"

echo -e "\n4. MAC Address Count:"
net show evpn mac vni all | grep "Number of MACs"

echo -e "\n5. VTEP Peers:"
net show vxlan vtep | grep -v "VNI"

echo -e "\n6. Interface Errors:"
net show interface all | grep -E "swp|vni" | grep -v "OK"

echo -e "\n=== Check Complete ==="
```

---

## 🎯 Quick Reference Commands

### Essential Verification Commands:
```bash
# BGP Status
net show bgp summary
net show bgp ipv4 unicast
net show bgp l2vpn evpn summary

# EVPN Status
net show evpn vni
net show evpn mac vni all
net show evpn rmac vni all
net show evpn next-hops vni all

# VxLAN Status
net show vxlan vtep
net show vxlan address
net show interface vni10

# Bridge Status
net show bridge macs
net show bridge vlan

# Route Verification
ip route show
bridge fdb show
```

---

## 💡 Pro Tips

1. **Always verify underlay before overlay** - If BGP IPv4 isn't working, EVPN won't work
2. **Check logs** - `sudo journalctl -u bgpd -u zebra -f` shows real-time issues
3. **Use symmetric topology** - Easier to troubleshoot when all leaves have same config
4. **Document baseline** - Save working configs and command outputs
5. **Test incrementally** - Add one feature at a time

---

## 🚀 Performance Optimization

### For AI Workloads:
```bash
# Enable PFC for lossless fabric
net add interface swp1 pfc priority 3

# Configure ECN for congestion management
net add qos ecn mode enabled

# Optimize BGP for fast convergence
net add bgp timers 3 9
net add bgp bestpath as-path multipath-relax

net commit
```

Remember: In AI clusters, even small optimizations can significantly impact training time!
