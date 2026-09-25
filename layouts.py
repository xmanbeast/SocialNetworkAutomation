import json
import os

LAYOUT_BODY_IQ = {
    "nombre": "body_iq_style",
    "descripcion": "Estilo infográfico con etiqueta de marca, círculo superior y texto inferior bicolor.",
    "campos_ia": [
        "brand_label",
        "text_part1",
        "keyword_yellow1",
        "text_part2",
        "keyword_yellow2",
        "caption",
        "image_prompt_details"
    ],
    "overlays": [
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 30,
            "altura_pct": 70,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 0,
            "alpha_fin": 240
        }
    ],
    "elementos": [
        {
            "tipo": "marca_con_lineas",
            "placeholder": "brand_label",
            "valor_fijo": "BODY IQ",
            "x_pct": 50,
            "y_pct": 57,
            "tamano": 61,
            "color_rgb": [
                255,
                204,
                0
            ]
        },
        {
            "tipo": "texto_bicolor",
            "bloques": [
                {
                    "texto": "text_part1",
                    "color": [
                        255,
                        255,
                        255
                    ]
                },
                {
                    "texto": "keyword_yellow1",
                    "color": [
                        255,
                        204,
                        0
                    ]
                },
                {
                    "texto": "text_part2",
                    "color": [
                        255,
                        255,
                        255
                    ]
                },
                {
                    "texto": "keyword_yellow2",
                    "color": [
                        255,
                        204,
                        0
                    ]
                }
            ],
            "x_pct": 8,
            "y_pct": 66,
            "ancho_max_pct": 90,
            "fuente": "bold",
            "tamano": 42
        }
    ]
}

LAYOUT_CLASSIC_CENTERED = {
    "nombre": "classic_centered",
    "descripcion": "Título centrado arriba + subtítulo educativo abajo.",
    "campos_ia": [
        "image_title",
        "image_subtitle",
        "caption",
        "image_prompt_details"
    ],
    "overlays": [
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 0,
            "altura_pct": 28,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 160,
            "alpha_fin": 0
        },
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 70,
            "altura_pct": 30,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 0,
            "alpha_fin": 180
        }
    ],
    "elementos": [
        {
            "tipo": "texto",
            "placeholder": "image_title",
            "x_pct": 50,
            "y_pct": 5,
            "alineacion": "centro",
            "ancho_max_pct": 84,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 255,
            "fuente": "bold",
            "tamano_min": 36,
            "tamano_max": 90,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 4
        },
        {
            "tipo": "texto",
            "placeholder": "image_subtitle",
            "x_pct": 50,
            "y_pct": "centro_en_overlay_inferior",
            "alineacion": "centro",
            "ancho_max_pct": 84,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 240,
            "fuente": "regular",
            "tamano_min": 22,
            "tamano_max": 50,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 3
        }
    ]
}

LAYOUT_DARK_HERO = {
    "nombre": "dark_hero",
    "descripcion": "Estilo cinematográfico: ícono + título enorme abajo con gradiente dramático.",
    "campos_ia": [
        "hero_title",
        "hero_subtitle",
        "caption",
        "image_prompt_details"
    ],
    "overlays": [
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 60,
            "altura_pct": 40,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 0,
            "alpha_fin": 200
        }
    ],
    "elementos": [
        {
            "tipo": "icono_emoji",
            "emoji": "🔥",
            "x_pct": 50,
            "y_pct": 10,
            "tamano_px": 48,
            "centrado": True
        },
        {
            "tipo": "texto",
            "placeholder": "hero_title",
            "x_pct": 50,
            "y_pct": 70,
            "alineacion": "centro",
            "ancho_max_pct": 85,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 255,
            "fuente": "heavy",
            "tamano_min": 40,
            "tamano_max": 85,
            "mayusculas": True,
            "sombra": True,
            "sombra_offset": 5
        },
        {
            "tipo": "texto",
            "placeholder": "hero_subtitle",
            "x_pct": 50,
            "y_pct": "debajo_de_hero_title",
            "alineacion": "centro",
            "ancho_max_pct": 80,
            "color_rgb": [
                255,
                204,
                0
            ],
            "color_alpha": 240,
            "fuente": "regular",
            "tamano_min": 20,
            "tamano_max": 36,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 3
        }
    ]
}

LAYOUT_INSTAGRAM_BOLD = {
    "nombre": "instagram_bold",
    "descripcion": "Estilo Instagram/TikTok: label + palabra clave bicolor + QUICK TIP con ícono.",
    "campos_ia": [
        "label",
        "word1",
        "word2",
        "tip_text",
        "caption",
        "image_prompt_details"
    ],
    "overlays": [
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 25,
            "altura_pct": 65,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 0,
            "alpha_fin": 200
        }
    ],
    "elementos": [
        {
            "tipo": "texto",
            "placeholder": "label",
            "x_pct": 5,
            "y_pct": 30,
            "alineacion": "izquierda",
            "ancho_max_pct": 90,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 200,
            "fuente": "bold",
            "tamano_min": 33,
            "tamano_max": 42,
            "mayusculas": True,
            "sombra": True,
            "sombra_offset": 2,
            "sufijo": ":"
        },
        {
            "tipo": "texto",
            "placeholder": "word1",
            "x_pct": 5,
            "y_pct": 37,
            "alineacion": "izquierda",
            "ancho_max_pct": 90,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 255,
            "fuente": "heavy",
            "tamano_min": 72,
            "tamano_max": 108,
            "mayusculas": True,
            "sombra": True,
            "sombra_offset": 4
        },
        {
            "tipo": "texto",
            "placeholder": "word2",
            "x_pct": 5,
            "y_pct": "debajo_de_word1",
            "alineacion": "izquierda",
            "ancho_max_pct": 90,
            "color_rgb": [
                255,
                204,
                0
            ],
            "color_alpha": 255,
            "fuente": "heavy",
            "tamano_min": 72,
            "tamano_max": 108,
            "mayusculas": True,
            "sombra": True,
            "sombra_offset": 4
        },
        {
            "tipo": "linea",
            "x1_pct": 5,
            "x2_pct": 48,
            "y_pct": "debajo_de_word2",
            "color_rgb": [
                255,
                204,
                0
            ],
            "color_alpha": 200,
            "grosor": 3
        },
        {
            "tipo": "icono_emoji",
            "emoji": "💡",
            "x_pct": 5,
            "y_pct": "debajo_de_separador",
            "offset_y_pct": 1,
            "tamano_px": 32
        },
        {
            "tipo": "texto",
            "placeholder": None,
            "valor_fijo": "QUICK TIP:",
            "id_ref": "quicktip_label",
            "x_pct": "despues_de_icono",
            "y_pct": "misma_linea_que_icono",
            "alineacion": "izquierda",
            "ancho_max_pct": 55,
            "color_rgb": [
                255,
                204,
                0
            ],
            "color_alpha": 255,
            "fuente": "bold",
            "tamano_min": 33,
            "tamano_max": 42,
            "mayusculas": True,
            "sombra": True,
            "sombra_offset": 2
        },
        {
            "tipo": "texto",
            "placeholder": "tip_text",
            "x_pct": 5,
            "y_pct": "debajo_de_quicktip_label",
            "alineacion": "izquierda",
            "ancho_max_pct": 88,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 230,
            "fuente": "regular",
            "tamano_min": 30,
            "tamano_max": 39,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 2
        }
    ]
}

LAYOUT_MINIMAL_QUOTE = {
    "nombre": "minimal_quote",
    "descripcion": "Frase poderosa centrada. Ideal para citas motivacionales.",
    "campos_ia": [
        "quote_text",
        "caption",
        "image_prompt_details"
    ],
    "overlays": [
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 0,
            "altura_pct": 100,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 100,
            "alpha_fin": 120
        }
    ],
    "elementos": [
        {
            "tipo": "texto",
            "placeholder": "quote_text",
            "x_pct": 50,
            "y_pct": 35,
            "alineacion": "centro",
            "ancho_max_pct": 80,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 255,
            "fuente": "bold",
            "tamano_min": 28,
            "tamano_max": 65,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 3
        },
        {
            "tipo": "linea",
            "x1_pct": 35,
            "x2_pct": 65,
            "y_pct": "debajo_de_quote",
            "color_rgb": [
                255,
                204,
                0
            ],
            "color_alpha": 200,
            "grosor": 2
        }
    ]
}

LAYOUT_STEP_BY_STEP = {
    "nombre": "step_by_step",
    "descripcion": "Estilo educativo con bloque superior y 3 puntos clave con viñetas numéricas.",
    "campos_ia": [
        "main_title",
        "step_1",
        "step_2",
        "step_3",
        "caption",
        "image_prompt_details"
    ],
    "overlays": [
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 0,
            "altura_pct": 35,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 180,
            "alpha_fin": 0
        },
        {
            "tipo": "gradiente_vertical",
            "y_inicio_pct": 60,
            "altura_pct": 40,
            "color": [
                0,
                0,
                0
            ],
            "alpha_inicio": 0,
            "alpha_fin": 200
        }
    ],
    "elementos": [
        {
            "tipo": "texto",
            "placeholder": "main_title",
            "x_pct": 50,
            "y_pct": 8,
            "alineacion": "centro",
            "ancho_max_pct": 85,
            "color_rgb": [
                255,
                204,
                0
            ],
            "color_alpha": 255,
            "fuente": "heavy",
            "tamano_min": 32,
            "tamano_max": 60,
            "mayusculas": True,
            "sombra": True,
            "sombra_offset": 3
        },
        {
            "tipo": "texto",
            "placeholder": "step_1",
            "x_pct": 8,
            "y_pct": 65,
            "alineacion": "izquierda",
            "ancho_max_pct": 84,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 255,
            "fuente": "bold",
            "tamano_min": 20,
            "tamano_max": 30,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 2
        },
        {
            "tipo": "texto",
            "placeholder": "step_2",
            "x_pct": 8,
            "y_pct": "debajo_de_step_1",
            "alineacion": "izquierda",
            "ancho_max_pct": 84,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 255,
            "fuente": "bold",
            "tamano_min": 20,
            "tamano_max": 30,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 2
        },
        {
            "tipo": "texto",
            "placeholder": "step_3",
            "x_pct": 8,
            "y_pct": "debajo_de_step_2",
            "alineacion": "izquierda",
            "ancho_max_pct": 84,
            "color_rgb": [
                255,
                255,
                255
            ],
            "color_alpha": 255,
            "fuente": "bold",
            "tamano_min": 20,
            "tamano_max": 30,
            "mayusculas": False,
            "sombra": True,
            "sombra_offset": 2
        }
    ]
}


LAYOUTS = {
    "classic_centered": LAYOUT_CLASSIC_CENTERED,
    "instagram_bold": LAYOUT_INSTAGRAM_BOLD,
    "minimal_quote": LAYOUT_MINIMAL_QUOTE,
    "dark_hero": LAYOUT_DARK_HERO,
    "step_by_step": LAYOUT_STEP_BY_STEP,
    "body_iq_style": LAYOUT_BODY_IQ,
}


def listar_layouts():
    return [{"nombre": k, "descripcion": v["descripcion"], "campos_ia": v["campos_ia"]} for k, v in LAYOUTS.items()]


def obtener_layout(nombre):
    if nombre not in LAYOUTS:
        raise KeyError(f"Layout '{nombre}' no encontrado. Disponibles: {', '.join(LAYOUTS.keys())}")
    return LAYOUTS[nombre]


def guardar_layout_personalizado(layout_dict, archivo="layouts_personalizados.json"):
    try:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)
    except:
        ruta = archivo
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            layouts_guardados = json.load(f)
    else:
        layouts_guardados = {}
    nombre = layout_dict["nombre"]
    layouts_guardados[nombre] = layout_dict
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(layouts_guardados, f, indent=2, ensure_ascii=False)
    LAYOUTS[nombre] = layout_dict
    return nombre


def cargar_layouts_personalizados(archivo="layouts_personalizados.json"):
    try:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)
    except:
        ruta = archivo
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            layouts_guardados = json.load(f)
        for nombre, layout in layouts_guardados.items():
            LAYOUTS[nombre] = layout


cargar_layouts_personalizados()
