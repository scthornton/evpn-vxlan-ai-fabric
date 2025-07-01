# 🚀 AI-Ready Data Center Network: EVPN-VxLAN Lab

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NVIDIA Air](https://img.shields.io/badge/Platform-NVIDIA%20Air-green.svg)](https://air.nvidia.com)
[![Network](https://img.shields.io/badge/Protocol-EVPN--VxLAN-orange.svg)](https://tools.ietf.org/html/rfc7432)

A comprehensive lab implementation of a modern data center fabric using EVPN-VxLAN overlay technology, designed to support high-performance AI/ML workloads. Built on NVIDIA Air platform with full automation and testing suite.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Lab Components](#lab-components)
- [Testing & Validation](#testing--validation)
- [Performance Results](#performance-results)
- [Troubleshooting](#troubleshooting)
- [Use Cases](#use-cases)
- [Contributing](#contributing)
- [Resources](#resources)
- [Author](#author)

## 🎯 Overview

This project demonstrates the design, implementation, and validation of an enterprise-grade EVPN-VxLAN network fabric optimized for AI infrastructure. It simulates the networking requirements of modern GPU clusters, including the demanding east-west traffic patterns of distributed AI training.

### Why This Matters

Modern AI training requires:
- **Ultra-low latency** for collective operations (AllReduce, AllGather)
- **Non-blocking bandwidth** between GPU nodes
- **Scalability** to thousands of endpoints
- **Multi-tenancy** for resource sharing
- **Resilience** to failures without disrupting training

This lab addresses all these requirements using industry-standard protocols and best practices aligned with NVIDIA's DGX BasePOD architecture.

## ✨ Features

### Network Design
- 🏗️ **CLOS Leaf-Spine Architecture** - Non-blocking, scalable fabric design
- 🔄 **EVPN-VxLAN Overlay** - Modern overlay solution for multi-tenancy
- 🚦 **eBGP Underlay** - Simple, scalable routing with fast convergence
- 🔐 **Multi-Tenant Isolation** - Secure segmentation for different workloads

### Automation & Testing
- 🐍 **Python Test Automation** - Comprehensive testing framework
- 📊 **Performance Analytics** - Bandwidth and latency measurements
- 🔥 **Failure Simulation** - Automated resilience testing
- 📈 **AI Traffic Patterns** - AllReduce and broadcast simulation

### Monitoring & Visualization
- 📉 **Real-time Metrics** - Performance dashboards
- 🗺️ **Topology Visualization** - Network diagram generation
- 📝 **Automated Reporting** - Test results and health checks
- 🔍 **Troubleshooting Tools** - Debug scripts and guides

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EVPN-VxLAN Overlay                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│         ┌──────────┐                    ┌──────────┐        │
│         │ Spine-1  │                    │ Spine-2  │        │
│         │ AS 65001 │                    │ AS 65002 │        │
│         │10.0.0.1  │                    │10.0.0.2  │        │
│         └────┬─────┘                    └────┬─────┘        │
│              │                                │               │
│     ┌────────┴────────┬────────┬─────────────┴────────┐     │
│     │                 │        │                       │     │
│ ┌───┴────┐      ┌────┴───┐  ┌─┴──────┐         ┌─────┴───┐ │
│ │ Leaf-1 │      │ Leaf-2 │  │ Leaf-3 │         │ Leaf-4  │ │
│ │AS 65011│      │AS 65012│  │AS 65013│         │AS 65014 │ │
│ │10.0.0.11│     │10.0.0.12│ │10.0.0.13│        │10.0.0.14│ │
│ └───┬────┘      └────┬───┘  └───┬────┘         └─────┬───┘ │
│     │                │          │                     │      │
│     │                │          │                     │      │
│ ┌───┴────┐      ┌────┴───┐  ┌──┴─────┐         ┌────┴────┐ │
│ │ GPU-1  │      │ GPU-2  │  │ GPU-3  │         │ GPU-4   │ │
│ │VLAN 10 │      │VLAN 10 │  │VLAN 20 │         │VLAN 20  │ │
│ └────────┘      └────────┘  └────────┘         └─────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **eBGP Everywhere** - Unique AS per node for optimal path selection
2. **/31 P2P Links** - Efficient IP utilization
3. **Loopback VTEPs** - VTEP availability independent of physical interfaces
4. **ECMP Load Balancing** - Utilize all available paths

## 📚 Prerequisites

### Required Knowledge
- Basic understanding of BGP and EVPN
- Familiarity with Linux CLI
- Python programming basics (for automation)

### Technical Requirements
- NVIDIA Air account (free)
- SSH client
- Python 3.8+ (for automation scripts)
- Web browser for Air GUI

### Recommended Background
- CCNP/JNCIP level networking knowledge
- Experience with data center fabrics
- Understanding of overlay technologies

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/scthornton/evpn-vxlan-lab.git
cd evpn-vxlan-lab
```

### 2. Set Up NVIDIA Air Environment
```bash
# Login to NVIDIA Air
# Create new simulation from EVPN template or upload topology.dot
# Start the simulation
```

### 3. Deploy Base Configuration
```bash
# Run the automated deployment script
./scripts/deploy_base_config.sh

# Or manually configure each device
ssh cumulus@<device-ip>
sudo net add configuration...
```

### 4. Run Validation Tests
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run comprehensive test suite
python tests/evpn_tester.py --topology configs/topology.json --tests all
```

### 5. View Results
```bash
# Check test report
cat evpn_test_report.txt

# View performance visualizations
open bandwidth_heatmap.png
```

## 🔧 Lab Components

### `/configs`
- `topology.json` - Lab topology definition
- `spine_config.txt` - Spine switch configurations
- `leaf_config.txt` - Leaf switch configurations
- `host_config.txt` - Host configurations

### `/scripts`
- `deploy_base_config.sh` - Automated deployment
- `health_check.sh` - Quick health validation
- `traffic_generator.py` - AI traffic pattern simulation
- `failover_test.sh` - Resilience testing

### `/tests`
- `evpn_tester.py` - Main test automation framework
- `performance_baseline.py` - Performance benchmarking
- `security_validation.py` - Multi-tenancy verification

### `/docs`
- `troubleshooting_guide.md` - Common issues and solutions
- `design_decisions.md` - Architecture rationale
- `performance_tuning.md` - Optimization guide

## 🧪 Testing & Validation

### Automated Test Suite

The lab includes comprehensive testing for:

#### 1. Control Plane Validation
```python
# BGP Underlay Testing
- Verify all BGP sessions established
- Check route propagation
- Validate ECMP functionality

# EVPN Overlay Testing  
- Confirm EVPN neighbor relationships
- Verify MAC/IP advertisement
- Check VNI configuration
```

#### 2. Data Plane Validation
```python
# Connectivity Testing
- End-to-end ping tests
- Multi-tenant isolation verification
- Broadcast/multicast functionality

# Performance Testing
- Bandwidth measurements (iperf3)
- Latency profiling (netperf)
- Jitter and packet loss analysis
```

#### 3. Resilience Testing
```python
# Failure Scenarios
- Single spine failure
- Leaf switch failure  
- Link flapping
- Recovery time measurement
```

#### 4. AI Workload Simulation
```python
# Traffic Patterns
- AllReduce communication pattern
- Broadcast operations
- Ring-based collective operations
- Parameter server patterns
```

### Running Tests

```bash
# Run all tests
python tests/evpn_tester.py --topology configs/topology.json --tests all

# Run specific test category
python tests/evpn_tester.py --topology configs/topology.json --tests bgp evpn

# Generate performance baseline
python tests/performance_baseline.py --duration 300
```

## 📊 Performance Results

### Baseline Performance Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|---------|
| E-W Bandwidth | > 9 Gbps | 9.4 Gbps | ✅ PASS |
| RTT Latency | < 0.5ms | 0.248ms | ✅ PASS |
| Convergence Time | < 3s | 0.9s | ✅ PASS |
| Packet Loss | 0% | 0% | ✅ PASS |

### AI Workload Performance

| Pattern | Total BW | Per-Flow BW | Efficiency |
|---------|----------|-------------|------------|
| AllReduce | 112 Gbps | 9.3 Gbps | 93% |
| Broadcast | 28 Gbps | 9.4 Gbps | 94% |
| Ring | 37 Gbps | 9.2 Gbps | 92% |

### Failure Recovery Times

| Scenario | Detection | Convergence | Total |
|----------|-----------|-------------|--------|
| Spine Failure | 0.3s | 0.6s | 0.9s |
| Leaf Failure | 0.2s | 0.4s | 0.6s |
| Link Failure | 0.1s | 0.3s | 0.4s |

## 🔧 Troubleshooting

### Common Issues

#### BGP Sessions Not Establishing
```bash
# Check connectivity
ping -I swp1 <neighbor-ip>

# Verify BGP configuration
net show bgp summary
net show bgp neighbor <neighbor-ip>

# Check logs
sudo journalctl -u bgpd -f
```

#### EVPN Routes Not Propagating
```bash
# Verify EVPN activation
net show bgp l2vpn evpn summary

# Check VNI advertisement
net show evpn vni
net show bgp l2vpn evpn route

# Verify VTEP configuration
net show vxlan vtep
```

#### No End-to-End Connectivity
```bash
# Check MAC learning
net show evpn mac vni all

# Verify VLAN to VNI mapping
net show bridge vlan

# Test underlay connectivity
traceroute -s <loopback-ip> <remote-loopback>
```

For detailed troubleshooting, see [docs/troubleshooting_guide.md](docs/troubleshooting_guide.md)

## 💡 Use Cases

### 1. AI/ML Infrastructure
- Distributed training clusters
- GPU-to-GPU communication optimization
- Parameter server architectures
- Inference serving networks

### 2. Cloud-Native Applications
- Kubernetes cluster networking
- Microservices communication
- Container overlay networks
- Service mesh integration

### 3. Traditional Enterprise
- Multi-tenant isolation
- Workload mobility
- Disaster recovery
- Hybrid cloud connectivity

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, fork the repository, and create pull requests.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Include docstrings for functions

## 📚 Resources

### Documentation
- [NVIDIA Air Platform Guide](https://docs.nvidia.com/networking-ethernet-software/guides/nvidia-air/)
- [Cumulus Linux Documentation](https://docs.nvidia.com/networking-ethernet-software/)
- [RFC 7432 - BGP MPLS-Based Ethernet VPN](https://tools.ietf.org/html/rfc7432)
- [NVIDIA DGX BasePOD Reference Architecture](https://docs.nvidia.com/dgx-basepod/)

### Related Projects
- [FRRouting](https://github.com/FRRouting/frr)
- [Containerlab](https://github.com/srl-labs/containerlab)
- [Batfish](https://github.com/batfish/batfish)

### Learning Resources
- [EVPN in the Data Center (Book)](https://www.oreilly.com/library/view/evpn-in-the/9781492029045/)
- [Building Data Centers with VXLAN BGP EVPN](https://www.cisco.com/c/en/us/td/docs/dcn/bpg/vxlan-bgp-evpn/index.html)

## 👤 Author

**Scott Thornton**

- LinkedIn: [@scthornton](https://www.linkedin.com/in/scthornton/)
- GitHub: [@scthornton](https://github.com/scthornton)
- Blog: [EVPN-VxLAN](https://scthornton.github.io/networking/ai-ml/2025/05/01/evpn-vxlan-blog-post.html)

### Background
Senior Infrastructure & Security Architect with 20+ years of experience in enterprise networking. Currently focused on AI infrastructure and security at Palo Alto Networks. Recent certifications include NVIDIA InfiniBand, RDMA Programming, and AI Infrastructure Operations.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- NVIDIA Air team for the excellent platform
- Cumulus Linux community for documentation
- EVPN/VxLAN pioneers who created these protocols
- The AI/ML community driving infrastructure innovation

---

⭐ If you find this project helpful, please consider giving it a star!

*Last updated: December 2024*
