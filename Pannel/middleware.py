# pannel/middleware.py
from django.db import connections
import logging

logger = logging.getLogger(__name__)

class SQLLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log des requêtes SQL
        for conn_name in ['discords']:
            try:
                conn = connections[conn_name]
                if hasattr(conn, 'queries') and conn.queries:
                    logger.debug(f"Requêtes {conn_name}: {conn.queries}")
            except Exception as e:
                logger.error(f"Erreur connexion {conn_name}: {e}")
        
        return response