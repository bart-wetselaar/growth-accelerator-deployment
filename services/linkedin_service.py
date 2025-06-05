"""
LinkedIn Service for Growth Accelerator Staffing Platform

This service provides functionality to interact with LinkedIn's API for:
- Retrieving candidate profiles
- Searching for potential candidates
- Importing candidates to Workable CRM
"""

import os
import json
import logging
import requests
from datetime import datetime
from urllib.parse import urlencode

# Import circuit breaker for LinkedIn API
try:
    from services.circuit_breaker_setup import linkedin_circuit
except ImportError:
    # For when the circuit breaker is not yet initialized
    linkedin_circuit = None

logger = logging.getLogger(__name__)

class LinkedInService:
    def __init__(self, client_id=None, client_secret=None, company_id=None):
        """
        Initialize LinkedIn service with API credentials
        
        Args:
            client_id (str, optional): LinkedIn API Client ID. If None, will use environment variable. Defaults to None.
            client_secret (str, optional): LinkedIn API Client Secret. If None, will use environment variable. Defaults to None.
            company_id (str, optional): LinkedIn Company ID. If None, will use environment variable. Defaults to None.
        """
        self.client_id = client_id or os.environ.get("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("LINKEDIN_CLIENT_SECRET")
        self.company_id = company_id or os.environ.get("LINKEDIN_COMPANY_ID")
        
        # Setup cache directory
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache", "linkedin")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Base URLs
        self.base_url = "https://api.linkedin.com/v2"
        self.auth_url = "https://www.linkedin.com/oauth/v2"
        
        logger.info(f"LinkedInService initialized for company ID {self.company_id}")
    
    def get_auth_url(self, redirect_uri, scope=None):
        """
        Get LinkedIn OAuth authorization URL
        
        Args:
            redirect_uri (str): Redirect URI for OAuth flow
            scope (list, optional): List of scopes to request. Defaults to None.
        
        Returns:
            str: LinkedIn authorization URL
        """
        if scope is None:
            scope = [
                "r_liteprofile", 
                "r_emailaddress", 
                "w_member_social",
                "r_organization_social"
            ]
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scope),
            "state": "random_state_string"  # Should be a random string for security
        }
        
        auth_url = f"{self.auth_url}/authorization?{urlencode(params)}"
        return auth_url
    
    def get_access_token(self, code, redirect_uri):
        """
        Exchange authorization code for access token
        
        Args:
            code (str): Authorization code from LinkedIn
            redirect_uri (str): Redirect URI used in authorization
        
        Returns:
            dict: Access token response with token and expiration
        """
        # Apply circuit breaker if available
        if linkedin_circuit is not None:
            return linkedin_circuit(self._get_access_token)(
                code, redirect_uri
            )
        return self._get_access_token(code, redirect_uri)
        
    def _get_access_token(self, code, redirect_uri):
        """
        Internal implementation of get_access_token, protected by circuit breaker
        """
        try:
            params = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = requests.post(f"{self.auth_url}/accessToken", data=params)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully obtained LinkedIn access token")
            
            # Cache token for later use
            with open(os.path.join(self.cache_dir, "access_token.json"), "w") as f:
                json.dump(token_data, f)
            
            return token_data
        except Exception as e:
            logger.error(f"Error getting LinkedIn access token: {str(e)}")
            return None
    
    def search_candidates(self, keywords, location=None, count=10, start=0, access_token=None, cached=True):
        """
        Search for candidates on LinkedIn
        
        Args:
            keywords (str): Search keywords
            location (str, optional): Location to search in. Defaults to None.
            count (int, optional): Number of results to return. Defaults to 10.
            start (int, optional): Start index for pagination. Defaults to 0.
            access_token (str, optional): LinkedIn access token. Defaults to None.
            cached (bool, optional): Whether to use cached results if available. Defaults to True.
        
        Returns:
            dict: Search results with candidates
        """
        # Apply circuit breaker if available
        if linkedin_circuit is not None:
            return linkedin_circuit(self._search_candidates)(
                keywords, location, count, start, access_token, cached
            )
        return self._search_candidates(keywords, location, count, start, access_token, cached)
        
    def _search_candidates(self, keywords, location=None, count=10, start=0, access_token=None, cached=True):
        """
        Internal implementation of search_candidates, protected by circuit breaker
        """
        cache_key = f"search_{keywords.replace(' ', '_')}_{location or 'all'}"
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Check cache if requested
        if cached and os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cache_data = json.load(f)
                    logger.debug(f"Using cached LinkedIn search results from {cache_path}")
                    return cache_data
            except Exception as e:
                logger.warning(f"Error reading LinkedIn search cache: {str(e)}")
        
        # For actual implementation, uncomment:
        # try:
        #     headers = {"Authorization": f"Bearer {access_token}"}
        #     params = {
        #         "keywords": keywords,
        #         "count": count,
        #         "start": start
        #     }
        #     
        #     if location:
        #         params["location"] = location
        #     
        #     response = requests.get(f"{self.base_url}/search/people", headers=headers, params=params)
        #     response.raise_for_status()
        #     data = response.json()
        #     
        #     # Cache the results
        #     with open(cache_path, "w") as f:
        #         json.dump(data, f)
        #     
        #     return data
        # except Exception as e:
        #     logger.error(f"Error searching LinkedIn candidates: {str(e)}")
        #     return {"people": []}
        
        # Placeholder data for development
        sample_data = {
            "people": [
                {
                    "id": "AbC123XyZ",
                    "firstName": "John",
                    "lastName": "Smith",
                    "headline": "Full Stack Developer with 5+ years of experience",
                    "location": {
                        "country": "Netherlands",
                        "city": "Amsterdam"
                    },
                    "industry": "Information Technology",
                    "profilePicture": {
                        "displayImage": "https://media.licdn.com/dms/image/sample1/profile.jpg"
                    }
                },
                {
                    "id": "DeF456UvW",
                    "firstName": "Emma",
                    "lastName": "Johnson",
                    "headline": "Senior Frontend Developer | React | Vue | Angular",
                    "location": {
                        "country": "Netherlands",
                        "city": "Rotterdam"
                    },
                    "industry": "Computer Software",
                    "profilePicture": {
                        "displayImage": "https://media.licdn.com/dms/image/sample2/profile.jpg"
                    }
                }
            ],
            "total": 2
        }
        
        # Cache the sample data
        with open(cache_path, "w") as f:
            json.dump(sample_data, f)
        
        return sample_data
    
    def get_profile(self, profile_id, access_token=None, cached=True):
        """
        Get a candidate profile from LinkedIn
        
        Args:
            profile_id (str): LinkedIn profile ID
            access_token (str, optional): LinkedIn access token. Defaults to None.
            cached (bool, optional): Whether to use cached results if available. Defaults to True.
        
        Returns:
            dict: Profile data
        """
        # Apply circuit breaker if available
        if linkedin_circuit is not None:
            return linkedin_circuit(self._get_profile)(
                profile_id, access_token, cached
            )
        return self._get_profile(profile_id, access_token, cached)
        
    def _get_profile(self, profile_id, access_token=None, cached=True):
        """
        Internal implementation of get_profile, protected by circuit breaker
        """
        cache_key = f"profile_{profile_id}"
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Check cache if requested
        if cached and os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cache_data = json.load(f)
                    logger.debug(f"Using cached LinkedIn profile from {cache_path}")
                    return cache_data
            except Exception as e:
                logger.warning(f"Error reading LinkedIn profile cache: {str(e)}")
        
        # For actual implementation, uncomment:
        # try:
        #     headers = {"Authorization": f"Bearer {access_token}"}
        #     response = requests.get(f"{self.base_url}/people/{profile_id}", headers=headers)
        #     response.raise_for_status()
        #     data = response.json()
        #     
        #     # Cache the results
        #     with open(cache_path, "w") as f:
        #         json.dump(data, f)
        #     
        #     return data
        # except Exception as e:
        #     logger.error(f"Error getting LinkedIn profile: {str(e)}")
        #     return {}
        
        # Placeholder data for development
        if profile_id == "AbC123XyZ":
            profile_data = {
                "id": "AbC123XyZ",
                "firstName": "John",
                "lastName": "Smith",
                "email": "john.smith@example.com",
                "vanityName": "johnsmith",
                "headline": "Full Stack Developer with 5+ years of experience",
                "summary": "Experienced developer with a focus on JavaScript frameworks and cloud solutions.",
                "location": {
                    "country": "Netherlands",
                    "city": "Amsterdam"
                },
                "industry": "Information Technology",
                "positions": [
                    {
                        "title": "Senior Developer",
                        "company": "Tech Solutions BV",
                        "startDate": {
                            "year": 2020,
                            "month": 3
                        },
                        "endDate": None,
                        "isCurrent": True
                    },
                    {
                        "title": "Frontend Developer",
                        "company": "Digital Innovation",
                        "startDate": {
                            "year": 2018,
                            "month": 6
                        },
                        "endDate": {
                            "year": 2020,
                            "month": 2
                        },
                        "isCurrent": False
                    }
                ],
                "skills": ["JavaScript", "React", "Node.js", "TypeScript", "AWS", "Docker"],
                "educations": [
                    {
                        "schoolName": "University of Amsterdam",
                        "fieldOfStudy": "Computer Science",
                        "degree": "Bachelor's",
                        "startDate": {
                            "year": 2014
                        },
                        "endDate": {
                            "year": 2018
                        }
                    }
                ]
            }
        else:
            profile_data = {
                "id": "DeF456UvW",
                "firstName": "Emma",
                "lastName": "Johnson",
                "email": "emma.johnson@example.com",
                "vanityName": "emmajohnson",
                "headline": "Senior Frontend Developer | React | Vue | Angular",
                "summary": "Creative developer specializing in user interfaces and experiences.",
                "location": {
                    "country": "Netherlands",
                    "city": "Rotterdam"
                },
                "industry": "Computer Software",
                "positions": [
                    {
                        "title": "Lead Frontend Developer",
                        "company": "WebApp Studios",
                        "startDate": {
                            "year": 2019,
                            "month": 5
                        },
                        "endDate": None,
                        "isCurrent": True
                    },
                    {
                        "title": "UI Developer",
                        "company": "Creative Software",
                        "startDate": {
                            "year": 2017,
                            "month": 3
                        },
                        "endDate": {
                            "year": 2019,
                            "month": 4
                        },
                        "isCurrent": False
                    }
                ],
                "skills": ["React", "Vue.js", "CSS/SASS", "UI/UX Design", "JavaScript", "TypeScript"],
                "educations": [
                    {
                        "schoolName": "Erasmus University Rotterdam",
                        "fieldOfStudy": "Digital Media Design",
                        "degree": "Master's",
                        "startDate": {
                            "year": 2015
                        },
                        "endDate": {
                            "year": 2017
                        }
                    }
                ]
            }
        
        # Cache the profile data
        with open(cache_path, "w") as f:
            json.dump(profile_data, f)
        
        return profile_data
    
    def import_to_workable(self, profile_id, workable_service=None):
        """
        Import LinkedIn profile to Workable CRM
        
        Args:
            profile_id (str): LinkedIn profile ID
            workable_service: WorkableService instance
        
        Returns:
            dict: Result of the import operation with workable_id if successful
        """
        # Apply circuit breaker if available
        if linkedin_circuit is not None:
            return linkedin_circuit(self._import_to_workable)(
                profile_id, workable_service
            )
        return self._import_to_workable(profile_id, workable_service)
        
    def _import_to_workable(self, profile_id, workable_service=None):
        """
        Internal implementation of import_to_workable, protected by circuit breaker
        """
        try:
            if workable_service is None:
                from services.workable_service import WorkableService
                workable_service = WorkableService()
            
            # Get profile data
            profile_data = self.get_profile(profile_id)
            
            if not profile_data:
                logger.error(f"Could not retrieve LinkedIn profile {profile_id}")
                return {"success": False, "error": "Profile not found"}
            
            # Format data for Workable
            candidate_data = {
                "firstname": profile_data.get("firstName", ""),
                "lastname": profile_data.get("lastName", ""),
                "email": profile_data.get("email", ""),
                "headline": profile_data.get("headline", ""),
                "summary": profile_data.get("summary", ""),
                "address": f"{profile_data.get('location', {}).get('city', '')}, {profile_data.get('location', {}).get('country', '')}",
                "phone": "",  # LinkedIn API doesn't provide phone numbers
                "education_entries": [],
                "experience_entries": [],
                "skills": [],
                "social_profiles": [
                    {
                        "type": "linkedin",
                        "url": f"https://www.linkedin.com/in/{profile_data.get('vanityName', profile_id)}"
                    }
                ],
                "tags": []
            }
            
            # Add skills
            if "skills" in profile_data:
                candidate_data["skills"] = profile_data["skills"]
                candidate_data["tags"] = profile_data["skills"]
            
            # Add education entries
            if "educations" in profile_data:
                for edu in profile_data["educations"]:
                    education_entry = {
                        "school": edu.get("schoolName", ""),
                        "degree": edu.get("degree", ""),
                        "field_of_study": edu.get("fieldOfStudy", ""),
                        "start_date": f"{edu.get('startDate', {}).get('year', '')}-01-01" if "startDate" in edu and "year" in edu["startDate"] else "",
                        "end_date": f"{edu.get('endDate', {}).get('year', '')}-01-01" if "endDate" in edu and "year" in edu["endDate"] else ""
                    }
                    candidate_data["education_entries"].append(education_entry)
            
            # Add experience entries
            if "positions" in profile_data:
                for pos in profile_data["positions"]:
                    start_month = pos.get("startDate", {}).get("month", 1)
                    start_year = pos.get("startDate", {}).get("year", "")
                    
                    if pos.get("isCurrent", False):
                        end_date = ""
                    else:
                        end_month = pos.get("endDate", {}).get("month", 1)
                        end_year = pos.get("endDate", {}).get("year", "")
                        end_date = f"{end_year}-{end_month:02d}-01" if end_year else ""
                    
                    experience_entry = {
                        "title": pos.get("title", ""),
                        "company": pos.get("company", ""),
                        "industry": profile_data.get("industry", ""),
                        "current": pos.get("isCurrent", False),
                        "start_date": f"{start_year}-{start_month:02d}-01" if start_year else "",
                        "end_date": end_date
                    }
                    candidate_data["experience_entries"].append(experience_entry)
            
            # Call Workable to create the candidate
            result = workable_service.create_candidate(candidate_data)
            
            if "id" in result:
                logger.info(f"Successfully imported LinkedIn profile {profile_id} to Workable with ID {result['id']}")
                return {"success": True, "workable_id": result["id"]}
            else:
                logger.error(f"Failed to import LinkedIn profile to Workable: {result}")
                return {"success": False, "error": result.get("error", "Unknown error")}
            
        except Exception as e:
            logger.error(f"Error importing LinkedIn profile to Workable: {str(e)}")
            return {"success": False, "error": str(e)}