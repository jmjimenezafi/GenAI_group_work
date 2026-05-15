import logging
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

REPORT_PATH = Path("report_output.md")
CSV_PATH = Path("data/new_claims.csv")
CLAIMS_PATH = Path("data/claims.csv")

logging.basicConfig(level=logging.INFO)


# ── Splash / loading ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gen AI Trabajo",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
    <style>
        .loading-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 60vh;
            gap: 1.5rem;
        }
        .loading-spinner {
            width: 56px;
            height: 56px;
            border: 6px solid #e0e0e0;
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }
        .loading-text {
            font-size: 1.2rem;
            color: #6b7280;
            font-family: sans-serif;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
""", unsafe_allow_html=True)

splash = st.empty()


@st.cache_resource(show_spinner=False)
def _load_app():
    """Importa los módulos pesados una sola vez y los cachea."""
    from utils.agents.report_csv_parser import parse_report_csv  # noqa: F401
    from utils.rag.qdrant_service import QdrantService            # noqa: F401
    from utils.workflow import run                                  # noqa: F401
    return True


with splash.container():
    st.markdown("""
        <div class="loading-wrapper">
            <div class="loading-spinner"></div>
            <div class="loading-text">🧠 Cargando modelos y servicios…</div>
        </div>
    """, unsafe_allow_html=True)

_load_app()
splash.empty()


# ── Importaciones reales (ya cacheadas, instantáneas) ───────────────────────
from utils.agents.report_csv_parser import parse_report_csv  # noqa: E402
from utils.rag.qdrant_service import QdrantService            # noqa: E402
from utils.workflow import run                                  # noqa: E402


# ── Logging helper ──────────────────────────────────────────────────────────
class StreamlitLogHandler(logging.Handler):
    def __init__(self, log_container):
        super().__init__()
        self.log_container = log_container
        self.logs = []

    def emit(self, record):
        msg = self.format(record)
        self.logs.append(msg)
        with self.log_container:
            st.code("\n".join(self.logs[-5:]), language="text")


# ── UI ──────────────────────────────────────────────────────────────────────
st.title("Gen AI Trabajo")
st.caption("Verificador de afirmaciones con RAG local y búsqueda web")

tab_analyzer, tab_claims = st.tabs(["🔍 Analizador", "📊 Claims"])

with tab_analyzer:
    with st.sidebar:
        st.header("Configuración")
        st.markdown(
            """
            - El sistema primero prueba RAG sobre Qdrant.
            - Si no puede responder, usa búsqueda web.
            - Al final genera Markdown y una fila CSV para Qdrant.
            """
        )
        st.divider()
        st.markdown("### Salidas")
        st.write("- `report_output.md`")
        st.write("- `data/new_claims.csv`")

    query = st.text_area(
        "Escribe la afirmación a verificar",
        placeholder="Ejemplo: Se ha probado que Irak estaba intentando obtener armas nucleares, y por eso comenzó la guerra de Irak.",
        height=140,
    )

    col_run, col_clear = st.columns([1, 1])
    run_clicked = col_run.button("Analizar", type="primary")
    clear_clicked = col_clear.button("Limpiar")

    if clear_clicked:
        st.session_state.pop("last_report", None)
        st.session_state.pop("last_csv", None)
        st.session_state.pop("last_error", None)
        st.session_state.pop("logs", None)
        st.rerun()

    if run_clicked:
        if not query.strip():
            st.error("Debes escribir una afirmación para analizar - Esto puede tomar varios minutos.")
        else:
            log_placeholder = st.empty()

            streamlit_handler = StreamlitLogHandler(log_placeholder)
            streamlit_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            streamlit_handler.setFormatter(formatter)

            logger = logging.getLogger()
            logger.addHandler(streamlit_handler)

            with st.status("Iniciando análisis...", expanded=True) as status:
                try:
                    st.write("⏳ Cargando transformers, modelos y llamadas a agentes...")

                    status.update(label="🔍 Ejecutando flujo de análisis… Espere unos minutos", state="running")
                    state = run(query.strip())

                    st.session_state["logs"] = "\n".join(streamlit_handler.logs)

                    if state.errors:
                        status.update(label="❌ Errores encontrados", state="error")
                        st.session_state["last_error"] = "\n".join(state.errors)
                        st.error("\n".join(state.errors))
                    elif state.report_markdown:
                        status.update(label="✅ Análisis completado", state="complete")
                        REPORT_PATH.write_text(state.report_markdown, encoding="utf-8")
                        csv_path = parse_report_csv(state, CSV_PATH)
                        st.session_state["last_report"] = state.report_markdown
                        st.session_state["last_csv"] = csv_path
                        st.success("Reporte generado correctamente.")
                    else:
                        status.update(label="⚠️ No se generó reporte", state="error")
                        st.warning("No se pudo generar el reporte.")

                finally:
                    logger.removeHandler(streamlit_handler)
                    import time
                    from utils.rag.rag_agent import client
                    try:
                        client.close()
                    except Exception:
                        pass
                    time.sleep(0.5)

    if st.session_state.get("last_report"):
        st.subheader("Reporte Markdown")
        st.markdown(st.session_state["last_report"], unsafe_allow_html=True)
        st.download_button(
            label="Descargar reporte Markdown",
            data=st.session_state["last_report"],
            file_name="report_output.md",
            mime="text/markdown",
        )

    if st.session_state.get("last_csv"):
        csv_path = Path(st.session_state["last_csv"])
        st.subheader("CSV generado")
        st.write(f"Archivo creado en: `{csv_path}`")
        if csv_path.exists():
            st.download_button(
                label="Descargar new_claims.csv",
                data=csv_path.read_text(encoding="utf-8"),
                file_name="new_claims.csv",
                mime="text/csv",
            )

    if st.session_state.get("last_error"):
        st.subheader("Errores")
        st.code(st.session_state["last_error"], language="text")


with tab_claims:
    st.header("Gestión de Claims")

    col1, col2 = st.columns([2, 1])

    # ───────────────── LEFT COLUMN ─────────────────
    with col1:
        st.subheader("Claims pendientes de subir")

        if CSV_PATH.exists():
            df_new = pd.read_csv(CSV_PATH)

            if len(df_new) > 0:

                # Añadir columna checkbox
                if "Eliminar" not in df_new.columns:
                    df_new.insert(0, "Eliminar", False)

                edited_df = st.data_editor(
                    df_new,
                    use_container_width=True,
                    num_rows="fixed",
                    hide_index=True,
                )

                st.write(f"📌 Total: {len(df_new)} claim(s) pendiente(s)")

                col_delete, col_save = st.columns(2)

                with col_delete:
                    if st.button("🗑️ Eliminar seleccionadas", use_container_width=True):

                        filtered_df = edited_df[
                            ~edited_df["Eliminar"]
                        ].drop(columns=["Eliminar"])

                        filtered_df.to_csv(CSV_PATH, index=False)

                        st.success("Claims eliminadas correctamente.")
                        st.rerun()

                with col_save:
                    if st.button("💾 Guardar cambios", use_container_width=True):

                        edited_df.drop(columns=["Eliminar"]).to_csv(
                            CSV_PATH,
                            index=False
                        )

                        st.success("Cambios guardados.")
                        st.rerun()

            else:
                st.info(
                    "No hay claims pendientes. "
                    "Genera un reporte en la pestaña de Analizador."
                )

        else:
            st.info(
                "No hay claims pendientes. "
                "Genera un reporte en la pestaña de Analizador."
            )

    # ───────────────── RIGHT COLUMN ─────────────────
    with col2:
        st.subheader("Acciones")

        has_claims = (
            CSV_PATH.exists()
            and len(pd.read_csv(CSV_PATH)) > 0
        )

        if has_claims:

            if st.button(
                "⬆️ Subir a Qdrant",
                type="primary",
                use_container_width=True
            ):

                with st.status(
                    "Subiendo claims a Qdrant...",
                    expanded=True
                ) as status:

                    try:
                        import time
                        from utils.rag.rag_agent import client as rag_client

                        status.update(
                            label="Leyendo archivo...",
                            state="running"
                        )

                        df = pd.read_csv(CSV_PATH)

                        status.update(
                            label="Conectando a Qdrant...",
                            state="running"
                        )

                        rag_client.close()

                        qdrant_service = QdrantService()

                        try:
                            status.update(
                                label="Creando colección...",
                                state="running"
                            )

                            qdrant_service.create_collection()

                            status.update(
                                label="Insertando puntos...",
                                state="running"
                            )

                            df.insert(
                                0,
                                "id",
                                [str(uuid.uuid4()) for _ in range(len(df))]
                            )

                            qdrant_service.add_points(df)

                            st.write(
                                f"✅ {len(df)} claim(s) cargado(s) en Qdrant"
                            )

                            status.update(
                                label="Actualizando histórico...",
                                state="running"
                            )

                            if CLAIMS_PATH.exists():

                                df_claims = pd.read_csv(CLAIMS_PATH)

                                df_claims = pd.concat([df_claims, df])

                                df_claims.to_csv(
                                    CLAIMS_PATH,
                                    index=False
                                )

                            else:
                                df.to_csv(
                                    CLAIMS_PATH,
                                    index=False
                                )

                            st.write(
                                f"📝 Histórico actualizado en `{CLAIMS_PATH}`"
                            )

                            status.update(
                                label="Limpiando archivos...",
                                state="running"
                            )

                            CSV_PATH.unlink()

                            st.write("🗑️ Archivo temporal eliminado")

                            status.update(
                                label="✅ Subida completada",
                                state="complete"
                            )

                            st.success(
                                "Claims subidos a Qdrant correctamente."
                            )

                            st.rerun()

                        finally:
                            qdrant_service.close()

                    except Exception as e:

                        status.update(
                            label="❌ Error en la subida",
                            state="error"
                        )

                        st.error(f"Error: {str(e)}")

        else:
            st.button(
                "⬆️ Subir a Qdrant",
                type="primary",
                disabled=True,
                use_container_width=True
            )

    # ───────────────── HISTORICAL ─────────────────
    st.divider()
    st.subheader("Histórico de claims")

    if CLAIMS_PATH.exists():
        df_claims = pd.read_csv(CLAIMS_PATH)
        st.dataframe(df_claims, use_container_width=True)
        st.write(f"📊 Total: {len(df_claims)} claim(s) en la base de datos")

        csv_content = df_claims.to_csv(index=False)
        st.download_button(
            label="Descargar histórico completo",
            data=csv_content,
            file_name="claims.csv",
            mime="text/csv",
        )
    else:
        st.info("El histórico de claims está vacío.")