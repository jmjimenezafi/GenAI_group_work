import uuid
from pathlib import Path

import pandas as pd

from qdrant_service import QdrantService



def main():
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "data"
    new_claims_path = data_dir / "new_claims.csv"
    claims_path = data_dir / "claims.csv"

    qdrant_service = QdrantService()
    try:
        qdrant_service.create_collection()
        df = pd.read_csv(new_claims_path)
        df.insert(0, "id", [str(uuid.uuid4()) for _ in range(len(df))])
        qdrant_service.add_points(df)
        print("Datos cargados en Qdrant exitosamente.")

        if claims_path.exists():
            df_claims = pd.read_csv(claims_path)
            df_claims = pd.concat([df_claims, df])
            df_claims.to_csv(claims_path, index=False)
        else:
            df.to_csv(claims_path, index=False)

        if new_claims_path.exists():
            new_claims_path.unlink()
    finally:
        qdrant_service.close()
    
if __name__ == "__main__":
    main()
    