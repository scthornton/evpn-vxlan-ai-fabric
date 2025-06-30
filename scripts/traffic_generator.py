#!/usr/bin/env python3
"""
traffic_generator.py - AI Traffic Pattern Simulation
Author: Scott Thornton
Description: Simulates various AI/ML collective communication patterns
"""

import argparse
import json
import logging
import multiprocessing
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TrafficPattern:
    """Represents an AI traffic pattern"""
    name: str
    description: str
    message_size: int
    duration: int
    connections_per_host: int
    bidirectional: bool


class AITrafficGenerator:
    """Generates AI/ML-specific traffic patterns"""
    
    # Common AI traffic patterns
    PATTERNS = {
        'allreduce': TrafficPattern(
            name='AllReduce',
            description='All-to-all reduction (gradient aggregation)',
            message_size=100_000_000,  # 100MB typical gradient size
            duration=30,
            connections_per_host=0,  # Connect to all others
            bidirectional=True
        ),
        'allgather': TrafficPattern(
            name='AllGather',
            description='All-to-all gather operation',
            message_size=50_000_000,  # 50MB
            duration=30,
            connections_per_host=0,  # Connect to all others
            bidirectional=True
        ),
        'broadcast': TrafficPattern(
            name='Broadcast',
            description='One-to-all broadcast',
            message_size=1_000_000_000,  # 1GB model broadcast
            duration=60,
            connections_per_host=0,  # From root to all
            bidirectional=False
        ),
        'ring': TrafficPattern(
            name='Ring',
            description='Ring-based collective',
            message_size=100_000_000,
            duration=30,
            connections_per_host=2,  # Next and previous in ring
            bidirectional=True
        ),
        'parameter_server': TrafficPattern(
            name='ParameterServer',
            description='Parameter server pattern',
            message_size=50_000_000,
            duration=60,
            connections_per_host=1,  # Workers to PS
            bidirectional=True
        )
    }
    
    def __init__(self, topology_file: str):
        """Initialize traffic generator with topology"""
        self.topology = self._load_topology(topology_file)
        self.hosts = self._extract_hosts()
        self.results = {}
        
    def _load_topology(self, topology_file: str) -> Dict:
        """Load topology from JSON file"""
        try:
            with open(topology_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load topology: {e}")
            sys.exit(1)
            
    def _extract_hosts(self) -> List[Dict]:
        """Extract host information from topology"""
        return self.topology.get('hosts', [])
    
    def generate_traffic(self, pattern_name: str, custom_params: Dict = None):
        """Generate specified traffic pattern"""
        if pattern_name not in self.PATTERNS:
            raise ValueError(f"Unknown pattern: {pattern_name}")
            
        pattern = self.PATTERNS[pattern_name]
        logger.info(f"Generating {pattern.name} traffic pattern")
        
        # Override default parameters if custom ones provided
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(pattern, key):
                    setattr(pattern, key, value)
        
        # Execute pattern
        if pattern_name == 'allreduce':
            self._generate_allreduce(pattern)
        elif pattern_name == 'allgather':
            self._generate_allgather(pattern)
        elif pattern_name == 'broadcast':
            self._generate_broadcast(pattern)
        elif pattern_name == 'ring':
            self._generate_ring(pattern)
        elif pattern_name == 'parameter_server':
            self._generate_parameter_server(pattern)
            
    def _generate_allreduce(self, pattern: TrafficPattern):
        """Generate AllReduce traffic pattern"""
        logger.info("Starting AllReduce pattern generation")
        
        # Phase 1: Reduce-scatter
        logger.info("Phase 1: Reduce-scatter")
        with ThreadPoolExecutor(max_workers=len(self.hosts)) as executor:
            futures = []
            
            for i, src_host in enumerate(self.hosts):
                # Each host sends to subset of others
                targets = self._get_reduce_scatter_targets(i, len(self.hosts))
                
                for target_idx in targets:
                    if target_idx != i:
                        dst_host = self.hosts[target_idx]
                        future = executor.submit(
                            self._run_iperf_client,
                            src_host,
                            dst_host,
                            pattern.duration // 2,
                            pattern.message_size // len(self.hosts)
                        )
                        futures.append((future, src_host['name'], dst_host['name']))
            
            # Collect results
            phase1_results = self._collect_results(futures, "reduce-scatter")
        
        # Phase 2: Allgather
        logger.info("Phase 2: Allgather")
        with ThreadPoolExecutor(max_workers=len(self.hosts)) as executor:
            futures = []
            
            for i, src_host in enumerate(self.hosts):
                for j, dst_host in enumerate(self.hosts):
                    if i != j:
                        future = executor.submit(
                            self._run_iperf_client,
                            src_host,
                            dst_host,
                            pattern.duration // 2,
                            pattern.message_size // len(self.hosts)
                        )
                        futures.append((future, src_host['name'], dst_host['name']))
            
            # Collect results
            phase2_results = self._collect_results(futures, "allgather")
        
        # Combine results
        self.results['allreduce'] = {
            'phase1_reduce_scatter': phase1_results,
            'phase2_allgather': phase2_results,
            'total_bandwidth_gbps': self._calculate_total_bandwidth([phase1_results, phase2_results])
        }
    
    def _generate_allgather(self, pattern: TrafficPattern):
        """Generate AllGather traffic pattern"""
        logger.info("Starting AllGather pattern generation")
        
        with ThreadPoolExecutor(max_workers=len(self.hosts) * len(self.hosts)) as executor:
            futures = []
            
            # All-to-all communication
            for src_host in self.hosts:
                for dst_host in self.hosts:
                    if src_host != dst_host:
                        future = executor.submit(
                            self._run_iperf_client,
                            src_host,
                            dst_host,
                            pattern.duration,
                            pattern.message_size
                        )
                        futures.append((future, src_host['name'], dst_host['name']))
            
            results = self._collect_results(futures, "allgather")
            self.results['allgather'] = results
    
    def _generate_broadcast(self, pattern: TrafficPattern):
        """Generate broadcast traffic pattern"""
        logger.info("Starting Broadcast pattern generation")
        
        # Select root node (first host)
        root_host = self.hosts[0]
        
        with ThreadPoolExecutor(max_workers=len(self.hosts) - 1) as executor:
            futures = []
            
            # Root broadcasts to all others
            for dst_host in self.hosts[1:]:
                future = executor.submit(
                    self._run_iperf_client,
                    root_host,
                    dst_host,
                    pattern.duration,
                    pattern.message_size
                )
                futures.append((future, root_host['name'], dst_host['name']))
            
            results = self._collect_results(futures, "broadcast")
            self.results['broadcast'] = results
    
    def _generate_ring(self, pattern: TrafficPattern):
        """Generate ring-based traffic pattern"""
        logger.info("Starting Ring pattern generation")
        
        with ThreadPoolExecutor(max_workers=len(self.hosts)) as executor:
            futures = []
            
            # Each host sends to next in ring
            for i, src_host in enumerate(self.hosts):
                dst_host = self.hosts[(i + 1) % len(self.hosts)]
                
                future = executor.submit(
                    self._run_iperf_client,
                    src_host,
                    dst_host,
                    pattern.duration,
                    pattern.message_size
                )
                futures.append((future, src_host['name'], dst_host['name']))
            
            results = self._collect_results(futures, "ring")
            self.results['ring'] = results
    
    def _generate_parameter_server(self, pattern: TrafficPattern):
        """Generate parameter server traffic pattern"""
        logger.info("Starting Parameter Server pattern generation")
        
        # First host is parameter server
        ps_host = self.hosts[0]
        worker_hosts = self.hosts[1:]
        
        with ThreadPoolExecutor(max_workers=len(worker_hosts) * 2) as executor:
            futures = []
            
            # Workers push gradients to PS
            for worker in worker_hosts:
                future = executor.submit(
                    self._run_iperf_client,
                    worker,
                    ps_host,
                    pattern.duration,
                    pattern.message_size
                )
                futures.append((future, worker['name'], ps_host['name']))
            
            # PS pushes updated parameters to workers
            for worker in worker_hosts:
                future = executor.submit(
                    self._run_iperf_client,
                    ps_host,
                    worker,
                    pattern.duration,
                    pattern.message_size
                )
                futures.append((future, ps_host['name'], worker['name']))
            
            results = self._collect_results(futures, "parameter_server")
            self.results['parameter_server'] = results
    
    def _run_iperf_client(self, src_host: Dict, dst_host: Dict, 
                         duration: int, message_size: int) -> Dict:
        """Run iperf3 client on source host"""
        try:
            # Calculate parallel streams based on message size
            parallel_streams = min(8, max(1, message_size // 100_000_000))
            
            cmd = [
                'sshpass', '-p', 'cumulus',
                'ssh', f"cumulus@{src_host['mgmt_ip']}",
                f"iperf3 -c {dst_host['data_ip']} -t {duration} "
                f"-P {parallel_streams} -l {min(message_size, 1_000_000)} -J"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'success': True,
                    'bandwidth_bps': data['end']['sum_sent']['bits_per_second'],
                    'retransmits': data['end']['sum_sent'].get('retransmits', 0),
                    'cpu_percent': data['end']['cpu_utilization_percent']['host_total']
                }
            else:
                logger.error(f"iperf3 failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Error running iperf3: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_reduce_scatter_targets(self, host_idx: int, total_hosts: int) -> List[int]:
        """Get target hosts for reduce-scatter phase"""
        # Simple strategy: each host sends to next sqrt(N) hosts
        chunk_size = int(np.sqrt(total_hosts))
        targets = []
        
        for i in range(chunk_size):
            target = (host_idx + i + 1) % total_hosts
            targets.append(target)
            
        return targets
    
    def _collect_results(self, futures: List[Tuple], pattern_name: str) -> Dict:
        """Collect and aggregate results from futures"""
        results = {
            'pattern': pattern_name,
            'flows': [],
            'total_bandwidth_gbps': 0,
            'failed_flows': 0,
            'avg_cpu_percent': 0
        }
        
        total_bandwidth = 0
        total_cpu = 0
        successful_flows = 0
        
        for future, src, dst in futures:
            try:
                result = future.result(timeout=300)
                
                if result['success']:
                    bandwidth_gbps = result['bandwidth_bps'] / 1e9
                    results['flows'].append({
                        'src': src,
                        'dst': dst,
                        'bandwidth_gbps': round(bandwidth_gbps, 2),
                        'retransmits': result['retransmits']
                    })
                    total_bandwidth += bandwidth_gbps
                    total_cpu += result['cpu_percent']
                    successful_flows += 1
                else:
                    results['failed_flows'] += 1
                    logger.warning(f"Flow {src}->{dst} failed: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                logger.error(f"Error collecting result for {src}->{dst}: {e}")
                results['failed_flows'] += 1
        
        # Calculate aggregates
        if successful_flows > 0:
            results['total_bandwidth_gbps'] = round(total_bandwidth, 2)
            results['avg_cpu_percent'] = round(total_cpu / successful_flows, 2)
            results['avg_per_flow_gbps'] = round(total_bandwidth / successful_flows, 2)
        
        return results
    
    def _calculate_total_bandwidth(self, phase_results: List[Dict]) -> float:
        """Calculate total bandwidth across phases"""
        total = 0
        for phase in phase_results:
            total += phase.get('total_bandwidth_gbps', 0)
        return round(total / len(phase_results), 2)  # Average across phases
    
    def run_benchmark(self, patterns: List[str] = None):
        """Run complete benchmark suite"""
        if patterns is None:
            patterns = list(self.PATTERNS.keys())
        
        logger.info(f"Running benchmark for patterns: {patterns}")
        
        for pattern in patterns:
            logger.info(f"Starting {pattern} benchmark")
            
            # Start iperf3 servers on all hosts
            self._start_iperf_servers()
            time.sleep(5)  # Wait for servers to start
            
            # Generate traffic
            self.generate_traffic(pattern)
            
            # Stop servers
            self._stop_iperf_servers()
            
            # Brief pause between patterns
            time.sleep(10)
        
        # Generate report
        self.generate_report()
    
    def _start_iperf_servers(self):
        """Start iperf3 servers on all hosts"""
        logger.info("Starting iperf3 servers on all hosts")
        
        for host in self.hosts:
            cmd = [
                'sshpass', '-p', 'cumulus',
                'ssh', f"cumulus@{host['mgmt_ip']}",
                'pkill iperf3; nohup iperf3 -s -D'
            ]
            subprocess.run(cmd, capture_output=True)
    
    def _stop_iperf_servers(self):
        """Stop iperf3 servers on all hosts"""
        logger.info("Stopping iperf3 servers")
        
        for host in self.hosts:
            cmd = [
                'sshpass', '-p', 'cumulus',
                'ssh', f"cumulus@{host['mgmt_ip']}",
                'pkill iperf3'
            ]
            subprocess.run(cmd, capture_output=True)
    
    def generate_report(self):
        """Generate comprehensive traffic generation report"""
        logger.info("Generating traffic report")
        
        report = []
        report.append("=" * 80)
        report.append("AI Traffic Pattern Generation Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        for pattern_name, results in self.results.items():
            report.append(f"\n{pattern_name.upper()} Pattern Results")
            report.append("-" * 40)
            
            if isinstance(results, dict):
                if 'total_bandwidth_gbps' in results:
                    report.append(f"Total Bandwidth: {results['total_bandwidth_gbps']} Gbps")
                
                if 'avg_per_flow_gbps' in results:
                    report.append(f"Average Per Flow: {results['avg_per_flow_gbps']} Gbps")
                
                if 'failed_flows' in results:
                    report.append(f"Failed Flows: {results['failed_flows']}")
                
                if 'avg_cpu_percent' in results:
                    report.append(f"Average CPU Usage: {results['avg_cpu_percent']}%")
        
        report.append("\n" + "=" * 80)
        report.append("Summary")
        report.append("=" * 80)
        
        # Calculate overall statistics
        total_bandwidth = sum(
            r.get('total_bandwidth_gbps', 0) 
            for r in self.results.values() 
            if isinstance(r, dict)
        )
        report.append(f"Combined Bandwidth (all patterns): {total_bandwidth} Gbps")
        
        # Save report
        report_text = '\n'.join(report)
        
        with open('traffic_generation_report.txt', 'w') as f:
            f.write(report_text)
        
        # Save detailed JSON results
        with open('traffic_generation_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(report_text)
        logger.info("Report saved to traffic_generation_report.txt")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Generate AI/ML traffic patterns for network testing'
    )
    parser.add_argument(
        '--topology',
        required=True,
        help='Topology JSON file'
    )
    parser.add_argument(
        '--patterns',
        nargs='+',
        choices=list(AITrafficGenerator.PATTERNS.keys()) + ['all'],
        default=['all'],
        help='Traffic patterns to generate'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration for each pattern (seconds)'
    )
    parser.add_argument(
        '--message-size',
        type=int,
        help='Override default message size (bytes)'
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = AITrafficGenerator(args.topology)
    
    # Prepare custom parameters
    custom_params = {}
    if args.duration:
        custom_params['duration'] = args.duration
    if args.message_size:
        custom_params['message_size'] = args.message_size
    
    # Determine patterns to run
    if 'all' in args.patterns:
        patterns = list(AITrafficGenerator.PATTERNS.keys())
    else:
        patterns = args.patterns
    
    # Run benchmark
    try:
        generator.run_benchmark(patterns)
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        generator._stop_iperf_servers()
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        generator._stop_iperf_servers()
        raise


if __name__ == "__main__":
