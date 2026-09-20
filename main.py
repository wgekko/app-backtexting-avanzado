# import streamlit as st
# import re

# # 1. Configuración de página
# st.set_page_config(page_title="App Financiera", layout="wide", initial_sidebar_state="collapsed", page_icon=":material/finance:")

# hide_sidebar_style = """
#     <style>
#         /* Oculta la barra lateral completa */
#         [data-testid="stSidebar"] {
#             display: none;
#         }
#         /* Ajusta el área principal para usar todo el ancho */
#         [data-testid="stAppViewContainer"] {
#             margin-left: 0px;
#         }
#     </style>
# """
# st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# def renderizar_menu_personalizado():
#     """Renderiza el menú HTML/JS superior de forma segura sin advertencias."""
#     try:
#         with open("components/style.css", "r", encoding="utf-8") as f:
#             css = f.read()
#         with open("components/js.js", "r", encoding="utf-8") as f:
#             js = f.read()
#         with open("index.html", "r", encoding="utf-8") as f:
#             html_raw = f.read()
#     except FileNotFoundError:
#         return

#     body_match = re.search(r'<body>(.*?)</body>', html_raw, re.DOTALL)
#     body_content = body_match.group(1) if body_match else html_raw
#     body_content = re.sub(r'<script.*?>.*?</script>', '', body_content, flags=re.DOTALL)

#     codigo_final = f"""
#     <!DOCTYPE html><html><head><style>
#     {css}
#     body {{ margin: 0 !important; padding: 0 !important; background-color: #000000; overflow: hidden; }}
#     </style></head><body>{body_content}
#     <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
#     <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/EasePack.min.js"></script>
#     <script>{js}</script></body></html>
#     """
    
#     # Reemplazo oficial para evitar el mensaje de error de 'st.components.v1.html'
#     try:
#         st.iframe(codigo_final, height=400)
#     except AttributeError:
#         # Fallback de seguridad en caso de que la API requiera st.html en tu entorno actual
#         st.html(codigo_final)

# # Renderiza la animación inicial superior
# renderizar_menu_personalizado()

# # ==========================================
# # INYECCIÓN DE CSS PARA BOTONES DE STREAMLIT
# # ==========================================
# st.markdown("""
# <style>
#     /* 1. Importamos la misma fuente de la barra de navegación */
#     @import url("https://use.typekit.net/ers2qgl.css");

#     /* 2. Aplicamos la tipografía y tamaño a TODOS los st.button */
#     div.stButton > button:first-child {
#         background-color: transparent !important;
#         color: #ffffff !important;
#         font-family: "ff-chambers-sans-web", sans-serif !important;
#         font-size: 1.3rem !important; /* Mismo tamaño que el nav */
#         font-weight: 500 !important;
#         text-transform: uppercase !important;
#         border: 1px solid #333 !important; /* Borde muy sutil */
#         border-radius: 0px !important;
#         width: 100% !important;
#         padding: 0.8rem !important;
#         transition: all 0.1s ease !important;
#     }

#     /* 3. Efecto visual al pasar el mouse (Simulación Scramble/Glitch) */
#     div.stButton > button:first-child:hover {
#         color: #fff !important;
#         border-color: #05eafa !important;
#         background-color: rgba(5, 234, 250, 0.05) !important;
#         /* Activamos la animación de distorsión */
#         animation: textGlitch 0.35s linear infinite alternate !important;
#     }

#     /* 4. Animación CSS que simula decodificación/distorsión rápida */
#     @keyframes textGlitch {
#         0%   { letter-spacing: 1px; text-shadow: 2px 0 #ff6bd3, -2px 0 #05eafa; }
#         25%  { letter-spacing: 2px; text-shadow: -2px 0 #ff6bd3, 1px 0 #05eafa; }
#         50%  { letter-spacing: 0px; text-shadow: 1px 0 #05eafa, -1px 0 #ff6bd3; transform: skew(-2deg); }
#         75%  { letter-spacing: 3px; text-shadow: -1px 0 #05eafa, 2px 0 #ff6bd3; }
#         100% { letter-spacing: 1px; text-shadow: 2px 0 #ff6bd3, -2px 0 #05eafa; transform: skew(2deg); }
#     }
# </style>
# """, unsafe_allow_html=True)


# # ==========================================
# # 3. INTERFAZ Y LÓGICA DE NAVEGACIÓN
# # ==========================================
# st.markdown("<h2 style='text-align: center;'>Bienvenido al Dashboard</h2>", unsafe_allow_html=True)
# st.markdown("<p style='text-align: center;'>Selecciona un módulo o utiliza los accesos directos.</p>", unsafe_allow_html=True)
# st.markdown("<br>", unsafe_allow_html=True)

# with st.container(border=True):
#     st.markdown("<p style='text-align: center; margin-bottom: 20px;'>Selecciona un módulo:</p>", unsafe_allow_html=True)

#     # Las proporciones exactas para centrar los 4 botones
#     espacio_izq, col1, col2, col3, col4, espacio_der = st.columns([2, 2, 2, 2, 2, 1])

#     with col1:
#         if st.button("Análisis ML"):
#             st.switch_page("pages/app11.py")

#     with col2:
#         if st.button("Simulador"):
#             st.switch_page("pages/main111.py")

#     with col3:
#         if st.button("Backtesting"):
#             st.switch_page("pages/precios1.py") 

#     with col4:
#         if st.button("Presupuestos"):
#             st.switch_page("pages/precios3.py")


import streamlit as st
import streamlit.components.v1 as components
import re

# 1. Configuración de página
st.set_page_config(page_title="App Financiera", layout="wide", initial_sidebar_state=None, page_icon=":material/finance:")


hide_sidebar_style = """
    <style>
        /* Oculta la barra lateral completa */
        [data-testid="stSidebar"] {
            display: none;
        }
        /* Ajusta el área principal para usar todo el ancho */
        [data-testid="stAppViewContainer"] {
            margin-left: 0px;
        }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

def renderizar_menu_personalizado():
    """Renderiza el menú HTML/JS superior en un iframe."""
    try:
        with open("components/style.css", "r", encoding="utf-8") as f:
            css = f.read()
        with open("components/js.js", "r", encoding="utf-8") as f:
            js = f.read()
        with open("index.html", "r", encoding="utf-8") as f:
            html_raw = f.read()
    except FileNotFoundError:
        return

    body_match = re.search(r'<body>(.*?)</body>', html_raw, re.DOTALL)
    body_content = body_match.group(1) if body_match else html_raw
    body_content = re.sub(r'<script.*?>.*?</script>', '', body_content, flags=re.DOTALL)

    codigo_final = f"""
    <!DOCTYPE html><html><head><style>
    {css}
    body {{ margin: 0 !important; padding: 0 !important; background-color: #000000; overflow: hidden; }}
    </style></head><body>{body_content}
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/EasePack.min.js"></script>
    <script>{js}</script></body></html>
    """
    components.html(codigo_final, height=400)

# Renderiza la animación inicial superior
renderizar_menu_personalizado()

# ==========================================
# 2. INYECCIÓN DE ESTILOS PARA BOTONES NATIVOS
# Sincroniza los estilos con tu archivo style.css
# ==========================================
st.markdown("""
<style>
    /* Importar la misma fuente que la barra superior */
    @import url("https://use.typekit.net/ers2qgl.css");

    /* Aplicar estilo a los botones nativos de Streamlit */
    div.stButton > button:first-child {
        background-color: transparent !important;
        color: #ffffff !important;
        font-family: "ff-chambers-sans-web", sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        padding: 12px 24px !important;
        width: 100% !important;
        border: none !important;
        border-radius: 0px !important;
        transition: all 0.3s ease !important;
        /* Simulando los vectores rectangulares celeste (#05eafa) y rosa (#ff6bd3) */
        box-shadow: -2px -2px 0px #ff6bd3, 2px 2px 0px #05eafa !important;
    }

    /* Animación Hover idéntica al estado activo de tu nav svg */
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 25px 2px #0763f7 !important;
        color: #05eafa !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. INTERFAZ Y LÓGICA DE NAVEGACIÓN
# ==========================================
st.subheader("Bienvenido al Dashboard SOCK TRADING", text_alignment="center")
st.markdown("Selecciona un módulo de los accesos directos.", text_alignment="center")

st.markdown("<br>", unsafe_allow_html=True)

import streamlit as st

# ==========================================
# INYECCIÓN DE CSS PARA BOTONES DE STREAMLIT
# ==========================================
st.markdown("""
<style>
    /* 1. Importamos la misma fuente de la barra de navegación */
    @import url("https://use.typekit.net/ers2qgl.css");

    /* 2. Aplicamos la tipografía y tamaño a TODOS los st.button */
    div.stButton > button:first-child {
        background-color: transparent !important;
        color: #ffffff !important;
        font-family: "ff-chambers-sans-web", sans-serif !important;
        font-size: 1.3rem !important; /* Mismo tamaño que el nav */
        font-weight: 500 !important;
        text-transform: uppercase !important;
        border: 1px solid #333 !important; /* Borde muy sutil */
        border-radius: 0px !important;
        width: 100% !important;
        padding: 0.8rem !important;
        transition: all 0.1s ease !important;
    }

    /* 3. Efecto visual al pasar el mouse (Simulación Scramble/Glitch) */
    div.stButton > button:first-child:hover {
        color: #fff !important;
        border-color: #05eafa !important;
        background-color: rgba(5, 234, 250, 0.05) !important;
        /* Activamos la animación de distorsión */
        animation: textGlitch 0.35s linear infinite alternate !important;
    }

    /* 4. Animación CSS que simula decodificación/distorsión rápida */
    @keyframes textGlitch {
        0%   { letter-spacing: 1px; text-shadow: 2px 0 #ff6bd3, -2px 0 #05eafa; }
        25%  { letter-spacing: 2px; text-shadow: -2px 0 #ff6bd3, 1px 0 #05eafa; }
        50%  { letter-spacing: 0px; text-shadow: 1px 0 #05eafa, -1px 0 #ff6bd3; transform: skew(-2deg); }
        75%  { letter-spacing: 3px; text-shadow: -1px 0 #05eafa, 2px 0 #ff6bd3; }
        100% { letter-spacing: 1px; text-shadow: 2px 0 #ff6bd3, -2px 0 #05eafa; transform: skew(2deg); }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# TUS BOTONES DE PYTHON NATIVOS
# ==========================================

with st.expander("Despliegua los accesos a los módulos de análisis de datos y gráficos ", icon=":material/finance_mode:"):
    with st.container(border=True):
        st.markdown("Selecciona un modelo :", text_alignment="center")

        #col1, col2, col3, col4 = st.columns(4)
        espacio_izq, col1, col2, col3, col4, col5, espacio_der = st.columns([1, 2, 2, 2, 2,2,1])


        with col1:
            if st.button("Backtesting Básico"):
                st.switch_page("pages/1_Análisis Backtesting Básico.py")

        with col2:
            if st.button("Backtesting Quant"):
                st.switch_page("pages/2_Análisis Backtesting Quant.py")

        with col3:
            if st.button("Modelo ML "):
                st.switch_page("pages/3_Análisis Modelos ML.py")    

        with col4:
            if st.button("Técnico Mediano Plazo "):
                st.switch_page("pages/4_Análisis Ténico Mediano Plazo.py")            

        with col5:
            if st.button("Técnico Largo Plazo "):
                st.switch_page("pages/5_Análisis Técnico Largo Plazo.py")          