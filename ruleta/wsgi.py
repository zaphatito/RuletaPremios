import os
import sys
from django.core.wsgi import get_wsgi_application


venv_path = '/home/perfumep/public_html/rueda/venv/lib/python3.12/site-packages'
if venv_path not in sys.path:
    sys.path.append(venv_path)

print("Python version ********************************************************************************************:", sys.version)
from django.core.wsgi import get_wsgi_application
sys.path.append('/home/perfumep/public_html/rueda/ruleta/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ruleta.settings')
application = get_wsgi_application()