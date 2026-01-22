
import os
import sys
import time
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_ANON_KEY")
client = create_client(URL, KEY)

def verify():
    print("--- Verificando Atualizações da Banca ---")
    
    # 1. Buscar status atual
    status = client.table("bankroll_status").select("*").single().execute()
    print(f"Status Atual: {status.data}")
    
    # 2. Buscar trades abertos
    trades = client.table("bankroll_trades").select("*").eq("status", "OPEN").execute()
    if not trades.data:
        print("Nenhum trade aberto para testar. Por favor, gere um sinal ou force a abertura de um trade.")
        return

    trade = trades.data[0]
    print(f"Testando Trade: {trade['id']} - {trade['symbol']}")
    print(f"Preço Anterior: {trade.get('current_price')} | ROI Anterior: {trade.get('current_roi')}%")
    
    # Esperar um pouco para ver se o background scanner atualiza
    print("Aguardando 10 segundos para o scanner rodar...")
    time.sleep(10)
    
    # 3. Buscar novamente
    updated_trade = client.table("bankroll_trades").select("*").eq("id", trade["id"]).single().execute()
    print(f"Preço Novo: {updated_trade.data.get('current_price')} | ROI Novo: {updated_trade.data.get('current_roi')}%")
    
    if updated_trade.data.get('current_price') != trade.get('current_price'):
        print("✅ SUCESSO: Preço/ROI atualizado no banco de dados!")
    else:
        print("❌ FALHA: O preço não mudou. Verifique se o backend está rodando e se há sinais sniper ativos.")

if __name__ == "__main__":
    verify()
