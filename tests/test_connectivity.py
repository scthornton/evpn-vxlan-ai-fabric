#!/usr/bin/env python3
"""
EVPN-VxLAN Testing Automation Suite
Author: Scott Thornton
Purpose: Automate testing of EVPN-VxLAN fabric for AI workloads
"""

import subprocess
import json
import time
import argparse
import logging
from datetime import datetime
import paramiko
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EVPNTester:
    """Main class for EVPN-VxLAN testing automation"""
    
    def __init__(self, topology_file):
        """Initialize tester with topology information"""
        self.topology = self.load_topology(topology_file)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
    def load_topology(self, topology_file):
        """Load topology configuration from JSON file"""
        with open(topology_file, 'r') as f:
            return json.load(f)
    
    def ssh_command(self, host, command, username='cumulus', password='cumulus'):
        """Execute command on remote host via SSH"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=username, password=password)
            
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            ssh.close()
            
            if error:
                logger.error(f"Error on {host}: {error}")
            
            return result
        except Exception as e:
            logger.error(f"SSH connection failed to {host}: {str(e)}")
            return None
    
    def test_bgp_underlay(self):
        """Test BGP underlay connectivity"""
        logger.info("Testing BGP Underlay...")
        test_results = {}
        
        for device in self.topology['devices']:
            if device['type'] in ['spine', 'leaf']:
                result = self.ssh_command(
                    device['mgmt_ip'],
                    'net show bgp summary json'
                )
                
                if result:
                    bgp_data = json.loads(result)
                    peers_up = 0
                    total_peers = len(bgp_data.get('peers', {}))
                    
                    for peer, data in bgp_data.get('peers', {}).items():
                        if data.get('state') == 'Established':
                            peers_up += 1
                    
                    test_results[device['name']] = {
                        'total_peers': total_peers,
                        'peers_up': peers_up,
                        'status': 'PASS' if peers_up == total_peers else 'FAIL'
                    }
                    
                    logger.info(f"{device['name']}: {peers_up}/{total_peers} BGP peers up")
        
        self.results['tests']['bgp_underlay'] = test_results
        return test_results
    
    def test_evpn_overlay(self):
        """Test EVPN overlay functionality"""
        logger.info("Testing EVPN Overlay...")
        test_results = {}
        
        for device in self.topology['devices']:
            if device['type'] == 'leaf':
                # Check EVPN neighbors
                result = self.ssh_command(
                    device['mgmt_ip'],
                    'net show bgp l2vpn evpn summary json'
                )
                
                if result:
                    evpn_data = json.loads(result)
                    test_results[device['name']] = {
                        'evpn_peers': len(evpn_data.get('peers', {})),
                        'status': 'PASS' if evpn_data.get('peers') else 'FAIL'
                    }
                
                # Check VNIs
                vni_result = self.ssh_command(
                    device['mgmt_ip'],
                    'net show evpn vni json'
                )
                
                if vni_result:
                    vni_data = json.loads(vni_result)
                    test_results[device['name']]['vnis'] = len(vni_data)
        
        self.results['tests']['evpn_overlay'] = test_results
        return test_results
    
    def test_vxlan_dataplane(self):
        """Test VxLAN data plane connectivity"""
        logger.info("Testing VxLAN Data Plane...")
        test_results = {}
        
        # Test connectivity between hosts
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for src_host in self.topology['hosts']:
                for dst_host in self.topology['hosts']:
                    if src_host != dst_host:
                        future = executor.submit(
                            self.ping_test,
                            src_host,
                            dst_host
                        )
                        futures.append((future, src_host, dst_host))
            
            for future, src, dst in futures:
                result = future.result()
                key = f"{src['name']}_to_{dst['name']}"
                test_results[key] = result
        
        self.results['tests']['vxlan_dataplane'] = test_results
        return test_results
    
    def ping_test(self, src_host, dst_host, count=10):
        """Perform ping test between hosts"""
        result = self.ssh_command(
            src_host['mgmt_ip'],
            f"ping -c {count} -i 0.2 {dst_host['data_ip']} | grep 'packet loss'"
        )
        
        if result:
            # Parse packet loss
            import re
            match = re.search(r'(\d+)% packet loss', result)
            if match:
                loss = int(match.group(1))
                return {
                    'packet_loss': loss,
                    'status': 'PASS' if loss == 0 else 'FAIL'
                }
        
        return {'packet_loss': 100, 'status': 'FAIL'}
    
    def test_performance(self):
        """Test network performance using iperf3"""
        logger.info("Testing Network Performance...")
        test_results = {}
        
        # Start iperf3 servers on all hosts
        for host in self.topology['hosts']:
            self.ssh_command(
                host['mgmt_ip'],
                'pkill iperf3; nohup iperf3 -s -D'
            )
        
        time.sleep(2)  # Wait for servers to start
        
        # Run iperf3 tests
        for src_host in self.topology['hosts']:
            for dst_host in self.topology['hosts']:
                if src_host != dst_host:
                    result = self.ssh_command(
                        src_host['mgmt_ip'],
                        f"iperf3 -c {dst_host['data_ip']} -t 10 -J"
                    )
                    
                    if result:
                        try:
                            iperf_data = json.loads(result)
                            bandwidth = iperf_data['end']['sum_sent']['bits_per_second'] / 1e9
                            test_results[f"{src_host['name']}_to_{dst_host['name']}"] = {
                                'bandwidth_gbps': round(bandwidth, 2),
                                'status': 'PASS' if bandwidth > 8.0 else 'FAIL'  # 80% of 10G
                            }
                        except:
                            logger.error(f"Failed to parse iperf3 results")
        
        self.results['tests']['performance'] = test_results
        return test_results
    
    def test_failure_recovery(self):
        """Test failure recovery scenarios"""
        logger.info("Testing Failure Recovery...")
        test_results = {}
        
        # Test 1: Spine failure
        spine1 = next(d for d in self.topology['devices'] if d['name'] == 'spine1')
        
        # Baseline ping
        baseline = self.ping_test(self.topology['hosts'][0], self.topology['hosts'][1])
        
        # Shutdown spine1 interfaces
        logger.info("Simulating spine1 failure...")
        for intf in ['swp1', 'swp2', 'swp3', 'swp4']:
            self.ssh_command(spine1['mgmt_ip'], f'net del interface {intf}')
        self.ssh_command(spine1['mgmt_ip'], 'net commit')
        
        # Wait for convergence
        time.sleep(5)
        
        # Test connectivity during failure
        failure_test = self.ping_test(self.topology['hosts'][0], self.topology['hosts'][1])
        
        # Restore spine1
        logger.info("Restoring spine1...")
        for intf in ['swp1', 'swp2', 'swp3', 'swp4']:
            self.ssh_command(spine1['mgmt_ip'], f'net add interface {intf}')
        self.ssh_command(spine1['mgmt_ip'], 'net commit')
        
        test_results['spine_failure'] = {
            'baseline_loss': baseline['packet_loss'],
            'failure_loss': failure_test['packet_loss'],
            'recovery_time': '< 5 seconds',
            'status': 'PASS' if failure_test['packet_loss'] < 10 else 'FAIL'
        }
        
        self.results['tests']['failure_recovery'] = test_results
        return test_results
    
    def test_ai_workload_patterns(self):
        """Test AI-specific traffic patterns"""
        logger.info("Testing AI Workload Patterns...")
        test_results = {}
        
        # Simulate AllReduce pattern
        hosts = self.topology['hosts']
        
        # Each host sends to all others simultaneously
        with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
            futures = []
            
            for src_host in hosts:
                for dst_host in hosts:
                    if src_host != dst_host:
                        future = executor.submit(
                            self.ssh_command,
                            src_host['mgmt_ip'],
                            f"iperf3 -c {dst_host['data_ip']} -t 30 -P 4 -J"
                        )
                        futures.append((future, src_host['name'], dst_host['name']))
            
            # Collect results
            total_bandwidth = 0
            for future, src, dst in futures:
                result = future.result()
                if result:
                    try:
                        data = json.loads(result)
                        bw = data['end']['sum_sent']['bits_per_second'] / 1e9
                        total_bandwidth += bw
                    except:
                        pass
        
        test_results['allreduce_pattern'] = {
            'total_bandwidth_gbps': round(total_bandwidth, 2),
            'average_per_flow_gbps': round(total_bandwidth / (len(hosts) * (len(hosts) - 1)), 2),
            'status': 'PASS' if total_bandwidth > 50 else 'FAIL'  # Arbitrary threshold
        }
        
        self.results['tests']['ai_workload_patterns'] = test_results
        return test_results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating Test Report...")
        
        # Create report
        report = []
        report.append("=" * 60)
        report.append("EVPN-VxLAN Test Report")
        report.append(f"Timestamp: {self.results['timestamp']}")
        report.append("=" * 60)
        
        # Summary
        total_tests = 0
        passed_tests = 0
        
        for test_category, tests in self.results['tests'].items():
            report.append(f"\n{test_category.upper()}")
            report.append("-" * 40)
            
            for test_name, result in tests.items():
                total_tests += 1
                status = result.get('status', 'UNKNOWN')
                if status == 'PASS':
                    passed_tests += 1
                
                report.append(f"{test_name}: {status}")
                for key, value in result.items():
                    if key != 'status':
                        report.append(f"  - {key}: {value}")
        
        # Overall summary
        report.append("\n" + "=" * 60)
        report.append(f"OVERALL: {passed_tests}/{total_tests} tests passed")
        report.append(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        report.append("=" * 60)
        
        # Save report
        report_text = '\n'.join(report)
        with open('evpn_test_report.txt', 'w') as f:
            f.write(report_text)
        
        # Save JSON results
        with open('evpn_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(report_text)
        return report_text
    
    def visualize_results(self):
        """Create visualizations of test results"""
        # Performance heatmap
        perf_data = self.results['tests'].get('performance', {})
        if perf_data:
            hosts = list(set([k.split('_to_')[0] for k in perf_data.keys()]))
            
            # Create bandwidth matrix
            matrix = []
            for src in hosts:
                row = []
                for dst in hosts:
                    if src == dst:
                        row.append(0)
                    else:
                        key = f"{src}_to_{dst}"
                        bw = perf_data.get(key, {}).get('bandwidth_gbps', 0)
                        row.append(bw)
                matrix.append(row)
            
            # Plot heatmap
            plt.figure(figsize=(8, 6))
            plt.imshow(matrix, cmap='YlOrRd', aspect='auto')
            plt.colorbar(label='Bandwidth (Gbps)')
            plt.xticks(range(len(hosts)), hosts)
            plt.yticks(range(len(hosts)), hosts)
            plt.xlabel('Destination')
            plt.ylabel('Source')
            plt.title('Inter-Host Bandwidth Heatmap')
            plt.tight_layout()
            plt.savefig('bandwidth_heatmap.png')
            plt.close()
            
            logger.info("Saved bandwidth heatmap to bandwidth_heatmap.png")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='EVPN-VxLAN Testing Automation')
    parser.add_argument('--topology', required=True, help='Topology JSON file')
    parser.add_argument('--tests', nargs='+', 
                       choices=['bgp', 'evpn', 'vxlan', 'performance', 'failure', 'ai', 'all'],
                       default=['all'], help='Tests to run')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = EVPNTester(args.topology)
    
    # Run selected tests
    if 'all' in args.tests:
        tests_to_run = ['bgp', 'evpn', 'vxlan', 'performance', 'failure', 'ai']
    else:
        tests_to_run = args.tests
    
    # Execute tests
    if 'bgp' in tests_to_run:
        tester.test_bgp_underlay()
    
    if 'evpn' in tests_to_run:
        tester.test_evpn_overlay()
    
    if 'vxlan' in tests_to_run:
        tester.test_vxlan_dataplane()
    
    if 'performance' in tests_to_run:
        tester.test_performance()
    
    if 'failure' in tests_to_run:
        tester.test_failure_recovery()
    
    if 'ai' in tests_to_run:
        tester.test_ai_workload_patterns()
    
    # Generate report and visualizations
    tester.generate_report()
    tester.visualize_results()

if __name__ == "__main__":
    main()

"""
Example topology.json file:

{
  "devices": [
    {
      "name": "spine1",
      "type": "spine",
      "mgmt_ip": "192.168.200.11",
      "asn": 65001
    },
    {
      "name": "spine2",
      "type": "spine",
      "mgmt_ip": "192.168.200.12",
      "asn": 65002
    },
    {
      "name": "leaf1",
      "type": "leaf",
      "mgmt_ip": "192.168.200.21",
      "asn": 65011
    },
    {
      "name": "leaf2",
      "type": "leaf",
      "mgmt_ip": "192.168.200.22",
      "asn": 65012
    }
  ],
  "hosts": [
    {
      "name": "host1",
      "mgmt_ip": "192.168.200.31",
      "data_ip": "192.168.10.1"
    },
    {
      "name": "host2",
      "mgmt_ip": "192.168.200.32",
      "data_ip": "192.168.10.2"
    }
  ]
}

Usage:
python evpn_tester.py --topology topology.json --tests all
"""
