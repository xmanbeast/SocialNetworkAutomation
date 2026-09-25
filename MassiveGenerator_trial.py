import os
import json
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from layouts import LAYOUTS, obtener_layout

# ==========================================
# CONFIGURACIÓN DE APIS Y DIRECTORIOS
# ==========================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
CARPETA_OUTPUT = "listo_para_subir"
ARCHIVO_HISTORIAL = "historial_posts.json"

# Asegurar que existan las carpetas
os.makedirs(CARPETA_OUTPUT, exist_ok=True)

# ==========================================
# DICCIONARIO DE ESTILOS VISUALES PARA LEONARDO
# ==========================================
ESTILOS_VISUALES = {
   "default": "High-end commercial photography, professional gym environment, cinematic lighting, deep contrast shadows, highly detailed fitness imagery, clean typography space for title",
    "cyberpunk": "Cyberpunk style, vibrant neon accents, high-tech gym interior, futuristic fitness equipment, atmospheric lighting",
    "minimalista": "Clean minimalist background, high-end studio lighting, vector and photographic blend, sleek aesthetics",
    "editorial": "High-end fitness magazine style, sophisticated dark editorial lighting, sharp focus on physical structure and muscle anatomy, clean typography layout space, professional studio photography, muted background tones",
    "dark_lab": "Dark technical laboratory aesthetic, subtle blue and white clinical illumination, industrial gym background with high contrast, precise mechanical focus, sleek minimalist typography area",
    "monochrome": "High contrast black and white fitness photography, sharp chiaroscuro lighting, deep shadows, professional bodybuilding focus, clean negative space for typography, premium artistic feel",
    "clay_animation": "Handmade claymation stop-motion style, crafted from colorful modeling clay, tactile texture with subtle fingerprints, miniature professional gym set design, bright studio lighting, clean solid background, negative space for typography",
    "disney_cartoon": "Stylized 2D cartoon animation style inspired by Disney, smooth hand-drawn character art, vibrant colors, expressive faces, rounded soft shapes, magical atmosphere, clean solid background, whimsical fitness theme, negative space for typography",
    "neon_glow": "High-energy fitness aesthetic, glowing neon rim lighting, dark moody studio with electric blue and hot pink highlights, cinematic fog, high-contrast dynamic action shot, sleek negative space for title",
    "3d_render": "Modern 3D render style, octane render quality, smooth surfaces, vibrant color palette with metallic textures, stylized fitness equipment, clean isometric composition, premium corporate aesthetic",
    "retro_synthwave": "80s retro synthwave aesthetic, sunset gradient background of purple and orange, wireframe grid elements, VHS glitch accents, high-end fitness styling, bold color contrast, clean typography layout space",
    "duotone_pop": "High-contrast duotone photography, bold color grading using electric cyan and deep crimson, graphic poster art style, striking visual rhythm, clean minimalist negative space for typography",
    "luxury_gold": "Luxury fitness branding, deep matte black background with subtle brushed gold illumination, premium metallic accents, sophisticated high-end studio lighting, elegant negative space for typography",
    "female_power": "High-end commercial photography of a powerful athletic woman training hard in a professional luxury gym, dramatic cinematic lighting, deep contrast shadows, highly detailed fitness imagery, clean typography space for title",
    "female_editorial": "High-end fitness magazine editorial featuring a fit female model, sophisticated dark editorial lighting, sharp focus on physical structure and muscle definition, clean typography layout space, professional studio photography, muted background tones",
    "anatomical_sci": "Scientific medical visualization style, professional athletic fitness model showing detailed muscle anatomy and skeletal structure, luminescent fiber-optic muscle glow, high-tech dark laboratory background, precise scientific focus, clean negative space for typography",
    "xray_neon_muscles": "Futuristic x-ray visual style, glowing translucent skin revealing detailed muscle anatomy underneath, electric blue and cyan illumination, high-contrast dark industrial gym background, advanced biometric tech aesthetic, clean typography space"
}


# ==========================================
# BLOQUES VISUALES DINÁMICOS (CLASIFICADOS POR IA)
# ==========================================
BLOQUES_VISUALES_DINAMICOS = {
    "anatomia_lesiones": (
        "In the upper area, a large glowing circular inset framed in a thin golden ring "
        "showing a sci-fi x-ray anatomical view highlighting the specific muscles or spine, "
        "glowing with golden light, connected by a subtle light beam to the main subject."
    ),
    "nutricion_suplementos": (
        "In the upper area, a circular inset showing premium supplements, macro ingredients, "
        "or clean organic food arranged neatly on a dark minimalist pedestal."
    ),
    "transformacion_fisica": (
        "In the upper area, a split-screen circular inset showing a before-and-after "
        "body transformation comparison under professional lighting."
    ),
    "entrenamiento_general": (
        "No circular inset. Focus entirely on a cinematic, wide-angle dramatic shot "
        "of the athlete executing the movement with deep atmospheric shadows."
    ),
}


# ==========================================
# FUNCIONES DE HISTORIAL (EVITAR DUPLICADOS)
# ==========================================
def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"temas_procesados": []}

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

# ==========================================
# LLAMADA A OPENROUTER — PROMPT DINÁMICO SEGÚN LAYOUT
# ==========================================
def generar_texto_y_prompt_ia(tema_libro, estilo_visual_nombre, layout_config, genero="libre"):
    """
    Genera caption + campos de texto para la imagen + prompt visual.
    El system_prompt se construye dinámicamente según los campos_ia del layout.
    
    Parámetro 'genero':
        - "female": fuerza personaje femenino
        - "male": fuerza personaje masculino
        - "libre": sin restricción, la IA decide
        - "sin_personaje": sin personas, solo objetos/equipamiento/escenarios
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    campos = layout_config.get("campos_ia", [])
    campos_texto = [c for c in campos if c not in ("caption", "image_prompt_details")]
    
    # Construir descripción de campos dinámicamente
    descripcion_campos = _generar_descripcion_campos_ia(layout_config)
    
    # Instrucción de género para image_prompt_details
    if genero == "female":
        instruccion_genero = (
            "IMPORTANTE: El atleta en 'image_prompt_details' DEBE ser MUJER "
            "(female athlete, woman, feminine physique). "
        )
    elif genero == "male":
        instruccion_genero = (
            "IMPORTANTE: El atleta en 'image_prompt_details' DEBE ser HOMBRE "
            "(male athlete, man, masculine physique). "
        )
    elif genero == "sin_personaje":
        instruccion_genero = (
            "IMPORTANTE: NO incluyas personas ni atletas en 'image_prompt_details'. "
            "Solo describe objetos, equipamiento de gimnasio, suplementos, comida, "
            "diagramas anatómicos, escenarios o composiciones abstractas. "
        )
    else:  # "libre"
        instruccion_genero = ""
    
    system_prompt = (
        "Eres un experto en marketing de fitness y culturismo. "
        "Devuelve EXCLUSIVAMENTE un objeto JSON válido con los siguientes campos:\n"
        f"{descripcion_campos}"
        "REQUISITOS ADICIONALES:\n"
        "- 'caption': Texto completo para Facebook/Instagram con ganchos potentes, explicación educativa, llamada a la acción y #tags.\n"
        "- 'image_prompt_details': Descripción minimalista en INGLÉS de UN SOLO atleta o detalle muscular. "
        "Evita pedir múltiples personas o secuencias (ej: 'close-up of a muscular arm gripping a heavy dumbbell').\n"
        f"{instruccion_genero}"
        "- 'tipo_visual': Clasifica el tema en UNA de estas categorías:\n"
        "  * 'anatomia_lesiones' → para temas de anatomía, lesiones, biomecánica, músculos específicos, dolor muscular\n"
        "  * 'nutricion_suplementos' → para temas de dieta, suplementos, creatina, proteína, macros, meal prep\n"
        "  * 'transformacion_fisica' → para temas de progreso, cambios corporales, antes/después, recomposición\n"
        "  * 'entrenamiento_general' → para rutinas, ejercicios, técnica de levantamiento, series, descanso, sobrecarga\n"
        "IMPORTANTE: Responde SOLO con el JSON, sin markdown, sin explicaciones adicionales."
    )
    
    user_prompt = (
        f"Genera contenido de fitness para el siguiente tema: '{tema_libro}'. "
        f"Devuelve SOLO el JSON con los campos requeridos."
    )
    
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1200
    }
    
    print(f"🧠 Generando texto con IA (layout: {layout_config.get('nombre')}, género: {genero})...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error en OpenRouter: {response.text}")
        return {}
    
    try:
        contenido = response.json()["choices"][0]["message"]["content"]
        # Limpiar posible markdown
        contenido = contenido.strip()
        if contenido.startswith("```"):
            contenido = contenido.split("```")[1]
            if contenido.startswith("json"):
                contenido = contenido[4:]
            contenido = contenido.strip()
        
        datos = json.loads(contenido)
        
        # Validar que todos los campos requeridos estén presentes
        for campo in campos:
            if campo not in datos:
                print(f"⚠️ Campo '{campo}' faltante en respuesta IA")
                datos[campo] = ""
        
        # Asegurar tipo_visual (nuevo campo dinámico) con fallback seguro
        if "tipo_visual" not in datos or datos["tipo_visual"] not in BLOQUES_VISUALES_DINAMICOS:
            datos["tipo_visual"] = "entrenamiento_general"
            print(f"⚠️ 'tipo_visual' no válido o ausente → usando fallback 'entrenamiento_general'")
        else:
            print(f"🎯 IA clasificó el tema como: '{datos['tipo_visual']}'")
        
        return datos
        
    except Exception as e:
        print(f"Error parseando respuesta IA: {e}")
        print(f"Contenido recibido: {contenido[:300]}...")
        return {}

# ==========================================
# GENERADOR DE GUIÓN PARA REELS
# ==========================================
def generar_guion_reel(tema_libro, genero="libre", estilo_visual="default", modo="leonardo"):
    """
    Genera un guion estructurado para Reel de fitness con múltiples escenas.
    
    Parámetros:
        tema_libro: tema del Reel
        genero: "female" | "male" | "libre" | "sin_personaje"
        estilo_visual: clave del diccionario ESTILOS_VISUALES
        modo: "leonardo" (4-6 escenas, 25-30s) | "kling" (2 bloques, 10s c/u, 20s total)
    
    Retorna JSON con caption, personaje_base y array de escenas o bloques.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Instrucción de género
    if genero == "female":
        instruccion_genero = (
            "IMPORTANTE: El personaje DEBE ser MUJER (female athlete, woman, feminine physique) "
            "en TODAS las escenas. El 'personaje_base' debe describir una mujer atlética con detalle. "
        )
    elif genero == "male":
        instruccion_genero = (
            "IMPORTANTE: El personaje DEBE ser HOMBRE (male athlete, man, masculine physique) "
            "en TODAS las escenas. El 'personaje_base' debe describir un hombre atlético con detalle. "
        )
    elif genero == "sin_personaje":
        instruccion_genero = (
            "IMPORTANTE: NO incluyas personas ni atletas en ninguna escena. "
            "Solo objetos, equipamiento de gimnasio, suplementos, diagramas anatómicos, "
            "comida, escenarios o composiciones abstractas. "
        )
    else:  # "libre"
        instruccion_genero = (
            "Puedes elegir libremente el género del personaje o mezclar. "
        )
    
    if modo == "kling":
        system_prompt = (
            "Eres un director creativo de Reels de fitness para Instagram/TikTok. "
            "Crea un guion para 2 CLIPS continuos de 10 segundos cada uno (20s total).\n\n"
            
            "Devuelve EXCLUSIVAMENTE un JSON con esta estructura:\n"
            "- 'caption': Texto EDUCATIVO para Instagram/TikTok (máximo 100 palabras). "
            "Usa TU conocimiento del tema para educar. DEBE tener esta ESTRUCTURA:\n"
            "  ① GANCHO (1 frase impactante + emoji).\n"
            "  ② CUERPO EDUCATIVO: Extrae 2-3 datos/beneficios/consejos/advertencias "
            "reales del tema en lista numerada con emojis (1️⃣ 2️⃣ 3️⃣). "
            "Cada punto: 2-3 frases que realmente ENSEÑEN algo.\n"
            "  ③ CTA (guarda, comenta, sigue).\n"
            "  ④ 4-5 hashtags relevantes.\n"
            "Ejemplo real para 'déficit calórico':\n"
            "\n"
            "¿Quieres perder grasa sin pasar hambre? 🔥\n"
            "El déficit calórico es la clave, pero mal hecho juega en tu contra:\n"
            "1️⃣ Quema grasa sostenible: Consume 300-500 kcal menos al día "
            "para perder peso sin sacrificar músculo ni energía.\n"
            "2️⃣ No te excedas: Un déficit muy agresivo relentiza tu "
            "metabolismo y eleva el cortisol, saboteando tu progreso.\n"
            "3️⃣ Consulta a un profesional: Un nutriólogo personaliza tu "
            "plan según tu cuerpo y objetivos.\n"
            "¡Guarda este Reel y compártelo! 🎯\n"
            "#DeficitCalorico #NutricionDeportiva #PerderGrasa #FitnessTips #Salud\n"

            "- 'personaje_base': Descripción FÍSICA DETALLADA en INGLÉS del personaje. "
            "Incluye: género, etnia, edad, pelo, tipo de cuerpo, ropa de gym.\n"
            f"{instruccion_genero}\n"
            
            "- 'bloques': Array de EXACTAMENTE 2 bloques. Cada bloque:\n"
            "  * 'prompt_video': Descripción en INGLÉS de la escena COMPLETA de 10s. "
            "Describe acción, cámara, ambiente, iluminación. "
            "DEBE empezar con el 'personaje_base' EXACTAMENTE IGUAL.\n"
            "  * 'subtitulos': Array de 1-3 subtítulos con 'texto' y 'timestamp_seg' (0-10).\n\n"
            
            "  Bloque 1 (0-10s): HOOK impactante + primer contexto.\n"
            "  Bloque 2 (10-20s): PAYOFF (tip/ciencia) + CTA final.\n\n"
            
            f"ESTILO VISUAL: '{estilo_visual}'. Inclúyelo en cada prompt_video. "
            f"Referencia: {ESTILOS_VISUALES.get(estilo_visual, ESTILOS_VISUALES['default'])}\n\n"
            
            "IMPORTANTE: Responde SOLO con el JSON, sin markdown."
        )
    else:
        system_prompt = (
            "Eres un director creativo experto en Reels de fitness para Instagram y TikTok. "
            "Transforma un tema de fitness en un guion visual para un Reel de 25-30 segundos.\n\n"
            
            "Devuelve EXCLUSIVAMENTE un JSON con esta estructura:\n"
            "- 'caption': Texto EDUCATIVO para Instagram/TikTok (máximo 100 palabras). "
            "Usa TU conocimiento del tema para educar. DEBE tener esta ESTRUCTURA:\n"
            "  ① GANCHO (1 frase impactante + emoji).\n"
            "  ② CUERPO EDUCATIVO: Extrae 2-3 datos/beneficios/consejos/advertencias "
            "reales del tema en lista numerada con emojis (1️⃣ 2️⃣ 3️⃣). "
            "Cada punto: 2-3 frases que realmente ENSEÑEN algo.\n"
            "  ③ CTA (guarda, comenta, sigue).\n"
            "  ④ 4-5 hashtags relevantes.\n"
            "Ejemplo real para 'déficit calórico':\n"
            "\n"
            "¿Quieres perder grasa sin pasar hambre? 🔥\n"
            "El déficit calórico es la clave, pero mal hecho juega en tu contra:\n"
            "1️⃣ Quema grasa sostenible: Consume 300-500 kcal menos al día "
            "para perder peso sin sacrificar músculo ni energía.\n"
            "2️⃣ No te excedas: Un déficit muy agresivo relentiza tu "
            "metabolismo y eleva el cortisol, saboteando tu progreso.\n"
            "3️⃣ Consulta a un profesional: Un nutriólogo personaliza tu "
            "plan según tu cuerpo y objetivos.\n"
            "¡Guarda este Reel y compártelo! 🎯\n"
            "#DeficitCalorico #NutricionDeportiva #PerderGrasa #FitnessTips #Salud\n"

            "- 'personaje_base': Descripción FÍSICA DETALLADA en INGLÉS del personaje principal. "
            "Incluye: género, etnia, edad aprox, pelo, tipo de cuerpo, ropa de gym. "
            "Ej: 'latina athletic woman, 28, long black ponytail, black sports bra, navy leggings, muscular arms'.\n"
            f"{instruccion_genero}\n"
            
            "- 'escenas': Array de 4-6 escenas. Cada una con:\n"
            "  * 'orden': número (1,2,3...)\n"
            "  * 'duracion_seg': 2-8 segundos (total 25-30s)\n"
            "  * 'subtitulo': Texto EXACTO del subtítulo en español (1-2 frases). "
            "Escena 1=HOOK impactante (5-8 palabras), 2-3=CONTEXTO, 4-5=PAYOFF (tip/ciencia), última=CTA.\n"
            "  * 'tipo_escena': 'hook'|'contexto'|'payoff'|'cta'\n"
            "  * 'prompt_video': Descripción en INGLÉS para generar ESTA escena. "
            "DEBE empezar con el 'personaje_base' EXACTAMENTE IGUAL, luego añadir acción/ángulo. "
            "Varía ángulos: close-up, wide shot, side angle, desde atrás.\n"
            f"  IMPORTANTE — ESTILO VISUAL: El video debe usar el estilo '{estilo_visual}'. "
            "Incluye SIEMPRE al FINAL de cada 'prompt_video' la frase del estilo. "
            f"Referencia de estilo: {ESTILOS_VISUALES.get(estilo_visual, ESTILOS_VISUALES['default'])}\n\n"
            
            "DURACIÓN TOTAL: 22-30 segundos sumando todas las escenas.\n"
            "IMPORTANTE: Responde SOLO con el JSON, sin markdown."
        )
    
    user_prompt = (
        f"Crea un guion para un Reel de fitness: '{tema_libro}'. "
        f"Devuelve SOLO el JSON."
    )
 # deepseek/deepseek-chat  google/gemini-2.5-flash
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 2500
    }
    
    print(f"🎬 Generando guion de Reel (tema: '{tema_libro[:50]}...', género: {genero})...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error en OpenRouter: {response.text}")
        return {}
    
    try:
        contenido = response.json()["choices"][0]["message"]["content"]
        contenido = contenido.strip()
        if contenido.startswith("```"):
            contenido = contenido.split("```")[1]
            if contenido.startswith("json"):
                contenido = contenido[4:]
            contenido = contenido.strip()
        
        datos = json.loads(contenido)
        
        if "bloques" in datos:
            # ── Formato Kling (2 bloques) ─────────────────────
            blqs = datos["bloques"]
            total_subs = sum(len(b.get("subtitulos", [])) for b in blqs)
            print(f"✅ Guion Kling: {len(blqs)} bloques, {total_subs} subtítulos")
            for i, b in enumerate(blqs):
                subs = [s.get("texto", "")[:50] for s in b.get("subtitulos", [])]
                print(f"   🎬 Bloque {i+1}: {len(subs)} subs — {subs}")
            return datos
            
        elif "escenas" in datos:
            # ── Formato Leonardo/Seedance (4-6 escenas) ───────
            total_segundos = sum(e.get("duracion_seg", 0) for e in datos["escenas"])
            print(f"✅ Guion Leonardo: {len(datos['escenas'])} escenas, {total_segundos}s total")
            for e in datos["escenas"]:
                print(f"   🎞️  Esc {e.get('orden')}: [{e.get('tipo_escena')}] {e.get('duracion_seg')}s — \"{e.get('subtitulo', '')[:60]}...\"")
            return datos
            
        else:
            print("❌ El guion no tiene 'escenas' ni 'bloques'. Respuesta inválida.")
            return {}
        
    except Exception as e:
        print(f"Error parseando guion: {e}")
        print(f"Contenido recibido: {contenido[:300] if 'contenido' in dir() else 'N/A'}...")
        return {}
def _generar_descripcion_campos_ia(layout_config):
    """Genera la descripción de campos para el system_prompt basado en el layout."""
    elementos = layout_config.get("elementos", [])
    
    lineas = []
    idx = 1
    
    for elem in elementos:
        tipo = elem.get("tipo")
        
        # Elemento texto estándar
        if tipo == "texto":
            placeholder = elem.get("placeholder")
            valor_fijo = elem.get("valor_fijo")
            if valor_fijo:
                continue
            
            fuente = elem.get("fuente", "regular")
            mayus = elem.get("mayusculas", False)
            tamano_max = elem.get("tamano_max", 50)
            
            if tamano_max >= 70:
                palabras = "4 a 6 palabras"
            elif tamano_max >= 40:
                palabras = "6 a 10 palabras"
            else:
                palabras = "10 a 15 palabras"
            
            extras = []
            if mayus:
                extras.append("en MAYÚSCULAS")
            if fuente == "heavy":
                extras.append("impactante y poderoso")
            
            extra_str = f" ({', '.join(extras)})" if extras else ""
            
            lineas.append(
                f"{idx}. '{placeholder}': Texto de {palabras}{extra_str} relacionado con el tema."
            )
            idx += 1
        
        # Elemento texto_bicolor (párrafo con palabras alternadas blanco/amarillo)
        elif tipo == "texto_bicolor":
            bloques = elem.get("bloques", [])
            for i, bloque in enumerate(bloques):
                key = bloque.get("texto", "")
                if not key:
                    continue
                color_rgb = bloque.get("color", [255, 255, 255])
                if color_rgb == [255, 204, 0]:
                    color_desc = "amarillo"
                    palabras_desc = "1-2 palabras clave en AMARILLO"
                else:
                    color_desc = "blanco"
                    palabras_desc = "4-8 palabras en blanco"
                lineas.append(
                    f"{idx}. '{key}': {palabras_desc} (parte {i+1} del párrafo bicolor inferior)."
                )
                idx += 1
    
    # Si no hay elementos visuales (layout mínimo), describir campos fijos
    if not lineas:
        campos = layout_config.get("campos_ia", [])
        for campo in campos:
            if campo == "prompt_title":
                lineas.append(f"{idx}. 'prompt_title': Un título corto y llamativo (máximo 6-8 palabras) para el tema.")
                idx += 1
            elif campo == "prompt_tip":
                lineas.append(f"{idx}. 'prompt_tip': Un consejo educativo breve (máximo 15 palabras) que enseñe algo valioso del tema.")
                idx += 1
    
    return "\n".join(lineas) + "\n"


# ==========================================
# ENSAMBLADOR DINÁMICO DE PROMPT PARA LEONARDO
# ==========================================
def ensamblar_prompt_leonardo(estilo_base, image_prompt_details, tipo_visual, genero="libre"):
    """
    Combina el estilo base + descripción del tema + fragmento visual dinámico
    en un único prompt optimizado para Leonardo AI, según la clasificación
    que la IA hizo del tema.
    
    Parámetro 'genero': controla el género del sujeto en el prompt.
    """
    fragmento = BLOQUES_VISUALES_DINAMICOS.get(tipo_visual, BLOQUES_VISUALES_DINAMICOS["entrenamiento_general"])
    
    # Construir instrucción de género (solo si el estilo base no la especifica ya)
    estilo_lower = estilo_base.lower()
    ya_tiene_genero = any(p in estilo_lower for p in ["woman", "female", " man ", "male ", "masculine", "feminine"])
    
    if genero == "female" and not ya_tiene_genero:
        sufijo_genero = "The subject is a female athlete, muscular woman, feminine physique. "
    elif genero == "male" and not ya_tiene_genero:
        sufijo_genero = "The subject is a male athlete, muscular man, masculine physique. "
    elif genero == "sin_personaje" and not ya_tiene_genero:
        sufijo_genero = "NO people, no human figures. The subject is equipment/supplements/food/objects only. "
    elif ya_tiene_genero and genero in ("female", "male"):
        print(f"   ⚠️  El estilo '{estilo_base[:60]}...' ya especifica género → se ignora genero='{genero}'")
        sufijo_genero = ""
    else:
        sufijo_genero = ""
    
    prompt = (
        f"{estilo_base}. "
        f"Main subject: {image_prompt_details}. "
        f"Composition: {fragmento} "
        f"{sufijo_genero}"
        "The bottom area features a clean dark space with a solid dark gradient reserved for text overlay. "
        "Single focused subject, professional athletic anatomy, perfect proportions, "
        "no floating objects, clean composition."
    )
    
    print(f"🧩 Prompt ensamblado dinámicamente | tipo_visual='{tipo_visual}' | estilo={estilo_base[:50]}...")
    return prompt


def _obtener_sufijo_genero(estilo_base, genero):
    """
    Devuelve un sufijo de género para el prompt de Leonardo.
    Si el estilo base ya especifica género, devuelve cadena vacía y emite un warning.
    """
    if genero == "libre":
        return ""
    
    estilo_lower = estilo_base.lower()
    ya_tiene_genero = any(p in estilo_lower for p in ["woman", "female", " man ", "male ", "masculine", "feminine"])
    
    if ya_tiene_genero and genero in ("female", "male", "sin_personaje"):
        print(f"   ⚠️  El estilo ya especifica género → se ignora genero_personaje='{genero}'")
        return ""
    
    if genero == "female":
        return "Female athlete, muscular woman, feminine physique. "
    elif genero == "male":
        return "Male athlete, muscular man, masculine physique. "
    elif genero == "sin_personaje":
        return "NO people, no human figures, no athletes. Subject is equipment, supplements, food, or objects only. "
    
    return ""


# ==========================================
# LLAMADA A LA API DE LEONARDO AI
# ==========================================
def generar_imagen_leonardo(prompt_detallado, titulo_en_imagen, estilo_nombre, datos_ia=None, usar_texto_en_prompt=False, tipo_visual=None, genero="libre"):
    url_base = "https://cloud.leonardo.ai/api/rest/v2/generations"
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Combinar el estilo elegido con el prompt específico del tema
    estilo_base = ESTILOS_VISUALES.get(estilo_nombre, ESTILOS_VISUALES["default"])
    
    if usar_texto_en_prompt and datos_ia:
        # Extraer título y tip de cualquier layout automáticamente
        titulo = (
            datos_ia.get("image_title") or
            f"{datos_ia.get('word1','')} {datos_ia.get('word2','')}".strip() or
            datos_ia.get("hero_title") or
            datos_ia.get("quote_text") or
            datos_ia.get("prompt_title") or ""
        )
        tip = (
            datos_ia.get("image_subtitle") or
            datos_ia.get("tip_text") or
            datos_ia.get("hero_subtitle") or
            datos_ia.get("prompt_tip") or ""
        )
        
        # Construir sufijo de género (solo si el estilo base no lo especifica ya)
        sufijo_genero = _obtener_sufijo_genero(estilo_base, genero)
        
        prompt_final = (
            f"{estilo_base} + "
            f"Text overlay included on image with Title: '{titulo}'"
        )
        if tip:
            prompt_final += f" and Quick Tip: '{tip}'"
        if sufijo_genero:
            prompt_final += f". {sufijo_genero}"
        
        print(f"📝 Texto en prompt de Leonardo — Titulo: {titulo} | Tip: {tip or '❌ VACÍO'} | Género: {genero}")
    else:
        # Usar ensamblador dinámico si hay tipo_visual, o prompt tradicional como fallback
        if tipo_visual and tipo_visual in BLOQUES_VISUALES_DINAMICOS:
            prompt_final = ensamblar_prompt_leonardo(estilo_base, prompt_detallado, tipo_visual, genero)
        else:
            # Fallback: versión sin ensamblador dinámico
            sufijo_genero = _obtener_sufijo_genero(estilo_base, genero)
            prompt_final = (
                f"{prompt_detallado}, {estilo_base}. "
                f"{sufijo_genero}"
                "Single focused subject, professional athletic anatomy, perfect proportions, "
                "no floating objects, clean composition, vast empty upper space for typography overlay"
            )
    
    print(f"📤 Prompt enviado a Leonardo:\n{prompt_final}\n")
    
    payload = {
        "model": "flux-dev",
        "parameters": {
            "prompt": prompt_final,
            "negative_prompt": (
                "deformed anatomy, twisted body, extra limbs, fused fingers, "
                "ugly, distorted face, bad proportions, disfigured, watermark, text, "
                "blurry, low quality, head out of frame, unnatural pose"
            ),
            "width": 1024,
            "height": 1024,
            "quantity": 1,
            "prompt_enhance": "ON"
        },
        "public": False
    }

    # 1. Solicitar generación
    response = requests.post(url_base, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error al iniciar generación en Leonardo: {response.text}")
        return None
    
    resp_data = response.json()
    # Intentar estructuras de respuesta v2 (generate.generationId) y v1 legacy
    generation_id = (
        resp_data.get("generate", {}).get("generationId") or
        resp_data.get("sdGenerationJob", {}).get("generationId") or
        resp_data.get("generationId") or
        resp_data.get("id")
    )
    if not generation_id:
        print(f"No se encontró generationId en la respuesta. Respuesta: {json.dumps(resp_data, indent=2)[:500]}")
        return None

    print(f"Generando imagen en Leonardo (ID: {generation_id})... Esperando resultado...")

    import time
    time.sleep(10)

    # 2. Obtener URL de la imagen generada (Polling) — GET en v1 (confirma generations_by_pk)
    url_status = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
    for _ in range(6):
        res_status = requests.get(url_status, headers=headers)
        if res_status.status_code == 200:
            data = res_status.json()
            images = data.get("generations_by_pk", {}).get("generated_images", [])
            if images:
                return images[0].get("url")
        time.sleep(10)
        
    return None

def descargar_imagen(url_imagen, ruta_destino):
    res = requests.get(url_imagen)
    if res.status_code == 200:
        with open(ruta_destino, "wb") as f:
            f.write(res.content)
        print(f"Imagen guardada exitosamente en: {ruta_destino}")

# ==========================================
# ==========================================
# MOTOR GENÉRICO DE RENDERIZADO DE LAYOUTS
# ==========================================
def render_layout(imagen_path, layout_config, datos_ia, salida_path=None):
    """
    Motor genérico que renderiza cualquier layout sobre una imagen.
    Itera sobre los elementos del layout y los dibuja en orden.
    """
    if salida_path is None:
        salida_path = imagen_path
    
    img = Image.open(imagen_path).convert("RGBA")
    ancho, alto = img.size
    overlay = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Contexto de renderizado (guarda posiciones calculadas para referencias dinámicas)
    ctx = {
        "ancho": ancho, "alto": alto,
        "ultima_y": 0, "ultima_x": 0,
        "fuentes": {},
        "posiciones": {},  # Guarda posiciones de elementos previos para referencias
    }
    
    # 1. Aplicar overlays (degradados)
    for ov in layout_config.get("overlays", []):
        _aplicar_overlay(overlay, ov, ancho, alto)
    
    # 2. Renderizar elementos en orden
    for i, elem in enumerate(layout_config.get("elementos", [])):
        tipo = elem.get("tipo")
        if tipo == "texto":
            _render_texto(overlay, elem, datos_ia, ctx)
        elif tipo == "linea":
            _render_linea(overlay, elem, ctx)
        elif tipo == "icono_emoji":
            _render_icono_emoji(overlay, elem, ctx)
        elif tipo == "icono_png":
            _render_icono_png(img, elem, ctx)
        elif tipo == "marca_con_lineas":
            _render_marca_con_lineas(overlay, elem, ctx)
        elif tipo == "texto_bicolor":
            _render_texto_bicolor(overlay, elem, datos_ia, ctx)
    
    # 3. Componer y guardar
    img_final = Image.alpha_composite(img, overlay)
    img_final = img_final.convert("RGB")
    img_final.save(salida_path, "JPEG", quality=95)
    
    print(f"✅ Layout '{layout_config.get('nombre')}' renderizado en: {salida_path}")


# ==========================================
# HELPERS DE RENDERIZADO
# ==========================================

def _obtener_fuente(nombre_fuente, tamanio, ctx):
    """Cache de fuentes para no recargarlas cada vez."""
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


def _calcular_posicion(elem, ctx, ancho_texto=0, alto_texto=0):
    """Calcula la posición (x, y) en píxeles para un elemento."""
    ancho = ctx["ancho"]
    alto = ctx["alto"]
    posiciones = ctx["posiciones"]
    
    x_pct = elem.get("x_pct", 0)
    y_pct = elem.get("y_pct", 0)
    alineacion = elem.get("alineacion", "izquierda")
    
    # Resolver referencias dinámicas en X
    if isinstance(x_pct, str):
        if x_pct == "despues_de_word1":
            if "word1_x_fin" in posiciones:
                x = posiciones["word1_x_fin"] + 10
            else:
                x = int(ancho * 0.55)
        elif x_pct == "despues_de_icono":
            if "icono_x_fin" in posiciones:
                x = posiciones["icono_x_fin"] + 8
            else:
                x = int(ancho * 0.12)
        else:
            x = int(ancho * 0.05)
    else:
        x = int(ancho * x_pct / 100)
    
    # Ajustar por alineación
    if alineacion == "centro":
        x = int(ancho / 2)
    elif alineacion == "derecha":
        x = int(ancho * 0.95) - ancho_texto
    
    # Resolver referencias dinámicas en Y
    if isinstance(y_pct, str):
        if y_pct == "centro_en_overlay_inferior":
            altura_bottom = int(alto * 0.30)
            y = alto - altura_bottom + (altura_bottom - alto_texto) // 2
        elif y_pct == "misma_linea_que_word1":
            y = posiciones.get("word1_y", int(alto * 0.10))
        elif y_pct == "misma_linea_que_icono":
            y = posiciones.get("icono_y", int(alto * 0.28))
        elif y_pct == "debajo_de_word1":
            y = posiciones.get("word1_y_fin", int(alto * 0.20)) + 5
        elif y_pct == "debajo_de_word2":
            y = posiciones.get("word2_y_fin", int(alto * 0.20)) + 5
        elif y_pct == "debajo_de_titulo":
            y = posiciones.get("titulo_y_fin", int(alto * 0.20)) + 5
        elif y_pct == "debajo_de_separador":
            y = posiciones.get("separador_y", int(alto * 0.24)) + 8
        elif y_pct == "debajo_de_quicktip_label":
            y = posiciones.get("quicktip_label_y_fin", int(alto * 0.33)) + 6
        elif y_pct == "debajo_de_hero_title":
            y = posiciones.get("hero_title_y_fin", int(alto * 0.78)) + 10
        elif y_pct == "debajo_de_quote":
            y = posiciones.get("quote_y_fin", int(alto * 0.55)) + 10
        else:
            y = posiciones.get("ultima_y", int(alto * 0.10)) + 10
    else:
        y = int(alto * y_pct / 100)
    
    # Aplicar offset
    offset = elem.get("offset_y_pct", 0)
    if offset:
        y += int(alto * offset / 100)
    
    return x, y


def _calcular_tamanio_fuente_optimo(texto, ancho_max, ruta_fuente, tamanio_min=24, tamanio_max=80):
    """Búsqueda binaria del tamaño de fuente óptimo."""
    if not texto:
        return tamanio_min
    lo, hi = tamanio_min, tamanio_max
    mejor = tamanio_min
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            font = ImageFont.truetype(ruta_fuente, mid) if ruta_fuente and os.path.exists(ruta_fuente) else ImageFont.load_default()
            lineas = texto.split('\n')
            cabe = all((font.getbbox(l)[2] - font.getbbox(l)[0]) <= ancho_max for l in lineas if l)
            if cabe:
                mejor = mid
                lo = mid + 1
            else:
                hi = mid - 1
        except:
            hi = mid - 1
    return mejor


def _dividir_texto_lineas(texto, font, ancho_max):
    """Divide texto en líneas para que quepa en ancho_max."""
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


def _aplicar_overlay(overlay_img, ov_config, ancho, alto):
    """Aplica un gradiente vertical como overlay."""
    y_inicio = int(alto * ov_config["y_inicio_pct"] / 100)
    altura = int(alto * ov_config["altura_pct"] / 100)
    color = ov_config["color"]
    alpha_ini = ov_config["alpha_inicio"]
    alpha_fin = ov_config["alpha_fin"]
    
    for i in range(altura):
        y = y_inicio + i
        if y < 0 or y >= alto:
            continue
        t = i / max(altura - 1, 1)
        alpha = int(alpha_ini + (alpha_fin - alpha_ini) * t)
        alpha = max(0, min(255, alpha))
        if alpha <= 0:
            continue
        rgba = (color[0], color[1], color[2], alpha)
        for x in range(ancho):
            overlay_img.putpixel((x, y), rgba)


def _render_texto(overlay, elem, datos_ia, ctx):
    """Renderiza un elemento de tipo texto."""
    placeholder = elem.get("placeholder")
    valor_fijo = elem.get("valor_fijo")
    
    # Obtener el texto
    if valor_fijo:
        texto = valor_fijo
    elif placeholder and placeholder in datos_ia:
        texto = str(datos_ia.get(placeholder, ""))
    else:
        return  # Sin texto que renderizar
    
    if not texto:
        return
    
    # Aplicar sufijo si existe
    sufijo = elem.get("sufijo", "")
    if sufijo and not texto.endswith(sufijo):
        texto = texto + sufijo
    
    # Mayúsculas
    if elem.get("mayusculas"):
        texto = texto.upper()
    
    ancho = ctx["ancho"]
    alto = ctx["alto"]
    ancho_max = int(ancho * elem.get("ancho_max_pct", 80) / 100)
    
    # Calcular tamaño de fuente óptimo
    fuente_nombre = elem.get("fuente", "regular")
    ruta_fuente_base = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if fuente_nombre in ("bold", "heavy") else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    
    tamanio = _calcular_tamanio_fuente_optimo(
        texto, ancho_max, ruta_fuente_base,
        elem.get("tamano_min", 22), elem.get("tamano_max", 60)
    )
    
    font = _obtener_fuente(fuente_nombre, tamanio, ctx)
    
    # Dividir en líneas
    lineas = _dividir_texto_lineas(texto, font, ancho_max)
    
    # Calcular altura total del bloque
    alturas = []
    for l in lineas:
        bbox = font.getbbox(l)
        alturas.append(bbox[3] - bbox[1])
    altura_total = sum(alturas) + (len(lineas) - 1) * 6
    
    # Calcular posición
    ancho_primera = font.getbbox(lineas[0])[2] - font.getbbox(lineas[0])[0]
    x, y = _calcular_posicion(elem, ctx, ancho_primera, altura_total)
    
    # Colores
    rgb = elem.get("color_rgb", [255, 255, 255])
    alpha = elem.get("color_alpha", 255)
    color_texto = tuple(rgb) + (alpha,)
    color_sombra = (0, 0, 0, 180)
    
    sombra = elem.get("sombra", False)
    sombra_offset = elem.get("sombra_offset", 2)
    
    # Dibujar cada línea
    draw = ImageDraw.Draw(overlay)
    y_actual = y
    alineacion = elem.get("alineacion", "izquierda")
    
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
    
    # Guardar posición para referencias futuras
    nombre_elem = elem.get("id_ref") or elem.get("placeholder") or "elem"
    ctx["posiciones"][f"{nombre_elem}_x"] = x
    ctx["posiciones"][f"{nombre_elem}_y"] = y
    ctx["posiciones"][f"{nombre_elem}_x_fin"] = x + ancho_primera
    ctx["posiciones"][f"{nombre_elem}_y_fin"] = y_actual
    ctx["posiciones"]["ultima_y"] = y_actual
    ctx["posiciones"]["ultima_x"] = x


def _render_linea(overlay, elem, ctx):
    """Renderiza una línea horizontal decorativa."""
    ancho = ctx["ancho"]
    alto  = ctx["alto"]

    x1 = int(ancho * elem.get("x1_pct", 5)  / 100)
    x2 = int(ancho * elem.get("x2_pct", 50) / 100)

    # Resolver y igual que _calcular_posicion para respetar referencias dinámicas
    y_pct = elem.get("y_pct", 0)
    if isinstance(y_pct, str):
        posiciones = ctx["posiciones"]
        if y_pct == "debajo_de_word2":
            y = posiciones.get("word2_y_fin", int(alto * 0.20)) + 8
        elif y_pct == "debajo_de_word1":
            y = posiciones.get("word1_y_fin", int(alto * 0.20)) + 8
        elif y_pct == "debajo_de_titulo":
            y = posiciones.get("titulo_y_fin", int(alto * 0.20)) + 8
        elif y_pct == "debajo_de_quote":
            y = posiciones.get("quote_y_fin", int(alto * 0.55)) + 8
        else:
            y = posiciones.get("ultima_y", int(alto * 0.20)) + 8
    else:
        y = int(alto * y_pct / 100)

    grosor = elem.get("grosor", 2)
    rgb    = elem.get("color_rgb", [180, 180, 180])
    alpha  = elem.get("color_alpha", 200)
    color  = tuple(rgb) + (alpha,)

    draw = ImageDraw.Draw(overlay)
    draw.rectangle([x1, y, x2, y + grosor], fill=color)

    ctx["posiciones"]["separador_y"] = y + grosor


def _render_icono_emoji(overlay, elem, ctx):
    """
    Renderiza un ícono usando formas geométricas (no emoji Unicode,
    ya que DejaVu Sans no los soporta en color).
    El tipo de ícono se define por el campo 'emoji' del elemento:
      💡  → círculo amarillo + punto blanco (foco)
      🔥  → triángulo naranja + rojo (fuego)
      ⭐  → círculo dorado (estrella)
      default → cuadrado blanco
    """
    emoji   = elem.get("emoji", "💡")
    tamanio = elem.get("tamano_px", 36)
    draw    = ImageDraw.Draw(overlay)

    # Calcular posición base
    x, y = _calcular_posicion(elem, ctx, tamanio, tamanio)

    if elem.get("centrado"):
        x = ctx["ancho"] // 2 - tamanio // 2

    r = tamanio // 2  # radio

    if emoji == "💡":
        # Círculo amarillo brillante
        draw.ellipse([x, y, x + tamanio, y + tamanio],
                     fill=(255, 210, 0, 230))
        # Punto blanco interior
        inner = tamanio // 4
        cx, cy = x + r, y + r
        draw.ellipse([cx - inner // 2, cy - inner // 2,
                      cx + inner // 2, cy + inner // 2],
                     fill=(255, 255, 255, 200))

    elif emoji == "🔥":
        # Triángulo naranja (fuego)
        pts = [x + r, y,
               x + tamanio, y + tamanio,
               x, y + tamanio]
        draw.polygon(pts, fill=(255, 100, 0, 220))
        # Triángulo rojo interior
        inner = tamanio // 3
        pts2 = [x + r, y + inner,
                x + tamanio - inner, y + tamanio,
                x + inner, y + tamanio]
        draw.polygon(pts2, fill=(220, 40, 0, 200))

    else:
        # Default: círculo blanco semi-transparente
        draw.ellipse([x, y, x + tamanio, y + tamanio],
                     fill=(255, 255, 255, 160))

    # Guardar posición para referencias dinámicas posteriores
    ctx["posiciones"]["icono_x"]     = x
    ctx["posiciones"]["icono_y"]     = y
    ctx["posiciones"]["icono_x_fin"] = x + tamanio + 8
    ctx["posiciones"]["icono_y_fin"] = y + tamanio


def _render_icono_png(imagen_base, elem, ctx):
    """Pega un icono PNG con transparencia desde assets/."""
    ruta_icono = elem.get("ruta", "")
    if not os.path.exists(ruta_icono):
        ruta_icono = os.path.join("assets", ruta_icono)
    
    if not os.path.exists(ruta_icono):
        print(f"⚠️ Icono no encontrado: {ruta_icono}")
        return
    
    icono = Image.open(ruta_icono).convert("RGBA")
    nuevo_ancho = elem.get("ancho_px", icono.width)
    if nuevo_ancho != icono.width:
        ratio = nuevo_ancho / icono.width
        nuevo_alto = int(icono.height * ratio)
        icono = icono.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
    
    x, y = _calcular_posicion(elem, ctx, icono.width, icono.height)
    imagen_base.paste(icono, (x, y), icono)
    
    ctx["posiciones"]["icono_x_fin"] = x + icono.width + 4


# ==========================================
# RENDERIZADORES PARA LAYOUTS PERSONALIZADOS
# ==========================================

def _render_marca_con_lineas(overlay, elem, ctx):
    """
    Renderiza una etiqueta de marca centrada con líneas horizontales
    decorativas a ambos lados. Ideal para sellos como 'BODY IQ' o 'SABÍAS QUE'.
    
    Resultado visual:
        ────────  BODY IQ  ────────
    """
    texto = elem.get("valor_fijo", elem.get("placeholder", "BODY IQ")).upper()
    ancho_img = ctx["ancho"]
    alto_img = ctx["alto"]
    
    y_pct = elem.get("y_pct", 74)
    y = int(alto_img * y_pct / 100)
    
    rgb = elem.get("color_rgb", [255, 204, 0])
    color = tuple(rgb) + (220,)
    
    tamano = elem.get("tamano", 18)
    font = _obtener_fuente("bold", tamano, ctx)
    draw = ImageDraw.Draw(overlay)
    
    bbox = font.getbbox(texto)
    ancho_texto = bbox[2] - bbox[0]
    alto_texto = bbox[3] - bbox[1]
    
    x_centro = ancho_img // 2
    linea_largo = 55
    espacio = 14
    grosor_linea = 2
    
    # Línea izquierda
    x_linea_izq = x_centro - ancho_texto // 2 - espacio - linea_largo
    y_centro_linea = y + alto_texto // 2 - grosor_linea // 2
    draw.rectangle(
        [x_linea_izq, y_centro_linea, x_linea_izq + linea_largo, y_centro_linea + grosor_linea],
        fill=color
    )
    
    # Línea derecha
    x_linea_der = x_centro + ancho_texto // 2 + espacio
    draw.rectangle(
        [x_linea_der, y_centro_linea, x_linea_der + linea_largo, y_centro_linea + grosor_linea],
        fill=color
    )
    
    # Texto centrado
    texto_x = x_centro - ancho_texto // 2
    draw.text((texto_x, y), texto, font=font, fill=color)
    
    ctx["posiciones"]["marca_y_fin"] = y + alto_texto + 10
    print(f"   🏷️  Marca renderizada: '{texto}' en y={y}px")


def _render_texto_bicolor(overlay, elem, datos_ia, ctx):
    """
    Renderiza un párrafo corrido con palabras en colores alternados
    (blanco + amarillo) en la parte inferior de la imagen.
    
    Los 'bloques' definen segmentos de texto y su color:
      - text_part1  → blanco
      - keyword_yellow1 → amarillo
      - text_part2  → blanco
      - keyword_yellow2 → amarillo
    
    Todo se concatena, se convierte a mayúsculas, y se wrappea
    automáticamente si excede el ancho máximo.
    """
    bloques = elem.get("bloques", [])
    if not bloques:
        return
    
    ancho_img = ctx["ancho"]
    alto_img = ctx["alto"]
    ancho_max = int(ancho_img * elem.get("ancho_max_pct", 84) / 100)
    x = int(ancho_img * elem.get("x_pct", 8) / 100)
    
    y = int(alto_img * elem.get("y_pct", 80) / 100)
    tamano = elem.get("tamano", 24)
    
    fuente_nombre = elem.get("fuente", "bold")
    
    font = _obtener_fuente(fuente_nombre, tamano, ctx)
    draw = ImageDraw.Draw(overlay)
    
    # Construir texto completo concatenando bloques (todo en MAYÚSCULAS)
    texto_completo = ""
    for bloque in bloques:
        key = bloque.get("texto", "")
        if key and key in datos_ia:
            fragmento = str(datos_ia[key]).strip().upper()
        else:
            fragmento = ""
        if fragmento:
            texto_completo += fragmento + " "
    texto_completo = texto_completo.strip()
    
    if not texto_completo:
        print("   ⚠️ texto_bicolor: sin datos para renderizar (IA no generó los campos)")
        return
    
    # Dividir en líneas según ancho máximo
    lineas = _dividir_texto_lineas(texto_completo, font, ancho_max)
    
    # Renderizar línea por línea, pintando cada palabra con su color
    y_actual = y
    espacio_ancho = font.getbbox(" ")[2]
    
    for linea in lineas:
        palabras = linea.split()
        x_actual = x
        for palabra in palabras:
            # Determinar color: buscar si esta palabra pertenece a algún bloque amarillo
            color_palabra = (255, 255, 255, 230)  # default blanco
            for bloque in bloques:
                key = bloque.get("texto", "")
                if key and key in datos_ia:
                    fragmento_upper = str(datos_ia[key]).strip().upper()
                    if palabra in fragmento_upper.split():
                        rgb = bloque.get("color", [255, 204, 0])
                        color_palabra = tuple(rgb) + (230,)
                        break
            
            bbox_palabra = font.getbbox(palabra)
            ancho_palabra = bbox_palabra[2] - bbox_palabra[0]
            draw.text((x_actual, y_actual), palabra, font=font, fill=color_palabra)
            x_actual += ancho_palabra + espacio_ancho
        
        altura_linea = font.getbbox(linea)[3] - font.getbbox(linea)[1] if linea else tamano
        y_actual += altura_linea + 4
    
    ctx["posiciones"]["texto_bicolor_y_fin"] = y_actual
    ctx["posiciones"]["ultima_y"] = y_actual
    print(f"   ✏️  Texto bicolor renderizado: {len(lineas)} línea(s) en y={y}px → y_fin={y_actual}px")


# FLUJO PRINCIPAL DE EJECUCIÓN
# ==========================================
def ejecutar_pipeline(lista_temas, estilo_elegido="default", layout_elegido="classic_centered", usar_pillow=True, usar_texto_en_prompt=False, reiniciar_historial=False, genero_personaje="libre"):
    """
    Pipeline principal de generación de contenido.
    
    Parámetro 'genero_personaje':
        - "female": fuerza personaje femenino en las imágenes
        - "male": fuerza personaje masculino en las imágenes
        - "libre": sin restricción, la IA decide (comportamiento por defecto)
        - "sin_personaje": sin personas, solo objetos/equipamiento/escenarios
    """
    historial = {"temas_procesados": []} if reiniciar_historial else cargar_historial()
    temas_ya_vistos = [item["tema"] for item in historial["temas_procesados"]]
    
    contador = len(historial["temas_procesados"]) + 1

    # Obtener el layout config (o layout mínimo si Pillow deshabilitado)
    if usar_pillow:
        layout = obtener_layout(layout_elegido)
        print(f"🎨 Layout activo: {layout['nombre']} — {layout['descripcion'][:50]}...")
    else:
        layout = {
            "nombre": "solo_leonardo",
            "descripcion": "Modo sin Pillow — IA genera caption + título + tip para prompt de Leonardo",
            "campos_ia": ["caption", "image_prompt_details", "prompt_title", "prompt_tip"],
            "elementos": [],
            "overlays": [],
        }
        print(f"🎨 Modo: Solo Leonardo (sin layout, sin Pillow)")

    print(f"👤 Modo género personaje: {genero_personaje}")

    for tema in lista_temas:
        if tema in temas_ya_vistos:
            print(f"-> Saltando (Ya procesado): {tema}")
            continue
            
        print(f"\n========================================")
        print(f"Procesando [{contador}]: {tema}")
        print(f"========================================")

        try:
            # 1. Generar textos y prompts con Claude/DeepSeek vía OpenRouter
            datos_ia = generar_texto_y_prompt_ia(tema, estilo_elegido, layout, genero_personaje)
            caption = datos_ia.get("caption", "")
            image_prompt_details = datos_ia.get("image_prompt_details", "")
            tipo_visual = datos_ia.get("tipo_visual", "entrenamiento_general")

            # Validar que caption y image_prompt_details estén presentes
            if not caption or not image_prompt_details:
                print("❌ La IA no generó caption o image_prompt_details. Saltando este tema.")
                print(f"   caption={'✅' if caption else '❌'} | image_prompt_details={'✅' if image_prompt_details else '❌'}")
                continue

            # 2. Generar imagen en Leonardo AI
            url_img = generar_imagen_leonardo(image_prompt_details, layout.get("nombre", "layout"), estilo_elegido, datos_ia, usar_texto_en_prompt, tipo_visual=tipo_visual, genero=genero_personaje)
            
            if url_img:
                # Nombres de archivo estructurados
                nombre_base = f"post_{contador:02d}_{layout_elegido}"
                ruta_img = os.path.join(CARPETA_OUTPUT, f"{nombre_base}.jpg")
                ruta_txt = os.path.join(CARPETA_OUTPUT, f"{nombre_base}.txt")

                # Descargar imagen
                descargar_imagen(url_img, ruta_img)

                # Renderizar layout con texto profesional (solo si usar_pillow=True)
                if usar_pillow:
                    render_layout(ruta_img, layout, datos_ia)
                else:
                    print(f"🖼️ Imagen sin texto Pillow — usando solo imagen de Leonardo")

                # Guardar archivo de texto con el caption
                with open(ruta_txt, "w", encoding="utf-8") as f:
                    f.write(caption)
                print(f"Caption guardado en: {ruta_txt}")

                # Registrar en el historial JSON
                historial["temas_procesados"].append({
                    "id": contador,
                    "tema": tema,
                    "estilo": estilo_elegido,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "imagen": f"{nombre_base}.jpg",
                    "texto": f"{nombre_base}.txt"
                })
                guardar_historial(historial)
                
                contador += 1
            else:
                print(f"⚠️ No se pudo obtener la imagen para el tema: {tema}")

        except Exception as e:
            print(f"❌ Error crítico procesando el tema '{tema}': {e}")

if __name__ == "__main__":
    # Lista de ejemplo extraída de tu libro de culturismo
   
   # temas_libro_culturismo_Schoenfeld = [
   # "Análisis de cargas ligeras vs cargas pesadas para el desarrollo muscular según Schoenfeld",
   # "¿Es obligatorio el fallo muscular? Perspectiva basada en la investigación de Schoenfeld",
   # "Estrés metabólico y oclusión vascular: Mecanismos secundarios de hipertrofia"
#]
    
    temas_libro_culturismo = [
        "Priorización de puntos débiles: Técnicas de aislamiento y frecuencia aumentada para corregir desequilibrios estéticos",
        "Psicología aplicada al culturismo: Técnicas de visualización, concentración y superación de la barrera mental",
        "Clasificación y estrategia según el somatotipo: Cómo adaptar el entrenamiento y la nutrición para ectomorfos, mesomorfos y endomorfos",
        "Principios de alta intensidad y entrenamiento avanzado: Uso de series trampa (cheating) y sistemas de doble división",
        "El arte de la pose y presentación escénica: Ejecución de posturas obligatorias y dominio del escenario",
        "Prevención y manejo de lesiones: Estrategias de recuperación articular, prevención de sobrecargas y cuidado del tejido conectivo"
    ]
    
    # Puedes cambiar el estilo aquí ("default", "cyberpunk", "minimalista")
    # y poner reiniciar_historial=True si quieres empezar desde cero.
   # LAYOUTS = {
   # "classic_centered": LAYOUT_CLASSIC_CENTERED,
   # "instagram_bold": LAYOUT_INSTAGRAM_BOLD,
   # "minimal_quote": LAYOUT_MINIMAL_QUOTE,
   # "dark_hero": LAYOUT_DARK_HERO,
        #}

    ejecutar_pipeline(
        lista_temas=temas_libro_culturismo, 
        estilo_elegido="default", 
        layout_elegido="body_iq_style",
        usar_pillow=True,
        usar_texto_en_prompt=False,
        reiniciar_historial=True,
        # genero_personaje: "female" | "male" | "libre" | "sin_personaje"
        genero_personaje="male"
    )
