"""
Structured Logging for SOC2 Compliance

Provides structured JSON logging with trace IDs, correlation IDs, and audit fields.
"""

import json
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps


class StructuredLogger:
    """
    Structured logger for SOC2 compliance.
    
    Features:
    - JSON structured logs
    - Trace ID correlation
    - Audit trail fields
    - Security event logging
    - Performance metrics
    """
    
    def __init__(self, service_name: str, environment: str = None):
        self.service_name = service_name
        self.environment = environment or os.environ.get('ENVIRONMENT', 'prod')
        self.trace_id = None
        self.correlation_id = None
    
    def set_trace_id(self, trace_id: str):
        """Set trace ID for request correlation"""
        self.trace_id = trace_id
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for cross-service tracing"""
        self.correlation_id = correlation_id
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'service': self.service_name,
            'environment': self.environment,
            'message': message,
            'trace_id': self.trace_id or str(uuid.uuid4()),
            'correlation_id': self.correlation_id,
        }
        
        # Add additional fields
        entry.update(kwargs)
        
        return entry
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        entry = self._create_log_entry('INFO', message, **kwargs)
        print(json.dumps(entry))
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message"""
        entry = self._create_log_entry('ERROR', message, **kwargs)
        
        if error:
            entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'stack_trace': self._get_stack_trace(error)
            }
        
        print(json.dumps(entry))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        entry = self._create_log_entry('WARN', message, **kwargs)
        print(json.dumps(entry))
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if self.environment != 'prod':
            entry = self._create_log_entry('DEBUG', message, **kwargs)
            print(json.dumps(entry))
    
    def audit(self, event_type: str, user_id: str, resource: str, action: str, **kwargs):
        """
        Log audit event for SOC2 compliance.
        
        Args:
            event_type: Type of audit event (access, modification, deletion, etc.)
            user_id: User or service performing the action
            resource: Resource being accessed/modified
            action: Action performed
        """
        entry = self._create_log_entry(
            'AUDIT',
            f'Audit event: {event_type}',
            audit_event={
                'event_type': event_type,
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'success': kwargs.get('success', True),
                'ip_address': kwargs.get('ip_address'),
                'user_agent': kwargs.get('user_agent'),
            },
            **{k: v for k, v in kwargs.items() if k not in ['success', 'ip_address', 'user_agent']}
        )
        print(json.dumps(entry))
    
    def security_event(self, event_type: str, severity: str, **kwargs):
        """
        Log security event.
        
        Args:
            event_type: Type of security event
            severity: high, medium, low
        """
        entry = self._create_log_entry(
            'SECURITY',
            f'Security event: {event_type}',
            security_event={
                'event_type': event_type,
                'severity': severity.upper(),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            },
            **kwargs
        )
        print(json.dumps(entry))
    
    def performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics"""
        entry = self._create_log_entry(
            'PERF',
            f'Performance: {operation}',
            performance={
                'operation': operation,
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            },
            **kwargs
        )
        print(json.dumps(entry))
    
    def _get_stack_trace(self, error: Exception) -> str:
        """Get stack trace from exception"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    def log_request(self, method: str, path: str, user_id: str = None, **kwargs):
        """Log incoming request"""
        self.info(
            f'Request: {method} {path}',
            request={
                'method': method,
                'path': path,
                'user_id': user_id,
            },
            **kwargs
        )
    
    def log_response(self, status_code: int, duration_ms: float, **kwargs):
        """Log response"""
        self.info(
            f'Response: {status_code}',
            response={
                'status_code': status_code,
                'duration_ms': duration_ms,
            },
            **kwargs
        )


def log_function_call(logger: StructuredLogger):
    """Decorator to log function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger.debug(f'Function call: {func.__name__}', function=func.__name__)
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.performance(f'{func.__name__}', duration)
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.error(f'Function error: {func.__name__}', error=e, duration_ms=duration)
                raise
        return wrapper
    return decorator

