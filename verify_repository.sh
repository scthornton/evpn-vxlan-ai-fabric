#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "EVPN-VxLAN Repository Verification"
echo "======================================"

# Track issues
ISSUES=0

# Function to check file exists and has content
check_file() {
    local file=$1
    local min_lines=${2:-1}
    
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        if [ $lines -ge $min_lines ]; then
            echo -e "${GREEN}✓${NC} $file (${lines} lines)"
        else
            echo -e "${YELLOW}⚠${NC} $file exists but only has ${lines} lines (expected >= ${min_lines})"
            ((ISSUES++))
        fi
    else
        echo -e "${RED}✗${NC} $file is missing"
        ((ISSUES++))
    fi
}

# Function to check directory exists
check_dir() {
    local dir=$1
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${RED}✗${NC} $dir/ is missing"
        ((ISSUES++))
    fi
}

echo -e "\n1. CHECKING ESSENTIAL FILES:"
echo "----------------------------"
check_file "README.md" 50
check_file "LICENSE" 10
check_file ".gitignore" 10
check_file "requirements.txt" 5
check_file "CONTRIBUTING.md" 10

echo -e "\n2. CHECKING DIRECTORY STRUCTURE:"
echo "--------------------------------"
check_dir ".github"
check_dir ".github/workflows"
check_dir ".github/ISSUE_TEMPLATE"
check_dir "configs"
check_dir "configs/spine"
check_dir "configs/leaf"
check_dir "configs/automation"
check_dir "docs"
check_dir "docs/images"
check_dir "scripts"
check_dir "tests"
check_dir "results"

echo -e "\n3. CHECKING GITHUB SPECIFIC FILES:"
echo "----------------------------------"
check_file ".github/workflows/ci.yml" 10
check_file ".github/ISSUE_TEMPLATE/bug_report.md" 5
check_file ".github/ISSUE_TEMPLATE/feature_request.md" 5

echo -e "\n4. CHECKING DOCUMENTATION:"
echo "--------------------------"
check_file "docs/design-decisions.md" 50
check_file "docs/performance-tuning.md" 50
check_file "docs/troubleshooting.md" 50
check_file "docs/images/topology.png" 1

echo -e "\n5. CHECKING CONFIGURATION FILES:"
echo "--------------------------------"
check_file "configs/topology.json" 20
check_file "configs/spine/spine1_example.conf" 10
check_file "configs/leaf/leaf1_example.conf" 10

echo -e "\n6. CHECKING SCRIPTS (with content):"
echo "-----------------------------------"
check_file "scripts/deploy_base_config.sh" 100
check_file "scripts/traffic_generator.py" 300
check_file "scripts/health_check.py" 30
check_file "scripts/generate_topology_diagram.py" 30

# Check if scripts are executable
echo -e "\n7. CHECKING SCRIPT PERMISSIONS:"
echo "-------------------------------"
for script in scripts/*.py scripts/*.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "${GREEN}✓${NC} $script is executable"
        else
            echo -e "${YELLOW}⚠${NC} $script is not executable"
            ((ISSUES++))
        fi
    fi
done

echo -e "\n8. CHECKING TEST FILES:"
echo "-----------------------"
check_file "tests/test_connectivity.py" 20
check_file "tests/test_evpn_fabric.py" 30
check_file "tests/evpn_tester.py" 300

echo -e "\n9. CHECKING RESULTS:"
echo "--------------------"
check_file "results/performance_baseline.json" 10
check_file "results/performance_report.md" 20

echo -e "\n10. CHECKING PYTHON CODE QUALITY:"
echo "---------------------------------"
# Check for actual Python code (not just comments)
for pyfile in scripts/*.py tests/*.py; do
    if [ -f "$pyfile" ]; then
        # Count lines that are not comments or blank
        code_lines=$(grep -v '^\s*#' "$pyfile" | grep -v '^\s*$' | wc -l)
        if [ $code_lines -lt 10 ]; then
            echo -e "${YELLOW}⚠${NC} $pyfile has only $code_lines lines of actual code"
            ((ISSUES++))
        else
            echo -e "${GREEN}✓${NC} $pyfile has $code_lines lines of code"
        fi
    fi
done

echo -e "\n======================================"
echo "VERIFICATION SUMMARY:"
echo "======================================"

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Your repository is complete.${NC}"
else
    echo -e "${RED}✗ Found $ISSUES issues that need attention.${NC}"
fi

echo -e "\nADDITIONAL RECOMMENDATIONS:"
echo "---------------------------"
echo "1. Ensure CI badge in README.md shows 'passing'"
echo "2. Create at least one GitHub issue"
echo "3. Add topics to your repository (evpn-vxlan, ai-infrastructure, etc.)"
echo "4. Write meaningful commit messages"
echo "5. Consider adding screenshots to docs/images/"

