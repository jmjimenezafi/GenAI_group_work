import logging
import os
from dotenv import load_dotenv

from utils.workflow import run
from utils.agents.report_csv_parser import parse_report_csv


load_dotenv()
logging.basicConfig(level=logging.INFO)


REPORT_OUTPUT_PATH = "report_output.md"

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
        with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(state.report_markdown)
        print(f"Reporte generado exitosamente en {REPORT_OUTPUT_PATH}")
        parse_report_csv(state)
        print("Reporte CSV generado exitosamente a partir del markdown.")


    else:
        print("No se pudo generar el reporte.")


if __name__ == "__main__":
    main()
