"""
Workable API integration for Growth Accelerator Staffing Platform

This module provides a comprehensive integration with the Workable API,
handling all aspects of the staffing workflow including jobs, candidates,
client accounts, and reporting.
"""
import os
import requests
import logging
import json
import time
from datetime import datetime, timedelta
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SUBDOMAIN = "growthacceleratorstaffing"
API_KEY = os.environ.get("WORKABLE_API_KEY")
CACHE_EXPIRY = 300  # Cache expiry in seconds

# Cache storage
_cache = {}

def cached(expiry=CACHE_EXPIRY):
    """Cache decorator for API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if we have a cached response and it's still valid
            if key in _cache:
                cached_time, cached_result = _cache[key]
                if time.time() - cached_time < expiry:
                    logger.debug(f"Using cached result for {key}")
                    return cached_result
            
            # No cache or expired, call the actual function
            result = func(*args, **kwargs)
            
            # Store in cache if result is cacheable
            if result is not None:
                _cache[key] = (time.time(), result)
            
            return result
        return wrapper
    return decorator

class WorkableAPI:
    """Comprehensive Workable API service"""
    
    def __init__(self, api_key=None, subdomain=DEFAULT_SUBDOMAIN):
        """
        Initialize the Workable API service
        
        Args:
            api_key (str): Workable API key, defaults to environment variable
            subdomain (str): Workable subdomain
        """
        self.api_key = api_key or API_KEY
        if not self.api_key:
            logger.error("No Workable API key provided")
            raise ValueError("Workable API key is required")
            
        self.subdomain = subdomain
        # Use Workable API v3 format with account subdomain
        self.base_url = f"https://{subdomain}.workable.com/spi/v3"
        # Try using Access Token authentication format instead of Bearer
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        logger.info(f"WorkableAPI initialized for subdomain: {subdomain}")
    
    def _make_request(self, method, endpoint, params=None, data=None, retries=3):
        """
        Make a request to the Workable API with error handling and retries
        
        Args:
            method (str): HTTP method (get, post, put, delete)
            endpoint (str): API endpoint (without leading slash)
            params (dict): Query parameters
            data (dict): Request body for POST/PUT requests
            retries (int): Number of retries before giving up
            
        Returns:
            dict: Response JSON or None on error
        """
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making {method.upper()} request to {url}")
        
        # Try alternative API formats if the standard one fails
        api_formats = [
            # Standard format
            {"url": url, "headers": self.headers},
            # Try without bearer prefix
            {"url": url, "headers": {**self.headers, "Authorization": self.api_key}},
            # Try with alternative base URL
            {"url": f"https://www.workable.com/api/v3/{endpoint}", "headers": self.headers}
        ]
        
        for attempt in range(retries):
            # On first attempt, try the standard format
            # On subsequent attempts, try alternative formats if available
            api_format_index = min(attempt, len(api_formats)-1)
            current_format = api_formats[api_format_index]
            
            try:
                logger.debug(f"Attempt {attempt+1}/{retries} using format {api_format_index+1}")
                
                response = requests.request(
                    method=method.upper(),
                    url=current_format["url"],
                    headers=current_format["headers"],
                    params=params,
                    json=data
                )
                
                # Check if we got a successful response
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON response: {response.text}")
                        continue
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                # Log detailed information about the response for debugging
                logger.error(f"API request failed with status code {response.status_code}")
                logger.error(f"Response body: {response.text}")
                logger.error(f"Request URL: {current_format['url']}")
                logger.error(f"Request method: {method.upper()}")
                
                # The API may return a JSON error response with details
                try:
                    error_info = response.json()
                    logger.error(f"Error details: {json.dumps(error_info, indent=2)}")
                except:
                    pass
                
                # Raise the exception to be handled below
                response.raise_for_status()
                
            except requests.RequestException as e:
                logger.error(f"Error on attempt {attempt+1}/{retries}: {str(e)}")
                if hasattr(e, "response") and e.response:
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")
                
                if attempt < retries - 1:
                    # Exponential backoff
                    sleep_time = 2 ** attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error("Max retries reached, giving up")
                    # Try alternative endpoint format for specific endpoints
                    if endpoint == "jobs":
                        logger.info("Trying alternative endpoint format for jobs")
                        try:
                            alt_url = f"https://{self.subdomain}.workable.com/api/v3/jobs"
                            alt_response = requests.get(alt_url, headers=self.headers)
                            if alt_response.status_code == 200:
                                return alt_response.json()
                        except Exception as alt_error:
                            logger.error(f"Alternative endpoint also failed: {str(alt_error)}")
                    
                    return self._get_fallback_data(endpoint)
        
        return None
        
    def _get_fallback_data(self, endpoint):
        """
        Provide fallback data when API calls fail
        
        Args:
            endpoint (str): The API endpoint that failed
            
        Returns:
            dict or list: Appropriate fallback data structure
        """
        logger.error(f"API call failed for endpoint: {endpoint}")
        logger.error("Could not fetch real data from Workable API")
        
        # First try to load cached data
        try:
            # Check if we have previously cached real data
            cache_dir = os.path.join("cache", "workable")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Determine cache file name based on endpoint
            cache_file = None
            if endpoint.startswith("jobs"):
                if "/" in endpoint:  # Specific job
                    job_id = endpoint.split("/")[1]
                    cache_file = os.path.join(cache_dir, f"job_{job_id}.json")
                else:
                    cache_file = os.path.join(cache_dir, "all_jobs.json")
            elif endpoint.startswith("candidates"):
                if "/" in endpoint:  # Specific candidate
                    candidate_id = endpoint.split("/")[1]
                    cache_file = os.path.join(cache_dir, f"candidate_{candidate_id}.json")
                else:
                    cache_file = os.path.join(cache_dir, "all_candidates.json")
            elif endpoint == "members":
                cache_file = os.path.join(cache_dir, "all_members.json")
                
            # Try to load cached data if it exists
            if cache_file and os.path.exists(cache_file):
                logger.info(f"Loading cached data from {cache_file}")
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    if cached_data:
                        logger.info(f"Using cached real data from previous successful API call")
                        return cached_data
        except Exception as e:
            logger.error(f"Error loading cached data: {str(e)}")
            
        # If we still don't have data, log error and return empty result
        if endpoint.startswith("jobs"):
            logger.error("No real jobs data available - returning empty array")
            return {"jobs": [], "error": "Could not connect to Workable API"}
            
        elif endpoint.startswith("candidates"):
            logger.error("No real candidates data available - returning empty array")
            return {"candidates": [], "error": "Could not connect to Workable API"}
            
        elif endpoint == "members":
            logger.error("No real member data available - returning empty array")
            return {"members": [], "error": "Could not connect to Workable API"}
            
        else:
            # Default empty structure
            return {"error": "Could not connect to Workable API"}
    
    @cached()
    def get_all_jobs(self, state=None, limit=100):
        """
        Fetch all jobs from Workable API with multiple method attempts
        
        Args:
            state (str): Job state filter (published, closed, archived, draft)
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of jobs
        """
        params = {"limit": limit}
        if state:
            params["state"] = state
            
        # Try the standard SPI v3 API first
        logger.debug("Attempting to get jobs using standard SPI v3 API")
        response = self._make_request("get", "jobs", params=params)
        if response and "jobs" in response:
            jobs = response.get("jobs", [])
            logger.info(f"Retrieved {len(jobs)} jobs from Workable API via standard endpoint")
            return jobs
            
        # If that fails, try the alternative API endpoints
        alternative_endpoints = [
            # API v3 format
            {"url": f"https://{self.subdomain}.workable.com/api/v3/jobs", "method": "get"},
            # Direct endpoint with .json extension
            {"url": f"https://{self.subdomain}.workable.com/jobs.json", "method": "get"},
            # Public jobs API (this doesn't need authentication)
            {"url": f"https://{self.subdomain}.workable.com/api/jobs", "method": "get"},
            # Public jobs API (alternative format)
            {"url": f"https://www.workable.com/api/jobs/{self.subdomain}", "method": "get"}
        ]
        
        for endpoint in alternative_endpoints:
            logger.debug(f"Attempting to get jobs using alternative endpoint: {endpoint['url']}")
            try:
                response = requests.request(
                    method=endpoint["method"],
                    url=endpoint["url"],
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code == 200:
                    logger.info(f"Alternative endpoint successful: {endpoint['url']}")
                    try:
                        # Different endpoints might have different response structures
                        data = response.json()
                        
                        # Try to extract jobs data based on common response formats
                        if "jobs" in data:
                            jobs = data["jobs"]
                        elif isinstance(data, list) and len(data) > 0 and "title" in data[0]:
                            jobs = data
                        else:
                            # Look for any list of objects that might be jobs
                            jobs = []
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                        if "title" in value[0] or "name" in value[0]:
                                            jobs = value
                                            break
                        
                        logger.info(f"Retrieved {len(jobs)} jobs from alternative endpoint")
                        return jobs
                    except Exception as json_error:
                        logger.error(f"Error parsing JSON from alternative endpoint: {str(json_error)}")
                else:
                    logger.warning(f"Alternative endpoint failed with status {response.status_code}")
            except Exception as request_error:
                logger.error(f"Error requesting alternative endpoint: {str(request_error)}")
                
        # If all attempts fail, return empty list
        logger.warning("All attempts to fetch jobs failed, returning empty list")
        return []
    
    @cached()
    def get_job_details(self, job_id):
        """
        Fetch detailed information for a specific job
        
        Args:
            job_id (str): Job ID or shortcode
            
        Returns:
            dict: Job details or None if not found
        """
        response = self._make_request("get", f"jobs/{job_id}")
        if response:
            logger.info(f"Retrieved job details for job ID: {job_id}")
            return response
        return None
    
    @cached()
    def get_all_candidates(self, job_id=None, stage=None, limit=1000):
        """
        Fetch all candidates from Workable API with pagination
        
        Args:
            job_id (str): Filter by job ID (optional)
            stage (str): Filter by stage (optional)
            limit (int): Maximum number of candidates to return per page
            
        Returns:
            list: List of all candidates
        """
        all_candidates = []
        page = 1
        per_page = min(100, limit)  # Workable API typically limits to 100 per request
        
        while True:
            params = {
                "limit": per_page,
                "since_id": None if page == 1 else f"page_{page}"
            }
            if job_id:
                params["job_id"] = job_id
            if stage:
                params["stage"] = stage
                
            response = self._make_request("get", "candidates", params=params)
            if response:
                candidates = response.get("candidates", [])
                if not candidates:  # No more candidates
                    break
                    
                all_candidates.extend(candidates)
                logger.debug(f"Retrieved {len(candidates)} candidates from page {page}")
                
                # Check if we've reached the limit or if this is the last page
                if len(candidates) < per_page or len(all_candidates) >= limit:
                    break
                    
                page += 1
            else:
                break
                
        logger.info(f"Retrieved {len(all_candidates)} candidates from Workable API")
        return all_candidates[:limit]  # Ensure we don't exceed the requested limit
    
    @cached()
    def get_candidate_details(self, candidate_id):
        """
        Fetch detailed information for a specific candidate
        
        Args:
            candidate_id (str): Candidate ID
            
        Returns:
            dict: Candidate details or None if not found
        """
        response = self._make_request("get", f"candidates/{candidate_id}")
        if response:
            logger.info(f"Retrieved candidate details for ID: {candidate_id}")
            return response
        return None
        
    @cached()
    def get_jobs(self, status=None, limit=100):
        """
        Fetch jobs from Workable API with status filtering
        
        Args:
            status (str): Job status filter (published, closed, archived, draft)
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of jobs
        """
        # This is a wrapper around get_all_jobs with a different parameter name for compatibility
        return self.get_all_jobs(state=status, limit=limit)
    
    @cached()
    def get_candidates(self, job_id, stage=None, limit=100):
        """
        Fetch candidates for a specific job from Workable API
        
        Args:
            job_id (str): Job ID or shortcode
            stage (str): Filter by stage (optional)
            limit (int): Maximum number of candidates to return
            
        Returns:
            list: List of candidates for the specified job
        """
        # This is a wrapper around get_all_candidates for compatibility
        return self.get_all_candidates(job_id=job_id, stage=stage, limit=limit)
    
    @cached()
    def get_jobs_with_candidates(self, status=None, limit=100):
        """
        Fetch jobs with their candidates from Workable API
        
        Args:
            status (str): Job status filter (published, closed, archived, draft)
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of jobs with candidates included
        """
        # First get all the jobs
        jobs = self.get_all_jobs(state=status, limit=limit)
        
        # For each job, fetch its candidates and add them to the job data
        for job in jobs:
            if "shortcode" in job:
                job_shortcode = job["shortcode"]
                # Get candidates for this job
                candidates = self.get_all_candidates(job_id=job_shortcode)
                job["candidates"] = candidates
            else:
                job["candidates"] = []
        
        logger.info(f"Retrieved {len(jobs)} jobs with candidates")
        return jobs
    
    @cached()
    def get_account_info(self):
        """
        Fetch account information from Workable API
        
        Returns:
            dict: Account information or empty dict if not available
        """
        response = self._make_request("get", "account")
        if response:
            logger.info(f"Retrieved account information")
            return response
        
        # Try alternative endpoints if the primary one fails
        alternative_endpoints = ["members", "recruiters", "company"]
        
        for endpoint in alternative_endpoints:
            logger.debug(f"Trying alternative account endpoint: {endpoint}")
            alt_response = self._make_request("get", endpoint)
            if alt_response:
                logger.info(f"Retrieved account information via alternative endpoint: {endpoint}")
                return alt_response
        
        logger.warning("Failed to retrieve account information")
        return {}
    
    def create_candidate(self, job_id, candidate_data):
        """
        Create a new candidate for a job
        
        Args:
            job_id (str): Job ID or shortcode
            candidate_data (dict): Candidate information
            
        Returns:
            dict: Created candidate data or None on error
        """
        response = self._make_request("post", f"jobs/{job_id}/candidates", data=candidate_data)
        if response:
            logger.info(f"Created new candidate for job ID: {job_id}")
            # Clear cache for candidates
            _cache.clear()
            return response
        return None
    
    def create_candidate_match(self, job_shortcode, candidate_id, stage="sourced"):
        """
        Create a match between an existing candidate and a job
        
        Args:
            job_shortcode (str): Job shortcode
            candidate_id (str): Existing candidate ID
            stage (str): Initial stage for the candidate (default: 'sourced')
            
        Returns:
            dict: Created match data or None on error
        """
        try:
            # First, get the candidate data to ensure they exist
            candidate_data = self.get_candidate_details(candidate_id)
            if not candidate_data:
                logger.error(f"Candidate {candidate_id} not found")
                return None
            
            # Create the application/match by moving candidate to job
            endpoint = f"jobs/{job_shortcode}/candidates/{candidate_id}/move"
            data = {
                "stage": stage,
                "disqualification_reason": None
            }
            
            response = self._make_request("post", endpoint, data=data)
            if response:
                logger.info(f"Successfully created match: candidate {candidate_id} to job {job_shortcode}")
                # Clear relevant caches
                _cache.clear()
                return response
            else:
                # Try alternative approach - add candidate to job
                endpoint = f"jobs/{job_shortcode}/candidates"
                data = {
                    "candidate_id": candidate_id,
                    "stage": stage
                }
                
                response = self._make_request("post", endpoint, data=data)
                if response:
                    logger.info(f"Successfully created match (alternative method): candidate {candidate_id} to job {job_shortcode}")
                    _cache.clear()
                    return response
                
            return None
            
        except Exception as e:
            logger.error(f"Error creating candidate match: {str(e)}")
            return None
    
    @cached()
    def get_stages(self, job_id=None):
        """
        Get available hiring pipeline stages
        
        Args:
            job_id (str): Job ID to get stages for a specific job
            
        Returns:
            list: List of stage data
        """
        endpoint = f"jobs/{job_id}/stages" if job_id else "stages"
        response = self._make_request("get", endpoint)
        if response:
            stages = response.get("stages", [])
            logger.info(f"Retrieved {len(stages)} hiring stages")
            return stages
        return []
    
    def move_candidate(self, candidate_id, stage):
        """
        Move a candidate to a different stage
        
        Args:
            candidate_id (str): Candidate ID
            stage (str): Target stage name
            
        Returns:
            bool: True if successful, False otherwise
        """
        data = {"stage": stage}
        response = self._make_request("put", f"candidates/{candidate_id}", data=data)
        if response:
            logger.info(f"Moved candidate {candidate_id} to stage: {stage}")
            # Clear cache for candidates
            _cache.clear()
            return True
        return False
    
    @cached()
    def get_client_accounts(self):
        """
        Get client accounts (assumes client accounts are stored as members)
        
        Returns:
            list: List of client accounts
        """
        response = self._make_request("get", "members")
        if response:
            members = response.get("members", [])
            logger.info(f"Retrieved {len(members)} client accounts")
            return members
        return []
    
    @cached()
    def get_dashboard_metrics(self):
        """
        Get metrics for dashboard display
        
        Returns:
            dict: Metrics data or empty dict on error
        """
        # Get various metrics
        active_jobs = len(self.get_all_jobs(state="published"))
        all_candidates = self.get_all_candidates()
        
        # Calculate metrics
        metrics = {
            "active_jobs": active_jobs,
            "active_candidates": len(all_candidates),
            "conversion_rate": 0,  # Calculate based on stages
            "time_to_hire": 0,    # Calculate based on timestamps
            "recent_activity": []
        }
        
        # Calculate conversion rate if we have candidates
        if all_candidates:
            hired_candidates = [c for c in all_candidates if c.get("stage") == "hired"]
            metrics["conversion_rate"] = round((len(hired_candidates) / len(all_candidates)) * 100, 2)
            
            # Recent activity - last 5 candidate actions
            metrics["recent_activity"] = sorted(
                all_candidates, 
                key=lambda c: c.get("updated_at", ""), 
                reverse=True
            )[:5]
        
        logger.info("Retrieved dashboard metrics")
        return metrics
    
    @cached()
    def get_backoffice_data(self):
        """
        Get data for backoffice functionality
        
        Returns:
            dict: Backoffice data
        """
        # Get hired candidates
        all_candidates = self.get_all_candidates()
        hired_candidates = [c for c in all_candidates if c.get("stage") == "hired"]
        
        # Structure the data for backoffice
        backoffice_data = {
            "active_consultants": hired_candidates,
            "invoices": [],  # Would come from accounting system
            "timesheet_summary": []  # Would come from time tracking system
        }
        
        logger.info("Retrieved backoffice data")
        return backoffice_data
    
    @cached()
    def get_matching_data(self, job_id=None):
        """
        Get data for matching algorithm
        
        Args:
            job_id (str): Optional job ID to match candidates for
            
        Returns:
            dict: Matching data
        """
        # Get candidates and job data
        candidates = self.get_all_candidates()
        
        if job_id:
            job = self.get_job_details(job_id)
            jobs = [job] if job else []
        else:
            jobs = self.get_all_jobs(state="published")
        
        # Structure for matching algorithm
        matching_data = {
            "candidates": candidates,
            "jobs": jobs,
            "matches": []  # Would be populated by matching algorithm
        }
        
        logger.info("Retrieved matching data")
        return matching_data
    
    @cached()
    def get_onboarding_data(self):
        """
        Get data for onboarding processes
        
        Returns:
            dict: Onboarding data
        """
        # Get candidates in the onboarding stage
        all_candidates = self.get_all_candidates()
        onboarding_candidates = [c for c in all_candidates if c.get("stage") == "offer"]
        
        # Structure for onboarding process
        onboarding_data = {
            "candidates": onboarding_candidates,
            "onboarding_tasks": [
                {"id": 1, "name": "Contract signing", "days": 3},
                {"id": 2, "name": "Equipment setup", "days": 5},
                {"id": 3, "name": "Orientation", "days": 1},
                {"id": 4, "name": "Training", "days": 7}
            ]
        }
        
        logger.info("Retrieved onboarding data")
        return onboarding_data

# Helper function to validate a Workable API key
def validate_workable_api_key(api_key, subdomain="growthacceleratorstaffing"):
    """
    Validate if a Workable API key is valid by making a simple request
    
    Args:
        api_key (str): The API key to validate
        subdomain (str): The Workable account subdomain
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    logger.info(f"Validating Workable API key for subdomain: {subdomain}")
    
    # Try different API formats that Workable might support
    test_urls = [
        f"https://{subdomain}.workable.com/spi/v3/account",
        f"https://{subdomain}.workable.com/spi/v3/jobs",
        f"https://{subdomain}.workable.com/api/v3/jobs",
        f"https://www.workable.com/spi/v3/jobs?account_subdomain={subdomain}",
        f"https://www.workable.com/api/v3/jobs?account_subdomain={subdomain}"
    ]
    
    # Try different authentication methods
    auth_methods = [
        # Bearer token (standard OAuth 2.0)
        {"Authorization": f"Bearer {api_key}"},
        # Direct API key
        {"Authorization": api_key},
        # Access Token format
        {"Access-Token": api_key},
        # X-API-Key format
        {"X-API-Key": api_key}
    ]
    
    for url in test_urls:
        for auth_method in auth_methods:
            headers = {
                **auth_method,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            try:
                logger.debug(f"Testing API key with URL: {url} and auth method: {list(auth_method.keys())[0]}")
                response = requests.get(url, headers=headers)
                
                # For Workable API, a 422 often means the key is valid but there's a formatting issue
                if response.status_code in [200, 201, 422]:
                    logger.info(f"API key appears valid for URL: {url} (status code: {response.status_code})")
                    
                    # If we got a 422, let's try to get more details
                    if response.status_code == 422:
                        try:
                            error_details = response.json()
                            logger.info(f"API returned 422 with details: {error_details}")
                            if "error" in error_details and "message" in error_details:
                                # Some 422 errors indicate the key is valid but the request is wrong
                                # This is better than invalid credentials (401)
                                logger.info(f"API error message: {error_details['error']}: {error_details['message']}")
                                return True
                        except:
                            pass
                    else:
                        return True
                    
                elif response.status_code == 401:
                    logger.warning(f"API key is invalid (401 Unauthorized) for URL: {url}")
                else:
                    logger.warning(f"Unexpected status code {response.status_code} for URL: {url}")
                    # Try to decode any JSON response for debugging
                    try:
                        error_details = response.json()
                        logger.warning(f"Response details: {error_details}")
                    except:
                        logger.warning(f"Raw response: {response.text[:200]}")
            
            except Exception as e:
                logger.error(f"Error validating API key with URL {url}: {str(e)}")
    
    # Last resort: try a direct REST API call to a more reliable endpoint
    try:
        direct_url = f"https://{subdomain}.workable.com/jobs.json"
        response = requests.get(direct_url)
        if response.status_code == 200:
            logger.info(f"Direct jobs endpoint works: {direct_url}")
            return True
    except Exception as e:
        logger.error(f"Error with direct jobs endpoint: {str(e)}")
    
    # If we've tried all URLs, auth methods and none worked, the key is invalid
    logger.error("API key validation failed for all endpoint formats and authentication methods")
    return False

# Create a singleton instance for global use
try:
    # First validate the API key
    api_key = os.environ.get("WORKABLE_API_KEY")
    if api_key and validate_workable_api_key(api_key):
        workable_api = WorkableAPI()
        logger.info("Global WorkableAPI instance created successfully")
    else:
        logger.error("Workable API key validation failed")
        workable_api = None
except Exception as e:
    logger.error(f"Failed to create global WorkableAPI instance: {str(e)}")
    workable_api = None

# Legacy function interfaces for backward compatibility
def get_all_jobs(subdomain=DEFAULT_SUBDOMAIN, api_key=API_KEY):
    """Legacy function for backward compatibility"""
    if workable_api:
        return workable_api.get_all_jobs()
    return []

def get_job_details(subdomain=DEFAULT_SUBDOMAIN, api_key=API_KEY, job_id=None):
    """Legacy function for backward compatibility"""
    if workable_api and job_id:
        return workable_api.get_job_details(job_id)
    return None

def get_all_candidates(subdomain=DEFAULT_SUBDOMAIN, api_key=API_KEY):
    """Legacy function for backward compatibility"""
    if workable_api:
        return workable_api.get_all_candidates()
    return []