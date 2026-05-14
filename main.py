import logging
import os
from dotenv import load_dotenv

from utils.workflow import run


load_dotenv()
logging.basicConfig(level=logging.INFO)


def main() -> None:
    query = input("Introduce la query para verificar: ").strip()
    if not query:
        print("Query vacia. Saliendo.")
        return

    state = run(query)
    if state.errors:
        print("Error en la ejecucion:\n- " + "\n- ".join(state.errors))
        return

    if state.report_markdown:
        print(state.report_markdown)
    else:
        print("No se pudo generar el reporte.")


if __name__ == "__main__":
    main()
