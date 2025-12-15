from django.shortcuts import render, redirect
from django.http import HttpRequest
import requests

CLIENT_ID = "1298395229073707068"
CLIENT_SECRET = "LnfevRX_BEtSAF_memkMJYN8y0WwikQT"
REDIRECT_URI = "https://voiliersremi.alwaysdata.net/oauth2/login/redirect"

auth_url_discord = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify"

def discord_login(request: HttpRequest):
    return redirect(auth_url_discord)

def discord_login_redirect(request: HttpRequest):
    code = request.GET.get('code')
    if not code:
        return redirect('home')

    try:
        user_info = exchange_code(code)
        request.session['user_info'] = user_info
        
        # Redirection directe vers l'URL du tableau de bord
        return redirect('board')  # URL absolue
        
    except Exception as e:
        print(f"Erreur lors du processus OAuth2: {e}")
        return redirect('home')

def exchange_code(code: str):
    # Le code d'échange reste le même
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify"
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    token_url = "https://discord.com/api/v10/oauth2/token"
    token_response = requests.post(token_url, data=data, headers=headers)
    token_response.raise_for_status()

    credentials = token_response.json()
    access_token = credentials['access_token']
    
    user_url = "https://discord.com/api/v10/users/@me"
    user_response = requests.get(user_url, headers={'Authorization': f'Bearer {access_token}'})
    user_response.raise_for_status()
    
    user_info = user_response.json()
    return user_info