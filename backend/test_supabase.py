"""
Script para testar a conexão com o Supabase e verificar os dados existentes
"""
import os
from supabase import create_client, Client

# Configurações do Supabase
SUPABASE_URL = "https://abphpbylwlgozmyumiwx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFicGhwYnlsd2xnb3pteXVtaXd4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgyMjc4NTQsImV4cCI6MjA4MzgwMzg1NH0.fHHahIbxD6qCHg2JIBLhp3Aj-5P8h3ZTA3CJNGckwsQ"

def test_supabase_connection():
    """Testa a conexão com o Supabase e lista os dados"""
    print("=" * 60, flush=True)
    print("TESTE DE CONEXÃO COM SUPABASE", flush=True)
    print("=" * 60, flush=True)
    
    try:
        # Criar cliente
        print(f"\n[1] Conectando ao Supabase...", flush=True)
        print(f"    URL: {SUPABASE_URL}", flush=True)
        
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("    ✅ Cliente criado com sucesso!", flush=True)
        
        # Testar tabela de sinais
        print(f"\n[2] Verificando tabela 'signals'...")
        try:
            # Buscar todos os sinais
            response = client.table("signals").select("*").execute()
            total_signals = len(response.data)
            print(f"    ✅ Total de sinais no banco: {total_signals}", flush=True)
            
            # Contar por status
            active = client.table("signals").select("*").eq("status", "ACTIVE").execute()
            print(f"    📊 Sinais ATIVOS: {len(active.data)}", flush=True)
            
            tp_hit = client.table("signals").select("*").eq("status", "TP_HIT").execute()
            print(f"    📊 Sinais TP_HIT: {len(tp_hit.data)}", flush=True)
            
            sl_hit = client.table("signals").select("*").eq("status", "SL_HIT").execute()
            print(f"    📊 Sinais SL_HIT: {len(sl_hit.data)}", flush=True)
            
            # Mostrar alguns exemplos de sinais finalizados
            if tp_hit.data or sl_hit.data:
                print(f"\n[3] Exemplos de sinais finalizados (para treinar a IA):", flush=True)
                finalized = client.table("signals").select("*").neq("status", "ACTIVE").limit(5).execute()
                for idx, signal in enumerate(finalized.data, 1):
                    payload = signal.get("payload", {})
                    print(f"\n    Sinal #{idx}:", flush=True)
                    print(f"      Symbol: {signal.get('symbol')}", flush=True)
                    print(f"      Direction: {signal.get('direction')}", flush=True)
                    print(f"      Status: {signal.get('status')}", flush=True)
                    print(f"      Entry: {signal.get('entry_price')}", flush=True)
                    print(f"      ROI: {signal.get('final_roi', 'N/A')}%", flush=True)
                    print(f"      Timestamp: {signal.get('timestamp')}", flush=True)
            
        except Exception as e:
            print(f"    ❌ Erro ao acessar tabela 'signals': {e}", flush=True)
        
        # Testar tabela de trading plan
        print(f"\n[4] Verificando tabela 'trading_plan'...", flush=True)
        try:
            response = client.table("trading_plan").select("*").execute()
            print(f"    ✅ Registros encontrados: {len(response.data)}", flush=True)
        except Exception as e:
            print(f"    ❌ Erro ao acessar tabela 'trading_plan': {e}", flush=True)
        
        print("\n" + "=" * 60, flush=True)
        print("TESTE CONCLUÍDO COM SUCESSO!", flush=True)
        print("=" * 60, flush=True)
        
    except Exception as e:
        print(f"\n❌ ERRO NA CONEXÃO: {e}", flush=True)
        print("=" * 60, flush=True)

if __name__ == "__main__":
    test_supabase_connection()
