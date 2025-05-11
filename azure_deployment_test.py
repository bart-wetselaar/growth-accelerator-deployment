#!/usr/bin/env python3
"""
Azure Deployment Test Script for Growth Accelerator Staffing Platform

Run this script after deploying to Azure to verify that key components are working properly.
"""

import argparse
import json
import sys
import time
from urllib.parse import urljoin

import requests

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
    print(f"\n{Colors.HEADER}{Colors.BOLD}==== {message} ===={Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def test_endpoint(base_url, endpoint, expected_status=200, description=""):
    """Test an endpoint and verify the expected status code"""
    url = urljoin(base_url, endpoint)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == expected_status:
            print_success(f"{url} - Status: {response.status_code} {description}")
            return True
        else:
            print_error(f"{url} - Expected status {expected_status}, got {response.status_code} {description}")
            return False
    except requests.RequestException as e:
        print_error(f"{url} - Request failed: {str(e)}")
        return False

def test_api_endpoint(base_url, endpoint, expected_status=200, description=""):
    """Test an API endpoint with JSON response"""
    url = urljoin(base_url, endpoint)
    try:
        response = requests.get(
            url,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == expected_status:
            try:
                json_response = response.json()
                print_success(f"{url} - Status: {response.status_code} - Valid JSON response {description}")
                return True
            except json.JSONDecodeError:
                print_error(f"{url} - Status: {response.status_code} - Invalid JSON response {description}")
                return False
        else:
            print_error(f"{url} - Expected status {expected_status}, got {response.status_code} {description}")
            return False
    except requests.RequestException as e:
        print_error(f"{url} - Request failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test Growth Accelerator Azure deployment")
    parser.add_argument("--url", required=True, help="Base URL for the deployed application (e.g., https://growth-accelerator-staffing.azurewebsites.net)")
    parser.add_argument("--admin-user", default="admin", help="Admin username for testing (default: admin)")
    parser.add_argument("--admin-password", default="password", help="Admin password for testing (default: password)")
    parser.add_argument("--wait", type=int, default=0, help="Wait time in seconds before starting tests (default: 0)")
    args = parser.parse_args()
    
    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url
    
    if args.wait > 0:
        print(f"Waiting {args.wait} seconds for the application to start...")
        time.sleep(args.wait)
    
    print_header("TESTING GROWTH ACCELERATOR STAFFING PLATFORM DEPLOYMENT")
    print(f"Testing deployment at: {args.url}")
    
    # Test basic pages (public facing)
    print_header("TESTING PUBLIC PAGES")
    public_pages_tests = [
        test_endpoint(args.url, "/", description="(Home page)"),
        test_endpoint(args.url, "/login", description="(Login page)"),
        test_endpoint(args.url, "/register", description="(Registration page)"),
        test_endpoint(args.url, "/api-info", description="(API info page)")
    ]
    
    public_pages_success = all(public_pages_tests)
    if public_pages_success:
        print_success("All public pages tests passed")
    else:
        print_error("Some public pages tests failed")
    
    # Test API endpoints
    print_header("TESTING API ENDPOINTS")
    api_tests = [
        test_api_endpoint(args.url, "/api/unified", expected_status=401, description="(Unified API - Unauthorized)"),
        test_api_endpoint(args.url, "/api/documentation", description="(API Documentation)")
    ]
    
    api_success = all(api_tests)
    if api_success:
        print_success("All API tests passed")
    else:
        print_warning("Some API tests failed - may require authentication")
    
    # Test health endpoint
    print_header("TESTING HEALTH ENDPOINT")
    health_tests = [
        test_endpoint(args.url, "/health", description="(Health check endpoint)")
    ]
    
    health_success = all(health_tests)
    if health_success:
        print_success("Health endpoint test passed")
    else:
        print_error("Health endpoint test failed")
    
    # Login test (advanced)
    print_header("TESTING AUTHENTICATION (OPTIONAL)")
    print_warning("Authentication tests skipped - run manually if needed")
    
    # Summary
    print_header("TEST SUMMARY")
    
    if public_pages_success and health_success:
        print_success("Core deployment tests passed!")
        print("The Growth Accelerator Staffing Platform appears to be deployed correctly.")
        print("\nNext steps:")
        print("1. Login with an admin account to verify all functionality")
        print("2. Test all API endpoints with proper authentication")
        print("3. Verify integration with external services (Workable, LinkedIn, Squarespace)")
        print("4. Set up monitoring and alerts in Azure Portal")
        sys.exit(0)
    else:
        print_error("Some deployment tests failed!")
        print("Please check the logs above for details on what failed.")
        print("\nTroubleshooting steps:")
        print("1. Check Azure App Service logs in the Azure Portal")
        print("2. Verify application settings and environment variables")
        print("3. Check that the database is properly configured")
        print("4. Verify that all required external services are accessible")
        sys.exit(1)

if __name__ == "__main__":
    main()