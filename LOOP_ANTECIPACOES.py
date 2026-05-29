import time
import sys
import traceback
from mvp_antecipacoes import get_mvp_antecipacoes  # importa sua função

def loop_extracao(pausa_seg=10):
    try:
        while True:
            print("\n--- Iniciando nova extração ---")
            get_mvp_antecipacoes()
            print(f"Aguardando {pausa_seg} segundos para a próxima execução...\n")
            time.sleep(pausa_seg)
    except Exception as e:
        print("❌ Erro durante a extração. Interrompendo o loop.")
        traceback.print_exc()  # mostra o erro completo
        # Se a exceção tiver um errno, usa ele; senão, retorna 1
        exit_code = getattr(e, "errno", 1)
        sys.exit(exit_code)

if __name__ == "__main__":
    loop_extracao()
