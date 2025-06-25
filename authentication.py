from functools import wraps
from flask import Flask, redirect, session, url_for
from db import Authentication
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from logger import log

def requiresViewer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Auth check here
        if not session.get('authenticated'):
            print("session is not authenticated")
            return redirect(url_for('login'))
        
        permissionLevel = session.get('permissionLevel')
        if not permissionLevel == 'viewer' and not permissionLevel == 'trainer':
            return redirect(url_for('login'))
        
        # Pass ALL arguments to the original function
        return f(*args, **kwargs)
    return decorated_function

def requiresTrainer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Auth check here
        if not session.get('authenticated'):
            print("Not authenticated")
            return redirect(url_for('login'))
        
        permissionLevel = session.get('permissionLevel')
        if not permissionLevel == 'trainer':
            print(f"wrong permission: {permissionLevel}")
            return redirect(url_for('login'))
        
        # Pass ALL arguments to the original function
        return f(*args, **kwargs)
    return decorated_function

def authenticate(password, request):
    """
    Compares provided plain text password to all stored hashes and automatically gives permissionLevel according to success full authentication Entry name
    
    Args:
        password: Plain text password to compare
        request: used for logging ip
        
    Returns:
        bool: True if successful and false if denied
    """
    authentications = Authentication.query.all()
    for authentication in authentications:
        if check_password_hash(authentication.passwordHash, password):
            print(authentication.name)
            session.clear()
            session.permanent = True
            session['authenticated'] = True
            session['permissionLevel'] = authentication.name
            session['loginTime'] = datetime.datetime.now()

            log(2, "authenticate", f"SUCCESS: Authenticated user with Ip: {request.remote_addr} to {authentication.name} realm")
            return True
    log(2, "authenticate", f'DENIED: Can not authenticate user with Ip: {request.remote_addr}, because "{password}" does not match any registered passwordHash')
    return False
