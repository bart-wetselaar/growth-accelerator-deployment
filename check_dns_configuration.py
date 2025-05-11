#!/usr/bin/env python3
"""
DNS Configuration Checker for Growth Accelerator Staffing Platform

This script checks if the DNS configuration for app.growthaccelerator.nl is correctly set up.

Requirements:
- dnspython package: pip install dnspython
- Python 3.6+

Usage:
    python check_dns_configuration.py --domain app.growthaccelerator.nl --verification-id <verification-id>
    python check_dns_configuration.py --domain app.growthaccelerator.nl --verification-id <verification-id> --monitor
"""

import argparse
import dns.resolver
import time
import sys
from datetime import datetime

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

def check_dns_records(domain, verification_id=None):
    results = {
        "txt_record_exists": False,
        "txt_record_value_correct": False,
        "cname_record_exists": False,
        "cname_record_value_correct": False
    }
    
    print(f"Checking DNS configuration for: {domain}")
    
    # Check TXT record
    txt_hostname = f"asuid.{domain}"
    try:
        txt_answers = dns.resolver.resolve(txt_hostname, 'TXT')
        results["txt_record_exists"] = True
        
        if verification_id:
            # Check if any of the TXT records match the verification ID
            for rdata in txt_answers:
                for txt_string in rdata.strings:
                    txt_value = txt_string.decode('utf-8')
                    if txt_value == verification_id:
                        results["txt_record_value_correct"] = True
                        break
    except dns.resolver.NXDOMAIN:
        print_warning(f"TXT record for {txt_hostname} not found")
    except Exception as e:
        print_error(f"Error checking TXT record: {str(e)}")
    
    # Check CNAME record
    try:
        cname_answers = dns.resolver.resolve(domain, 'CNAME')
        results["cname_record_exists"] = True
        
        for rdata in cname_answers:
            cname_target = str(rdata.target).rstrip('.')
            if 'azurewebsites.net' in cname_target:
                results["cname_record_value_correct"] = True
                break
    except dns.resolver.NXDOMAIN:
        print_warning(f"CNAME record for {domain} not found")
    except dns.resolver.NoAnswer:
        print_warning(f"No CNAME record found for {domain}, it might be an A record")
        # Try to get A record
        try:
            a_answers = dns.resolver.resolve(domain, 'A')
            print(f"Found A record for {domain}: {', '.join(str(r) for r in a_answers)}")
        except:
            pass
    except Exception as e:
        print_error(f"Error checking CNAME record: {str(e)}")
    
    return results

def print_results(domain, results):
    print_header("DNS CONFIGURATION CHECK RESULTS")
    
    # TXT record check
    txt_hostname = f"asuid.{domain}"
    if results["txt_record_exists"]:
        print_success(f"TXT record for {txt_hostname} exists")
        if results["txt_record_value_correct"]:
            print_success(f"TXT record value matches verification ID")
        else:
            print_error(f"TXT record value does not match verification ID")
    else:
        print_error(f"TXT record for {txt_hostname} not found")
    
    # CNAME record check
    if results["cname_record_exists"]:
        print_success(f"CNAME record for {domain} exists")
        if results["cname_record_value_correct"]:
            print_success(f"CNAME record points to Azure App Service")
        else:
            print_error(f"CNAME record does not point to Azure App Service")
    else:
        print_error(f"CNAME record for {domain} not found")
    
    # Overall status
    if results["txt_record_exists"] and results["txt_record_value_correct"] and \
       results["cname_record_exists"] and results["cname_record_value_correct"]:
        print_success("DNS configuration is correct and ready for Azure App Service")
    else:
        print_warning("DNS configuration is incomplete or incorrect")
        print("\nRecommended actions:")
        if not results["txt_record_exists"]:
            print(f"  1. Add TXT record for {txt_hostname}")
        elif not results["txt_record_value_correct"]:
            print(f"  1. Update TXT record for {txt_hostname} with correct verification ID")
        
        if not results["cname_record_exists"]:
            print(f"  2. Add CNAME record for {domain} pointing to your Azure App Service")
        elif not results["cname_record_value_correct"]:
            print(f"  2. Update CNAME record for {domain} to point to your Azure App Service")

def monitor_dns_propagation(domain, verification_id, interval=300, max_checks=12):
    """Monitor DNS propagation over time"""
    print_header(f"MONITORING DNS PROPAGATION FOR {domain}")
    print(f"Checking every {interval} seconds, press Ctrl+C to stop")
    print("")
    
    check_count = 0
    try:
        while True:
            check_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Check #{check_count} at {timestamp}")
            
            results = check_dns_records(domain, verification_id)
            
            # Print simple status
            status = []
            if results["txt_record_exists"]:
                status.append("TXT: ✓")
                if results["txt_record_value_correct"]:
                    status.append("TXT Value: ✓")
                else:
                    status.append("TXT Value: ✗")
            else:
                status.append("TXT: ✗")
            
            if results["cname_record_exists"]:
                status.append("CNAME: ✓")
                if results["cname_record_value_correct"]:
                    status.append("CNAME Value: ✓")
                else:
                    status.append("CNAME Value: ✗")
            else:
                status.append("CNAME: ✗")
            
            print(" | ".join(status))
            print("")
            
            # Check if we're done
            if all(results.values()):
                print_success(f"DNS configuration is complete and correct for {domain}")
                print("You can now proceed with the Azure App Service custom domain setup.")
                break
            
            if check_count >= max_checks:
                print_warning(f"Reached maximum number of checks ({max_checks}). DNS propagation may still be in progress.")
                print("Continue monitoring manually or run this script again later.")
                break
            
            # Wait for the next check
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")

def main():
    parser = argparse.ArgumentParser(
        description="Check DNS configuration for Growth Accelerator Staffing Platform"
    )
    parser.add_argument(
        "--domain",
        default="app.growthaccelerator.nl",
        help="Domain name to check (default: app.growthaccelerator.nl)"
    )
    parser.add_argument(
        "--verification-id",
        help="Azure domain verification ID to check against TXT record"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Continuously monitor DNS propagation"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds for monitoring mode (default: 300)"
    )
    
    args = parser.parse_args()
    
    try:
        # Check if dnspython is installed
        import dns.resolver
    except ImportError:
        print_error("dnspython package not installed. Please install it with 'pip install dnspython'.")
        return 1
    
    print_header("DNS CONFIGURATION CHECK")
    
    if args.monitor:
        if not args.verification_id:
            print_error("Verification ID is required for monitoring mode.")
            return 1
        monitor_dns_propagation(args.domain, args.verification_id, args.interval)
    else:
        results = check_dns_records(args.domain, args.verification_id)
        print_results(args.domain, results)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())