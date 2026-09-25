"""
video_renderer.py
=================
Renderiza Reels de fitness a partir de un guion y clips generados por IA.

Dependencias: moviepy, requests
Instalar: pip install moviepy requests
"""

import os
import time
import json
import requests
from moviepy import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    AudioFileClip,
    vfx,
)


# ==========================================
# CONFIGURACIÓN
# ==========================================
LEONARDO_API_KEY = "173dfb1a-5233-4ece-bb27-1fa9eeeb091c"

# Resolución vertical para Reels (9:16)
REEL_WIDTH = 1080
REEL_HEIGHT = 1920


# ==========================================
# GENERACIÓN DE VIDEO CON LEONARDO (TEXT-TO-VIDEO)
# ==========================================
def leonardo_texto_a_video(prompt_video, duracion_estimada=6, modelo="motion_2.0-fast", estilo_visual=None):
    """
    Genera un clip de video a partir de texto usando Leonardo text-to-video.

    Args:
        prompt_video: descripción en inglés de la escena
        duracion_estimada: duración deseada en segundos (referencia)
        modelo: modelo de video a usar
        estilo_visual: clave de ESTILOS_VISUALES (ej: "clay_animation", "cyberpunk")

    Returns:
        URL de descarga del video generado, o None si falla
    """
    # Inyectar estilo visual directamente (DeepSeek a veces lo ignora)
    if estilo_visual and estilo_visual != "default":
        from MassiveGenerator_trial import ESTILOS_VISUALES
        estilo_desc = ESTILOS_VISUALES.get(estilo_visual, "")
        if estilo_desc:
            prompt_video = f"{estilo_desc}: {prompt_video}"
            print(f"   🎨 Estilo inyectado: {estilo_visual}")
    # Endpoint v2 — mismo que imágenes, soporta selección de modelo
    url_base = "https://cloud.leonardo.ai/api/rest/v2/generations"
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    # Payload formato v2 (igual que generación de imágenes)
    payload = {
        "model": modelo,
        "parameters": {
            "prompt": prompt_video,
            "negative_prompt": (
                "deformed anatomy, twisted body, extra limbs, fused fingers, "
                "ugly, distorted face, bad proportions, disfigured, watermark, text, "
                "blurry, low quality, head out of frame, unnatural pose"
            ),
            "height": 1280,
            "width": 720,
            "frameInterpolation": True,
            "promptEnhance": True,
        },
        "public": False,
    }

    print(f"   🎥 Generando video ({modelo})...")
    print(f"      Prompt: {prompt_video[:120]}...")

    response = requests.post(url_base, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"   ❌ Error al iniciar generación de video: {response.text[:300]}")
        return None

    resp_data = response.json()

    # Extraer generationId con regex — funciona con cualquier modelo
    import re
    resp_str = json.dumps(resp_data)
    match = re.search(r'"generationId"\s*:\s*"([a-f0-9-]{36})"', resp_str)
    generation_id = match.group(1) if match else None

    # Fallback: buscar por "id"
    if not generation_id:
        match = re.search(r'"id"\s*:\s*"([a-f0-9-]{36})"', resp_str)
        generation_id = match.group(1) if match else None

    if not generation_id:
        print(f"   🔍 No se encontró generationId. Top keys: {list(resp_data.keys()) if isinstance(resp_data, dict) else f'list({len(resp_data)} items)'}")
        print(f"   🔍 Respuesta: {resp_str[:300]}")
        return None

    print(f"   ⏳ Generando video (ID: {generation_id})...")

    # Polling para obtener el video generado
    url_status = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
    max_intentos = 45  # 450s / 7.5 min — text-to-video 720p puede tardar bastante
    import json as _json

    for intento in range(max_intentos):
        time.sleep(10)
        res_status = requests.get(url_status, headers=headers)

        if res_status.status_code != 200:
            print(f"   ⚠️  Error en polling (intento {intento + 1}): {res_status.status_code}")
            continue

        data = res_status.json()
        gen = data.get("generations_by_pk", {})

        # Debug completo en el intento 1 para ver estructura real
        if intento == 0:
            print(f"   🔍 Estructura generations_by_pk: { {k: type(v).__name__ for k, v in gen.items()} }")

        # Buscar video en TODAS las variantes posibles del campo
        generated = (
            gen.get("generated_videos")
            or gen.get("generated_images")
            or data.get("motionVideoGenerationJob", {}).get("generated_videos")
            or data.get("generated_videos")
            or data.get("generated_images")
            or []
        )

        if generated:
            item = generated[0]
            # motionMP4URL es el video real, url es solo la imagen estática
            video_url = (
                item.get("motionMP4URL")
                or item.get("video_url")
                or item.get("download_url")
                or item.get("mp4_url")
                or item.get("url")
            )
            if video_url:
                print(f"   ✅ Video listo: {video_url[:80]}...")
                return video_url
            else:
                if intento == 0:
                    print(f"   🔍 Item sin URL, claves disponibles: {list(item.keys())}")

        # Status
        status = (
            gen.get("status")
            or data.get("motionVideoGenerationJob", {}).get("status")
            or data.get("status", "")
        )

        if status and status.upper() in ("FAILED", "ERROR", "CANCELLED"):
            print(f"   ❌ Generación fallida: {status}")
            print(f"   🔍 Respuesta: {_json.dumps(data, indent=2)[:600]}")
            return None

        print(f"   ⏳ Intento {intento + 1}/{max_intentos} — status: {status or 'PENDING'}")

    print(f"   ❌ Timeout: el video no se generó en {max_intentos * 10}s")
    return None


def descargar_video(url_video, ruta_destino):
    """Descarga un video desde una URL a un archivo local."""
    print(f"   📥 Descargando video...")
    try:
        response = requests.get(url_video, stream=True, timeout=120)

        if response.status_code != 200:
            print(f"   ❌ Error descargando video: HTTP {response.status_code}")
            return False

        with open(ruta_destino, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        size_mb = os.path.getsize(ruta_destino) / (1024 * 1024)
        print(f"   ✅ Video descargado: {ruta_destino} ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"   ❌ Excepción descargando video: {e}")
        return False
# ==========================================
# MONTAJE DEL REEL CON MOVIEPY
# ==========================================
def montar_reel(
    rutas_clips, escenas, output_path="reel_final.mp4",
    musica_path=None, font_size=72, font_color="white",
    stroke_color="black", stroke_width=3,
):
    """Monta un Reel uniendo clips y superponiendo subtítulos sincronizados."""
    if not rutas_clips:
        print("❌ No hay clips para montar el Reel.")
        return None

    print(f"\n🎬 Montando Reel con {len(rutas_clips)} clips...")
    clips_procesados = []

    for i, (ruta_clip, escena) in enumerate(zip(rutas_clips, escenas)):
        duracion = escena.get("duracion_seg", 5)
        subtitulo = escena.get("subtitulo", "")
        tipo = escena.get("tipo_escena", "payoff")
        print(f"   🎞️  Clip {i+1}: [{tipo}] {duracion}s — \"{subtitulo[:50]}...\"")

        clip = VideoFileClip(ruta_clip)

        # Ajustar a 9:16 (centrado con crop)
        clip_w, clip_h = clip.size
        if clip_w / clip_h > 9 / 16:
            new_w = int(clip_h * 9 / 16)
            clip = clip.cropped(x_center=clip_w // 2, width=new_w, height=clip_h)
        elif clip_w / clip_h < 9 / 16:
            new_h = int(clip_w * 16 / 9)
            clip = clip.cropped(x1=0, y1=(clip_h - new_h) // 2, width=clip_w, height=new_h)

        clip = clip.resized(width=REEL_WIDTH, height=REEL_HEIGHT)

        # Ajustar duración (moviepy v2: loop via vfx.Loop)
        if clip.duration < duracion:
            clip = clip.with_effects([vfx.Loop(duration=duracion)])
        elif clip.duration > duracion:
            clip = clip.subclipped(0, duracion)

        # Subtítulo
        if subtitulo:
            txt_clip = _crear_subtitulo(
                subtitulo, duracion, tipo, font_size=font_size,
                font_color=font_color, stroke_color=stroke_color,
                stroke_width=stroke_width,
            )
            txt_clip = txt_clip.with_position(("center", int(REEL_HEIGHT * 0.72)))
            clip = CompositeVideoClip([clip, txt_clip])

        clips_procesados.append(clip)

    reel = concatenate_videoclips(clips_procesados, method="compose")

    # Música
    if musica_path and os.path.exists(musica_path):
        print(f"   🎵 Añadiendo música: {musica_path}")
        musica = AudioFileClip(musica_path)
        musica = musica.subclipped(0, min(musica.duration, reel.duration))
        if musica.duration < reel.duration:
            musica = musica.with_effects([vfx.Loop(duration=reel.duration)])
        musica = musica.with_effects([vfx.MultiplyVolume(0.3)])
        reel = reel.with_audio(musica)

    # Exportar con audio solo si hay música
    tiene_audio = musica_path and os.path.exists(musica_path)
    print(f"   💾 Exportando Reel a {output_path}...")
    reel.write_videofile(
        output_path, fps=24, codec="libx264",
        bitrate="5000k", preset="medium", threads=4,
        audio=bool(tiene_audio),
    )

    # Liberar recursos (ignorar errores de cierre)
    try:
        for c in clips_procesados:
            c.close()
        reel.close()
    except Exception:
        pass

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Reel generado: {output_path} ({size_mb:.1f} MB)")
    return output_path


def _crear_subtitulo(texto, duracion, tipo_escena, font_size=72,
                     font_color="white", stroke_color="black", stroke_width=3):
    """Crea clip de texto con estilo según tipo de escena."""
    max_width = REEL_WIDTH - 120
    FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    if tipo_escena == "hook":
        fs = int(font_size * 1.3)
        color = "#FFD700"
    elif tipo_escena == "cta":
        fs = int(font_size * 1.15)
        color = "#00FF88"
    else:
        fs = font_size
        color = font_color

    txt = TextClip(
        text=texto, font=FUENTE, font_size=fs,
        color=color, stroke_color=stroke_color, stroke_width=stroke_width,
        size=(max_width, None), method="caption", text_align="center",
    )
    txt = txt.with_duration(duracion)
    txt = txt.with_effects([vfx.FadeIn(min(0.3, duracion * 0.15))])
    return txt


# ==========================================
# PIPELINE COMPLETO: TEMA → REEL
# ==========================================
def pipeline_reel(tema, genero="libre", estilo_visual="default", modelo_video="motion_2.0-fast", musica_path=None, output_dir="reels_output"):
    """Orquesta todo: guion → clips → Reel final."""
    from MassiveGenerator_trial import generar_guion_reel

    os.makedirs(output_dir, exist_ok=True)
    print("=" * 50)
    print(f"🎬 PIPELINE REEL: {tema}")
    print(f"   Estilo: {estilo_visual} | Género: {genero} | Modelo: {modelo_video}")
    print("=" * 50)

    guion = generar_guion_reel(tema, genero=genero, estilo_visual=estilo_visual)
    if not guion or "escenas" not in guion:
        print("❌ No se pudo generar el guion. Abortando.")
        return None

    escenas = guion["escenas"]
    print(f"\n📋 Guion: {len(escenas)} escenas, personaje: {guion.get('personaje_base', 'N/A')[:60]}...")

    # Generar video para cada escena
    rutas_clips = []
    for i, escena in enumerate(escenas):
        prompt_video = escena.get("prompt_video", "")
        if not prompt_video:
            continue
        print(f"\n--- Escena {i+1}/{len(escenas)} ---")
        video_url = leonardo_texto_a_video(
            prompt_video,
            escena.get("duracion_seg", 5),
            modelo=modelo_video,
            estilo_visual=estilo_visual,
        )
        if not video_url:
            continue
        ruta_clip = os.path.join(output_dir, f"clip_{i+1:02d}.mp4")
        if descargar_video(video_url, ruta_clip):
            rutas_clips.append(ruta_clip)

    if not rutas_clips:
        print("❌ No se generó ningún clip.")
        return None

    nombre = f"reel_{tema[:30].replace(' ','_').replace('?','').replace('¿','')}.mp4"
    output_path = os.path.join(output_dir, nombre)
    reel_path = montar_reel(rutas_clips, escenas, output_path, musica_path)

    # Guardar guion
    guion_path = output_path.replace(".mp4", "_guion.json")
    with open(guion_path, "w", encoding="utf-8") as f:
        json.dump(guion, f, indent=2, ensure_ascii=False)
    print(f"📄 Guion: {guion_path}")

    return reel_path


# ==========================================
# REEL CON IMÁGENES + KEN BURNS (sin video AI)
def montar_reel_imagenes(rutas_imagenes, escenas, output_path="reel_imagenes.mp4",
                         musica_path=None, font_size=68):
    """
    Monta un Reel usando imágenes estáticas con fade entre ellas + subtítulos.
    Alternativa rápida, profesional y 100% confiable a AI video.
    """
    from moviepy import ImageClip

    if not rutas_imagenes:
        print("❌ No hay imágenes para montar.")
        return None

    print(f"\n🎬 Montando Reel con {len(rutas_imagenes)} imágenes + fade...")
    clips = []

    for i, (ruta_img, escena) in enumerate(zip(rutas_imagenes, escenas)):
        duracion = escena.get("duracion_seg", 5)
        subtitulo = escena.get("subtitulo", "")
        tipo = escena.get("tipo_escena", "payoff")

        print(f"   🖼️  Imagen {i+1}: [{tipo}] {duracion}s — \"{subtitulo[:50]}...\"")

        # Cargar imagen
        img = ImageClip(ruta_img, duration=duracion)

        # Ajustar de cuadrado (1024x1024) a 9:16 vertical (1080x1920)
        img_w, img_h = img.size
        scale = max(REEL_WIDTH / img_w, REEL_HEIGHT / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        img = img.resized((new_w, new_h))
        img = img.cropped(
            x_center=new_w // 2, y_center=new_h // 2,
            width=REEL_WIDTH, height=REEL_HEIGHT,
        )

        # Zoom estático según tipo de escena
        if tipo == "hook":
            zoom = 1.08
        elif tipo == "cta":
            zoom = 1.04
        else:
            zoom = 1.06

        zw, zh = int(REEL_WIDTH * zoom), int(REEL_HEIGHT * zoom)
        img = img.resized((zw, zh))
        img = img.cropped(x_center=zw // 2, y_center=zh // 2,
                          width=REEL_WIDTH, height=REEL_HEIGHT)

        # Fade in/out entre escenas
        if i > 0:
            img = img.with_effects([vfx.FadeIn(0.4)])
        if i < len(rutas_imagenes) - 1:
            img = img.with_effects([vfx.FadeOut(0.4)])

        # Subtítulo
        if subtitulo:
            txt_clip = _crear_subtitulo(
                subtitulo, duracion, tipo, font_size=font_size,
            )
            txt_clip = txt_clip.with_position(("center", int(REEL_HEIGHT * 0.72)))
            img = CompositeVideoClip([img, txt_clip])

        clips.append(img)

    reel = concatenate_videoclips(clips, method="compose")

    # Música
    if musica_path and os.path.exists(musica_path):
        print(f"   🎵 Añadiendo música: {musica_path}")
        musica = AudioFileClip(musica_path)
        musica = musica.subclipped(0, min(musica.duration, reel.duration))
        if musica.duration < reel.duration:
            musica = musica.with_effects([vfx.Loop(duration=reel.duration)])
        musica = musica.with_effects([vfx.MultiplyVolume(0.3)])
        reel = reel.with_audio(musica)

    # Exportar
    tiene_audio = musica_path and os.path.exists(musica_path)
    print(f"   💾 Exportando Reel a {output_path}...")
    reel.write_videofile(
        output_path, fps=24, codec="libx264",
        bitrate="4000k", preset="fast", threads=4,
        audio=bool(tiene_audio),
    )

    try:
        for c in clips:
            c.close()
        reel.close()
    except Exception:
        pass

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Reel generado: {output_path} ({size_mb:.1f} MB, {reel.duration:.1f}s)")
    return output_path


def pipeline_reel_imagenes(tema, genero="libre", estilo_visual="default",
                           musica_path=None, output_dir="reels_output"):
    """
    Pipeline rápido: guion → imágenes Leonardo → Reel Ken Burns.
    Sin video AI — más rápido, barato y profesional.
    """
    from MassiveGenerator_trial import generar_guion_reel, generar_imagen_leonardo, descargar_imagen

    os.makedirs(output_dir, exist_ok=True)
    print("=" * 50)
    print(f"🎬 PIPELINE REEL (imágenes): {tema}")
    print(f"   Estilo: {estilo_visual} | Género: {genero}")
    print("=" * 50)

    guion = generar_guion_reel(tema, genero=genero, estilo_visual=estilo_visual)
    if not guion or "escenas" not in guion:
        print("❌ No se pudo generar el guion.")
        return None

    escenas = guion["escenas"]
    print(f"\n📋 Guion: {len(escenas)} escenas, personaje: {guion.get('personaje_base', 'N/A')[:60]}...")

    # Generar imagen para cada escena
    rutas_imagenes = []
    for i, escena in enumerate(escenas):
        prompt_img = escena.get("prompt_video", "")
        if not prompt_img:
            continue
        print(f"\n--- Escena {i+1}/{len(escenas)} ---")
        url_img = generar_imagen_leonardo(
            prompt_img, titulo_en_imagen=f"escena_{i+1}",
            estilo_nombre=estilo_visual, usar_texto_en_prompt=False,
            genero=genero, tipo_visual=None,  # sin bloques dinámicos para Reels
        )
        if not url_img:
            print(f"   ❌ Falló imagen escena {i+1}")
            continue
        ruta_img = os.path.join(output_dir, f"img_{i+1:02d}.jpg")
        descargar_imagen(url_img, ruta_img)
        if os.path.exists(ruta_img):
            rutas_imagenes.append(ruta_img)

    if len(rutas_imagenes) < 2:
        print("❌ Se necesitan al menos 2 imágenes.")
        return None

    nombre = f"reel_img_{tema[:25].replace(' ','_').replace('?','').replace('¿','')}.mp4"
    output_path = os.path.join(output_dir, nombre)
    reel_path = montar_reel_imagenes(rutas_imagenes, escenas, output_path, musica_path)

    # Guardar guion
    guion_path = output_path.replace(".mp4", "_guion.json")
    with open(guion_path, "w", encoding="utf-8") as f:
        json.dump(guion, f, indent=2, ensure_ascii=False)
    print(f"📄 Guion: {guion_path}")

    return reel_path
    print(f"   ✅ Video descargado: {ruta_destino} ({size_mb:.1f} MB)")
    return True