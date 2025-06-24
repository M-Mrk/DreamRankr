from db import db, LogEntries

def getLevelIdentifier(level):
    """
    Converts numeric or string log levels to standardized string identifiers.
    
    Args:
        level: Log level as integer (0-4) or string ('debug', 'info', etc.)
        
    Returns:
        str: Standardized level identifier
        
    Raises:
        None: Returns "Unknown" for unrecognized levels
    """
    try:
        if level == 0 or level == "debug":
            return "Debug"          # For long-term debugging information
        elif level == 1 or level == "info":
            return "Information"    # General operational information
        elif level == 2 or level == "auth":
            return "Authentication" # Authentication and authorization events
        elif level == 3 or level == "warning":
            return "Warning"        # Warning conditions that should be monitored
        elif level == 4 or level == "error":
            return "Error"          # Error conditions that need attention
        else:
            return "Unknown"        # Fallback for unrecognized levels
    except Exception:
        return "Unknown"
        
def getOriginIdentifier(origin):
    """
    Standardizes the origin identifier for log entries.
    
    Args:
        origin: Source function or module name as string
        
    Returns:
        str: Lowercase standardized origin identifier
        
    Raises:
        TypeError: If origin is not a string
    """
    if origin and isinstance(origin, str):
        return origin.lower()
    raise TypeError(f"Expected str in logger.py getOriginIdentifier got: {type(origin).__name__}")

def log(level, origin, message):
    """
    Creates a log entry in the database with the provided information.
    Handles database errors gracefully by falling back to console output.
    
    Args:
        level: Log level (0-4 or string: debug, info, auth, warning, error)
        origin: Source of the log message (function/module name)
        message: Log message content describing the event
        
    Returns:
        None
        
    Raises:
        None: Exceptions are caught and handled internally
    """
    # Validate that all required parameters are provided
    if not (level and origin and message):
        print(f"ERROR: Invalid log parameters - level: {level}, origin: {origin}, message: {message}")
        return
        
    try:
        # Create new log entry with standardized identifiers
        new_LogEntry = LogEntries(
            level=getLevelIdentifier(level),
            origin=getOriginIdentifier(origin),
            message=str(message)  # Ensure message is string
        )
        
        # Attempt to save to database
        db.session.add(new_LogEntry)
        db.session.commit()
        
    except Exception as e:
        # Fallback to console output if database logging fails
        print(f"ERROR writing Log to database: {str(e)}")
        print(f"Failed log entry - Level: {level}, Origin: {origin}, Message: {message}")
        
        # Attempt to rollback any partial transaction
        try:
            db.session.rollback()
        except Exception as rollback_error:
            print(f"ERROR during rollback: {str(rollback_error)}")