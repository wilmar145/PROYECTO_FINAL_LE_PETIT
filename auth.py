from authlib.integrations.flask_client import OAuth

oauth = OAuth()

auth0 = oauth.register(
    'auth0',
    client_id='B6yg1f2RoxUPZMTjhwaxYRATAAeJkSca',
    client_secret='mlFjXEvoB734dZU3PSiRYpRnwAS5T2NakBU1z9OE-oC0pogGQu7f7mJhidWeQnCr', # <--- ¡Pégalo aquí directamente!
    server_metadata_url='https://dev-fnxf4lcudrkaaiuh.us.auth0.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid profile email',
        'token_endpoint_auth_method': 'client_secret_post', # Esto es vital para evitar el Unauthorized
    }
)