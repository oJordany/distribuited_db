from middleware.request_handler import RequestHandler
from utils.config import MIDDLEWARE_HOST, MIDDLEWARE_PORT

if __name__ == '__main__':
    # O Middleware agora inicia um servidor real que espera o client_app.py
    handler = RequestHandler(MIDDLEWARE_HOST, MIDDLEWARE_PORT)
    handler.start()