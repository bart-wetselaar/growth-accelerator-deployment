#!/usr/bin/env python3
"""
Azure Architecture Visualization Generator for Growth Accelerator Staffing Platform

This script generates a visual representation of the Azure architecture that will be
deployed for the Growth Accelerator Staffing Platform.

Requirements:
- graphviz package: pip install graphviz
"""

import argparse
import os
import sys
from graphviz import Digraph

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    print(f"{Colors.BLUE}{Colors.BOLD}==== {message} ===={Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}Error: {message}{Colors.ENDC}")

def generate_architecture_diagram(output_file="azure_architecture", format="png"):
    """
    Generate a Graphviz diagram of the Azure architecture for Growth Accelerator Staffing Platform.
    
    Args:
        output_file (str): Output file name without extension
        format (str): Output format (png, svg, pdf)
    
    Returns:
        str: Path to the generated file
    """
    print_header("GENERATING AZURE ARCHITECTURE DIAGRAM")
    print(f"Creating visualization of Azure resources that will be deployed...")
    
    # Create a new directed graph
    dot = Digraph(comment='Growth Accelerator Staffing Platform - Azure Architecture',
                 format=format)
    
    # Set graph attributes
    dot.attr('graph', 
             rankdir='TB',
             splines='ortho',
             nodesep='0.8',
             ranksep='1.2',
             fontname='Arial',
             fontsize='14',
             ratio='fill',
             size='11,8')
    
    # Set global node attributes
    dot.attr('node', 
             shape='box',
             style='filled',
             color='#D4D4D4',
             fillcolor='#FFFFFF',
             fontname='Arial',
             fontsize='12',
             height='0.6',
             width='1.6')
    
    # Set global edge attributes
    dot.attr('edge', 
             fontname='Arial',
             fontsize='10',
             color='#707070')
    
    # Create clusters for logical grouping
    with dot.subgraph(name='cluster_0') as c:
        c.attr(label='Azure Resource Group', 
               style='filled', 
               color='#E9F1FB', 
               fillcolor='#E9F1FB')
        
        # App Service Plan
        c.node('app_service_plan', 
               'App Service Plan\nPremiumV2 (P1v2)', 
               shape='box',
               fillcolor='#0078D4',
               fontcolor='white',
               color='#0078D4')
        
        # Web App
        c.node('web_app', 
               'Web App\nGrowth Accelerator\nStaffing', 
               shape='box',
               fillcolor='#0078D4',
               fontcolor='white',
               color='#0078D4')
        
        # PostgreSQL
        c.node('postgresql', 
               'Azure Database\nfor PostgreSQL', 
               shape='cylinder',
               fillcolor='#FFB900',
               fontcolor='black',
               color='#FFB900')
        
        # Application Insights
        c.node('app_insights', 
               'Application Insights', 
               shape='box',
               fillcolor='#68217A',
               fontcolor='white',
               color='#68217A')
        
        # Key Vault
        c.node('key_vault', 
               'Azure Key Vault', 
               shape='box',
               fillcolor='#4CAF50',
               fontcolor='white',
               color='#4CAF50')
        
        # CDN Profile
        c.node('cdn', 
               'Azure CDN\nStandard', 
               shape='box',
               fillcolor='#FF9800',
               fontcolor='black',
               color='#FF9800')
        
    # External resources
    dot.node('container_registry', 
             'GitHub Container\nRegistry', 
             shape='box',
             fillcolor='#24292E',
             fontcolor='white',
             color='#24292E')
    
    dot.node('dns', 
             'DNS\napp.growthaccelerator.nl', 
             shape='box',
             fillcolor='#512BD4',
             fontcolor='white',
             color='#512BD4')
    
    dot.node('users', 
             'Users', 
             shape='ellipse',
             fillcolor='#EFEFEF',
             fontcolor='black',
             color='#D4D4D4')
    
    # External APIs
    dot.node('workable_api', 
             'Workable API', 
             shape='box',
             fillcolor='#00A4EF',
             fontcolor='white',
             color='#00A4EF')
    
    dot.node('linkedin_api', 
             'LinkedIn API', 
             shape='box',
             fillcolor='#0077B5',
             fontcolor='white',
             color='#0077B5')
    
    dot.node('squarespace_api', 
             'Squarespace API', 
             shape='box',
             fillcolor='#000000',
             fontcolor='white',
             color='#000000')
    
    # Add edges
    dot.edge('users', 'dns', label='HTTPS')
    dot.edge('dns', 'cdn', label='CNAME Record')
    dot.edge('cdn', 'web_app', label='Origin')
    
    dot.edge('container_registry', 'web_app', label='Image Pull')
    dot.edge('app_service_plan', 'web_app', label='Hosts')
    dot.edge('web_app', 'postgresql', label='Connection\nString')
    dot.edge('web_app', 'app_insights', label='Telemetry')
    dot.edge('web_app', 'key_vault', label='Secret\nRetrieval')
    
    dot.edge('web_app', 'workable_api', label='API Calls')
    dot.edge('web_app', 'linkedin_api', label='API Calls')
    dot.edge('web_app', 'squarespace_api', label='API Calls')
    
    try:
        # Render and save the diagram
        output_path = dot.render(filename=output_file, cleanup=True)
        print_success(f"Architecture diagram generated successfully: {output_path}")
        return output_path
    except Exception as e:
        print_error(f"Failed to generate architecture diagram: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Generate Azure architecture visualization for Growth Accelerator Staffing Platform"
    )
    parser.add_argument(
        "--output", "-o", 
        default="azure_architecture", 
        help="Output file name without extension"
    )
    parser.add_argument(
        "--format", "-f",
        default="png",
        choices=["png", "svg", "pdf"],
        help="Output format (png, svg, pdf)"
    )
    
    args = parser.parse_args()
    
    try:
        # Check if graphviz is installed
        import graphviz
    except ImportError:
        print_error("Graphviz Python package not installed. Please install it with 'pip install graphviz'.")
        print("You also need the Graphviz binary installed on your system.")
        print("For Ubuntu/Debian: sudo apt-get install graphviz")
        print("For macOS: brew install graphviz")
        print("For Windows: Download from https://graphviz.org/download/")
        return 1
    
    output_path = generate_architecture_diagram(args.output, args.format)
    
    if output_path:
        print("\nYou can find the architecture diagram at:")
        print(f"  {output_path}")
        print("\nTo include this diagram in your documentation, use:")
        if args.format == "svg":
            print(f"  <img src=\"{os.path.basename(output_path)}\" alt=\"Azure Architecture\" />")
        else:
            print(f"  ![Azure Architecture]({os.path.basename(output_path)})")
        
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())