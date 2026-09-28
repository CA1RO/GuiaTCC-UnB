"""
Etapa 1 do Pipeline — Ingestão de Dados (Bronze)

Responsável por:
- Download de dados abertos da UnB (CSV via API CKAN)
- Download de currículos Lattes (XML do CNPq)
- Armazenamento bruto (imutável) no MinIO (bucket bronze)

Frequência: Semanal (domingos às 02h) ou sob demanda.
Conforme aba "5 Pipeline", linha 1.
"""

import hashlib
import io
import logging
from datetime import datetime

import requests
from minio import Minio

from src.config import settings

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    """Cria cliente MinIO."""
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        secure=settings.minio_secure,
        region="us-east-1",
    )


def garantir_buckets() -> None:
    """Cria os buckets bronze e silver se ainda não existirem."""
    client = get_minio_client()
    for bucket in (settings.minio_bucket_bronze, settings.minio_bucket_silver):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("Bucket criado: %s", bucket)


def ingerir_dados_abertos_unb(url: str, nome_arquivo: str) -> dict:
    """
    Baixa dados abertos da UnB e armazena no bucket bronze.

    Args:
        url: URL do CSV/JSON do portal de dados abertos.
        nome_arquivo: Nome para salvar no MinIO.

    Returns:
        Metadados da ingestão (hash, tamanho, timestamp).
    """
    logger.info(f"Iniciando download de dados abertos: {url}")

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    conteudo = response.content
    md5_hash = hashlib.md5(conteudo).hexdigest()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    client = get_minio_client()
    object_name = f"dados_abertos/{timestamp}/{nome_arquivo}"

    client.put_object(
        settings.minio_bucket_bronze,
        object_name,
        io.BytesIO(conteudo),
        length=len(conteudo),
        content_type="application/octet-stream",
    )

    metadata = {
        "object_name": object_name,
        "size_bytes": len(conteudo),
        "md5": md5_hash,
        "timestamp": timestamp,
        "source_url": url,
    }
    logger.info(f"Dados armazenados em bronze/{object_name} ({len(conteudo)} bytes)")
    return metadata


def ingerir_curriculo_lattes(xml_content: bytes, id_lattes: str) -> dict:
    """
    Armazena currículo Lattes bruto (XML) no bucket bronze.

    Args:
        xml_content: Conteúdo XML do currículo.
        id_lattes: Identificador Lattes do docente.

    Returns:
        Metadados da ingestão.
    """
    md5_hash = hashlib.md5(xml_content).hexdigest()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    client = get_minio_client()
    object_name = f"lattes/{timestamp}/{id_lattes}.xml"

    client.put_object(
        settings.minio_bucket_bronze,
        object_name,
        io.BytesIO(xml_content),
        length=len(xml_content),
        content_type="application/xml",
    )

    metadata = {
        "object_name": object_name,
        "size_bytes": len(xml_content),
        "md5": md5_hash,
        "id_lattes": id_lattes,
        "timestamp": timestamp,
    }
    logger.info(f"Currículo Lattes {id_lattes} armazenado em bronze/{object_name}")
    return metadata
