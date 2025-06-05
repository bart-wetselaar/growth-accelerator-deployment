"""
Feedback Service for Growth Accelerator Staffing Platform

This service handles user feedback and suggestions management.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import flask
from sqlalchemy import desc

from db import db
from db.models import Feedback, FeedbackCategory, FeedbackResponse, FeedbackStatus, User

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        logger.info("FeedbackService initialized")
    
    def submit_feedback(self, data: Dict, user_id: Optional[int] = None) -> Dict:
        """
        Submit new feedback
        
        Args:
            data (dict): Feedback data including category, subject, message, etc.
            user_id (int, optional): ID of the logged-in user if available
            
        Returns:
            dict: Response with status and feedback details
        """
        try:
            # Validate required fields
            if 'subject' not in data or not data['subject'].strip():
                return {
                    'status': 'error',
                    'message': 'Subject is required'
                }
            
            if 'message' not in data or not data['message'].strip():
                return {
                    'status': 'error',
                    'message': 'Message is required'
                }
            
            # Create new feedback entry
            feedback = Feedback()
            
            # Set user ID if available
            if user_id:
                feedback.user_id = user_id
                
                # Get user email and name if not provided
                if 'email' not in data or not data['email']:
                    user = User.query.get(user_id)
                    if user:
                        data['email'] = user.email
                        data['name'] = user.username
            
            # Set attributes from data
            feedback.name = data.get('name', 'Anonymous')
            feedback.email = data.get('email', '')
            feedback.subject = data['subject']
            feedback.message = data['message']
            feedback.page_url = data.get('page_url', '')
            
            # Handle category
            category_value = data.get('category', 'general')
            try:
                feedback.category = FeedbackCategory(category_value)
            except ValueError:
                feedback.category = FeedbackCategory.GENERAL
            
            # Handle screenshot if provided
            if 'screenshot_data' in data and data['screenshot_data']:
                # Process base64 data and save to file
                try:
                    # Extract base64 data
                    import base64
                    import uuid
                    
                    # Extract MIME type and data
                    screenshot_data = data['screenshot_data']
                    if ',' in screenshot_data:
                        mime_part, base64_data = screenshot_data.split(',', 1)
                    else:
                        base64_data = screenshot_data
                    
                    # Decode base64
                    image_data = base64.b64decode(base64_data)
                    
                    # Generate unique filename
                    filename = f"feedback_screenshot_{uuid.uuid4()}.png"
                    directory = os.path.join('static', 'uploads', 'screenshots')
                    
                    # Create directory if it doesn't exist
                    os.makedirs(directory, exist_ok=True)
                    
                    # Save the file
                    filepath = os.path.join(directory, filename)
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    # Store the relative URL
                    feedback.screenshot_url = os.path.join('uploads', 'screenshots', filename)
                    
                except Exception as e:
                    logger.error(f"Error processing screenshot: {str(e)}")
            
            # Save the feedback
            db.session.add(feedback)
            db.session.commit()
            
            # Notify admin about new feedback
            self._notify_admin_of_new_feedback(feedback)
            
            return {
                'status': 'success',
                'message': 'Feedback submitted successfully',
                'feedback_id': feedback.id
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting feedback: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to submit feedback: {str(e)}"
            }
    
    def get_feedback(self, feedback_id: int, include_responses: bool = True) -> Dict:
        """
        Get a specific feedback by ID
        
        Args:
            feedback_id (int): The feedback ID
            include_responses (bool): Whether to include responses
            
        Returns:
            dict: Feedback details
        """
        try:
            feedback = Feedback.query.get(feedback_id)
            if not feedback:
                return {
                    'status': 'error',
                    'message': 'Feedback not found'
                }
            
            # Prepare response data
            result = {
                'id': feedback.id,
                'subject': feedback.subject,
                'message': feedback.message,
                'category': feedback.category.value,
                'status': feedback.status.value,
                'created_at': feedback.created_at.isoformat(),
                'is_public': feedback.is_public
            }
            
            # Include user info if available
            if feedback.user_id:
                user = User.query.get(feedback.user_id)
                if user:
                    result['user'] = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
            else:
                result['name'] = feedback.name
                result['email'] = feedback.email
            
            # Include screenshot URL if available
            if feedback.screenshot_url:
                result['screenshot_url'] = feedback.screenshot_url
            
            # Include responses if requested
            if include_responses:
                responses = []
                for resp in feedback.responses.filter_by(is_internal=False).order_by(FeedbackResponse.created_at).all():
                    response_data = {
                        'id': resp.id,
                        'message': resp.message,
                        'created_at': resp.created_at.isoformat()
                    }
                    
                    # Include responder info if available
                    if resp.responder_id:
                        responder = User.query.get(resp.responder_id)
                        if responder:
                            response_data['responder'] = {
                                'username': responder.username
                            }
                    
                    responses.append(response_data)
                
                result['responses'] = responses
            
            return {
                'status': 'success',
                'feedback': result
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to retrieve feedback: {str(e)}"
            }
    
    def list_feedback(self, page: int = 1, per_page: int = 20, 
                     status: Optional[str] = None, 
                     category: Optional[str] = None,
                     is_public: Optional[bool] = None) -> Dict:
        """
        List feedback with optional filtering
        
        Args:
            page (int): Page number
            per_page (int): Items per page
            status (str, optional): Filter by status
            category (str, optional): Filter by category
            is_public (bool, optional): Filter by public visibility
            
        Returns:
            dict: Paginated list of feedback
        """
        try:
            # Start with base query
            query = Feedback.query
            
            # Apply filters
            if status:
                try:
                    status_enum = FeedbackStatus(status)
                    query = query.filter_by(status=status_enum)
                except ValueError:
                    pass
            
            if category:
                try:
                    category_enum = FeedbackCategory(category)
                    query = query.filter_by(category=category_enum)
                except ValueError:
                    pass
            
            if is_public is not None:
                query = query.filter_by(is_public=is_public)
            
            # Count total
            total = query.count()
            
            # Order by created date (newest first)
            query = query.order_by(desc(Feedback.created_at))
            
            # Paginate
            items = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Format results
            results = []
            for item in items:
                feedback_data = {
                    'id': item.id,
                    'subject': item.subject,
                    'message': item.message,
                    'category': item.category.value,
                    'status': item.status.value,
                    'created_at': item.created_at.isoformat(),
                    'is_public': item.is_public,
                    'response_count': item.responses.count()
                }
                
                # Include user info if available
                if item.user_id:
                    user = User.query.get(item.user_id)
                    if user:
                        feedback_data['user'] = {
                            'username': user.username
                        }
                else:
                    feedback_data['name'] = item.name
                
                results.append(feedback_data)
            
            return {
                'status': 'success',
                'feedback': results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing feedback: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to list feedback: {str(e)}"
            }
    
    def add_response(self, feedback_id: int, message: str, 
                    responder_id: Optional[int] = None,
                    is_internal: bool = False) -> Dict:
        """
        Add a response to a feedback
        
        Args:
            feedback_id (int): The feedback ID
            message (str): Response message
            responder_id (int, optional): ID of the staff member responding
            is_internal (bool): Whether this is an internal note
            
        Returns:
            dict: Response with status
        """
        try:
            # Verify feedback exists
            feedback = Feedback.query.get(feedback_id)
            if not feedback:
                return {
                    'status': 'error',
                    'message': 'Feedback not found'
                }
            
            # Create response
            response = FeedbackResponse(
                feedback_id=feedback_id,
                message=message,
                responder_id=responder_id,
                is_internal=is_internal
            )
            
            db.session.add(response)
            
            # Update feedback status if needed
            if feedback.status == FeedbackStatus.NEW:
                feedback.status = FeedbackStatus.UNDER_REVIEW
            
            db.session.commit()
            
            # Notify user if this is a public response
            if not is_internal:
                self._notify_user_of_response(feedback, response)
            
            return {
                'status': 'success',
                'message': 'Response added successfully',
                'response_id': response.id
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding response: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to add response: {str(e)}"
            }
    
    def update_feedback_status(self, feedback_id: int, status: str, 
                              admin_notes: Optional[str] = None) -> Dict:
        """
        Update the status of a feedback
        
        Args:
            feedback_id (int): The feedback ID
            status (str): New status value
            admin_notes (str, optional): Additional admin notes
            
        Returns:
            dict: Response with status
        """
        try:
            # Verify feedback exists
            feedback = Feedback.query.get(feedback_id)
            if not feedback:
                return {
                    'status': 'error',
                    'message': 'Feedback not found'
                }
            
            # Update status
            try:
                new_status = FeedbackStatus(status)
                old_status = feedback.status
                feedback.status = new_status
                
                # Add admin notes if provided
                if admin_notes:
                    if feedback.admin_notes:
                        feedback.admin_notes += f"\n\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Status changed from {old_status.value} to {new_status.value}:\n{admin_notes}"
                    else:
                        feedback.admin_notes = f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Status changed to {new_status.value}:\n{admin_notes}"
                
                db.session.commit()
                
                # Notify user of status change
                self._notify_user_of_status_change(feedback)
                
                return {
                    'status': 'success',
                    'message': f'Feedback status updated to {new_status.value}'
                }
                
            except ValueError:
                return {
                    'status': 'error',
                    'message': f'Invalid status value: {status}'
                }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating feedback status: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to update status: {str(e)}"
            }
    
    def toggle_public_visibility(self, feedback_id: int) -> Dict:
        """
        Toggle public visibility of a feedback
        
        Args:
            feedback_id (int): The feedback ID
            
        Returns:
            dict: Response with status
        """
        try:
            # Verify feedback exists
            feedback = Feedback.query.get(feedback_id)
            if not feedback:
                return {
                    'status': 'error',
                    'message': 'Feedback not found'
                }
            
            # Toggle visibility
            feedback.is_public = not feedback.is_public
            db.session.commit()
            
            return {
                'status': 'success',
                'message': f"Feedback is now {'public' if feedback.is_public else 'private'}",
                'is_public': feedback.is_public
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error toggling feedback visibility: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to update visibility: {str(e)}"
            }
    
    def get_feedback_statistics(self) -> Dict:
        """
        Get statistics about feedback
        
        Returns:
            dict: Statistics about feedback
        """
        try:
            # Count total feedback
            total_count = Feedback.query.count()
            
            # Count by status
            status_counts = {}
            for status in FeedbackStatus:
                count = Feedback.query.filter_by(status=status).count()
                status_counts[status.value] = count
            
            # Count by category
            category_counts = {}
            for category in FeedbackCategory:
                count = Feedback.query.filter_by(category=category).count()
                category_counts[category.value] = count
            
            # Count new feedback in the last week
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = Feedback.query.filter(Feedback.created_at >= week_ago).count()
            
            # Count public feedback
            public_count = Feedback.query.filter_by(is_public=True).count()
            
            return {
                'status': 'success',
                'statistics': {
                    'total_count': total_count,
                    'by_status': status_counts,
                    'by_category': category_counts,
                    'recent_count': recent_count,
                    'public_count': public_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback statistics: {str(e)}")
            return {
                'status': 'error',
                'message': f"Unable to retrieve statistics: {str(e)}"
            }
    
    def _notify_admin_of_new_feedback(self, feedback: Feedback) -> None:
        """Send notification to admin about new feedback"""
        # In a real implementation, this would send an email or notification
        # For now, we just log it
        logger.info(f"New feedback #{feedback.id} received: {feedback.subject}")
        
        # Try to find admin users to notify
        try:
            admin_users = User.query.filter_by(role='admin').all()
            admin_emails = [user.email for user in admin_users if user.email]
            
            if admin_emails:
                # In a real implementation, send email to these addresses
                logger.info(f"Would notify admins: {', '.join(admin_emails)}")
        except Exception as e:
            logger.error(f"Error finding admin users to notify: {str(e)}")
    
    def _notify_user_of_response(self, feedback: Feedback, response: FeedbackResponse) -> None:
        """Notify user about a new response to their feedback"""
        # In a real implementation, this would send an email
        # For now, we just log it
        logger.info(f"New response to feedback #{feedback.id} added")
        
        # Determine user email
        user_email = None
        if feedback.user_id:
            user = User.query.get(feedback.user_id)
            if user:
                user_email = user.email
        else:
            user_email = feedback.email
            
        if user_email:
            # In a real implementation, send email to this address
            logger.info(f"Would notify user at: {user_email}")
    
    def _notify_user_of_status_change(self, feedback: Feedback) -> None:
        """Notify user about a status change to their feedback"""
        # In a real implementation, this would send an email
        # For now, we just log it
        logger.info(f"Feedback #{feedback.id} status changed to: {feedback.status.value}")
        
        # Only notify on certain status changes
        if feedback.status not in [FeedbackStatus.PLANNED, FeedbackStatus.IN_PROGRESS, FeedbackStatus.COMPLETED]:
            return
            
        # Determine user email
        user_email = None
        if feedback.user_id:
            user = User.query.get(feedback.user_id)
            if user:
                user_email = user.email
        else:
            user_email = feedback.email
            
        if user_email:
            # In a real implementation, send email to this address
            logger.info(f"Would notify user at: {user_email} about status change to {feedback.status.value}")