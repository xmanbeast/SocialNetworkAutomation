#!/usr/bin/env python3
"""
generar_carrusel.py - Script independiente para carruseles educativos.
Estructura: Portada -> Desarrollo -> CTA (3-7 slides).
"""

import os, json, time, requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# === CONFIGURACION ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
CARPETA_OUTPUT = "listo_para_subir"
ARCHIVO_HISTORIAL = "historial_carruseles.json"
os.makedirs(CARPETA_OUTPUT, exist_ok=True)

AZUL_BRILLANTE = (0, 180, 216)
AZUL_CLARO = (125, 211, 252)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

# === ESTILOS VISUALES ===
ESTILOS_VISUALES = {
    "default": "High-end commercial photography, professional gym, cinematic lighting, deep shadows, clean typography space",
    "cyberpunk": "Cyberpunk style, neon accents, high-tech gym, futuristic equipment, atmospheric lighting",
    "minimalista": "Clean minimalist background, high-end studio lighting, vector-photographic blend, sleek aesthetics",
    "editorial": "High-end fitness magazine style, dark editorial lighting, sharp focus on anatomy, professional studio",
    "dark_lab": "Dark technical lab aesthetic, blue-white clinical illumination, industrial gym, precise focus",
    "monochrome": "High contrast black-white fitness photography, chiaroscuro lighting, deep shadows, premium artistic feel",
    "clay_animation": "Handmade claymation stop-motion, colorful modeling clay, tactile texture, miniature gym set, bright studio",
    "disney_cartoon": "Stylized 2D Disney cartoon animation, vibrant colors, expressive faces, magical atmosphere, whimsical fitness",
    "neon_glow": "High-energy fitness, neon rim lighting, dark moody studio, electric blue and hot pink, cinematic fog",
    "3d_render": "Modern 3D octane render, smooth surfaces, vibrant metallic textures, stylized equipment, isometric composition",
    "retro_synthwave": "80s retro synthwave, sunset gradient purple-orange, wireframe grid, VHS glitch, bold color contrast",
    "duotone_pop": "High-contrast duotone, electric cyan and deep crimson, graphic poster art, clean minimalist negative space",
    "luxury_gold": "Luxury fitness branding, matte black, brushed gold illumination, premium metallic, elegant negative space",
    "female_power": "Powerful athletic woman training, luxury gym, dramatic cinematic lighting, deep shadows, detailed fitness",
    "female_editorial": "Fit female model, fitness magazine editorial, dark lighting, muscle definition, muted background",
    "anatomical_sci": "Scientific medical visualization, muscle anatomy, fiber-optic glow, high-tech dark lab, clean negative space",
    "xray_neon_muscles": "Futuristic x-ray, glowing translucent skin, detailed muscle anatomy, electric blue, industrial gym",
}

# === HISTORIAL ===
def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"carruseles_procesados": []}

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

# === LAYOUTS DEL CARRUSEL ===

LAYOUT_COVER = {
    "nombre": "carousel_cover",
    "tipo": "cover",
    "overlays": [
        {"tipo": "gradiente_vertical", "y_inicio_pct": 55, "altura_pct": 45,
         "color": [0,0,0], "alpha_inicio": 0, "alpha_fin": 220},
    ],
    "elementos": [
        {"tipo": "texto_cover_keywords",
         "placeholder_white": "cover_white_text", "placeholder_blue": "cover_blue_text",
         "x_pct": 6, "y_pct": 8, "ancho_max_pct": 88,
         "fuente": "heavy", "tamano_min": 40, "tamano_max": 70,
         "mayusculas": True, "sombra": True, "sombra_offset": 3},
        {"tipo": "texto", "placeholder": "cover_subtitle",
         "x_pct": 8, "y_pct": "debajo_de_cover_keywords", "ancho_max_pct": 84,
         "color_rgb": [255,255,255], "color_alpha": 220,
         "fuente": "regular", "tamano_min": 21, "tamano_max": 30,
         "mayusculas": False, "sombra": True, "sombra_offset": 2},
        {"tipo": "texto", "placeholder": None, "valor_fijo": "SWIPE \u2192",
         "x_pct": 50, "y_pct": 93, "alineacion": "centro", "ancho_max_pct": 40,
         "color_rgb": [125,211,252], "color_alpha": 200,
         "fuente": "bold", "tamano_min": 16, "tamano_max": 22,
         "mayusculas": True, "sombra": False},
    ],
}

LAYOUT_DEVELOPMENT = {
    "nombre": "carousel_development",
    "tipo": "development",
    "overlays": [
        {"tipo": "gradiente_vertical", "y_inicio_pct": 50, "altura_pct": 50,
         "color": [0,0,0], "alpha_inicio": 0, "alpha_fin": 210},
    ],
    "elementos": [
        {"tipo": "texto", "placeholder": None, "valor_fijo": "QUICK TIP:",
         "x_pct": 6, "y_pct": 4, "ancho_max_pct": 40,
         "color_rgb": [125,211,252], "color_alpha": 230,
         "fuente": "bold", "tamano_min": 20, "tamano_max": 28,
         "mayusculas": True, "sombra": False},
        {"tipo": "texto", "placeholder": "slide_title",
         "x_pct": 6, "y_pct": "debajo_de_quicktip_label", "ancho_max_pct": 88,
         "color_rgb": [255,255,255], "color_alpha": 255,
         "fuente": "heavy", "tamano_min": 32, "tamano_max": 52,
         "mayusculas": True, "sombra": True, "sombra_offset": 3},
        {"tipo": "texto", "placeholder": "slide_body",
         "x_pct": 6, "y_pct": 62, "ancho_max_pct": 88,
         "color_rgb": [255,255,255], "color_alpha": 240,
         "fuente": "regular", "tamano_min": 21, "tamano_max": 28,
         "mayusculas": False, "sombra": True, "sombra_offset": 2},
        {"tipo": "texto", "placeholder": "slide_number_display",
         "x_pct": 90, "y_pct": 93, "alineacion": "derecha", "ancho_max_pct": 15,
         "color_rgb": [125,211,252], "color_alpha": 180,
         "fuente": "bold", "tamano_min": 14, "tamano_max": 18,
         "mayusculas": False, "sombra": False},
    ],
}

LAYOUT_CTA = {
    "nombre": "carousel_cta",
    "tipo": "cta",
    "overlays": [
        {"tipo": "gradiente_vertical", "y_inicio_pct": 0, "altura_pct": 30,
         "color": [0,0,0], "alpha_inicio": 140, "alpha_fin": 0},
        {"tipo": "gradiente_vertical", "y_inicio_pct": 55, "altura_pct": 45,
         "color": [0,0,0], "alpha_inicio": 0, "alpha_fin": 210},
    ],
    "elementos": [
        {"tipo": "texto", "placeholder": "cta_line1",
         "x_pct": 50, "y_pct": 48, "alineacion": "centro", "ancho_max_pct": 85,
         "color_rgb": [255,255,255], "color_alpha": 255,
         "fuente": "heavy", "tamano_min": 36, "tamano_max": 60,
         "mayusculas": True, "sombra": True, "sombra_offset": 4},
        {"tipo": "texto", "placeholder": "cta_line2",
         "x_pct": 50, "y_pct": "debajo_de_cta_line1", "alineacion": "centro", "ancho_max_pct": 85,
         "color_rgb": [0,180,216], "color_alpha": 255,
         "fuente": "heavy", "tamano_min": 30, "tamano_max": 48,
         "mayusculas": True, "sombra": True, "sombra_offset": 3},
        {"tipo": "texto", "placeholder": "cta_hashtag",
         "x_pct": 50, "y_pct": "debajo_de_cta_line2", "alineacion": "centro", "ancho_max_pct": 70,
         "color_rgb": [125,211,252], "color_alpha": 200,
         "fuente": "bold", "tamano_min": 18, "tamano_max": 24,
         "mayusculas": False, "sombra": True, "sombra_offset": 2},
    ],
}

# ==========================================
# FUNCIONES DE RENDERIZADO PILLOW
# ==========================================

def _obtener_fuente(nombre_fuente, tamanio, ctx):
    key = f"{nombre_fuente}_{tamanio}"
    if key in ctx["fuentes"]:
        return ctx["fuentes"][key]
    fuentes_map = {
        "bold": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "heavy": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "regular": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
        "light": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    }
    rutas = fuentes_map.get(nombre_fuente, fuentes_map["regular"])
    fuente = None
    for ruta in rutas:
        if os.path.exists(ruta):
            fuente = ImageFont.truetype(ruta, tamanio)
            break
    if fuente is None:
        fuente = ImageFont.load_default()
    ctx["fuentes"][key] = fuente
    return fuente

def _dividir_texto_lineas(texto, font, ancho_max):
    if not texto:
        return [""]
    palabras = texto.split()
    lineas = []
    linea_actual = ""
    for palabra in palabras:
        prueba = f"{linea_actual} {palabra}".strip()
        bbox = font.getbbox(prueba)
        if (bbox[2] - bbox[0]) <= ancho_max:
            linea_actual = prueba
        else:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = palabra
    if linea_actual:
        lineas.append(linea_actual)
    return lineas if lineas else [texto]

def _calcular_tamanio_fuente_optimo(texto, ancho_max, ruta_fuente, tmin=24, tmax=80):
    if not texto:
        return tmin
    lo, hi = tmin, tmax
    mejor = tmin
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            if ruta_fuente and os.path.exists(ruta_fuente):
                font = ImageFont.truetype(ruta_fuente, mid)
            else:
                font = ImageFont.load_default()
            lineas = texto.split('\n')
            cabe = all((font.getbbox(l)[2] - font.getbbox(l)[0]) <= ancho_max for l in lineas if l)
            if cabe:
                mejor = mid
                lo = mid + 1
            else:
                hi = mid - 1
        except Exception:
            hi = mid - 1
    return mejor

def _aplicar_overlay(overlay_img, ov_config, ancho, alto):
    y_inicio = int(alto * ov_config["y_inicio_pct"] / 100)
    altura = int(alto * ov_config["altura_pct"] / 100)
    color = ov_config["color"]
    a_ini = ov_config["alpha_inicio"]
    a_fin = ov_config["alpha_fin"]
    for i in range(altura):
        y = y_inicio + i
        if y < 0 or y >= alto:
            continue
        t = i / max(altura - 1, 1)
        alpha = int(a_ini + (a_fin - a_ini) * t)
        alpha = max(0, min(255, alpha))
        if alpha <= 0:
            continue
        rgba = (color[0], color[1], color[2], alpha)
        for x in range(ancho):
            overlay_img.putpixel((x, y), rgba)

def _calcular_posicion(elem, ctx, ancho_texto=0, alto_texto=0, font=None, lineas=None):
    ancho_i = ctx["ancho"]
    alto_i = ctx["alto"]
    posiciones = ctx["posiciones"]
    y_pct = elem.get("y_pct", 0)
    if isinstance(y_pct, str):
        ref = y_pct
        if ref.startswith("debajo_de_"):
            key = ref[len("debajo_de_"):]
            y = posiciones.get(f"{key}_y_fin", posiciones.get(key, int(alto_i * 0.25))) + 10
        else:
            y = posiciones.get("ultima_y", int(alto_i * 0.25)) + 10
    else:
        y = int(alto_i * y_pct / 100)
    alineacion = elem.get("alineacion", "izquierda")
    if alineacion == "centro":
        x = int(ancho_i / 2)
    elif alineacion == "derecha":
        x = int(ancho_i * 0.95) - ancho_texto
    else:
        x = int(ancho_i * elem.get("x_pct", 0) / 100)
    return x, y

def _render_texto(overlay, elem, datos_ia, ctx, texto_forzado=None):
    placeholder = elem.get("placeholder")
    valor_fijo = elem.get("valor_fijo")
    if texto_forzado is not None:
        texto = texto_forzado
    elif valor_fijo:
        texto = valor_fijo
    elif placeholder and placeholder in datos_ia:
        texto = str(datos_ia.get(placeholder, ""))
    else:
        return
    if not texto:
        return
    if elem.get("mayusculas"):
        texto = texto.upper()
    ancho = ctx["ancho"]
    alto = ctx["alto"]
    ancho_max = int(ancho * elem.get("ancho_max_pct", 80) / 100)
    fuente_nombre = elem.get("fuente", "regular")
    ruta_base = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                 if fuente_nombre in ("bold", "heavy")
                 else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    tamanio = _calcular_tamanio_fuente_optimo(
        texto, ancho_max, ruta_base,
        elem.get("tamano_min", 22), elem.get("tamano_max", 60))
    font = _obtener_fuente(fuente_nombre, tamanio, ctx)
    lineas = _dividir_texto_lineas(texto, font, ancho_max)
    alturas = []
    for l in lineas:
        bbox = font.getbbox(l)
        alturas.append(bbox[3] - bbox[1])
    altura_total = sum(alturas) + (len(lineas) - 1) * 6
    x, y = _calcular_posicion(elem, ctx, ancho_max, altura_total, font, lineas)
    rgb = elem.get("color_rgb", [255,255,255])
    alpha = elem.get("color_alpha", 255)
    color_texto = tuple(rgb) + (alpha,)
    color_sombra = (0,0,0,180)
    sombra = elem.get("sombra", False)
    sombra_offset = elem.get("sombra_offset", 2)
    draw = ImageDraw.Draw(overlay)
    y_actual = y
    alineacion = elem.get("alineacion", "izquierda")
    ancho_primera = font.getbbox(lineas[0])[2] - font.getbbox(lineas[0])[0]
    for i, linea in enumerate(lineas):
        bbox = font.getbbox(linea)
        ancho_linea = bbox[2] - bbox[0]
        if alineacion == "centro":
            x_linea = ancho // 2 - ancho_linea // 2
        elif alineacion == "derecha":
            x_linea = int(ancho * 0.95) - ancho_linea
        else:
            x_linea = x
        if sombra:
            draw.text((x_linea + sombra_offset, y_actual + sombra_offset), linea, font=font, fill=color_sombra)
        draw.text((x_linea, y_actual), linea, font=font, fill=color_texto)
        y_actual += alturas[i] + 6
    nombre_elem = elem.get("id_ref") or elem.get("placeholder") or "elem"
    ctx["posiciones"][f"{nombre_elem}_x"] = x
    ctx["posiciones"][f"{nombre_elem}_y"] = y
    ctx["posiciones"][f"{nombre_elem}_x_fin"] = x + ancho_primera
    ctx["posiciones"][f"{nombre_elem}_y_fin"] = y_actual
    ctx["posiciones"]["ultima_y"] = y_actual
    ctx["posiciones"]["ultima_x"] = x

def _render_texto_cover_keywords(overlay, elem, datos_ia, ctx):
    white_text = str(datos_ia.get("cover_white_text", "")).strip()
    blue_text = str(datos_ia.get("cover_blue_text", "")).strip()
    if not white_text and not blue_text:
        return
    ancho = ctx["ancho"]
    alto = ctx["alto"]
    ancho_max = int(ancho * elem.get("ancho_max_pct", 88) / 100)
    fuente_nombre = elem.get("fuente", "heavy")
    ruta_base = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    texto_total = f"{white_text} {blue_text}".strip()
    if elem.get("mayusculas"):
        texto_total = texto_total.upper()
        white_text = white_text.upper()
        blue_text = blue_text.upper()
    tmin = elem.get("tamano_min", 32)
    tmax = elem.get("tamano_max", 70)
    tamanio = _calcular_tamanio_fuente_optimo(texto_total, ancho_max, ruta_base, tmin, tmax)
    font = _obtener_fuente(fuente_nombre, tamanio, ctx)
    draw = ImageDraw.Draw(overlay)
    sombra = elem.get("sombra", True)
    sombra_offset = elem.get("sombra_offset", 3)
    color_sombra = (0, 0, 0, 180)
    x = int(ancho * elem.get("x_pct", 6) / 100)
    y = int(alto * elem.get("y_pct", 8) / 100)
    x_actual = x
    y_linea = y
    espacio = font.getbbox(" ")[2] - font.getbbox(" ")[0]
    palabras_white = white_text.split() if white_text else []
    palabras_blue = blue_text.split() if blue_text else []
    def _cabe(palabra, x_pos):
        bbox = font.getbbox(palabra)
        return (x_pos + (bbox[2] - bbox[0])) <= (x + ancho_max)
    all_p = []
    for p in palabras_white:
        all_p.append((p, "white"))
    for p in palabras_blue:
        all_p.append((p, "blue"))
    max_altura = 0
    for palabra, color_tipo in all_p:
        bbox = font.getbbox(palabra)
        ancho_p = bbox[2] - bbox[0]
        alto_p = bbox[3] - bbox[1]
        max_altura = max(max_altura, alto_p)
        if not _cabe(palabra, x_actual) and x_actual > x:
            x_actual = x
            y_linea += max_altura + 6
            max_altura = alto_p
        color_fill = (255, 255, 255, 240) if color_tipo == "white" else (0, 180, 216, 250)
        if sombra:
            draw.text((x_actual + sombra_offset, y_linea + sombra_offset),
                      palabra, font=font, fill=color_sombra)
        draw.text((x_actual, y_linea), palabra, font=font, fill=color_fill)
        x_actual += ancho_p + espacio
    y_fin = y_linea + max_altura + 6
    ctx["posiciones"]["cover_keywords_y_fin"] = y_fin
    ctx["posiciones"]["debajo_de_cover_keywords"] = y_fin
    ctx["posiciones"]["ultima_y"] = y_fin

def render_layout_carrusel(imagen_path, layout_config, datos_ia, salida_path=None):
    if salida_path is None:
        salida_path = imagen_path
    img = Image.open(imagen_path).convert("RGBA")
    ancho, alto = img.size
    overlay = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    ctx = {
        "ancho": ancho, "alto": alto,
        "ultima_y": 0, "ultima_x": 0,
        "fuentes": {}, "posiciones": {},
    }
    for ov in layout_config.get("overlays", []):
        _aplicar_overlay(overlay, ov, ancho, alto)
    for elem in layout_config.get("elementos", []):
        tipo = elem.get("tipo")
        if tipo == "texto":
            _render_texto(overlay, elem, datos_ia, ctx)
        elif tipo == "texto_cover_keywords":
            _render_texto_cover_keywords(overlay, elem, datos_ia, ctx)
    img_final = Image.alpha_composite(img, overlay)
    img_final = img_final.convert("RGB")
    img_final.save(salida_path, "JPEG", quality=95)
    print(f"   \u2705 Layout '{layout_config.get('nombre')}' -> {os.path.basename(salida_path)}")

# ==========================================
# GENERAR CONTENIDO DEL CARRUSEL (OPENROUTER)
# ==========================================
def generar_contenido_carrusel(tema, estilo_visual_nombre, genero="libre"):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    if genero == "female":
        instr_gen = "Atleta MUJER en todos los image_prompt_details."
    elif genero == "male":
        instr_gen = "Atleta HOMBRE en todos los image_prompt_details."
    elif genero == "sin_personaje":
        instr_gen = "NO personas. Solo objetos, equipamiento, diagramas o escenarios."
    else:
        instr_gen = ""

    system_prompt = (
        "Eres experto en marketing de fitness. Crea un carrusel educativo de 5 slides.\n\n"
        "Devuelve SOLO este JSON:\n"
        '{"caption":"...","slides":[\n'
        '  {"slide_number":1,"tipo":"cover","cover_white_text":"FRASE CONECTORA",'
        '"cover_blue_text":"CONCEPTO CLAVE","cover_subtitle":"subtitulo descriptivo",'
        '"image_prompt_details":"descripcion en INGLES de imagen de portada"},\n'
        '  {"slide_number":2,"tipo":"development","slide_title":"TITULO CORTO",'
        '"slide_body":"tip educativo 15-25 palabras","image_prompt_details":"..."},\n'
        '  {"slide_number":3,"tipo":"development","slide_title":"...","slide_body":"...","image_prompt_details":"..."},\n'
        '  {"slide_number":4,"tipo":"development","slide_title":"...","slide_body":"...","image_prompt_details":"..."},\n'
        '  {"slide_number":5,"tipo":"cta","cta_line1":"GUARDA Y COMPARTE","cta_line2":"SIGUE PARA MAS",'
        '"cta_hashtag":"#Hashtag","image_prompt_details":"..."}\n'
        "]}\n\n"
        "REQUISITOS:\n"
        f"- {instr_gen}\n"
        "- cover_white_text: frase en BLANCO (ej: 'LA VERDAD SOBRE'). cover_blue_text: concepto en AZUL (ej: 'HIPERTROFIA').\n"
        "- slide_title: 3-6 palabras en MAYUSCULAS.\n"
        "- slide_body: 15-25 palabras educativo.\n"
        "- image_prompt_details: INGLES, 1 frase, minimalista.\n"
        "- Responde SOLO con el JSON, sin markdown.\n"
    )

    user_prompt = f"Genera carrusel de fitness de 5 slides para: '{tema}'. Solo JSON."

    payload = {
        "model": "anthropic/claude-sonnet-4.6",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    print(f"\U0001F9E0 Generando contenido del carrusel...")
    response = requests.post(url, headers=headers, json=payload, timeout=90)

    if response.status_code != 200:
        print(f"\u274c OpenRouter error: {response.text[:200]}")
        return None

    try:
        contenido = response.json()["choices"][0]["message"]["content"]
        contenido = contenido.strip()
        if contenido.startswith("```"):
            contenido = contenido.split("```")[1]
            if contenido.startswith("json"):
                contenido = contenido[4:]
            contenido = contenido.strip()
        datos = json.loads(contenido)
        if "slides" not in datos or len(datos["slides"]) < 3:
            print(f"\u274c Pocas slides: {len(datos.get('slides',[]))}")
            return None
        print(f"\u2705 {len(datos['slides'])} slides generadas")
        return datos
    except Exception as e:
        print(f"\u274c Parse error: {e}")
        return None

# ==========================================
# GENERAR IMAGEN (LEONARDO AI)
# ==========================================
def ensamblar_prompt_carrusel(estilo_base, image_prompt_details, genero="libre"):
    sufijo_gen = ""
    estilo_lower = estilo_base.lower()
    if genero == "female" and not any(p in estilo_lower for p in ["woman", "female"]):
        sufijo_gen = "Female athlete, muscular woman. "
    elif genero == "male" and not any(p in estilo_lower for p in [" man ", "male "]):
        sufijo_gen = "Male athlete, muscular man. "
    elif genero == "sin_personaje":
        sufijo_gen = "NO people, only objects/equipment/scenes. "
    prompt = (
        f"{estilo_base}. Main subject: {image_prompt_details}. "
        f"{sufijo_gen}"
        "Single focused subject, clean composition, "
        "negative space for text overlay on bottom. No watermarks."
    )
    return prompt

def generar_imagen_leonardo(prompt_final):
    url_base = "https://cloud.leonardo.ai/api/rest/v2/generations"
    headers = {"Authorization": f"Bearer {LEONARDO_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "flux-dev",
        "parameters": {
            "prompt": prompt_final,
            "negative_prompt": (
                "deformed anatomy, extra limbs, fused fingers, ugly, "
                "distorted face, bad proportions, watermark, text, blurry, low quality"
            ),
            "width": 1024, "height": 1024, "quantity": 1, "prompt_enhance": "ON"
        },
        "public": False
    }
    response = requests.post(url_base, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        print(f"   \u274c Leonardo init: {response.text[:150]}")
        return None
    resp_data = response.json()
    # Fix: Leonardo v2 a veces devuelve lista en vez de dict
    if isinstance(resp_data, list):
        resp_data = resp_data[0] if resp_data else {}

    gen_id = (
        resp_data.get("generate", {}).get("generationId") or
        resp_data.get("sdGenerationJob", {}).get("generationId") or
        resp_data.get("generationId") or resp_data.get("id")
    )
    if not gen_id:
        print(f"   \u274c No generationId. Raw: {json.dumps(resp_data)[:200]}")
        return None
    print(f"   \u23f3 Generating... (ID: {gen_id})")
    time.sleep(10)
    url_status = f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}"
    for _ in range(8):
        res = requests.get(url_status, headers=headers, timeout=30)
        if res.status_code == 200:
            data = res.json()
            images = data.get("generations_by_pk", {}).get("generated_images", [])
            if images:
                return images[0].get("url")
        time.sleep(10)
    return None

def descargar_imagen(url_imagen, ruta_destino):
    try:
        res = requests.get(url_imagen, timeout=60)
        if res.status_code == 200:
            with open(ruta_destino, "wb") as f:
                f.write(res.content)
            return True
    except Exception as e:
        print(f"   \u274c Download: {e}")
    return False

# ==========================================
# PIPELINE PRINCIPAL
# ==========================================
def ejecutar_pipeline_carrusel(lista_temas, estilo_elegido="default",
                                genero_personaje="libre", reiniciar_historial=False):
    historial = {"carruseles_procesados": []} if reiniciar_historial else cargar_historial()
    temas_ya = [item["tema"] for item in historial["carruseles_procesados"]]
    contador = len(historial["carruseles_procesados"]) + 1
    print(f"\U0001F3A8 Estilo: {estilo_elegido} | Genero: {genero_personaje}")
    for tema in lista_temas:
        if tema in temas_ya:
            print(f"\u23ed Saltando: {tema[:50]}...")
            continue
        print(f"\n{'='*60}")
        print(f"\U0001F3A0 CARRUSEL [{contador}]: {tema[:60]}")
        print(f"{'='*60}")
        try:
            datos = generar_contenido_carrusel(tema, estilo_elegido, genero_personaje)
            if not datos:
                continue
            caption = datos.get("caption", "")
            slides = datos.get("slides", [])
            if len(slides) < 3:
                print(f"\u26a0 Solo {len(slides)} slides. Saltando.")
                continue
            nombre_carp = f"carrusel_{contador:02d}"
            ruta_carp = os.path.join(CARPETA_OUTPUT, nombre_carp)
            os.makedirs(ruta_carp, exist_ok=True)
            estilo_base = ESTILOS_VISUALES.get(estilo_elegido, ESTILOS_VISUALES["default"])
            slides_gen = []
            for idx, slide in enumerate(slides):
                slide_num = slide.get("slide_number", idx + 1)
                slide_tipo = slide.get("tipo", "development")
                image_prompt = slide.get("image_prompt_details", "")
                if not image_prompt:
                    continue
                print(f"\n   \U0001F4C4 Slide {slide_num}/{len(slides)} [{slide_tipo}]")
                prompt_final = ensamblar_prompt_carrusel(estilo_base, image_prompt, genero_personaje)
                url_img = generar_imagen_leonardo(prompt_final)
                if not url_img:
                    continue
                nombre_slide = f"slide_{slide_num:02d}_{slide_tipo}.jpg"
                ruta_slide = os.path.join(ruta_carp, nombre_slide)
                if not descargar_imagen(url_img, ruta_slide):
                    continue
                print(f"   \U0001F4BE {nombre_slide}")
                if slide_tipo == "cover":
                    layout = LAYOUT_COVER
                elif slide_tipo == "cta":
                    layout = LAYOUT_CTA
                else:
                    layout = LAYOUT_DEVELOPMENT
                slide_data = dict(slide)
                if slide_tipo == "development":
                    slide_data["slide_number_display"] = f"{slide_num}/{len(slides)}"
                render_layout_carrusel(ruta_slide, layout, slide_data)
                slides_gen.append({"numero": slide_num, "tipo": slide_tipo, "archivo": nombre_slide})
            if slides_gen:
                with open(os.path.join(ruta_carp, "caption.txt"), "w", encoding="utf-8") as f:
                    f.write(caption)
                historial["carruseles_procesados"].append({
                    "id": contador, "tema": tema, "estilo": estilo_elegido,
                    "genero": genero_personaje,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "carpeta": nombre_carp, "num_slides": len(slides_gen),
                    "slides": slides_gen,
                })
                guardar_historial(historial)
                print(f"\n\u2705 Carrusel {contador}: {len(slides_gen)} slides en {nombre_carp}/")
                contador += 1
            else:
                print(f"\u274c Ningun slide generado")
        except Exception as e:
            print(f"\u274c Error: {e}")
            import traceback
            traceback.print_exc()

# ==========================================
# __MAIN__
# ==========================================
if __name__ == "__main__":
    temas_carrusel = [
        "La ciencia detras de la hipertrofia muscular: mecanismos y aplicacion practica"

    ]
    ejecutar_pipeline_carrusel(
        lista_temas=temas_carrusel,
        estilo_elegido="default",
        genero_personaje="male",
        reiniciar_historial=True,
    )
