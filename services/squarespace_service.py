import os
import logging
import requests
from datetime import datetime
from flask import current_app
from api.squarespace import SquarespaceAPI
from services.base_service import BaseService

# Import circuit breaker for Squarespace API
try:
    from services.circuit_breaker_setup import squarespace_circuit
except ImportError:
    # For when the circuit breaker is not yet initialized
    squarespace_circuit = None

logger = logging.getLogger(__name__)

class SquarespaceService(BaseService):
    """Service for interacting with Squarespace API"""
    
    def __init__(self, app=None):
        """Initialize the Squarespace service"""
        super().__init__(app)
        self.api = SquarespaceAPI()
        logger.info("SquarespaceService initialized")
        
    def get_website_info(self):
        """Get information about the Squarespace website"""
        return self.api.get_website_info()
        
    def get_collections(self):
        """Get all collections for the website"""
        return self.api.get_collections()
        
    def get_collection(self, collection_id):
        """Get details of a specific collection"""
        return self.api.get_collection(collection_id)
        
    def get_jobs(self, limit=20, offset=0, cached=True):
        """
        Get jobs from Squarespace
        
        Args:
            limit: Maximum number of jobs to return
            offset: Offset for pagination
            cached: Whether to use cached data (ignored for Squarespace)
            
        Returns:
            List of jobs
        """
        # Apply circuit breaker if available
        if squarespace_circuit is not None:
            return squarespace_circuit(self._get_jobs)(
                limit, offset, cached
            )
        return self._get_jobs(limit, offset, cached)
        
    def _get_jobs(self, limit=20, offset=0, cached=True):
        """
        Internal implementation of get_jobs, protected by circuit breaker
        """
        try:
            # Always fetch from Squarespace API
            response = self.api.list_jobs(limit=limit, offset=offset)
            
            if "error" in response:
                logger.error(f"Error fetching jobs from Squarespace: {response['error']}")
                return {"jobs": []}
                
            # Transform to common format
            jobs = []
            for item in response.get("items", []):
                # Extract job data
                job = {
                    "id": item.get("id"),
                    "title": item.get("title", "Untitled Job"),
                    "squarespace_id": item.get("id"),
                    "description": self._extract_html_content(item),
                    "created_at": item.get("addedOn"),
                    "updated_at": item.get("updatedOn"),
                    "source": "squarespace"
                }
                
                # Get custom fields
                if "customContent" in item:
                    custom = item["customContent"]
                    job["location"] = custom.get("location", "")
                    job["job_type"] = custom.get("jobType", "Full-time")
                    job["company"] = custom.get("company", "Growth Accelerator")
                    
                    # Try to parse salary range
                    salary = custom.get("salary", "")
                    if salary and "-" in salary:
                        try:
                            parts = salary.replace("€", "").split("-")
                            job["rate_min"] = int(parts[0].strip())
                            job["rate_max"] = int(parts[1].strip())
                        except (ValueError, IndexError):
                            job["rate_min"] = 0
                            job["rate_max"] = 0
                
                jobs.append(job)
            
            return {"jobs": jobs}
        except Exception as e:
            logger.error(f"Error in get_jobs: {str(e)}")
            return {"jobs": []}
    
    def get_job(self, job_id):
        """
        Get a job from Squarespace by ID
        
        Args:
            job_id: Squarespace job ID
            
        Returns:
            Job data or None if not found
        """
        # Apply circuit breaker if available
        if squarespace_circuit is not None:
            return squarespace_circuit(self._get_job)(job_id)
        return self._get_job(job_id)
        
    def _get_job(self, job_id):
        """
        Internal implementation of get_job, protected by circuit breaker
        """
        try:
            response = self.api.get_job(job_id)
            
            if "error" in response:
                logger.error(f"Error fetching job from Squarespace: {response['error']}")
                return None
                
            # Transform to common format
            job = {
                "id": response.get("id"),
                "title": response.get("title", "Untitled Job"),
                "squarespace_id": response.get("id"),
                "description": self._extract_html_content(response),
                "created_at": response.get("addedOn"),
                "updated_at": response.get("updatedOn"),
                "source": "squarespace"
            }
            
            # Get custom fields
            if "customContent" in response:
                custom = response["customContent"]
                job["location"] = custom.get("location", "")
                job["job_type"] = custom.get("jobType", "Full-time")
                job["company"] = custom.get("company", "Growth Accelerator")
                
                # Try to parse salary range
                salary = custom.get("salary", "")
                if salary and "-" in salary:
                    try:
                        parts = salary.replace("€", "").split("-")
                        job["rate_min"] = int(parts[0].strip())
                        job["rate_max"] = int(parts[1].strip())
                    except (ValueError, IndexError):
                        job["rate_min"] = 0
                        job["rate_max"] = 0
            
            return job
        except Exception as e:
            logger.error(f"Error in get_job: {str(e)}")
            return None
    
    def sync_job(self, job):
        """
        Sync a job to Squarespace
        
        Args:
            job: Job model or dictionary
            
        Returns:
            Result of the synchronization
        """
        # Apply circuit breaker if available
        if squarespace_circuit is not None:
            return squarespace_circuit(self._sync_job)(job)
        return self._sync_job(job)
        
    def _sync_job(self, job):
        """
        Internal implementation of sync_job, protected by circuit breaker
        """
        try:
            return self.api.sync_job(job)
        except Exception as e:
            logger.error(f"Error syncing job to Squarespace: {str(e)}")
            raise
    
    def sync_all_jobs(self, limit=None):
        """
        Sync all open jobs to Squarespace
        
        Args:
            limit: Optional limit on the number of jobs to sync
            
        Returns:
            Dictionary with sync statistics
        """
        # Apply circuit breaker if available
        if squarespace_circuit is not None:
            return squarespace_circuit(self._sync_all_jobs)(limit)
        return self._sync_all_jobs(limit)
        
    def _sync_all_jobs(self, limit=None):
        """
        Internal implementation of sync_all_jobs, protected by circuit breaker
        """
        try:
            return self.api.sync_all_jobs(limit=limit)
        except Exception as e:
            logger.error(f"Error syncing all jobs to Squarespace: {str(e)}")
            raise
    
    def create_placement(self, placement_data):
        """
        Create a placement in Squarespace
        
        Args:
            placement_data: Dictionary with placement data
            
        Returns:
            Created placement data
        """
        # Apply circuit breaker if available
        if squarespace_circuit is not None:
            return squarespace_circuit(self._create_placement)(placement_data)
        return self._create_placement(placement_data)
        
    def _create_placement(self, placement_data):
        """
        Internal implementation of create_placement, protected by circuit breaker
        """
        try:
            return self.api.create_placement(placement_data)
        except Exception as e:
            logger.error(f"Error creating placement in Squarespace: {str(e)}")
            raise
    
    def _extract_html_content(self, item):
        """Extract HTML content from a Squarespace item"""
        if "body" in item and "content" in item["body"]:
            return item["body"]["content"]
        return ""