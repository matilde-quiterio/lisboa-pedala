import sqlite3
import uuid
import contextlib
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class EstadoOrdem(Enum):
    PENDENTE_AVALIACAO = "PENDENTE_AVALIACAO"
    SEM_INTERVENCAO_NECESSARIA = "SEM_INTERVENCAO_NECESSARIA"
    EM_INTERVENCAO = "EM_INTERVENCAO"
    CONCLUIDA = "CONCLUIDA"

class OrigemAvaria(Enum):
    TELEMETRIA = "TELEMETRIA"
    MANUAL = "MANUAL"

@dataclass
class OrdemManutencao:
    ordem_id: str
    bicicleta_id: str
    origem: OrigemAvaria
    descricao_avaria: str
    estado: EstadoOrdem
    mensagem_id_origem: Optional[str] = None
    necessita_intervencao: Optional[bool] = None
    descricao_intervencao: Optional[str] = None
    resultado: Optional[str] = None

class ManutencaoRepository:
    def __init__(self, db_path: str = "manutencao.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ordens_manutencao (
                        ordem_id TEXT PRIMARY KEY,
                        bicicleta_id TEXT NOT NULL,
                        origem TEXT NOT NULL,
                        descricao_avaria TEXT NOT NULL,
                        estado TEXT NOT NULL,
                        mensagem_id_origem TEXT UNIQUE,
                        resultado TEXT
                    )
                """)
                
                cursor = conn.execute("PRAGMA table_info(ordens_manutencao)")
                colunas = [row[1] for row in cursor.fetchall()]
                
                if "necessita_intervencao" not in colunas:
                    conn.execute("ALTER TABLE ordens_manutencao ADD COLUMN necessita_intervencao INTEGER")
                if "descricao_intervencao" not in colunas:
                    conn.execute("ALTER TABLE ordens_manutencao ADD COLUMN descricao_intervencao TEXT")
                
                # Migração: converte registos antigos CANCELADA para o novo fluxo preservando os restantes dados
                conn.execute("""
                    UPDATE ordens_manutencao
                    SET estado = 'SEM_INTERVENCAO_NECESSARIA', necessita_intervencao = 0
                    WHERE estado = 'CANCELADA'
                """)

    def salvar(self, ordem: OrdemManutencao) -> None:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                necessita_int = 1 if ordem.necessita_intervencao is True else (0 if ordem.necessita_intervencao is False else None)
                conn.execute("""
                    INSERT INTO ordens_manutencao (
                        ordem_id, bicicleta_id, origem, descricao_avaria, estado, 
                        mensagem_id_origem, necessita_intervencao, descricao_intervencao, resultado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ordem_id) DO UPDATE SET
                        estado=excluded.estado,
                        necessita_intervencao=excluded.necessita_intervencao,
                        descricao_intervencao=excluded.descricao_intervencao,
                        resultado=excluded.resultado
                """, (
                    ordem.ordem_id, ordem.bicicleta_id, ordem.origem.value, 
                    ordem.descricao_avaria, ordem.estado.value, ordem.mensagem_id_origem, 
                    necessita_int, ordem.descricao_intervencao, ordem.resultado
                ))

    def _row_to_ordem(self, row: sqlite3.Row) -> OrdemManutencao:
        necessita_int = None
        if row["necessita_intervencao"] is not None:
            necessita_int = bool(row["necessita_intervencao"])
            
        estado_str = row["estado"]
        try:
            estado = EstadoOrdem(estado_str)
        except ValueError:
            raise ValueError(f"Estado desconhecido ou corrompido na base de dados: '{estado_str}'")

        return OrdemManutencao(
            ordem_id=row["ordem_id"],
            bicicleta_id=row["bicicleta_id"],
            origem=OrigemAvaria(row["origem"]),
            descricao_avaria=row["descricao_avaria"],
            estado=estado,
            mensagem_id_origem=row["mensagem_id_origem"],
            necessita_intervencao=necessita_int,
            descricao_intervencao=row["descricao_intervencao"],
            resultado=row["resultado"]
        )

    def obter_por_mensagem_id(self, mensagem_id: str) -> Optional[OrdemManutencao]:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM ordens_manutencao WHERE mensagem_id_origem = ?", (mensagem_id,))
            row = cursor.fetchone()
            return self._row_to_ordem(row) if row else None

    def obter_por_id(self, ordem_id: str) -> Optional[OrdemManutencao]:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM ordens_manutencao WHERE ordem_id = ?", (ordem_id,))
            row = cursor.fetchone()
            return self._row_to_ordem(row) if row else None

    def listar_todas(self) -> List[OrdemManutencao]:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM ordens_manutencao")
            return [self._row_to_ordem(row) for row in cursor.fetchall()]

class ManutencaoService:
    def __init__(self, repo: ManutencaoRepository):
        self.repo = repo

    def processar_avaria_telemetria(self, mensagem_id: str, bicicleta_id: str, codigo_avaria: str, descricao: str) -> None:
        if self.repo.obter_por_mensagem_id(mensagem_id):
            return

        ordem = OrdemManutencao(
            ordem_id=str(uuid.uuid4()),
            bicicleta_id=bicicleta_id,
            origem=OrigemAvaria.TELEMETRIA,
            descricao_avaria=f"[{codigo_avaria}] {descricao}",
            estado=EstadoOrdem.PENDENTE_AVALIACAO,
            mensagem_id_origem=mensagem_id
        )
        self.repo.salvar(ordem)

    def reportar_avaria_manual(self, bicicleta_id: str, descricao: str) -> OrdemManutencao:
        ordem = OrdemManutencao(
            ordem_id=str(uuid.uuid4()),
            bicicleta_id=bicicleta_id,
            origem=OrigemAvaria.MANUAL,
            descricao_avaria=descricao,
            estado=EstadoOrdem.PENDENTE_AVALIACAO
        )
        self.repo.salvar(ordem)
        return ordem

    def avaliar_ordem(self, ordem_id: str, necessita_intervencao: bool, resultado: Optional[str] = None) -> OrdemManutencao:
        ordem = self.repo.obter_por_id(ordem_id)
        if not ordem:
            raise ValueError("Ordem não encontrada.")
            
        if ordem.estado != EstadoOrdem.PENDENTE_AVALIACAO:
            raise ValueError(f"Não é possível avaliar a ordem a partir do estado '{ordem.estado.value}'. Apenas ordens pendentes podem ser avaliadas.")

        ordem.necessita_intervencao = necessita_intervencao
        
        if necessita_intervencao:
            ordem.estado = EstadoOrdem.EM_INTERVENCAO
        else:
            if not resultado:
                raise ValueError("O resultado da avaliação é obrigatório quando não há necessidade de intervenção.")
            ordem.estado = EstadoOrdem.SEM_INTERVENCAO_NECESSARIA
            ordem.resultado = resultado
        
        self.repo.salvar(ordem)
        return ordem

    def registar_intervencao(self, ordem_id: str, descricao_intervencao: str, resultado: str) -> OrdemManutencao:
        ordem = self.repo.obter_por_id(ordem_id)
        if not ordem:
            raise ValueError("Ordem não encontrada.")
        
        if ordem.estado != EstadoOrdem.EM_INTERVENCAO:
             raise ValueError("A ordem não se encontra em intervenção.")

        ordem.descricao_intervencao = descricao_intervencao
        ordem.resultado = resultado
        ordem.estado = EstadoOrdem.CONCLUIDA
        self.repo.salvar(ordem)
        return ordem