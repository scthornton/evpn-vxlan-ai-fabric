#!/usr/bin/env python3
"""
Generate network topology diagram for EVPN-VxLAN fabric
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.lines as lines

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Colors
spine_color = '#4A90E2'
leaf_color = '#7ED321'
host_color = '#F5A623'

# Title
ax.text(0.5, 0.95, 'EVPN-VxLAN Fabric for AI Workloads', 
        ha='center', fontsize=18, fontweight='bold')
ax.text(0.5, 0.91, '2-Spine, 4-Leaf CLOS Architecture', 
        ha='center', fontsize=12, style='italic')

# Draw spines
spine1 = Rectangle((0.3, 0.75), 0.15, 0.08, facecolor=spine_color, edgecolor='black', linewidth=2)
spine2 = Rectangle((0.55, 0.75), 0.15, 0.08, facecolor=spine_color, edgecolor='black', linewidth=2)
ax.add_patch(spine1)
ax.add_patch(spine2)

# Spine labels
ax.text(0.375, 0.79, 'Spine1', ha='center', va='center', fontsize=11, fontweight='bold')
ax.text(0.375, 0.76, 'AS 65001', ha='center', va='center', fontsize=9)
ax.text(0.625, 0.79, 'Spine2', ha='center', va='center', fontsize=11, fontweight='bold')
ax.text(0.625, 0.76, 'AS 65002', ha='center', va='center', fontsize=9)

# Draw leaves
leaf_positions = [0.1, 0.3, 0.5, 0.7]
leaves = []
for i, x in enumerate(leaf_positions):
    leaf = Rectangle((x, 0.45), 0.12, 0.08, facecolor=leaf_color, edgecolor='black', linewidth=2)
    ax.add_patch(leaf)
    ax.text(x + 0.06, 0.49, f'Leaf{i+1}', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(x + 0.06, 0.46, f'AS 6501{i+1}', ha='center', va='center', fontsize=9)

# Draw hosts
for i, x in enumerate(leaf_positions):
    host = Rectangle((x, 0.2), 0.12, 0.06, facecolor=host_color, edgecolor='black', linewidth=2)
    ax.add_patch(host)
    ax.text(x + 0.06, 0.23, f'GPU{i+1}', ha='center', va='center', fontsize=10, fontweight='bold')

# Draw connections
# Spine to leaf connections (full mesh)
for spine_x in [0.375, 0.625]:
    for leaf_x in [x + 0.06 for x in leaf_positions]:
        line = ax.plot([spine_x, leaf_x], [0.75, 0.53], 'k-', alpha=0.5, linewidth=1.5)[0]
        # Add connection labels on some links
        if spine_x == 0.375 and leaf_x < 0.3:
            ax.text((spine_x + leaf_x)/2, 0.64, 'eBGP', fontsize=8, alpha=0.7, rotation=-45)

# Leaf to host connections
for i, x in enumerate(leaf_positions):
    ax.plot([x + 0.06, x + 0.06], [0.45, 0.26], 'k-', linewidth=2.5)
    ax.text(x + 0.08, 0.35, 'VLAN 10', fontsize=8, rotation=-90, alpha=0.7)

# Add VXLAN tunnel representation
ax.plot([0.16, 0.76], [0.35, 0.35], 'b--', linewidth=2, alpha=0.6)
ax.text(0.46, 0.36, 'VXLAN Tunnels', ha='center', fontsize=10, color='blue', alpha=0.8)

# Add legend
legend_y = 0.08
ax.text(0.05, legend_y + 0.03, 'Legend:', fontweight='bold', fontsize=11)
ax.add_patch(Rectangle((0.15, legend_y), 0.03, 0.02, facecolor=spine_color))
ax.text(0.19, legend_y + 0.01, 'Spine Switch', fontsize=10)
ax.add_patch(Rectangle((0.32, legend_y), 0.03, 0.02, facecolor=leaf_color))
ax.text(0.36, legend_y + 0.01, 'Leaf Switch (VTEP)', fontsize=10)
ax.add_patch(Rectangle((0.52, legend_y), 0.03, 0.02, facecolor=host_color))
ax.text(0.56, legend_y + 0.01, 'GPU Host', fontsize=10)

# Add key specifications
specs_x = 0.85
specs_y = 0.7
ax.text(specs_x, specs_y, 'Specifications:', fontweight='bold', fontsize=10)
ax.text(specs_x, specs_y - 0.04, '• Underlay: eBGP', fontsize=9)
ax.text(specs_x, specs_y - 0.08, '• Overlay: EVPN', fontsize=9)
ax.text(specs_x, specs_y - 0.12, '• Encap: VXLAN', fontsize=9)
ax.text(specs_x, specs_y - 0.16, '• Links: 100G', fontsize=9)
ax.text(specs_x, specs_y - 0.20, '• MTU: 9216', fontsize=9)

# Clean up
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Save figure
plt.tight_layout()
plt.savefig('docs/images/topology.png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("✅ Topology diagram saved to docs/images/topology.png")

# Also save a smaller version for README
plt.savefig('docs/images/topology_small.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
print("✅ Small topology diagram saved to docs/images/topology_small.png")
