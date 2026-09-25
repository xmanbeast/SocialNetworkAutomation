#!/usr/bin/env python3
"""
generar_reels.py
================
Script de entrada para generar Reels de fitness automáticamente.

Uso:
    python generar_reels.py

Configura los temas y el género del personaje abajo en __main__.
"""

import sys
import os

# Añadir el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_renderer import pipeline_reel, pipeline_reel_imagenes


if __name__ == "__main__":
    # ==========================================
    # CONFIGURACIÓN — edita esto para cada lote
    # ==========================================

    # Temas para los Reels (uno por cada video)
    temas = [
        "La verdad detrás de la creatina para que nos sirve has un resumen que no sea corto pero no tan largo para el caption de instagram",
    ]

    # Género del personaje:
    GENERO = "male"

    # MODO de generación:
    #   "imagenes" → rápido, imágenes + Ken Burns (recomendado, ~2 min)
    #   "video"    → AI video text-to-video (experimental, ~30 min)
    MODO = "imagenes"

    # Estilo visual: default , clay animation
    ESTILO = "disney_cartoon"

    # Modelo de video — solo aplica si MODO = "video"
    # MODELO_VIDEO = "motion_2.0-fast"
    MODELO_VIDEO = "kling-3.0"
    # Música de fondo (opcional)
    MUSICA = None

    # Carpeta de salida
    OUTPUT_DIR = "reels_output"

    # ==========================================
    # EJECUCIÓN
    # ==========================================
    for i, tema in enumerate(temas, 1):
        print(f"\n{'='*60}")
        print(f"🎬 REEL {i}/{len(temas)} ({MODO})")
        print(f"{'='*60}")

        if MODO == "imagenes":
            resultado = pipeline_reel_imagenes(
                tema=tema,
                genero=GENERO,
                estilo_visual=ESTILO,
                musica_path=MUSICA,
                output_dir=OUTPUT_DIR,
            )
        else:
            resultado = pipeline_reel(
                tema=tema,
                genero=GENERO,
                estilo_visual=ESTILO,
                modelo_video=MODELO_VIDEO,
                musica_path=MUSICA,
                output_dir=OUTPUT_DIR,
            )

        if resultado:
            print(f"\n🎉 Reel {i} completado: {resultado}")
        else:
            print(f"\n❌ Reel {i} falló: {tema}")

    print(f"\n🏁 Todos los Reels procesados. Revisa la carpeta '{OUTPUT_DIR}/'")