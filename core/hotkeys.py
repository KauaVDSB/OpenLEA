"""
Módulo de Controle de Execução e Teclas de Atalho de Interrupção - OpenLEA.
Implementa parada abrupta de emergência e parada suave após o paciente atual.
"""

import threading
import sys
import os

class ControleExecucao:
    """Gerenciador central thread-safe de estado de interrupção do robô."""

    def __init__(self):
        self._lock = threading.Lock()
        self._interromper_imediato = False
        self._interromper_apos_atual = False
        self._motivo = ""
        self._listener_thread = None
        self._ativo = False

    def solicitar_parada_imediata(self, motivo: str = "Parada de emergência solicitada pelo operador"):
        """Interrompe a execução imediatamente na próxima checagem segura."""
        with self._lock:
            self._interromper_imediato = True
            self._motivo = motivo

    def solicitar_parada_suave(self, motivo: str = "Parada solicitada após concluir o paciente atual"):
        """Permite que o paciente em andamento seja finalizado e encerra o lote antes do próximo."""
        with self._lock:
            self._interromper_apos_atual = True
            self._motivo = motivo

    @property
    def deve_parar_imediato(self) -> bool:
        with self._lock:
            return self._interromper_imediato

    @property
    def deve_parar_apos_atual(self) -> bool:
        with self._lock:
            return self._interromper_apos_atual or self._interromper_imediato

    @property
    def motivo(self) -> str:
        with self._lock:
            return self._motivo

    def resetar(self):
        with self._lock:
            self._interromper_imediato = False
            self._interromper_apos_atual = False
            self._motivo = ""

    def iniciar_listener_teclado(self):
        """Inicia escuta não-bloqueante de teclas de atalho (Windows)."""
        if self._ativo:
            return
        self._ativo = True
        
        # Thread de monitoramento via msvcrt (Windows console) ou signal
        def _monitor():
            if sys.platform == "win32":
                try:
                    import msvcrt
                    while self._ativo and not self.deve_parar_imediato:
                        if msvcrt.kbhit():
                            ch = msvcrt.getch()
                            # ESC (ASCII 27) = Parada Imediata
                            if ch == b"\x1b":
                                self.solicitar_parada_imediata("ESC pressionado (Parada Imediata)")
                                break
                            # 'p' ou 'P' = Parada Suave (Pausa após paciente atual)
                            elif ch in (b"p", b"P"):
                                self.solicitar_parada_suave("Tecla P pressionada (Parada após paciente atual)")
                        threading.Event().wait(0.1)
                except Exception:
                    pass

        self._listener_thread = threading.Thread(target=_monitor, daemon=True)
        self._listener_thread.start()

    def parar_listener_teclado(self):
        self._ativo = False
        self._listener_thread = None


# Instância global singleton
controle_execucao = ControleExecucao()
