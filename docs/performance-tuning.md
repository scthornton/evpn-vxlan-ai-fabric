# Performance Tuning Guide: EVPN-VxLAN for AI Workloads

## Overview

This guide provides comprehensive performance tuning recommendations for EVPN-VxLAN fabrics supporting AI/ML workloads. The optimizations focus on minimizing latency, maximizing throughput, and ensuring consistent performance for distributed training operations.

## Table of Contents

1. [Understanding AI Traffic Patterns](#understanding-ai-traffic-patterns)
2. [Hardware Optimizations](#hardware-optimizations)
3. [Network Protocol Tuning](#network-protocol-tuning)
4. [QoS and Traffic Management](#qos-and-traffic-management)
5. [Linux Kernel Optimizations](#linux-kernel-optimizations)
6. [Application-Level Tuning](#application-level-tuning)
7. [Monitoring and Baselines](#monitoring-and-baselines)
8. [Troubleshooting Performance Issues](#troubleshooting-performance-issues)

## Understanding AI Traffic Patterns

### Collective Operations

AI training generates unique traffic patterns:

| Operation | Traffic Pattern | Network Requirement |
|-----------|----------------|-------------------|
| AllReduce | All-to-all burst | High bisection bandwidth |
| AllGather | All-to-all sustained | Low latency, high throughput |
| Broadcast | One-to-all | Efficient multicast |
| ReduceScatter | All-to-all staged | Consistent latency |

### Traffic Characteristics

```python
# Typical AI training traffic profile
{
    "message_sizes": ["1KB-10MB", "100MB-1GB for gradients"],
    "burst_pattern": "Synchronized across all nodes",
    "latency_sensitive": True,
    "loss_tolerant": False,  # Even small loss impacts training
    "bandwidth_intensive": True
}
```

## Hardware Optimizations

### NIC Configuration

#### Enable SR-IOV for GPU Direct
```bash
# Intel NICs
echo 8 > /sys/class/net/eth0/device/sriov_numvfs

# Mellanox NICs
mstconfig -d /dev/mst/mt4099_pci_cr0 set SRIOV_EN=1 NUM_OF_VFS=8
```

#### Optimize Ring Buffers
```bash
# Increase ring buffer sizes for high-throughput
ethtool -G eth0 rx 4096 tx 4096

# Verify settings
ethtool -g eth0
```

#### CPU Affinity
```bash
# Bind NIC interrupts to specific CPUs
echo 2 > /proc/irq/24/smp_affinity_list
echo 3 > /proc/irq/25/smp_affinity_list

# Use irqbalance with proper NUMA awareness
systemctl stop irqbalance
irqbalance --policyscript=/etc/irqbalance-numa.sh
```

### Switch ASIC Optimizations

#### Buffer Allocation
```bash
# On Cumulus Linux - optimize buffer allocation for elephant flows
net add qos buffer pool AI_POOL size 20971520
net add qos buffer profile AI_PROFILE pool AI_POOL size 2097152 threshold 16777216
net add interface swp1-48 qos buffer profile AI_PROFILE
```

#### ECMP Hash Tuning
```bash
# Optimize ECMP hashing for AI traffic patterns
net add forwarding ecmp hash-fields ip-protocol
net add forwarding ecmp hash-fields dst-ip
net add forwarding ecmp hash-fields src-ip
net add forwarding ecmp hash-fields dst-port
net add forwarding ecmp hash-fields src-port
net add forwarding ecmp adaptive-load-balance enable
```

## Network Protocol Tuning

### BGP Optimizations

#### Fast Convergence
```bash
# Aggressive timers for rapid failover
net add bgp timers 1 3
net add bgp timers connect 1

# Enable BGP fast-external-failover
net add bgp fast-external-failover

# Add BFD for microsecond failure detection
net add bgp neighbor 10.1.1.1 bfd
net add bgp neighbor 10.1.1.1 bfd detect-multiplier 3
net add bgp neighbor 10.1.1.1 bfd min-rx 50
net add bgp neighbor 10.1.1.1 bfd min-tx 50
```

#### Route Optimization
```bash
# Increase maximum paths for better load distribution
net add bgp maximum-paths 64
net add bgp bestpath as-path multipath-relax

# Enable add-path for backup path pre-computation
net add bgp neighbor 10.1.1.1 addpath-tx-all-paths
net add bgp neighbor 10.1.1.1 addpath-rx-all-paths
```

### EVPN Optimizations

#### MAC Mobility
```bash
# Optimize for workload mobility in dynamic environments
net add bgp l2vpn evpn mac-mobility threshold 5
net add bgp l2vpn evpn mac-mobility window 180
```

#### Route Advertisement
```bash
# Tune route advertisement intervals
net add bgp l2vpn evpn advertise-interval 0
net add bgp l2vpn evpn route-target auto-derivation
```

### VxLAN Optimizations

#### Packet Processing
```bash
# Enable hardware offload
ethtool -K eth0 tx-udp_tnl-segmentation on
ethtool -K eth0 tx-udp_tnl-csum-segmentation on
ethtool -K eth0 rx-udp_tnl-segmentation on

# Verify offload status
ethtool -k eth0 | grep udp_tnl
```

## QoS and Traffic Management

### Priority Flow Control (PFC)

Essential for RoCE/RDMA traffic:

```bash
# Enable PFC on priority 3 (RDMA traffic)
net add interface swp1 pfc priority 3
net add interface swp1 pfc rx enable
net add interface swp1 pfc tx enable

# Configure PFC watchdog
net add interface swp1 pfc watchdog enable
net add interface swp1 pfc watchdog action drop
net add interface swp1 pfc watchdog timeout 200
```

### DSCP Marking and Trust

```bash
# Trust DSCP markings from hosts
net add interface swp1-48 qos trust dscp

# Map DSCP to priority queues
net add qos dscp-map DSCP_AI dscp 46 priority 7  # EF for latency-sensitive
net add qos dscp-map DSCP_AI dscp 34 priority 5  # AF41 for throughput
net add qos dscp-map DSCP_AI dscp 26 priority 3  # AF31 for bulk transfer
```

### Weighted Fair Queuing

```bash
# Configure WFQ for AI traffic classes
net add qos scheduler DWRR_AI 
net add qos scheduler DWRR_AI priority 7 weight 40  # Latency-sensitive
net add qos scheduler DWRR_AI priority 5 weight 35  # Throughput
net add qos scheduler DWRR_AI priority 3 weight 20  # Bulk
net add qos scheduler DWRR_AI priority 0 weight 5   # Default

net add interface swp1-48 qos scheduler DWRR_AI
```

### ECN Configuration

```bash
# Enable ECN for congestion management
net add qos ecn mode symmetric
net add qos ecn red min 150000 max 1500000 probability 100

# Per-queue ECN thresholds
net add qos ecn queue 7 min 100000 max 500000
net add qos ecn queue 5 min 200000 max 1000000
```

## Linux Kernel Optimizations

### Network Stack Tuning

```bash
# /etc/sysctl.d/99-ai-network.conf

# Core network settings
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.netdev_max_backlog = 30000
net.core.netdev_budget = 600
net.core.netdev_budget_usecs = 8000

# TCP optimizations for AI workloads
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1
net.ipv4.tcp_window_scaling = 1

# Enable TCP fastopen
net.ipv4.tcp_fastopen = 3

# Increase connection tracking for many flows
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_buckets = 262144

# Disable reverse path filtering for asymmetric routing
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0

# Apply settings
sysctl -p /etc/sysctl.d/99-ai-network.conf
```

### NUMA Optimization

```bash
# Bind network processing to NUMA node with NIC
numactl --cpunodebind=0 --membind=0 /usr/sbin/irqbalance

# Check NUMA topology
numactl --hardware

# Set IRQ affinity to local NUMA node
./set_irq_affinity.sh local eth0
```

### Huge Pages

```bash
# Enable huge pages for better memory performance
echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Make persistent
echo "vm.nr_hugepages = 1024" >> /etc/sysctl.conf
```

## Application-Level Tuning

### MPI Optimizations

```bash
# Environment variables for collective operations
export OMPI_MCA_btl_tcp_eager_limit=524288
export OMPI_MCA_btl_tcp_max_send_size=524288
export OMPI_MCA_btl_tcp_rdma_pipeline_send_length=524288
export OMPI_MCA_coll_tuned_use_dynamic_rules=1
export OMPI_MCA_coll_tuned_allreduce_algorithm=6  # Recursive doubling
```

### NCCL Tuning

```bash
# NVIDIA NCCL optimizations
export NCCL_SOCKET_IFNAME=eth0
export NCCL_IB_DISABLE=0
export NCCL_ALGO=Ring
export NCCL_PROTO=Simple
export NCCL_NSOCKS_PERTHREAD=4
export NCCL_SOCKET_NTHREADS=8
export NCCL_BUFFSIZE=8388608
```

## Monitoring and Baselines

### Key Metrics to Monitor

```python
# Performance monitoring script
#!/usr/bin/env python3

import subprocess
import json
import time

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'latency': {'target': 0.5, 'unit': 'ms'},
            'throughput': {'target': 90, 'unit': 'Gbps'},
            'pfc_pause_frames': {'target': 0, 'unit': 'frames/sec'},
            'ecn_marks': {'target': '<1%', 'unit': 'percentage'},
            'buffer_drops': {'target': 0, 'unit': 'packets/sec'},
            'cpu_softirq': {'target': '<20%', 'unit': 'percentage'}
        }
    
    def collect_metrics(self):
        results = {}
        
        # Latency measurement
        latency_cmd = "ping -c 100 -i 0.01 10.0.0.12 | grep avg | awk -F'/' '{print $5}'"
        results['latency'] = float(subprocess.check_output(latency_cmd, shell=True))
        
        # Interface statistics
        stats_cmd = "ip -s -j link show eth0"
        stats = json.loads(subprocess.check_output(stats_cmd, shell=True))
        
        # Add more metric collection...
        
        return results
    
    def evaluate_performance(self, metrics):
        for metric, value in metrics.items():
            target = self.metrics[metric]['target']
            if isinstance(target, (int, float)):
                if value > target:
                    print(f"WARNING: {metric} = {value} exceeds target {target}")
```

### Baseline Testing

```bash
# Bandwidth baseline
for i in {1..10}; do
    iperf3 -c 192.168.10.2 -t 30 -P 8 -J >> bandwidth_baseline.json
done

# Latency baseline
for i in {1..1000}; do
    ping -c 1000 -i 0.01 192.168.10.2 >> latency_baseline.txt
done

# Analyze results
python3 analyze_baseline.py --bandwidth bandwidth_baseline.json --latency latency_baseline.txt
```

## Troubleshooting Performance Issues

### Common Issues and Solutions

#### Issue: High Tail Latency
```bash
# Check for microbursts
ethtool -S eth0 | grep -E 'pause|drop|error'

# Solution: Enable PFC and tune buffers
net add interface swp1 pfc priority 3
net add qos buffer profile AI_PROFILE size 4194304
```

#### Issue: Uneven ECMP Distribution
```bash
# Check flow distribution
net show interface counters | grep swp

# Solution: Tune ECMP hash
net add forwarding ecmp hash-polynomial 0x801
net add forwarding ecmp adaptive-load-balance enable
```

#### Issue: TCP Incast
```bash
# Symptoms: Sudden throughput drops with many-to-one traffic

# Solution 1: Increase switch buffers
net add qos buffer pool INCAST_POOL size 33554432

# Solution 2: Enable TCP pacing
tc qdisc add dev eth0 root fq maxrate 95gbit

# Solution 3: Tune TCP RTO
echo 10 > /proc/sys/net/ipv4/tcp_rto_min
```

### Performance Validation Checklist

- [ ] All interfaces negotiated at expected speed
- [ ] No CRC or alignment errors
- [ ] PFC enabled and no pause storms
- [ ] ECN marking but minimal drops
- [ ] ECMP distributing flows evenly
- [ ] CPU softirq below 20%
- [ ] No packet drops in kernel
- [ ] Application seeing expected throughput

## Best Practices Summary

1. **Start with baseline measurements** before optimization
2. **Optimize systematically** - one change at a time
3. **Monitor continuously** - performance can degrade over time
4. **Test with realistic workloads** - synthetic tests may not reveal all issues
5. **Document all changes** - maintain tuning runbooks
6. **Plan for growth** - ensure optimizations scale

## References

- [NVIDIA Collective Communication Library (NCCL) Documentation](https://docs.nvidia.com/deeplearning/nccl/)
- [RoCE Configuration Best Practices](https://community.mellanox.com/s/article/roce-configuration-best-practices)
- [Data Center TCP (DCTCP)](https://datatracker.ietf.org/doc/html/rfc8257)
- [High Performance Browser Networking](https://hpbn.co/)

---

*Guide maintained by: Scott Thornton*  
*Last updated: December 2024*  
*Version: 1.0*
