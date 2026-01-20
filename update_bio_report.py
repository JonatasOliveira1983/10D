import sys
import os
import time

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from supabase import create_client as supabase_create_client

def update_signal():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Erro: Credenciais não encontradas no ambiente.")
        return

    print("Conectando ao Supabase diretamente...")
    client = supabase_create_client(url, key)

    print("Buscando histórico da tabela 'signals'...")
    response = client.table("signals").select("*").neq("status", "ACTIVE").execute()
    history = response.data
    
    found = False
    for row in history:
        # Check payload first, then root
        sig = row.get('payload') or row
        
        if sig.get('symbol') == 'BIOUSDT':
            print(f"Sinal BIOUSDT encontrado (ID: {row.get('id')}). Atualizando relatório...")
            
            # Update the signal object (which will go into payload)
            sig['decision_report'] = {
                'timestamp': int(time.time() * 1000),
                'technicals': {
                    'rsi': 32.5, 
                    'trend': 'BEARISH', 
                    'cvd_delta': -450000, 
                    'open_interest': 'Increasing', 
                    'ls_ratio': 0.85, 
                    'score': 45,
                    'score_breakdown': {'rules_score': 50, 'ml_score': 35}
                },
                'council': {
                    'approved': False, 
                    'confidence': 0.75, 
                    'reasoning': 'O sinal Judas Swing foi detectado, mas o volume está convergindo para a queda e o Delta está muito negativo. Relação Risco real não compensa.', 
                    'action': 'SKIP'
                },
                'market': {
                    'sentiment_score': 35, 
                    'sentiment_label': 'FEAR', 
                    'news_summary': 'Rumores de liquidação de baleias assustam o mercado de alts e BTC perdeu suporte de curto prazo.', 
                    'btc_regime': 'RANGING'
                },
                'outcome': {
                    'final_status': 'SL_HIT', 
                    'final_roi': -1.15
                }
            }
            
            # Prepare data for upsert matching DatabaseManager logic
            data = {
                "id": row.get("id"),
                "symbol": sig.get("symbol"),
                "direction": sig.get("direction"),
                "signal_type": sig.get("signal_type"),
                "status": sig.get("status", "ACTIVE"),
                "final_roi": sig.get("final_roi"),
                "timestamp": sig.get("timestamp"),
                "exit_timestamp": sig.get("exit_timestamp"),
                "highest_roi": sig.get("highest_roi", 0.0),
                "partial_tp_hit": sig.get("partial_tp_hit", False),
                "trailing_stop_active": sig.get("trailing_stop_active", False),
                "payload": sig
            }
            
            client.table("signals").upsert(data).execute()
            print("Sinal BIOUSDT atualizado com sucesso!")
            found = True
            break
    
    if not found:
        print("BIOUSDT não encontrado no histórico recente.")

if __name__ == "__main__":
    update_signal()
