import pywhatkit
import datetime
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class Messenger:
    def __init__(self, browser_path: str = None):
        """
        Initialize the messaging utility.
        
        Args:
            browser_path (str, optional): Path to the browser executable
        """
        self.browser_path = browser_path
        if browser_path:
            pywhatkit.config.browser_path = browser_path
    
    def send_whatsapp_message(self, 
                             phone_number: str, 
                             message: str, 
                             delay: int = 2,
                             scheduled_time: Optional[datetime.datetime] = None) -> Dict:
        """
        Send a WhatsApp message now or at a scheduled time.
        
        Args:
            phone_number (str): Phone number with country code
            message (str): Message to send
            delay (int): Delay in minutes if scheduled_time is None
            scheduled_time (datetime, optional): Specific time to send the message
        
        Returns:
            dict: Status of the operation
        """
        try:
            # Format phone number to ensure it starts with '+'
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            
            # Get the current time
            now = datetime.datetime.now()
            
            # Use scheduled time if provided, otherwise add delay to current time
            if scheduled_time:
                send_hour = scheduled_time.hour
                send_minute = scheduled_time.minute
            else:
                send_hour = now.hour
                send_minute = now.minute + delay
                
                # Adjust for minute overflow
                if send_minute >= 60:
                    send_hour = (send_hour + 1) % 24
                    send_minute = send_minute % 60
            
            # Send the message
            pywhatkit.sendwhatmsg(phone_number, message, send_hour, send_minute, wait_time=20)
            
            logger.info(f"Message scheduled to {phone_number} at {send_hour}:{send_minute}")
            return {
                "status": "success",
                "message": f"Message scheduled to be sent at {send_hour}:{send_minute}"
            }
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send message: {str(e)}"
            }
    
    def send_bulk_messages(self, 
                          recipients: List[str], 
                          message: str, 
                          interval_minutes: int = 2) -> Dict:
        """
        Send messages to multiple recipients with a time interval.
        
        Args:
            recipients (list): List of phone numbers
            message (str): Message to send
            interval_minutes (int): Time interval between messages
        
        Returns:
            dict: Status of the operation with details for each recipient
        """
        results = []
        now = datetime.datetime.now()
        
        for i, recipient in enumerate(recipients):
            # Calculate scheduled time with increasing intervals
            scheduled_time = now + datetime.timedelta(minutes=interval_minutes * i)
            
            # Send the message
            result = self.send_whatsapp_message(
                recipient, 
                message, 
                scheduled_time=scheduled_time
            )
            
            results.append({
                "recipient": recipient,
                "result": result
            })
        
        return {
            "status": "completed",
            "results": results
        }
    
    def send_whatsapp_with_template(self, 
                                   phone_number: str, 
                                   template: str, 
                                   variables: Dict, 
                                   delay: int = 2) -> Dict:
        """
        Send a WhatsApp message using a template with variables.
        
        Args:
            phone_number (str): Phone number with country code
            template (str): Message template with placeholders
            variables (dict): Variables to replace in the template
            delay (int): Delay in minutes
        
        Returns:
            dict: Status of the operation
        """
        try:
            # Replace variables in the template
            message = template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                message = message.replace(placeholder, str(value))
            
            # Send the message
            return self.send_whatsapp_message(phone_number, message, delay)
            
        except Exception as e:
            logger.error(f"Error sending template message: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send template message: {str(e)}"
            }