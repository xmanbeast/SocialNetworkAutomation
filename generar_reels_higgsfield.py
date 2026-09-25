#!/usr/bin/env python3
"""
generar_reels_higgsfield.py
============================
Pipeline para generar Reels de fitness usando DeepSeek (guion) +
Higgsfield Seedance (text-to-video) + FFmpeg (subtítulos).

Flujo:
    1. DeepSeek (OpenRouter) → genera guion con 4-6 escenas
    2. Higgsfield Seedance → genera UN video a partir de un prompt unificado
    3. FFmpeg → quema subtítulos cronometrados en el video final

Dependencias:
    pip install higgsfield-client python-dotenv
    sudo apt install ffmpeg

Uso:
    python generar_reels_higgsfield.py
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# ── path para importar módulos locales ──────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from MassiveGenerator_trial import generar_guion_reel
from video_renderer import descargar_video


# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════

# Cargar credenciales de Higgsfield desde .env.local
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.local"))
HF_KEY = os.getenv("HF_KEY", "")

# OpenRouter (DeepSeek) — key del proyecto principal
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Modelos de Higgsfield disponibles para text-to-video
HIGGSFIELD_MODELS = {
    "seedance-2.0": {
        "endpoint": "bytedance/seedance-2.0/text-to-video",
        "duracion_max": 15,
        "resoluciones": ["480p", "720p", "1080p", "4k"],
        "modo": "leonardo",
    },
    "seedance-2.5": {
        "endpoint": "bytedance/seedance-2.5/text-to-video",
        "duracion_max": 30,
        "resoluciones": ["480p", "720p"],
        "extra_params": ["bitrate_mode", "output_format"],
        "modo": "leonardo",
    },
    "kling-2.6": {
        "endpoint": "kling-video/v2.6/pro/text-to-video",
        "duracion_max": 10,
        "two_clips": True,          # genera 2 clips y los concatena con FFmpeg
        "sound_param": True,        # usa "sound":"on"/"off" en vez de generate_audio
        "no_resolution": True,      # no acepta parámetro resolution
        "modo": "kling",
    },
}

# Fuente para subtítulos FFmpeg
FFMPEG_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Directorio de salida por defecto
OUTPUT_DIR_DEFAULT = "reels_output"
os.makedirs(OUTPUT_DIR_DEFAULT, exist_ok=True)
# ═══════════════════════════════════════════════════════════════════
# 1. HIGGSFIELD — GENERAR VIDEO TEXT-TO-VIDEO
# ═══════════════════════════════════════════════════════════════════

def higgsfield_texto_a_video(
    prompt: str,
    modelo: str = "seedance-2.5",
    duracion: int = 20,
    resolucion: str = "720p",
    aspect_ratio: str = "9:16",
    output_format: str = "mp4",
    generar_audio: bool = False,
    output_dir: str = OUTPUT_DIR_DEFAULT,
) -> str | None:
    """
    Genera un video con Higgsfield Seedance a partir de un prompt de texto.

    Args:
        prompt: Descripción en inglés de la escena a generar.
        modelo: "seedance-2.0" | "seedance-2.5".
        duracion: Duración en segundos (4-15 para 2.0, 4-30 para 2.5).
        resolucion: "480p" | "720p" | "1080p" | "4k".
        aspect_ratio: "16:9" | "9:16" | "1:1" | etc.
        output_format: "mp4" | "mov" (solo seedance-2.5).
        generar_audio: Si True, Higgsfield genera audio.
        output_dir: Carpeta de salida.

    Returns:
        Ruta local al video descargado, o None si falla.
    """
    if not HF_KEY or HF_KEY == "your-api-key-id:your-api-key-secret":
        print("❌ HF_KEY no configurada en .env.local")
        return None

    model_info = HIGGSFIELD_MODELS.get(modelo)
    if not model_info:
        print(f"❌ Modelo '{modelo}' no encontrado. Disponibles: {list(HIGGSFIELD_MODELS)}")
        return None

    endpoint = model_info["endpoint"]
    duracion = max(4, min(duracion, model_info["duracion_max"]))

    # Construir argumentos según el modelo
    arguments = {
        "prompt": prompt,
        "duration": duracion,
        "aspect_ratio": aspect_ratio,
    }

    # Kling usa "sound" en vez de "generate_audio"
    if model_info.get("sound_param"):
        arguments["sound"] = "on" if generar_audio else "off"
    else:
        arguments["generate_audio"] = generar_audio

    # Solo agregar resolution si el modelo lo soporta
    if not model_info.get("no_resolution"):
        arguments["resolution"] = resolucion

    if "extra_params" in model_info:
        if "output_format" in model_info["extra_params"]:
            arguments["output_format"] = output_format
        if "bitrate_mode" in model_info["extra_params"]:
            arguments["bitrate_mode"] = "high"

    print(f"\n{'='*60}")
    print(f"🎥 Generando video con Higgsfield ({modelo})")
    print(f"   Endpoint: {endpoint}")
    print(f"   Duración: {duracion}s | Res: {resolucion} | Aspecto: {aspect_ratio}")
    print(f"   Prompt: {prompt[:150]}...")
    print(f"{'='*60}")

    try:
        import higgsfield_client
        from higgsfield_client import (
            Completed, Failed, NSFW, Cancelled,
            Queued, InProgress, DONE_STATUSES,
        )

        t_inicio = time.time()

        # ── 1. Enviar request (retorna inmediatamente) ─────────
        print("   ⏳ Enviando request a Higgsfield...")
        controller = higgsfield_client.submit(endpoint, arguments=arguments)

        # ── 2. Polling manual con timeout largo ────────────────
        MAX_ESPERA = 1800       # 30 minutos máximo
        POLL_DELAY = 15         # consultar cada 15 segundos
        ultimo_estado = None

        print(f"   ⏳ Esperando generación (máx {MAX_ESPERA // 60} min, polling cada {POLL_DELAY}s)...")

        for status_update in controller.poll_request_status(delay=POLL_DELAY):
            elapsed = time.time() - t_inicio
            current = status_update.status if hasattr(status_update, 'status') else status_update

            # Mostrar progreso cuando cambia el estado
            if type(current) != type(ultimo_estado):
                minutos = elapsed / 60
                nombre_estado = type(current).__name__
                print(f"   📡 [{minutos:5.1f} min] Estado: {nombre_estado}")
                ultimo_estado = current

            # Timeout máximo
            if elapsed > MAX_ESPERA:
                print(f"   ⏰ Timeout: más de {MAX_ESPERA // 60} min esperando. Cancelando...")
                try:
                    controller.cancel()
                except Exception:
                    pass
                return None

            # ── Estados terminales con error ──────────────────
            if isinstance(current, Failed):
                print("   ❌ Generación FALLIDA (Failed)")
                # Intentar extraer info del error
                try:
                    err_result = controller.get()
                    error_detail = (
                        err_result.get("error")
                        or err_result.get("detail")
                        or err_result.get("message")
                        or json.dumps(err_result, indent=2)
                    )
                    print(f"   🔍 Detalle del error:\n{error_detail}")
                except Exception:
                    pass
                return None

            if isinstance(current, NSFW):
                print("   ❌ Contenido rechazado por filtro NSFW")
                return None

            if isinstance(current, Cancelled):
                print("   ❌ Request cancelado")
                return None

        # ── 3. Obtener resultado final ─────────────────────────
        result = controller.get()
        t_total = time.time() - t_inicio
        print(f"   ✅ Video listo en {t_total / 60:.1f} min")

        # Debug: mostrar estructura completa si no hay video
        video_url = result.get("video", {}).get("url", "")
        if not video_url:
            print("   ❌ No se encontró 'video.url' en la respuesta")
            print(f"   🔍 Respuesta completa:\n{json.dumps(result, indent=2, default=str)[:800]}")
            return None

        print(f"   📥 Descargando: {video_url[:100]}...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"higgsfield_{modelo}_{timestamp}.{output_format}"
        ruta_destino = os.path.join(output_dir, nombre)

        if descargar_video(video_url, ruta_destino):
            return ruta_destino
        return None

    except ImportError:
        print("   ❌ higgsfield_client no instalado: pip install higgsfield-client")
        return None
    except Exception as e:
        print(f"   ❌ Error en Higgsfield: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ═══════════════════════════════════════════════════════════════════
# 2. CONSTRUIR PROMPT UNIFICADO (todas las escenas → un solo prompt)
# ═══════════════════════════════════════════════════════════════════

def construir_prompt_unificado(escenas: list, personaje_base: str = "",
                               estilo_visual: str = "default") -> str:
    """
    Fusiona los temas de las escenas en un prompt CONCISO para Higgsfield.
    Evita concatenar prompts largos que disparan el costo del API.
    """
    subtemas = [e.get("subtitulo", "") for e in escenas if e.get("subtitulo")]
    duracion_total = sum(e.get("duracion_seg", 5) for e in escenas)

    # Extraer solo la esencia: una frase corta por escena
    ideas = ", ".join(subtemas[:3])  # máx 3 ideas clave
    if not ideas:
        ideas = "fitness training techniques"

    # Prompt compacto: personaje + tema + estilo
    personaje = f"{personaje_base}. " if personaje_base else ""
    prompt = (
        f"9:16 vertical fitness video, {duracion_total}s. "
        f"{personaje}{ideas}. "
        f"Cinematic gym lighting, smooth camera movement, clean background. "
        f"No text or watermarks."
    )

    chars = len(prompt)
    print(f"\n📝 Prompt unificado ({chars} chars): {prompt[:200]}...")
    return prompt
# ═══════════════════════════════════════════════════════════════════
# 2.5 FFMPEG — CONCATENAR VIDEOS
# ═══════════════════════════════════════════════════════════════════

def concatenar_videos_ffmpeg(rutas_clips: list, output_path: str) -> str | None:
    """
    Une múltiples videos con FFmpeg usando el demuxer concat.
    """
    if len(rutas_clips) < 2:
        print("⚠️  Se necesitan al menos 2 clips para concatenar.")
        if rutas_clips:
            subprocess.run(["cp", rutas_clips[0], output_path], check=False)
            return output_path
        return None

    # Crear archivo de lista para FFmpeg concat demuxer
    list_path = output_path + ".txt"
    with open(list_path, "w") as f:
        for ruta in rutas_clips:
            f.write(f"file '{os.path.abspath(ruta)}'\n")

    print(f"\n🔗 Concatenando {len(rutas_clips)} clips con FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path,
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        os.remove(list_path)

        if res.returncode != 0:
            print(f"   ❌ FFmpeg concat falló: {res.stderr[-300:]}")
            return None

        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"   ✅ Video concatenado: {output_path} ({size_mb:.1f} MB)")
            return output_path
        return None

    except Exception as e:
        print(f"   ❌ Error concatenando: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# 3. FFMPEG — QUEMAR SUBTÍTULOS CRONOMETRADOS
# ═══════════════════════════════════════════════════════════════════

def quemar_subtitulos_ffmpeg(
    video_path: str,
    escenas: list,
    output_path: str,
    font_path: str = FFMPEG_FONT,
    font_size: int = 56,
) -> str | None:
    """
    Usa FFmpeg drawtext para quemar subtítulos temporizados en el video.

    Cada escena define:
        - subtitulo: texto a mostrar
        - duracion_seg: cuánto dura
        - tipo_escena: 'hook' | 'contexto' | 'payoff' | 'cta'
        - orden: posición en la secuencia
    """
    if not os.path.exists(video_path):
        print(f"❌ Video no encontrado: {video_path}")
        return None

    # Buscar fuente si la principal no existe
    if not os.path.exists(font_path):
        alternativas = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        font_path = next((f for f in alternativas if os.path.exists(f)), None)
        if not font_path:
            print("❌ No se encontró fuente TTF. Instala fonts-dejavu-core o liberation-fonts")
            return None
        print(f"   ✅ Fuente: {font_path}")

    # ── Calcular timestamps ──────────────────────────────────────
    tiempo = 0.0
    segmentos = []  # (start, end, texto, tipo)

    for escena in sorted(escenas, key=lambda e: e.get("orden", 0)):
        duracion = escena.get("duracion_seg", 5)
        subtitulo = escena.get("subtitulo", "")
        tipo = escena.get("tipo_escena", "contexto")

        # Permitir start_seg manual (ej: modo kling con timestamps IA)
        if "start_seg" in escena:
            tiempo = escena["start_seg"]

        if subtitulo:
            segmentos.append((tiempo, tiempo + duracion, subtitulo, tipo))
        tiempo += duracion

    if not segmentos:
        print("⚠️  Sin subtítulos. Copiando video...")
        subprocess.run(["cp", video_path, output_path], check=False)
        return output_path

    print(f"\n🎬 Quemando {len(segmentos)} subtítulos con FFmpeg ({tiempo:.0f}s)...")
    for inicio, fin, sub, tipo in segmentos:
        print(f"   [{inicio:5.1f}s→{fin:5.1f}s] [{tipo}] {sub[:60]}")

    # ── Colores por tipo ─────────────────────────────────────────
    COLORES = {
        "hook":     "0xFFD700",
        "cta":      "0x00FF88",
        "contexto": "0xFFFFFF",
        "payoff":   "0xFFFFFF",
    }
    BORDE = "0x000000"
    GROSOR = 3
    BOX_COLOR = "black@0.4"    # caja semitransparente
    BOX_BORDER = 12            # padding de la caja

    # ── Colores por tipo ─────────────────────────────────────────
    COLORES = {
        "hook":     "0xFFD700",
        "cta":      "0x00FF88",
        "contexto": "0xFFFFFF",
        "payoff":   "0xFFFFFF",
    }
    BORDE = "0x000000"
    GROSOR = 3
    BOX_COLOR = "black@0.4"
    BOX_BORDER = 12

    # ── Escapar texto para FFmpeg drawtext ───────────────────
    def _escape(texto: str) -> str:
        """Convierte caracteres peligrosos en alternativas Unicode seguras
           que se ven igual pero no rompen el parser de FFmpeg."""
        return (texto
                .replace("\\", "\\\\")       # backslash
                .replace(":", "\\:")         # separador de filtros FFmpeg
                .replace("'", "\u2019")      # ' → ’ (right single quote, seguro)
                .replace('"', "\u201c")      # " → " (left double quote, preventivo)
                .replace("%", "\\%")         # interpretado por FFmpeg
                .replace("{", "\\{")         # special
                .replace("}", "\\}"))        # special

    # ── Dividir texto en multiples lineas (word-wrap con presupuesto) ──
    def _wrap_text(texto: str, max_chars: int = 20) -> str:
        """Word-wrap: cada linea <= max_chars, partiendo en espacios.
           Garantiza que ninguna linea exceda el presupuesto de ancho."""
        palabras = texto.split()
        n = len(texto)

        # Corto → una sola linea
        if n <= max_chars:
            return texto

        if not palabras:
            return texto

        lineas = []
        actual = []
        chars = 0

        for p in palabras:
            # Si una palabra sola excede el presupuesto, forzarla igual
            if len(p) > max_chars and not actual:
                lineas.append(p)
                continue

            espacio = 1 if chars > 0 else 0
            if chars + espacio + len(p) <= max_chars:
                actual.append(p)
                chars += espacio + len(p)
            else:
                if actual:
                    lineas.append(" ".join(actual))
                actual = [p]
                chars = len(p)

        if actual:
            lineas.append(" ".join(actual))

        # Maximo 3 lineas; si hay mas, fusionar las ultimas
        if len(lineas) > 3:
            lineas = lineas[:2] + [" ".join(lineas[2:])]

        return "\n".join(lineas)

    # ── Construir filtros drawtext ──────────────────────────
    filtros = []
    for inicio, fin, subtitulo, tipo in segmentos:
        color = COLORES.get(tipo, "0xFFFFFF")
        texto_escapado = _escape(subtitulo)
        texto_wrapped = _wrap_text(texto_escapado)
        t = texto_wrapped

        # Fontsize basado en la LINEA MAS LARGA
        lineas = texto_wrapped.replace("\\n", "\n").split("\n")
        num_lineas = len(lineas)
        max_ch = max(len(L) for L in lineas) if lineas else 10
        MAX_W = 520               # ancho seguro en px (~12% margen del video 1080px)
        RATIO = 0.65             # ratio conservador chars→px para DejaVu Sans Bold
        fs_calc = MAX_W / (max_ch * RATIO) if max_ch > 0 else font_size
        factor = {"hook": 1.15, "cta": 1.05}.get(tipo, 1.0)
        fs = int(min(fs_calc * factor, font_size * 1.2))
        fs = max(fs, 52 if max_ch <= 15 else 40 if max_ch <= 22 else 28)

        # Posicion Y dinamica: mas arriba si hay multiples lineas
        if num_lineas >= 3:
            y_pos = "h*0.66"
        elif num_lineas == 2:
            y_pos = "h*0.70"
        else:
            y_pos = "h*0.76"

        filtro = (
            f"drawtext=fontfile='{font_path}':"
            f"text='{t}':"
            f"fontsize={fs}:"
            f"fontcolor={color}:"
            f"bordercolor={BORDE}:"
            f"borderw={GROSOR}:"
            f"box=1:"
            f"boxcolor={BOX_COLOR}:"
            f"boxborderw={BOX_BORDER}:"
            f"fix_bounds=1:"
            f"x=(w-text_w)/2:"
            f"y={y_pos}:"
            f"line_spacing=8:"
            f"enable='between(t,{inicio:.2f},{fin:.2f})'"
        )
        filtros.append(filtro)

    filter_complex = ",".join(filtros)

    # ── Ejecutar FFmpeg ──────────────────────────────────────────
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", filter_complex,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path,
    ]

    print(f"   🔧 Ejecutando FFmpeg (filtros: {len(filtros)} drawtext)...")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            print(f"   ❌ FFmpeg falló (código {res.returncode}):")
            print(f"   {res.stderr[-400:]}")
            return None

        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"   ✅ Video con subtítulos: {output_path} ({size_mb:.1f} MB)")
            return output_path
        else:
            print("   ❌ FFmpeg no generó archivo de salida")
            return None

    except subprocess.TimeoutExpired:
        print("   ❌ Timeout (>10 min)")
        return None
    except FileNotFoundError:
        print("   ❌ FFmpeg no instalado: sudo apt install ffmpeg")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════
# 4. PIPELINE COMPLETO HIGGSFIELD
# ═══════════════════════════════════════════════════════════════════

def pipeline_reel_higgsfield(
    tema: str,
    genero: str = "libre",
    estilo_visual: str = "default",
    modelo_higgsfield: str = "seedance-2.5",
    resolucion: str = "720p",
    output_dir: str = OUTPUT_DIR_DEFAULT,
    generar_audio: bool = False,
    font_size: int = 56,
    musica_path: str | None = None,
) -> str | None:
    """
    Pipeline: DeepSeek (guion) → Higgsfield (video) → FFmpeg (subtítulos).
    Soporta modo Leonardo (1 video) y Kling (2 clips concatenados).
    """
    os.makedirs(output_dir, exist_ok=True)
    model_info = HIGGSFIELD_MODELS.get(modelo_higgsfield, {})
    modo = model_info.get("modo", "leonardo")

    print(f"\n{'='*70}")
    print(f"🎬 PIPELINE REEL HIGGSFIELD: {tema}")
    print(f"   Modo: {modo} | Modelo: {modelo_higgsfield} | Género: {genero}")
    print(f"{'='*70}")

    # ── 1. Generar guion con DeepSeek ───────────────────────────
    print(f"\n📝 Generando guion con DeepSeek (modo={modo})...")
    guion = generar_guion_reel(tema, genero=genero, estilo_visual=estilo_visual, modo=modo)

    if not guion:
        print("❌ No se pudo generar el guion.")
        return None

    personaje_base = guion.get("personaje_base", "")
    caption = guion.get("caption", "")
    nombre_limpio = tema[:30].replace(" ", "_").replace("?", "").replace("¿", "")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
# ═══════════════════════════════════════════════════════════════
    # FLUJO KLING: N clips de 10s → concatenar → subtítulos
    # ═══════════════════════════════════════════════════════════════
    if modo == "kling" and "bloques" in guion:
        bloques = guion["bloques"]
        print(f"   ✅ Guion Kling: {len(bloques)} bloques")

        # ── Generar 2 clips ─────────────────────────────────
        rutas_clips = []
        for i, bloque in enumerate(bloques):
            prompt = bloque.get("prompt_video", f"fitness scene part {i+1}")
            print(f"\n   🎬 Clip {i+1}/{len(bloques)} (10s)...")
            clip_path = higgsfield_texto_a_video(
                prompt=prompt, modelo=modelo_higgsfield,
                duracion=10, resolucion=resolucion, aspect_ratio="9:16",
                generar_audio=generar_audio, output_dir=output_dir,
            )
            if not clip_path:
                print(f"   ❌ Falló clip {i+1}")
                return None
            rutas_clips.append(clip_path)

        # ── Concatenar ──────────────────────────────────────
        concat_path = os.path.join(output_dir, f"concat_{nombre_limpio}_{ts}.mp4")
        video_path = concatenar_videos_ffmpeg(rutas_clips, concat_path)
        if not video_path:
            return None

        # ── Convertir bloques a escenas para FFmpeg ─────────
        # Recolectar TODOS los subtítulos con offset por bloque
        CLIP_DUR = 10  # cada clip Kling dura 10s
        subs_planos = []
        for i, bloque in enumerate(bloques):
            offset = i * CLIP_DUR
            for sub in bloque.get("subtitulos", []):
                sub_corregido = dict(sub)
                sub_corregido["timestamp_seg"] = sub.get("timestamp_seg", 0) + offset
                subs_planos.append(sub_corregido)

        # Ordenar por timestamp y calcular duración real entre cada par
        subs_planos.sort(key=lambda s: s.get("timestamp_seg", 0))
        VIDEO_DUR = len(bloques) * CLIP_DUR  # dinámico: 2 bloques=20s, 3=30s, etc.

        escenas_ffmpeg = []
        for idx, sub in enumerate(subs_planos):
            t_inicio = sub.get("timestamp_seg", 0)

            # Duración = hasta el siguiente subtítulo (o hasta el final del video)
            if idx + 1 < len(subs_planos):
                t_fin = subs_planos[idx + 1].get("timestamp_seg", VIDEO_DUR)
            else:
                t_fin = VIDEO_DUR

            duracion_real = max(t_fin - t_inicio, 1.0)  # mínimo 1s

            escenas_ffmpeg.append({
                "orden": idx + 1,
                "subtitulo": sub.get("texto", ""),
                "start_seg": t_inicio,
                "duracion_seg": round(duracion_real, 1),
                "tipo_escena": "hook" if idx < len(subs_planos) // 2 else "payoff",
            })

        # ── Quemar subtítulos ───────────────────────────────
        print(f"\n🔤 Quemando subtítulos...")
        output_path = os.path.join(output_dir, f"reel_hf_{nombre_limpio}_{ts}.mp4")
        reel_final = quemar_subtitulos_ffmpeg(
            video_path=video_path, escenas=escenas_ffmpeg,
            output_path=output_path, font_size=font_size,
        )

    # ═══════════════════════════════════════════════════════════════
    # FLUJO LEONARDO/SEEDANCE: 1 video unificado → subtítulos
    # ═══════════════════════════════════════════════════════════════
    else:
        escenas = guion.get("escenas", [])
        if not escenas:
            print("❌ El guion no tiene escenas.")
            return None

        duracion_total = sum(e.get("duracion_seg", 5) for e in escenas)
        print(f"   ✅ Guion Leonardo: {len(escenas)} escenas, {duracion_total:.0f}s")

        prompt_unificado = construir_prompt_unificado(escenas, personaje_base, estilo_visual)
        duracion_max = model_info.get("duracion_max", 30)
        duracion_ajustada = min(int(duracion_total), duracion_max)

        video_path = higgsfield_texto_a_video(
            prompt=prompt_unificado, modelo=modelo_higgsfield,
            duracion=duracion_ajustada, resolucion=resolucion, aspect_ratio="9:16",
            generar_audio=generar_audio, output_dir=output_dir,
        )

        if not video_path:
            print("❌ Falló la generación del video.")
            return None

        print(f"\n🔤 Quemando subtítulos...")
        output_path = os.path.join(output_dir, f"reel_hf_{nombre_limpio}_{ts}.mp4")
        reel_final = quemar_subtitulos_ffmpeg(
            video_path=video_path, escenas=escenas,
            output_path=output_path, font_size=font_size,
        )

    # ── Común: guardar metadatos ──────────────────────────────────
    if not reel_final:
        print("❌ Falló el quemado de subtítulos.")
        return None

    guion_path = output_path.replace(".mp4", "_guion.json")
    with open(guion_path, "w", encoding="utf-8") as f:
        json.dump({
            "tema": tema, "genero": genero,
            "estilo_visual": estilo_visual,
            "modelo_higgsfield": modelo_higgsfield,
            "modo": modo, "personaje_base": personaje_base,
            "caption": caption, "guion": guion,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2, ensure_ascii=False)

    caption_path = output_path.replace(".mp4", "_caption.txt")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption)

    print(f"📄 Metadatos: {guion_path}")
    print(f"📄 Caption: {caption_path}")
    print(f"\n{'='*70}")
    print(f"🏁 REEL COMPLETADO: {reel_final}")
    print(f"{'='*70}")

    # ── Música opcional ─────────────────────────────────────────
    if musica_path and os.path.exists(musica_path):
        nombre_con_musica = output_path.replace(".mp4", "_con_musica.mp4")
        reel_con_musica = agregar_musica_ffmpeg(reel_final, musica_path, nombre_con_musica)
        if reel_con_musica:
            return reel_con_musica

    return reel_final
# ═══════════════════════════════════════════════════════════════════
def agregar_musica_ffmpeg(
    video_path: str,
    musica_path: str,
    output_path: str,
    volumen: float = 0.25,
) -> str | None:
    """
    Mezcla música de fondo al video usando FFmpeg.
    Si la música es más corta que el video, la loopa.
    Si el video no tiene audio, solo agrega la música.

    Args:
        video_path: Video sin música.
        musica_path: Archivo de música (.mp3, .wav, etc).
        output_path: Video con música.
        volumen: Volumen de la música (0.0 a 1.0).

    Returns:
        output_path si éxito, None si falla.
    """
    if not os.path.exists(musica_path):
        print(f"⚠️  Música no encontrada: {musica_path}")
        return None

    print(f"\n🎵 Agregando música: {os.path.basename(musica_path)} (vol: {volumen})")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", musica_path,
        "-filter_complex",
        f"[1:a]volume={volumen},aloop=loop=-1:size=2e9[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]",
        "-map", "0:v",
        "-map", "[outa]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            # Si falla, intentar sin audio original (video puede no tener pista de audio)
            print("   ⚠️  Falló mix con audio original. Intentando solo música...")
            cmd2 = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-stream_loop", "-1", "-i", musica_path,
                "-filter_complex", f"[1:a]volume={volumen}[bgm]",
                "-map", "0:v", "-map", "[bgm]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", output_path,
            ]
            res2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
            if res2.returncode != 0:
                print(f"   ❌ FFmpeg música falló: {res2.stderr[-300:]}")
                return None

        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"   ✅ Video con música: {output_path} ({size_mb:.1f} MB)")
            return output_path
        return None

    except Exception as e:
        print(f"   ❌ Error música: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
# 5. FFMPEG — AGREGAR MÚSICA DE FONDO
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ╔══════════════════════════════════════════════════════════════╗
    # ║ CONFIGURACIÓN — edita esto para cada lote                    ║
    # ╚══════════════════════════════════════════════════════════════╝

    temas = [
   # 4. Sueño y recuperación muscular
    "Sueño y testosterona: Cómo dormir mejor aumenta tu fuerza, recuperación y crecimiento muscular natural",
    ]

    GENERO = "male"
    ESTILO = "clay_animation"
    MODELO_HIGGSFIELD = "kling-2.6"
    RESOLUCION = "720p"
    GENERAR_AUDIO = False
    FONT_SIZE = 56
    MUSICA ="assets/music/kntrawater.mp3"  #None  # Ej: "assets/music/mi_cancion.mp3" o None para sin música
    OUTPUT_DIR = "reels_output"

    # ╔══════════════════════════════════════════════════════════════╗
    # ║ EJECUCIÓN                                                     ║
    # ╚══════════════════════════════════════════════════════════════╝

    if HF_KEY == "your-api-key-id:your-api-key-secret":
        print("=" * 60)
        print("⚠️  HF_KEY NO CONFIGURADA")
        print("=" * 60)
        print("1. Ve a https://console.higgsfield.ai y crea una API key")
        print("2. Edita .env.local con tu key: HF_KEY=tu-key-id:tu-key-secret")
        print("=" * 60)
        sys.exit(1)

    for i, tema in enumerate(temas, 1):
        print(f"\n{'#'*70}")
        print(f"# REEL {i}/{len(temas)}")
        print(f"{'#'*70}")

        resultado = pipeline_reel_higgsfield(
            tema=tema,
            genero=GENERO,
            estilo_visual=ESTILO,
            modelo_higgsfield=MODELO_HIGGSFIELD,
            resolucion=RESOLUCION,
            output_dir=OUTPUT_DIR,
            generar_audio=GENERAR_AUDIO,
            font_size=FONT_SIZE,
            musica_path=MUSICA,
        )

        if resultado:
            print(f"\n🎉 Reel {i} completado: {resultado}")
        else:
            print(f"\n❌ Reel {i} falló: {tema}")

    print(f"\n🏁 Todos los Reels procesados. Revisa la carpeta '{OUTPUT_DIR}/'")
