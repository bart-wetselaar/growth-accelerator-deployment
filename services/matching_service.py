"""
Advanced Matching Service for Growth Accelerator Staffing Platform

This service implements intelligent matching between jobs and consultants,
with configurable weights and multiple scoring dimensions.
"""
import logging
import math
from datetime import datetime, timedelta
from sqlalchemy import and_, func, text

from db import db
from db.models import (
    Consultant, Job, Skill, ConsultantSkill, JobSkill, 
    MatchScore, MatchingWeights, Application, ApplicationStatus
)

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        logger.info("MatchingService initialized")
        # Try to get global matching weights
        self.global_weights = MatchingWeights.query.filter_by(client_id=None).first()
        
        # If no global weights exist, create default
        if not self.global_weights:
            self.global_weights = MatchingWeights(
                skill_weight=0.5,
                experience_weight=0.2,
                rate_weight=0.2,
                location_weight=0.1
            )
            db.session.add(self.global_weights)
            db.session.commit()
    
    def find_matches_for_job(self, job_id, limit=20, min_score=50, recalculate=False):
        """
        Find the best consultant matches for a specific job
        
        Args:
            job_id (int): The job ID to find matches for
            limit (int): Maximum number of matches to return
            min_score (float): Minimum match score (0-100)
            recalculate (bool): Force recalculation of all match scores
            
        Returns:
            dict: Response with matching consultants
        """
        try:
            job = Job.query.get(job_id)
            if not job:
                return {'status': 'error', 'message': 'Job not found'}
            
            # Get client-specific weights if available, otherwise use global weights
            weights = MatchingWeights.query.filter_by(client_id=job.client_id).first() or self.global_weights
            
            # Check if we need to calculate matches
            stale_time = datetime.now(timezone.utc) - timedelta(hours=24)
            if recalculate or not MatchScore.query.filter_by(job_id=job_id).first() or \
               MatchScore.query.filter(and_(
                   MatchScore.job_id == job_id,
                   MatchScore.last_calculated < stale_time
               )).first():
                self._calculate_matches_for_job(job, weights)
            
            # Get consultants who already applied
            existing_applications = db.session.query(Application.consultant_id).filter_by(job_id=job_id).all()
            existing_applicants = [app[0] for app in existing_applications]
            
            # Query match scores
            query = MatchScore.query.filter_by(job_id=job_id).filter(MatchScore.total_score >= min_score)
            
            # Exclude consultants who already applied
            if existing_applicants:
                query = query.filter(~MatchScore.consultant_id.in_(existing_applicants))
            
            # Order by score descending
            match_scores = query.order_by(MatchScore.total_score.desc()).limit(limit).all()
            
            # Format response
            matches = []
            for score in match_scores:
                consultant = Consultant.query.get(score.consultant_id)
                if not consultant:
                    continue
                
                # Get consultant skills
                skills = []
                for cs in consultant.skills:
                    skill = Skill.query.get(cs.skill_id)
                    if skill:
                        skills.append({
                            'name': skill.name,
                            'level': cs.level,
                            'years': cs.years_experience
                        })
                
                matches.append({
                    'consultant_id': consultant.id,
                    'name': f"{consultant.first_name} {consultant.last_name}",
                    'email': consultant.email,
                    'phone': consultant.phone,
                    'hourly_rate': consultant.hourly_rate,
                    'skills': skills,
                    'linkedin_profile': consultant.linkedin_profile,
                    'match_score': {
                        'total': score.total_score,
                        'skill': score.skill_score,
                        'experience': score.experience_score,
                        'rate': score.rate_score,
                        'location': score.location_score
                    }
                })
            
            return {
                'status': 'success',
                'job': {
                    'id': job.id,
                    'title': job.title,
                    'client': job.client.name if job.client else 'Unknown Client',
                    'location': job.location
                },
                'matches': matches,
                'weights_used': {
                    'skill': weights.skill_weight,
                    'experience': weights.experience_weight,
                    'rate': weights.rate_weight,
                    'location': weights.location_weight
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding matches for job: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to find matches: {str(e)}"
            }
    
    def find_jobs_for_consultant(self, consultant_id, limit=10, min_score=50, recalculate=False):
        """
        Find the best job matches for a specific consultant
        
        Args:
            consultant_id (int): The consultant ID to find matches for
            limit (int): Maximum number of matches to return
            min_score (float): Minimum match score (0-100)
            recalculate (bool): Force recalculation of all match scores
            
        Returns:
            dict: Response with matching jobs
        """
        try:
            consultant = Consultant.query.get(consultant_id)
            if not consultant:
                return {'status': 'error', 'message': 'Consultant not found'}
            
            # Check if we need to calculate matches
            stale_time = datetime.now(timezone.utc) - timedelta(hours=24)
            if recalculate or MatchScore.query.filter(and_(
                MatchScore.consultant_id == consultant_id,
                MatchScore.last_calculated < stale_time
            )).first():
                self._calculate_matches_for_consultant(consultant)
            
            # Get jobs that consultant already applied to
            existing_applications = db.session.query(Application.job_id).filter_by(consultant_id=consultant_id).all()
            existing_applications = [app[0] for app in existing_applications]
            
            # Query match scores
            query = MatchScore.query.filter_by(consultant_id=consultant_id).filter(MatchScore.total_score >= min_score)
            
            # Exclude jobs the consultant already applied to
            if existing_applications:
                query = query.filter(~MatchScore.job_id.in_(existing_applications))
            
            # Only include open jobs
            open_jobs = db.session.query(Job.id).filter_by(status='open').all()
            open_job_ids = [j[0] for j in open_jobs]
            if open_job_ids:
                query = query.filter(MatchScore.job_id.in_(open_job_ids))
            
            # Order by score descending
            match_scores = query.order_by(MatchScore.total_score.desc()).limit(limit).all()
            
            # Format response
            matches = []
            for score in match_scores:
                job = Job.query.get(score.job_id)
                if not job:
                    continue
                
                # Get required skills
                skills = []
                for js in job.required_skills:
                    skill = Skill.query.get(js.skill_id)
                    if skill:
                        skills.append({
                            'name': skill.name,
                            'required': js.is_required,
                            'importance': js.importance
                        })
                
                matches.append({
                    'job_id': job.id,
                    'title': job.title,
                    'client': job.client.name if job.client else 'Unknown Client',
                    'location': job.location,
                    'rate_range': f"${job.rate_min:.0f} - ${job.rate_max:.0f}",
                    'job_type': job.job_type,
                    'required_skills': skills,
                    'match_score': {
                        'total': score.total_score,
                        'skill': score.skill_score,
                        'experience': score.experience_score,
                        'rate': score.rate_score,
                        'location': score.location_score
                    }
                })
            
            return {
                'status': 'success',
                'consultant': {
                    'id': consultant.id,
                    'name': f"{consultant.first_name} {consultant.last_name}",
                    'hourly_rate': consultant.hourly_rate
                },
                'matches': matches
            }
            
        except Exception as e:
            logger.error(f"Error finding jobs for consultant: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to find job matches: {str(e)}"
            }
    
    def recalculate_all_matches(self):
        """
        Recalculate all match scores in the system
        
        Returns:
            dict: Status and count of calculated matches
        """
        try:
            # Get all open jobs
            open_jobs = Job.query.filter_by(status='open').all()
            
            # Get all active consultants
            active_consultants = Consultant.query.filter_by(status='active').all()
            
            # Track statistics
            total_matches = 0
            total_jobs = len(open_jobs)
            total_consultants = len(active_consultants)
            
            # Process each job
            for job in open_jobs:
                # Get client-specific weights if available
                weights = MatchingWeights.query.filter_by(client_id=job.client_id).first() or self.global_weights
                job_matches = self._calculate_matches_for_job(job, weights)
                total_matches += job_matches
            
            return {
                'status': 'success',
                'message': f"Recalculated all matches: {total_matches} match scores for {total_jobs} jobs and {total_consultants} consultants"
            }
            
        except Exception as e:
            logger.error(f"Error recalculating all matches: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to recalculate matches: {str(e)}"
            }
    
    def update_matching_weights(self, weights_data, client_id=None):
        """
        Update matching algorithm weights
        
        Args:
            weights_data (dict): Dictionary with weight values
            client_id (int, optional): Client ID for client-specific weights
            
        Returns:
            dict: Status and updated weights
        """
        try:
            # Get existing weights or create new
            if client_id:
                weights = MatchingWeights.query.filter_by(client_id=client_id).first()
                if not weights:
                    weights = MatchingWeights(client_id=client_id)
            else:
                weights = self.global_weights
            
            # Update weights
            if 'skill_weight' in weights_data:
                weights.skill_weight = float(weights_data['skill_weight'])
            
            if 'experience_weight' in weights_data:
                weights.experience_weight = float(weights_data['experience_weight'])
            
            if 'rate_weight' in weights_data:
                weights.rate_weight = float(weights_data['rate_weight'])
            
            if 'location_weight' in weights_data:
                weights.location_weight = float(weights_data['location_weight'])
            
            # Normalize weights to sum to 1.0
            total = weights.skill_weight + weights.experience_weight + weights.rate_weight + weights.location_weight
            if total > 0:
                weights.skill_weight /= total
                weights.experience_weight /= total
                weights.rate_weight /= total
                weights.location_weight /= total
            
            # Save changes
            if not weights.id:
                db.session.add(weights)
            db.session.commit()
            
            # If this is the global weights, update the service instance
            if not client_id:
                self.global_weights = weights
            
            return {
                'status': 'success',
                'message': f"Updated matching weights for {'client ' + str(client_id) if client_id else 'global default'}",
                'weights': {
                    'skill': weights.skill_weight,
                    'experience': weights.experience_weight,
                    'rate': weights.rate_weight,
                    'location': weights.location_weight
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating matching weights: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to update weights: {str(e)}"
            }
    
    def get_matching_statistics(self):
        """
        Get statistics about the matching system
        
        Returns:
            dict: Statistics about matches
        """
        try:
            # Count total matches
            total_matches = MatchScore.query.count()
            
            # Count recent matches (last 24 hours)
            day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            recent_matches = MatchScore.query.filter(MatchScore.last_calculated >= day_ago).count()
            
            # Get average score
            avg_score = db.session.query(func.avg(MatchScore.total_score)).scalar() or 0
            
            # Count high scores (>75)
            high_scores = MatchScore.query.filter(MatchScore.total_score > 75).count()
            
            # Count low scores (<50)
            low_scores = MatchScore.query.filter(MatchScore.total_score < 50).count()
            
            # Top matches by job
            top_job_matches = db.session.query(
                MatchScore.job_id,
                func.count(MatchScore.id).label('match_count')
            ).filter(MatchScore.total_score > 75).group_by(MatchScore.job_id).order_by(
                text('match_count DESC')
            ).limit(5).all()
            
            top_jobs = []
            for job_id, count in top_job_matches:
                job = Job.query.get(job_id)
                if job:
                    top_jobs.append({
                        'id': job.id,
                        'title': job.title,
                        'high_score_matches': count
                    })
            
            return {
                'status': 'success',
                'statistics': {
                    'total_matches': total_matches,
                    'recent_matches': recent_matches,
                    'average_score': round(avg_score, 1),
                    'high_score_matches': high_scores,
                    'low_score_matches': low_scores,
                    'top_matching_jobs': top_jobs
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting matching statistics: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to retrieve statistics: {str(e)}"
            }
    
    def _calculate_matches_for_job(self, job, weights):
        """
        Calculate match scores between a job and all consultants
        
        Args:
            job: Job object
            weights: MatchingWeights object with scoring weights
            
        Returns:
            int: Number of matches calculated
        """
        try:
            # Get active consultants
            consultants = Consultant.query.filter_by(status='active').all()
            
            # Get job required skills
            job_skills = {}
            total_importance = 0
            for js in job.required_skills:
                job_skills[js.skill_id] = {
                    'required': js.is_required,
                    'importance': js.importance or 3  # Default to medium importance (1-5)
                }
                total_importance += js.importance or 3
            
            # Lookup table for fast location matching
            job_location_lower = job.location.lower() if job.location else ""
            
            match_count = 0
            for consultant in consultants:
                # Calculate skill match score
                skill_score = self._calculate_skill_match(consultant, job_skills, total_importance)
                
                # Calculate experience match score
                experience_score = self._calculate_experience_match(consultant, job)
                
                # Calculate rate match score
                rate_score = self._calculate_rate_match(consultant, job)
                
                # Calculate location match score
                location_score = self._calculate_location_match(consultant, job_location_lower)
                
                # Calculate total score using weights
                total_score = (
                    skill_score * weights.skill_weight +
                    experience_score * weights.experience_weight +
                    rate_score * weights.rate_weight +
                    location_score * weights.location_weight
                ) * 100  # Scale to 0-100
                
                # Update or create match score record
                match = MatchScore.query.filter_by(
                    consultant_id=consultant.id,
                    job_id=job.id
                ).first()
                
                if match:
                    match.total_score = total_score
                    match.skill_score = skill_score * 100
                    match.experience_score = experience_score * 100
                    match.rate_score = rate_score * 100
                    match.location_score = location_score * 100
                    match.last_calculated = datetime.now(timezone.utc)
                else:
                    match = MatchScore(
                        consultant_id=consultant.id,
                        job_id=job.id,
                        total_score=total_score,
                        skill_score=skill_score * 100,
                        experience_score=experience_score * 100,
                        rate_score=rate_score * 100,
                        location_score=location_score * 100
                    )
                    db.session.add(match)
                
                match_count += 1
            
            db.session.commit()
            return match_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error calculating matches for job {job.id}: {str(e)}")
            return 0
    
    def _calculate_matches_for_consultant(self, consultant):
        """
        Calculate match scores between a consultant and all open jobs
        
        Args:
            consultant: Consultant object
            
        Returns:
            int: Number of matches calculated
        """
        try:
            # Get open jobs
            open_jobs = Job.query.filter_by(status='open').all()
            
            # Get consultant skills
            consultant_skills = {}
            for cs in consultant.skills:
                consultant_skills[cs.skill_id] = {
                    'level': cs.level or 3,  # Default to medium level (1-5)
                    'years': cs.years_experience or 1  # Default to 1 year
                }
            
            match_count = 0
            for job in open_jobs:
                # Get client-specific weights if available
                weights = MatchingWeights.query.filter_by(client_id=job.client_id).first() or self.global_weights
                
                # Get job required skills
                job_skills = {}
                total_importance = 0
                for js in job.required_skills:
                    job_skills[js.skill_id] = {
                        'required': js.is_required,
                        'importance': js.importance or 3  # Default to medium importance (1-5)
                    }
                    total_importance += js.importance or 3
                
                # Calculate skill match score
                skill_score = self._calculate_skill_match(consultant, job_skills, total_importance)
                
                # Calculate experience match score
                experience_score = self._calculate_experience_match(consultant, job)
                
                # Calculate rate match score
                rate_score = self._calculate_rate_match(consultant, job)
                
                # Calculate location match score
                job_location_lower = job.location.lower() if job.location else ""
                location_score = self._calculate_location_match(consultant, job_location_lower)
                
                # Calculate total score using weights
                total_score = (
                    skill_score * weights.skill_weight +
                    experience_score * weights.experience_weight +
                    rate_score * weights.rate_weight +
                    location_score * weights.location_weight
                ) * 100  # Scale to 0-100
                
                # Update or create match score record
                match = MatchScore.query.filter_by(
                    consultant_id=consultant.id,
                    job_id=job.id
                ).first()
                
                if match:
                    match.total_score = total_score
                    match.skill_score = skill_score * 100
                    match.experience_score = experience_score * 100
                    match.rate_score = rate_score * 100
                    match.location_score = location_score * 100
                    match.last_calculated = datetime.now(timezone.utc)
                else:
                    match = MatchScore(
                        consultant_id=consultant.id,
                        job_id=job.id,
                        total_score=total_score,
                        skill_score=skill_score * 100,
                        experience_score=experience_score * 100,
                        rate_score=rate_score * 100,
                        location_score=location_score * 100
                    )
                    db.session.add(match)
                
                match_count += 1
            
            db.session.commit()
            return match_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error calculating matches for consultant {consultant.id}: {str(e)}")
            return 0
    
    def _calculate_skill_match(self, consultant, job_skills, total_importance):
        """Calculate skill match score (0-1.0)"""
        if not job_skills:
            return 0.5  # Neutral score if no skills required
        
        score = 0.0
        missing_required = False
        
        # Check consultant skills against job requirements
        for cs in consultant.skills:
            if cs.skill_id in job_skills:
                # This consultant has a required skill
                js_info = job_skills[cs.skill_id]
                importance = js_info['importance'] / total_importance
                
                # Calculate level match (normalize to 0-1 range)
                level_match = (cs.level or 3) / 5.0
                
                # Add to score, weighted by importance
                score += level_match * importance
        
        # Check if any required skills are missing
        for skill_id, js_info in job_skills.items():
            if js_info['required']:
                has_skill = False
                for cs in consultant.skills:
                    if cs.skill_id == skill_id:
                        has_skill = True
                        break
                
                if not has_skill:
                    missing_required = True
                    break
        
        # Penalize for missing required skills
        if missing_required:
            score = max(0, score - 0.3)
        
        return min(1.0, score)
    
    def _calculate_experience_match(self, consultant, job):
        """Calculate experience match score (0-1.0)"""
        # This is a simplified implementation
        # In a real system, you might use years of experience in specific areas,
        # or perhaps previous similar job roles
        
        # Get average years of experience for consultant skills
        total_years = 0
        skill_count = 0
        
        for cs in consultant.skills:
            if cs.years_experience:
                total_years += cs.years_experience
                skill_count += 1
        
        if skill_count == 0:
            # No experience data available
            return 0.5
        
        avg_years = total_years / skill_count
        
        # Normalize to a 0-1 scale (assuming 10+ years is max score)
        # Using a logarithmic scale to avoid overly penalizing junior candidates
        experience_score = min(1.0, math.log10(1 + avg_years) / math.log10(11))
        
        return experience_score
    
    def _calculate_rate_match(self, consultant, job):
        """Calculate rate match score (0-1.0)"""
        if not consultant.hourly_rate or not job.rate_min or not job.rate_max:
            return 0.5  # Neutral score if no rate info
        
        # Perfect match if rate falls within job's range
        if job.rate_min <= consultant.hourly_rate <= job.rate_max:
            return 1.0
        
        # Calculate how far outside the range
        if consultant.hourly_rate < job.rate_min:
            # Consultant charges less than minimum
            # This might be good for the client, but possibly indicates
            # less experience than desired
            difference = job.rate_min - consultant.hourly_rate
            percentage = difference / job.rate_min
            # A small difference below min is still a good match
            return max(0, 1.0 - percentage)
        else:
            # Consultant charges more than maximum
            difference = consultant.hourly_rate - job.rate_max
            percentage = difference / job.rate_max
            # Score decreases as rate exceeds maximum
            return max(0, 1.0 - percentage)
    
    def _calculate_location_match(self, consultant, job_location_lower):
        """Calculate location match score (0-1.0)"""
        # Simple implementation - in a real system you might use
        # geographic distance, timezone compatibility, etc.
        
        if not job_location_lower or not consultant.location:
            return 0.5  # Neutral score if location info missing
        
        consultant_location = consultant.location.lower()
        
        # Perfect match for exact locations
        if consultant_location == job_location_lower:
            return 1.0
        
        # Check for partial matches (city in same region/country)
        # This is a simplified approach
        location_parts = job_location_lower.split(',')
        consultant_parts = consultant_location.split(',')
        
        # Compare the largest geographic unit (likely country)
        if len(location_parts) > 1 and len(consultant_parts) > 1:
            job_country = location_parts[-1].strip()
            consultant_country = consultant_parts[-1].strip()
            if job_country == consultant_country:
                return 0.8  # Good but not perfect match - same country
        
        # No match found, give a low score
        return 0.2