# se importan librerias para mover los archivos y validar los formatos
import pathlib                                      
import shutil                                      
import logging                                      
import json                                         
import xml.etree.ElementTree as ET                  
import csv                                          

# -------------------------------------------------------------------
# configuracion del log

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s") # Formato de log
logger = logging.getLogger()                        # Instancia del registrador de logs

# -------------------------------------------------------------------
# configuracion de las rutas de las carpetas 
base_path = pathlib.Path(".")                       # directorio actual
landing = base_path / "landing"                     
bronze = base_path / "bronze"                       
bad_data = base_path / "bad_data"                   

# -------------------------------------------------------------------
# funcion para validar los formatos de los archivos 
def validar_integridad(archivo):                    
    ext = archivo.suffix.lower()                    
    with archivo.open("r", encoding="utf-8") as f:  
        if ext == ".json":                          
            json.load(f)                            # Valida estructura de llaves
        elif ext == ".xml":                         
            ET.parse(f)                             # Validar etiquetas de apertura/cierre
        elif ext == ".csv":                         
            sample = f.read(2048)                   
            if not sample: raise ValueError("Vacío") 
            csv.Sniffer().sniff(sample)             # Valida si tiene delimitadores
        else:                                      
            if not f.read(1): raise ValueError("Ilegible") 

# -------------------------------------------------------------------
# funcion para mover los archivos a las carpetas
def ejecutar_bronze_pipeline():                     
    bronze.mkdir(exist_ok=True)                     # valida si existen las carpetas 
    bad_data.mkdir(exist_ok=True)                   
    
    archivos = list(landing.glob("*"))              
    logger.info(f"Archivos: {len(archivos)} ") 
    stats = {"Bronze": 0, "Bad Data": 0}            

    for archivo in archivos:                        # Itera sobre cada archivo
        if not archivo.is_file(): continue          # Ignora si es una subcarpeta

        try:                                        
            if archivo.stat().st_size == 0:         # revisa si tiene un tamaño de 0 (vacio)
                raise ValueError("Archivo 0 bytes") 
            
            validar_integridad(archivo)             # Llama a la funcion para validar los formatos
            
            shutil.move(str(archivo), bronze / archivo.name) # Mover archivo a bronze
            logger.info(f" Bronze: {archivo.name}") 
            stats["Bronze"] += 1                    

        except (json.JSONDecodeError, ET.ParseError, csv.Error, ValueError, UnicodeDecodeError,OSError) as e:
            logger.warning(f" Bad Data: {archivo.name} | {e}") 
            shutil.move(str(archivo), bad_data / archivo.name) # Mover archivo a bad
            stats["Bad Data"] += 1                  

        except Exception as e:                      # Captura de errores inesperados
            logger.error(f" Crítico: {archivo.name}", exc_info=True) 
            try:                                    # mueve el archivo a la carpeta bad data
                shutil.move(str(archivo), bad_data / archivo.name) 
                stats["Bad Data"] += 1              
            except:                                 
                logger.error("No se pudo mover")    

    logger.info(f"Archivos reubicados| Bronze: {stats['Bronze']} | Bad Data: {stats['Bad Data']}") #  final

if __name__ == "__main__":                          
    ejecutar_bronze_pipeline()                      # Inicia el script