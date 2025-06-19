from db import db, LogEntries

def getLevelIdentifier(level):
    if level == 0 or level == "debug": #For longterm debuging
        output = "Debug"
    elif level == 1 or level == "info":
        output = "Information"
    elif level == 2 or level == "auth":
        output = "Authentication"
    elif level == 3 or level == "warning":
        output = "Warning"
    elif level == 4 or level == "error":
        output = "Error"
    else:
        output = "Unknown"
    return output
        
def getOriginIdentifier(origin):
    if origin and isinstance(origin, str):
        output = origin.lower()
        return output
    raise TypeError(f"Expected str in logger.py getOriginIdentifier got: {type(origin).__name__}")

def log(level, origin, message):
    if level and origin and message:
        new_LogEntry = LogEntries (
            level = getLevelIdentifier(level),
            origin = getOriginIdentifier(origin),
            message = message
        )
        try:
            db.session.add(new_LogEntry)
            db.session.commit()
        except Exception as e:
            print("ERROR writing Log, because: " + str(e))