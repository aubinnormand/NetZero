import pandas as pd
from pathlib import Path
import geopandas as gpd

# -----------------------------
# Fonctions d'importation
# -----------------------------
def import_data_raw(filename, folder="data_raw", n_header=0, sep=',', encoding='utf-8'):
    """
    Importation d'un CSV depuis Data/data_raw
    """
    data_path = Path("..") / "Data" / folder / filename
    return pd.read_csv(data_path, header=n_header, sep=sep, encoding=encoding)

def clean_year_column(df, year_col=None, new_name='Year', keep_numeric=True, reset_index=True):
    """
    Nettoie une colonne représentant les années dans un DataFrame.

    Paramètres :
    - df : DataFrame pandas à traiter
    - year_col : nom ou index de la colonne à considérer comme années (par défaut la première colonne)
    - new_name : nom de la colonne après renommage
    - keep_numeric : si True, ne garde que les lignes numériques
    - reset_index : si True, réinitialise l'index

    Retourne :
    - DataFrame nettoyé
    """
    import pandas as pd

    # Si aucune colonne spécifiée, on prend la première
    if year_col is None:
        year_col = df.columns[0]

    # Renommer la colonne
    df = df.rename(columns={year_col: new_name})

    # Garder uniquement les lignes numériques si demandé
    if keep_numeric:
        df = df[pd.to_numeric(df[new_name], errors='coerce').notna()].copy()

    # Convertir en int
    df[new_name] = df[new_name].astype(int)

    # Réinitialiser l'index si demandé
    if reset_index:
        df.reset_index(drop=True, inplace=True)

    return df


def import_data_sig(filename, folder="SIG"):
    """
    Importation d'un fichier SIG (GeoJSON, Shapefile...) depuis Data/SIG
    """
    data_path = Path("..") / "Data" / folder / filename
    return gpd.read_file(data_path)


# -----------------------------
# Fonctions de formatage
# -----------------------------

def melt_long_format(df, id_vars=['Country'], var_name='Year', value_name='Value',source=None, unit=None, indicator=None):
    """
    Transformer un DataFrame en format long (tidy) et ajouter des métadonnées
    """
    df_long = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
    
    # Ajout des métadonnées si fournies
    if unit is not None:
        df_long['Unit'] = unit
    if indicator is not None:
        df_long['Indicator'] = indicator
    if source is not None:
        df_long['Source'] = source
    
    return df_long

def save_long_dataframe(df, indicator=None, source=None, folder="data_final", sep=',', index=False, encoding='utf-8'):
    """
    Sauvegarde un DataFrame au format long avec un nom de fichier dynamique basé sur l'indicateur et la source.

    Paramètres :
    - df : DataFrame à sauvegarder
    - indicator : nom de l'indicateur (ex: "LULUCF Net emissions")
    - source : nom de la source (ex: "GCB")
    - folder : dossier de destination
    - sep : séparateur CSV
    - index : si True, sauvegarder l'index
    - encoding : encodage du fichier
    """
    from pathlib import Path
    import re

    # Nettoyer les noms pour faire un nom de fichier valide
    def clean_name(name):
        if name is None:
            return "unknown"
        name = re.sub(r'\s+', '_', name)      # espaces -> _
        name = re.sub(r'[^\w\-_]', '', name)  # supprimer caractères spéciaux
        return name

    indicator_name = clean_name(indicator)
    source_name = clean_name(source)

    filename = f"{indicator_name}_{source_name}.csv"

    save_path = Path("..") / "Data" / folder / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(save_path, sep=sep, index=index, encoding=encoding)

    print(f"DataFrame sauvegardé dans {save_path}")
    return save_path

def concat_intermediate_files(folder_in="data_intermediate", folder_out="data_final", final_filename="data_final.csv", sep=',', encoding='utf-8'):
    """
    Concatène tous les fichiers CSV dans un dossier intermédiaire et sauvegarde le résultat final.

    Paramètres :
    - folder_in : dossier contenant les fichiers CSV intermédiaires
    - folder_out : dossier où sauvegarder le fichier final
    - final_filename : nom du fichier CSV final
    - sep : séparateur CSV
    - encoding : encodage du fichier
    """
    import pandas as pd
    from pathlib import Path
    import glob

    # Construire le chemin des fichiers
    folder_path = Path("..") / "Data" / folder_in
    files = glob.glob(str(folder_path / "*.csv"))

    if not files:
        print(f"Aucun fichier CSV trouvé dans {folder_path}")
        return None

    # Charger et concaténer tous les fichiers
    dfs = [pd.read_csv(f, sep=sep, encoding=encoding) for f in files]
    df_final = pd.concat(dfs, ignore_index=True)

    # Sauvegarder le résultat final
    save_path = Path("..") / "Data" / folder_out / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(save_path, sep=sep, index=False, encoding=encoding)

    print(f"DataFrame final sauvegardé dans {save_path} ({len(df_final)} lignes)")
    return df_final


