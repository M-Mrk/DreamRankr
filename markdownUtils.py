import os
import markdown
from logger import log
from flask import current_app as app

def getMarkDownFileContent(fileName):
    filePath = os.path.join(app.root_path, 'user_content', f'{fileName}.md')

    if not os.path.exists(filePath):
        log(4, 'getMarkDownFileContent', f"Requested file {fileName} does not exist at {filePath}")
        return None
    
    with open(filePath, 'r', encoding='utf-8') as f:
        markdownContent = f.read()
    
    htmlContent = markdown.markdown(markdownContent)
    return htmlContent