# Design Decisions: EVPN-VxLAN Architecture for AI Infrastructure

## Executive Summary

This document outlines the key architectural decisions made in designing an EVPN-VxLAN fabric optimized for AI/ML workloads. Each decision is backed by technical rationale and considers the unique requirements of GPU clusters and distributed training workloads.

## Table of Contents

1. [Underlay Design Decisions](#underlay-design-decisions)
2. [Overlay Design Decisions](#overlay-design-decisions)
3. [Topology Choices](#topology-choices)
4. [Protocol Selection](#protocol-selection)
5. [Scalability Considerations](#scalability-considerations)
6. [Performance Optimizations](#performance-optimizations)
7. [Security Architecture](#security-architecture)
8. [Operational Decisions](#operational-decisions)

## Underlay Design Decisions

### Decision: eBGP for Underlay Routing

**Choice**: External BGP (eBGP) with unique AS per node

**Rationale**:
- **Simplicity**: No need for IGP (OSPF/IS-IS), reducing protocol complexity
- **Loop Prevention**: BGP AS-PATH provides native loop prevention
- **Scalability**: Proven to scale to largest data centers (Facebook, Google)
- **Fast Convergence**: With tuned timers, achieves sub-second convergence

**Alternatives Considered**:
- **OSPF**: More complex in large-scale deployments, potential LSA flooding issues
- **IS-IS**: Less familiar to most engineers, limited vendor support
- **iBGP with IGP**: Additional protocol complexity without clear benefits

**Trade-offs**:
- Requires unique AS numbering (using 4-byte AS solves this)
- Slightly more complex initial configuration

### Decision: /31 Point-to-Point Links

**Choice**: Use /31 subnet masks for all fabric links

**Rationale**:
- **IP Conservation**: Uses only 2 IPs per link vs 4 with /30
- **Simplicity**: No broadcast domain considerations
- **Industry Standard**: Widely adopted in modern data centers

**Implementation**:
```
Spine1-Leaf1: 10.1.1.0/31 (.0 = Spine, .1 = Leaf)
Spine1-Leaf2: 10.1.2.0/31
```

### Decision: Loopback-based VTEPs

**Choice**: Use loopback interfaces for VXLAN tunnel endpoints

**Rationale**:
- **High Availability**: VTEP remains reachable via any active uplink
- **Load Balancing**: ECMP naturally distributes traffic
- **Simplicity**: Single VTEP IP per leaf regardless of uplink count

## Overlay Design Decisions

### Decision: EVPN as Control Plane

**Choice**: MP-BGP EVPN over static VxLAN or other overlays

**Rationale**:
- **Standards-Based**: IETF RFC 7432, broad vendor support
- **Feature-Rich**: Supports L2 and L3 services, multi-tenancy
- **Efficient**: Reduces flooding through proxy-ARP/ND
- **Scalable**: Proven in 100k+ endpoint deployments

**AI Workload Benefits**:
- **Fast Convergence**: Critical for maintaining training job continuity
- **All-Active Multi-homing**: Maximizes bandwidth for GPU nodes
- **Efficient BUM Handling**: Reduces unnecessary broadcast in large clusters

### Decision: VxLAN Encapsulation

**Choice**: VxLAN over other overlay technologies

**Rationale**:
- **UDP-Based**: Works with existing ECMP hashing
- **Hardware Support**: Broad ASIC support for line-rate encap/decap
- **Proven Scale**: Used in largest cloud providers
- **Tool Support**: Wide monitoring and troubleshooting ecosystem

**Considerations for AI**:
- **MTU**: Requires jumbo frames (9000+ bytes) for optimal performance
- **Overhead**: 50-byte header acceptable given modern 100G+ links

## Topology Choices

### Decision: 2-Tier Leaf-Spine Architecture

**Choice**: Simple leaf-spine over 3-tier or more complex topologies

**Rationale**:
- **Predictable Latency**: Maximum 3 hops between any endpoints
- **Non-Blocking**: With proper oversubscription ratios
- **Cost-Effective**: Fewer devices than 3-tier for same endpoint count
- **Operational Simplicity**: Easier to troubleshoot and maintain

**Scaling Strategy**:
- Start with 2 spines, scale to 4-8 as needed
- Each spine connects to all leaves
- Supports up to 48 leaves with 48-port spines

### Decision: 3:1 Oversubscription Ratio

**Choice**: Design for 3:1 oversubscription at leaf level

**Rationale**:
- **Cost/Performance Balance**: Full 1:1 rarely needed except for storage
- **AI Traffic Patterns**: Burst nature allows statistical multiplexing
- **Upgrade Path**: Can reduce to 2:1 or 1:1 by adding spines

**Calculation Example**:
```
Leaf with 48x 25G host ports = 1.2T southbound
4x 100G uplinks = 400G northbound
Oversubscription = 1200/400 = 3:1
```

## Protocol Selection

### Decision: BGP Timer Optimization

**Choice**: Aggressive BGP timers (3/9 seconds)

**Rationale**:
- **Fast Detection**: 3-second keepalive detects failures quickly
- **Rapid Convergence**: 9-second hold timer triggers fast reconvergence
- **CPU Impact**: Minimal on modern control planes
- **AI Workload Friendly**: Minimizes training disruption

**Configuration**:
```
net add bgp timers 3 9
net add bgp timers connect 10
```

### Decision: ECMP with 64-way Load Balancing

**Choice**: Enable maximum ECMP paths

**Rationale**:
- **Bandwidth Utilization**: Uses all available paths
- **Resilience**: Graceful degradation with failures
- **AI Traffic Distribution**: Spreads collective operations across links

**Tuning**:
```
net add bgp maximum-paths 64
net add bgp bestpath as-path multipath-relax
```

## Scalability Considerations

### Decision: Hierarchical IP Addressing

**Choice**: Structured IP scheme with clear boundaries

**Rationale**:
- **Aggregation**: Enables route summarization if needed
- **Troubleshooting**: Easy to identify device type by IP
- **Automation**: Predictable IPs simplify scripts

**Scheme**:
```
Loopbacks:     10.0.0.0/24    (Spines: .1-.10, Leaves: .11-.60)
P2P Links:     10.1.0.0/16    (Spine1: 10.1.x.x, Spine2: 10.2.x.x)
Management:    192.168.200.0/24
Host Networks: 192.168.0.0/16 (Per-tenant allocation)
```

### Decision: 4-Byte AS Numbers

**Choice**: Use 4-byte private AS range (4200000000-4294967294)

**Rationale**:
- **Scale**: Supports massive deployments without AS depletion
- **Organization**: Can encode location/role in AS number
- **Future-Proof**: No need to renumber as fabric grows

**Scheme**:
```
Spines: 420000XXXX (last 4 digits = spine number)
Leaves: 421000XXXX (last 4 digits = leaf number)
```

## Performance Optimizations

### Decision: Jumbo Frames Throughout

**Choice**: 9216-byte MTU on all fabric interfaces

**Rationale**:
- **VxLAN Overhead**: Accommodates 50-byte header without fragmentation
- **AI Workloads**: Large messages benefit from jumbo frames
- **RDMA Ready**: Required for RoCE deployments

### Decision: PFC for Lossless Ethernet

**Choice**: Enable Priority Flow Control on AI traffic classes

**Rationale**:
- **RDMA Support**: Required for RoCE to function properly
- **Training Stability**: Packet loss can disrupt distributed training
- **Selective Application**: Only on high-priority queues

**Configuration**:
```
net add interface swp1 pfc priority 3,4
net add qos roce mode lossless
```

### Decision: ECN for Congestion Management

**Choice**: Enable Explicit Congestion Notification

**Rationale**:
- **Proactive Management**: Signals congestion before drops occur
- **AI-Friendly**: Maintains training performance under load
- **Standard**: Works with modern TCP stacks

## Security Architecture

### Decision: Micro-Segmentation via VNIs

**Choice**: Use separate VNIs for different security zones

**Rationale**:
- **Isolation**: Hardware-enforced separation
- **Flexibility**: Easy to create/modify segments
- **Scale**: Supports 16M unique segments

**Implementation**:
```
VNI 10000-19999: Production AI workloads
VNI 20000-29999: Development/test
VNI 30000-39999: Management/monitoring
```

### Decision: Control Plane Protection

**Choice**: Implement CoPP and BGP security features

**Rationale**:
- **Stability**: Prevents control plane exhaustion
- **Security**: Protects against BGP hijacking
- **Best Practice**: Industry standard hardening

**Features**:
- BGP MD5 authentication
- Maximum prefix limits
- Route filtering
- Control plane policing

## Operational Decisions

### Decision: Ansible for Configuration Management

**Choice**: Ansible over other automation tools

**Rationale**:
- **Agentless**: No software to install on switches
- **Declarative**: Describes desired state
- **Wide Support**: Works with all major vendors
- **Easy Learning Curve**: YAML-based playbooks

### Decision: Standardized Naming Convention

**Choice**: Descriptive, hierarchical naming

**Rationale**:
- **Self-Documenting**: Name indicates role and location
- **Automation-Friendly**: Predictable patterns
- **Troubleshooting**: Easy to identify devices

**Convention**:
```
spine1-pod1
leaf1-rack1-pod1
border-leaf1-pod1
```

### Decision: Comprehensive Monitoring

**Choice**: Multi-layer monitoring approach

**Rationale**:
- **Proactive**: Detect issues before impact
- **Correlation**: Link network and application metrics
- **SLA Compliance**: Prove network meets AI workload needs

**Stack**:
- **Metrics**: Prometheus + Grafana
- **Logs**: ELK stack
- **Traces**: Jaeger for distributed tracing
- **Synthetic**: Continuous mesh testing

## Validation and Testing

### Decision: Continuous Validation

**Choice**: Automated testing in CI/CD pipeline

**Rationale**:
- **Confidence**: Every change is validated
- **Speed**: Rapid deployment with safety
- **Documentation**: Tests serve as living documentation

**Test Categories**:
1. **Unit Tests**: Configuration syntax and logic
2. **Integration Tests**: Protocol establishment
3. **Performance Tests**: Bandwidth and latency
4. **Chaos Tests**: Failure injection

## Future Considerations

### AI-Specific Enhancements

1. **In-Network Computing**: P4-programmable switches for aggregation
2. **Adaptive Routing**: ML-based traffic engineering
3. **GPU-Direct Integration**: Bypass CPU for ultra-low latency
4. **Intent-Based Networking**: Declarative AI workload requirements

### Technology Evolution

1. **400G/800G Migration**: Prepare for next-gen speeds
2. **SRv6 Evaluation**: Potential EVPN-VxLAN replacement
3. **Kubernetes Integration**: CNI plugin development
4. **Edge Computing**: Extend fabric to edge sites

## Conclusion

These design decisions create a robust, scalable, and performant network fabric suitable for demanding AI workloads while maintaining operational simplicity. The architecture provides a strong foundation that can evolve with emerging requirements while protecting existing investments.

---

*Document maintained by: Scott Thornton*  
*Last updated: December 2024*  
*Version: 1.0*
