"""
Modelos de Dados Tipados e Contratos de Negócio - OpenLEA (OftalmoPE Tech).
Define entidades de pacientes, resultados de emissão e relatórios de lote.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import uuid


@dataclass
class RegistroPaciente:
    """Representa a solicitação de emissão de LEA de um paciente extraída da planilha."""
    row_index: int
    reg: str
    consulta: str
    medico: str
    unidade: str  # Obrigatória - sem fallback silencioso
    data_validade: str  # Formato ddmmaaaa
    nome_paciente: Optional[str] = None
    cid10: str = "H409"
    mot_cobr: str = "52"
    s_apac_ap_cod: str = "21"

    def __post_init__(self):
        self.reg = str(self.reg).strip()
        self.consulta = str(self.consulta).strip().upper()
        self.medico = str(self.medico).strip().upper()
        self.unidade = str(self.unidade).strip().upper()
        self.data_validade = str(self.data_validade).strip().replace("/", "").replace("-", "")
        if not self.unidade:
            raise ValueError(f"Linha {self.row_index}: Unidade hospitalar é obrigatória e não foi preenchida.")


@dataclass
class ResultadoItem:
    """Resultado individual do processamento de uma LEA no MWSUS."""
    item: RegistroPaciente
    sucesso: bool
    motivo_falha: Optional[str] = None
    tempo_processamento: float = 0.0
    interrompido: bool = False


@dataclass
class RelatorioLote:
    """Consolidação das métricas de execução de um lote de LEAs."""
    lote_id: str = field(default_factory=lambda: f"lea_{uuid.uuid4().hex[:12]}")
    total_itens: int = 0
    total_sucesso: int = 0
    total_inconsistencias: int = 0
    tempo_execucao_segundos: float = 0.0
    modo_simulacao: bool = False
    resultados: List[ResultadoItem] = field(default_factory=list)
    arquivo_origem: str = ""
    timestamp_inicio: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def taxa_sucesso(self) -> float:
        if self.total_itens == 0:
            return 0.0
        return (self.total_sucesso / self.total_itens) * 100.0

    @property
    def taxa_sucesso_percentual(self) -> float:
        return self.taxa_sucesso
