import os
import markdown
from logger import log
from flask import current_app as app

def checkIfFileOrDb(contentId):
    if any(char.isalpha() for char in contentId):
        return 'file'
    return 'db'

def getMarkDownFileContent(fileName, raw):
    filePath = os.path.join(app.root_path, 'user_content', f'{fileName}.md')

    if not os.path.exists(filePath):
        log(4, 'getMarkDownFileContent', f"Requested file {fileName} does not exist at {filePath}")
        return None
    
    with open(filePath, 'r', encoding='utf-8') as f:
        markdownContent = f.read()

    if not raw:
        htmlContent = markdown.markdown(markdownContent)
        return htmlContent
    else:
        return markdownContent

def getMarkDownContent(contentId, raw=False):
    if checkIfFileOrDb(contentId) == 'file':
        return getMarkDownFileContent(contentId, raw)
    elif checkIfFileOrDb(contentId) == 'db':
        contentId = int(contentId)
        pass
    else:
        log(4, "getMarkDownContent", f"Could not decipher if contentId was for a file or db entry: {contentId}")

def changeMarkDownFile(fileName, content):
    filePath = os.path.join(app.root_path, 'user_content', f'{fileName}.md')

    try:
        with open(filePath, 'w', encoding='utf-8') as f:
            f.write(content)
        log(2, 'changeMarkDownFile', f"Successfully wrote content to {filePath}")
    except Exception as e:
        log(4, 'changeMarkDownFile', f"Failed to write content to {filePath}: {e}")

def changeMarkDown(contentId, content):
    if checkIfFileOrDb(contentId) == 'file':
        changeMarkDownFile(contentId, content)
    elif checkIfFileOrDb(contentId) == 'db':
        contentId = int(contentId)
        pass
    else:
        log(4, "changeMarkDown", f"Could not decipher if contentId was for a file or db entry: {contentId}")