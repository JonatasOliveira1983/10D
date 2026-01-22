import requests
import time
import sys

print("Verificando API da Banca em localhost:5000...")

max_retries = 10
for i in range(max_retries):
    try:
        response = requests.get('http://localhost:5000/api/bankroll/status')
        if response.status_code == 200:
            print(f"SUCESSO! API respondeu: {response.status_code}")
            print(f"Dados: {response.json()}")
            sys.exit(0)
        else:
            print(f"API respondeu com erro: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"Tentativa {i+1}/{max_retries}: Backend ainda não disponível...")
        time.sleep(2)

print("FALHA: Não foi possível conectar ao backend.")
sys.exit(1)
