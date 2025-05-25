import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from google.oauth2.service_account import Credentials

import gspread
def tipo_identificacion(valor):
    if pd.isna(valor):
        return ""
    valor_str = str(valor).strip()
    if valor_str.isdigit():
        if len(valor_str) in [9, 10]:
            return "CI"
        elif len(valor_str) > 10:
            return "RUC"
        else:
            return "CI"  # Asumimos que es CI si es muy corto también
    else:
        return "PASAPORTE"

def derecho_emision(prima):
    if prima <= 250:
        return 0.05
    elif prima <= 500:
        return 1
    elif prima <= 1000:
        return 3
    elif prima <= 2000:
        return 5
    elif prima <= 4000:
        return 7
    else:
        return 9

# Clasificación MAPFRE por tasa
def clasificar_tipo_vehiculo_mapfre_por_tasa(ciudad, tasa_seguro):
    ciudad = ciudad.upper()
    tasa_seguro = round(tasa_seguro, 4)
    if ciudad == "QUITO":
        if tasa_seguro in [0.0519, 0.0571, 0.0597, 0.0624]: return "TAXIS"
        if tasa_seguro in [0.0416, 0.0457, 0.0478, 0.0522]: return "PESADOS"
        if tasa_seguro in [0.0337, 0.0370, 0.0387, 0.0423]: return "CAMIONETAS"
        if tasa_seguro in [0.0426, 0.0370, 0.0303, 0.0281, 0.0197]: return "LIVIANOS"
    elif ciudad == "GUAYAQUIL":
        if tasa_seguro in [0.0540, 0.0594, 0.0621, 0.0645]: return "TAXIS"
        if tasa_seguro in [0.0447, 0.0491, 0.0514, 0.0562]: return "PESADOS"
        if tasa_seguro in [0.0349, 0.0384, 0.0401, 0.0430]: return "CAMIONETAS"
        if tasa_seguro in [0.0442, 0.0384, 0.0314, 0.0291, 0.0197]: return "LIVIANOS"
    else:
        if tasa_seguro in [0.0561, 0.0617, 0.0645]: return "TAXIS"
        if tasa_seguro in [0.0488, 0.0537, 0.0562]: return "PESADOS"
        if tasa_seguro in [0.0374, 0.0411, 0.0430]: return "CAMIONETAS"
        if tasa_seguro in [0.0478, 0.0416, 0.0343, 0.0312, 0.0239]: return "LIVIANOS"
    return "LIVIANOS"

# Clasificación AIG por tasa
def clasificar_tipo_vehiculo_aig_por_tasa(tasa_seguro):
    tasa_seguro = round(tasa_seguro, 4)
    if tasa_seguro == 0.06:
        return "PESADOS"
    elif tasa_seguro in [0.0570, 0.0633]:
        return "CAMIONETAS"
    else:
        return "LIVIANOS"

# Clasificación ZURICH por tasa
def clasificar_tipo_vehiculo_zurich_por_tasa(tasa_seguro):
    tasa_seguro = round(tasa_seguro, 4)
    if tasa_seguro in [0.0570, 0.0633]:
        return "CAMIONETAS"
    else:
        return "LIVIANOS"

# Bandas MAPFRE
def obtener_tasas_validas_mapfre(ciudad, tipo, valor):
    ciudad = ciudad.upper()
    tipo = tipo.upper()
    bandas = {
        "QUITO": {
            "LIVIANOS": [(20000, [0.0426, 0.0469, 0.0490, 0.0536]), (30000, [0.0370, 0.0407, 0.0426, 0.0460]), (40000, [0.0303, 0.0333, 0.0348, 0.0383]), (50000, [0.0281, 0.0309, 0.0323, 0.0347]), (float("inf"), [0.0197, 0.0217, 0.0227, 0.0275])],
            "CAMIONETAS": [(20000, [0.0426, 0.0469, 0.0490, 0.0536]), (40000, [0.0370, 0.0407, 0.0426, 0.0460]), (float("inf"), [0.0337, 0.0370, 0.0387, 0.0423])],
            "TAXIS": [(float("inf"), [0.0519, 0.0571, 0.0597, 0.0624])],
            "PESADOS": [(float("inf"), [0.0416, 0.0457, 0.0478, 0.0522])]
        },
        "GUAYAQUIL": {
            "LIVIANOS": [(20000, [0.0442, 0.0486, 0.0509, 0.0550]), (30000, [0.0384, 0.0422, 0.0442, 0.0478]), (40000, [0.0314, 0.0346, 0.0361, 0.0394]), (50000, [0.0291, 0.0320, 0.0335, 0.0358]), (float("inf"), [0.0197, 0.0217, 0.0227, 0.0275])],
            "CAMIONETAS": [(20000, [0.0442, 0.0486, 0.0509, 0.0550]), (40000, [0.0384, 0.0422, 0.0442, 0.0478]), (float("inf"), [0.0349, 0.0384, 0.0401, 0.0430])],
            "TAXIS": [(float("inf"), [0.0540, 0.0594, 0.0621, 0.0645])],
            "PESADOS": [(float("inf"), [0.0447, 0.0491, 0.0514, 0.0562])]
        },
        "OTROS": {
            "LIVIANOS": [(20000, [0.0478, 0.0526, 0.0550]), (30000, [0.0416, 0.0457, 0.0478]), (40000, [0.0343, 0.0377, 0.0394]), (50000, [0.0312, 0.0343, 0.0358]), (float("inf"), [0.0239, 0.0263, 0.0275])],
            "CAMIONETAS": [(20000, [0.0478, 0.0526, 0.0550]), (40000, [0.0416, 0.0457, 0.0478]), (float("inf"), [0.0374, 0.0411, 0.0430])],
            "TAXIS": [(float("inf"), [0.0561, 0.0617, 0.0645])],
            "PESADOS": [(float("inf"), [0.0488, 0.0537, 0.0562])]
        }
    }
    ciudad_dict = bandas.get(ciudad, bandas["OTROS"])
    tipo_dict = ciudad_dict.get(tipo, [])
    for limite, tasas in tipo_dict:
        if valor <= limite:
            return tasas
    return []

def obtener_tasas_validas_aig(valor, uso, modelo):
    uso = uso.upper()
    modelo = modelo.upper()
    if "PESADO" in uso or "COMERCIAL" in uso:
        return [0.06]
    elif "CAMIONETA" in modelo:
        return [0.0570, 0.0633]
    else:
        bandas = [
            (20000, [0.0470, 0.0517, 0.0541]), (25000, [0.0450, 0.0495, 0.0518]), (30000, [0.0410, 0.0451, 0.0472]),
            (35000, [0.0380, 0.0418, 0.0437]), (40000, [0.0360, 0.0396, 0.0414]), (45000, [0.0340, 0.0374, 0.0391]),
            (50000, [0.0290, 0.0319, 0.0334]), (float("inf"), [0.0270, 0.0297, 0.0311])
        ]
        for limite, tasas in bandas:
            if valor <= limite:
                return tasas
    return []

def obtener_tasas_validas_zurich(valor, modelo):
    modelo = modelo.upper()
    if "CAMIONETA" in modelo:
        return [0.0570, 0.0633]
    else:
        bandas = [
            (20000, [0.0540, 0.0600]), (30000, [0.0400, 0.0444]), (40000, [0.0310, 0.0344]), (float("inf"), [0.0290, 0.0322])
        ]
        for limite, tasas in bandas:
            if valor <= limite:
                return tasas
    return []
# ————— (3) Función para actualizar pólizas —————
def actualizar_datos_poliza(df_base: pd.DataFrame, df_respuesta: pd.DataFrame) -> pd.DataFrame:
    df_base = df_base.copy().set_index("ID INSURATLAN")
    df_respuesta = df_respuesta.copy().set_index("ID INSURATLAN")

    # Columnas que puede proveer la aseguradora
    for col in ["NÚMERO PÓLIZA VEHÍCULOS", "NÚMERO FACTURA VEHÍCULOS"]:
        if col in df_respuesta.columns:
            # esto reemplaza valores en df_base con los de df_respuesta
            df_base.update(df_respuesta[[col]])

    return df_base.reset_index()
def obtener_TEC(row):
    aseguradora = row["ASEGURADORA"].upper()
    valor = row["VALOR TOTAL ASEGURADO"]
    
    if "MAPFRE" in aseguradora:
        # clasificamos por tasa y recuperamos la banda
        tipo = clasificar_tipo_vehiculo_mapfre_por_tasa(row["CIUDAD"], row["TASA SEGURO"])
        tasas = obtener_tasas_validas_mapfre(row["CIUDAD"], tipo, valor)
    elif "AIG" in aseguradora:
        # aquí 'uso' podrías usar row["USO VEHÍCULO"] o clasificar_uso_vehiculo
        uso   = row.get("USO VEHÍCULO", "")
        tasas = obtener_tasas_validas_aig(valor, uso, row.get("MODELO",""))
    elif "ZURICH" in aseguradora:
        tasas = obtener_tasas_validas_zurich(valor, row.get("MODELO",""))
    else:
        return np.nan

    # devolvemos la primera tasa de la lista
    return tasas[0] if tasas else np.nan
# Validación de tasa seguro
def validar_tasa_seguro(row, aseguradora):
    valor = row["VALOR TOTAL ASEGURADO"]
    tasa_seguro = row["TASA SEGURO"]
    if pd.isna(valor) or pd.isna(tasa_seguro):
        return False
    tasa_seguro = round(tasa_seguro, 4)

    if aseguradora == "MAPFRE":
        tipo = clasificar_tipo_vehiculo_mapfre_por_tasa(row.get("CIUDAD", ""), tasa_seguro)
        tasas_validas = obtener_tasas_validas_mapfre(row.get("CIUDAD", ""), tipo, valor)
    elif aseguradora == "AIG":
        tipo = clasificar_tipo_vehiculo_aig_por_tasa(tasa_seguro)
        tasas_validas = obtener_tasas_validas_aig(valor, tipo, row.get("MODELO", ""))
    elif aseguradora == "ZURICH":
        tipo = clasificar_tipo_vehiculo_zurich_por_tasa(tasa_seguro)
        tasas_validas = obtener_tasas_validas_zurich(valor, tipo)
    else:
        return True

    return any(np.isclose(tasa_seguro, t) for t in tasas_validas)

# Cálculo de mark up MAPFRE
def obtener_mark_up_mapfre(row):
    ciudad = row.get("CIUDAD", "")
    tasa_seguro = row["TASA SEGURO"]
    tipo = clasificar_tipo_vehiculo_mapfre_por_tasa(ciudad, tasa_seguro)
    valor = row["VALOR TOTAL ASEGURADO"]
    tasa_aplicada = row["TASA APLICADA"]
    try:
        banda = obtener_tasas_validas_mapfre(ciudad, tipo, valor)
        max_tasa = max(banda) if banda else np.nan
        if np.isclose(tasa_aplicada, tasa_seguro) and tasa_aplicada < max_tasa:
            return 0.10
        elif tasa_seguro < tasa_aplicada:
            return 0.15
        else:
            return 0.0
    except:
        return 0.0

def obtener_mark_up_zurich(row):
    valor = row["VALOR TOTAL ASEGURADO"]
    tasa_aplica = row["TASA APLICADA"]
    tasa_seguro = row["TASA SEGURO"]
    
    if pd.isna(valor) or pd.isna(tasa_aplica) or pd.isna(tasa_seguro):
        return 0.0

    if not np.isclose(tasa_aplica, tasa_seguro):
        return 0.0

    # Obtener banda ZURICH por modelo
    modelo = row.get("MODELO", "")
    tasas_banda = obtener_tasas_validas_zurich(valor, modelo)

    if tasas_banda and np.isclose(tasa_seguro, max(tasas_banda)):
        return 0.10
    else:
        return 0.0

        
def asignar_plan(row):
    valor = row["VALOR TOTAL ASEGURADO"]
    aseguradora = row["ASEGURADORA"].upper()
    
    if "ZURICH" in aseguradora:
        if valor <= 20000:
            return "HASTA 20K"
        elif 20000 < valor <= 30000:
            return "ENTRE 20,01K - 30K"
        elif 30000 < valor <= 40000:
            return "ENTRE 30,01K - 40K"
        else:
            return "MAYORES A 40,01K"

    elif "MAPFRE" in aseguradora:
        tipo = clasificar_tipo_vehiculo_mapfre_por_tasa(row.get("CIUDAD", ""), row["TASA SEGURO"])
        if tipo == "PESADOS":
            return "VEHICULO PESADO"
        elif tipo == "CAMIONETAS":
            if valor <= 40000:
                return "PICK UP Entre $20.001 a $40.000"
            else:
                return "PICK UP Mayores a $40.001"
        elif valor <= 20000:
            return "Menores o igual a $20.000 "
        elif valor <= 30000:
            return "Entre $20.001 a $30.000"
        elif valor <= 40000:
            return "Entre $30.001 a $40.000"
        elif valor <= 60000:
            return "Entre $40.001 a $60.000"
        else:
            return "Mayores a $60.001"
    
    elif "AIG" in aseguradora:
        if valor <= 20000:
            return "HASTA 20K"
        elif valor <= 25000:
            return "ENTRE 20,01K - 25K"
        elif valor <= 30000:
            return "ENTRE 25,01K - 30K"
        elif valor <= 35000:
            return "ENTRE 30,01K - 35K"
        elif valor <= 40000:
            return "ENTRE 35,01K - 40K"
        elif valor <= 45000:
            return "ENTRE 40,01K - 45K"
        elif valor <= 50000:
            return "ENTRE 45,01K - 50K"
        else:
            return "MAYORES A 50,001K"
 
def dividir_nombres(nombre_completo):
    partes = str(nombre_completo).strip().split()
    # Aseguramos mínimo 4 palabras para evitar errores
    while len(partes) < 4:
        partes.append("")
    return pd.Series({
        "APELLIDO1": partes[0],
        "APELLIDO2": partes[1],
        "NOMBRE1": partes[2],
        "NOMBRE2": partes[3]
    })   
    return ""
def tipo_identificacion(valor):
    if pd.isna(valor):
        return ""
    valor_str = str(valor).strip()
    if valor_str.isdigit():
        if len(valor_str) in [9, 10]:
            return "CI"
        elif len(valor_str) > 10:
            return "RUC"
        else:
            return "CI"  # Asumimos que es CI si es muy corto también
    else:
        return "PASAPORTE"  

df_dict = pd.read_csv("nombres_genero_ecuador.csv")
diccionario_genero = dict(zip(df_dict["NOMBRE"], df_dict["GENERO"]))

def inferir_genero(nombre1):
    if not isinstance(nombre1, str):
        return ""
    nombre = nombre1.strip().upper().split()[0]
    return diccionario_genero.get(nombre, "FEMENINO" if nombre.endswith("A") else "MASCULINO")
    
def clasificar_uso_vehiculo(plan):
    plan = str(plan).upper()
    if "TAXI" in plan or "COMERCIAL" in plan:
        return "PUBLICO"
    elif "PESADO" in plan:
        return "TRABAJO"
    elif "LIVIANO" in plan or "CAMIONETA" in plan or "PICK UP" in plan:
        return "PARTICULAR"
    else:
        return "PARTICULAR"  # valor por defecto

def calcular_cotizacion(df):
    
    df = df.copy()
    df = df.reset_index(drop=True)
    if "ID INSURATLAN" in df.columns:
        # nos aseguramos de que sean floats/int o NA
        df["ID INSURATLAN"] = pd.to_numeric(df["ID INSURATLAN"], errors="coerce")
        max_id = int(df["ID INSURATLAN"].max(skipna=True)) if df["ID INSURATLAN"].notna().any() else 49999
        mask_nuevos = df["ID INSURATLAN"].isna()
        n_nuevos  = mask_nuevos.sum()
        # si hay filas sin ID, les asignamos el rango siguiente
        if n_nuevos > 0:
            df.loc[mask_nuevos, "ID INSURATLAN"] = np.arange(max_id + 1, max_id + 1 + n_nuevos)
    else:
        #  ————— 2) Si no existe la columna, la creamos desde cero —————
        df = df.reset_index(drop=True)
        df["ID INSURATLAN"] = df.index + 50000

    # FECH: igual a FECHA LIQ EN ARQUIVO (asegúrate que esa columna exista en tu archivo)
    df["FECHA"] = df["Fecha Liq"]
    df["NÚMERO CERTIFICADO"] = df["No.OPERACION"]
    nombres_df = df["ASEGURADO"].apply(dividir_nombres)
    df["NOMBRE COMPLETO"]= df["ASEGURADO"]
    df = pd.concat([df, nombres_df], axis=1)
    df["VALOR TOTAL ASEGURADO"] = pd.to_numeric(df["VALOR TOTAL ASEGURADO"], errors='coerce')
    df["TASA APLICADA"] = pd.to_numeric(df["TASA APLICADA"], errors='coerce')
    df["TASA SEGURO"] = pd.to_numeric(df["TASA SEGURO"], errors='coerce')
    df["ASEGURADORA"] = df["ASEGURADORA"].str.upper().str.strip()

    # TEC y MARK UP por aseguradora
    df["TEC"] = df.apply(obtener_TEC, axis=1)
    df["MARK_UP_%"] = df.apply(
        lambda row:
            obtener_mark_up_mapfre(row) if "MAPFRE" in row["ASEGURADORA"]
            else (obtener_mark_up_zurich(row) if "ZURICH" in row["ASEGURADORA"] else 0.0),
        axis=1
    )

    # Comisión por aseguradora
    df["COM_PCT"] = df["ASEGURADORA"].map({
        "MAPFRE": 0.23,
        "AIG": 0.25,
        "ZURICH": 0.24
    })

    # Validación de tasa seguro según aseguradora
    df["TASA_SEGURA_VALIDA"] = df.apply(
        lambda row: validar_tasa_seguro(row, row["ASEGURADORA"]), axis=1
    )

    # Cálculo financiero
    df["PRIMA_TECNICA"] = df["VALOR TOTAL ASEGURADO"] * df["TEC"]
    df["COMISION_TOTAL"] = df["PRIMA_TECNICA"] * df["COM_PCT"]
    df["COMISION LIDERSEG"] = df["COMISION_TOTAL"] * 0.4
    df["COMISION CANAL"] = df["COMISION_TOTAL"] * 0.4
    df["COMISION INSURANCE"] = df["COMISION_TOTAL"] * 0.2
    df["VALOR MARKUP"] = df["VALOR TOTAL ASEGURADO"] * df["TEC"] * df["MARK_UP_%"]

    # Prima vehículos solo si tasa es válida
    df["PRIMA VEHICULOS"] = np.where(
        df["TASA_SEGURA_VALIDA"],
        df["VALOR TOTAL ASEGURADO"] * df["TASA SEGURO"],
        np.nan
    )
    df["COMISIÓN PRIMA VEHÍCULOS"]=df["COMISION_TOTAL"]
    df["COMISIÓN TOTAL"]=df["COMISION_TOTAL"]

    # Impuestos
    df["IMPUESTO VEHÍCULOS SUPER DE BANCOS"] = df["PRIMA VEHICULOS"] * 0.035
    df["IMPUESTO VEHÍCULOS SEGURO CAMPESINO"] = df["PRIMA VEHICULOS"] * 0.005
    df["IMPUESTO VEHÍCULOS EMISIÓN"] = np.where(
        df["ASEGURADORA"].str.upper().str.contains("ZURICH"),
        0.45,
        df["PRIMA VEHICULOS"].apply(lambda x: derecho_emision(x) if pd.notnull(x) else np.nan)
    )
    df["SUBTOTAL"] = df["PRIMA VEHICULOS"] + df["IMPUESTO VEHÍCULOS SUPER DE BANCOS"] + df["IMPUESTO VEHÍCULOS SEGURO CAMPESINO"] + df["IMPUESTO VEHÍCULOS EMISIÓN"]
    df["IMPUESTO VEHÍCULOS IVA"] = df["SUBTOTAL"] * 0.15
    df["PRIMA TOTAL VEHÍCULOS"] = df["SUBTOTAL"] + df["IMPUESTO VEHÍCULOS IVA"]
    df["PLAN"] = df.apply(asignar_plan, axis=1)
    df["TIPO IDENTIFICACIÓN"] = df["IDENTIFICACION"].apply(tipo_identificacion)
    df["NÚMERO IDENTIFICACIÓN"]= df["IDENTIFICACION"]
    from datetime import timedelta

    # 1. GENERO por inferencia básica del nombre (no 100% precisa)
    df["GENERO"] = df["NOMBRE1"].apply(inferir_genero)
    # 2. OBSERVACION
    df["OBSERVACIÓN"] = df["OBSERVACIONES"]

    # 3. FECHA VIGENCIA
    df["FECHA VIGENCIA"] = pd.to_datetime(df["FECHA DE SOLICITUD/ INICIO DE VIGENCIA"], errors="coerce")
    df["MES VIGENCIA"] = df["FECHA VIGENCIA"].dt.month
    df["ANO VIGENCIA"] = df["FECHA VIGENCIA"].dt.year
    df["POLIZA MAESTRA"]= ""
    # 4. FECHA EXPIRACION = FECHA VIGENCIA + 1 año
    df["FECHA EXPIRACIÓN"] = df["FECHA VIGENCIA"] + pd.DateOffset(years=1)
    df["NÚMERO RENOVACIÓN"] = 0
    df["DÍAS EXTRA"] = 0

    # 5. DÍAS VIGENCIA = diferencia en días
    df["DÍAS VIGENCIA"] = (df["FECHA EXPIRACIÓN"] - df["FECHA VIGENCIA"]).dt.days

    # 6. CUOTA MENSUAL VEHÍCULOS
    df["CUOTA MENSUAL VEHÍCULOS"] = df.apply(
        lambda row: row["PRIMA TOTAL VEHÍCULOS"] / 12 if "ZURICH" in row["ASEGURADORA"] or "AIG" in row["ASEGURADORA"]
        else row["PRIMA TOTAL VEHÍCULOS"] / 10 if "MAPFRE" in row["ASEGURADORA"]
        else np.nan,
        axis=1
    )

    # 7. CANAL, VENDEDOR, FORMA PAGO
    df["CANAL"] = "CREDIPRIME"
    df["VENDEDOR"] = "SANTIAGO VITERI PUYOL"
    df["FORMA PAGO"] = "CREDITO"
    df["TIPO PRIMA"]= "Variable"
    df["USUARIO CREADOR PÓLIZA"] = "SANTIAGO VITERI PUYOL"

    # 8. MESES PAGO
    df["MESES PAGO"] = df["ASEGURADORA"].apply(lambda x: 10 if "MAPFRE" in x else 10)

    # 9. ORIGEN DE VENTA
    df["ORIGEN DE VENTA"] = df["CONCESIONARIO"].apply(
        lambda x: "AGENCIA SEMINUEVO" if isinstance(x, str) and "1001 AUTOS" in x.upper() else "AGENCIA NUEVO"
    )
    df["ESTADO VEHÍCULO"] = df["CONCESIONARIO"].apply(
        lambda x: "SEMINUEVO" if isinstance(x, str) and "1001 AUTOS" in x.upper() else "NUEVO"
    )
    df["AGENCIA"]=df["CONCESIONARIO"]

    # 10. TIPO PLACA
    import re
    def tipo_placa(placa):
        if isinstance(placa, str) and re.fullmatch(r"[A-Z]{3}[0-9]{3,4}", placa.replace(" ", "")):
            return "PLACA"
        return "RAM"
    
    df["TIPO PLACA"] = df["PLACA / RAMV"].apply(tipo_placa)
    df["PLACA"]=df["PLACA / RAMV"]
    df["CIUDAD CLIENTE"] =df["CIUDAD"]
    df["SEGURO DEDUCIBLE"]=0
    df["NÚMERO IDENTIFICACIÓN VENDEDOR"]="060350371"
    df["NÚMERO IDENTIFICACIÓN CREADOR"]="060350371"
    # 11. ESTADO POLIZA
    df["ESTADO PÓLIZA"] = "POLIZA CREADA"
    df["FECHA PAGO"] = df["FECHA VIGENCIA"] + pd.DateOffset(months=1)
    df["USO VEHÍCULO"] = df["PLAN"].apply(clasificar_uso_vehiculo)
    df["VALOR ASEGURADO"]=df["VALOR TOTAL ASEGURADO"]
    df["ACCESORIOS"]=df["DETALLE DE EXTRAS"]
    df["TOTAL PAGAR"]=df["PRIMA TOTAL VEHÍCULOS"]
    df["CUOTA MENSUAL"]=df["CUOTA MENSUAL VEHÍCULOS"]
    df["DÉBITO (MEDIO DE PAGO)"]= "Tabla de Amortización"
    df["BENEFICIARIO ACREEDOR"]=df["ENDOSO A"]
    # 12. Columnas vacías
    df["NÚMERO PÓLIZA VEHÍCULOS"] = ""
    df["NÚMERO ENDOSO VEHÍCULOS"] = ""
    df["NÚMERO FACTURA VEHÍCULOS"] = ""
    return df
def reorganizar_columnas_salida(df: pd.DataFrame) -> pd.DataFrame:
    # Lista organizada de columnas de salida
    columnas_ordenadas = [
        "ID INSURATLAN", "FECHA", "TASA SEGURO", "NÚMERO RENOVACIÓN", "TIPO IDENTIFICACIÓN", "NÚMERO IDENTIFICACIÓN",
        "NOMBRE1", "NOMBRE2", "APELLIDO1", "APELLIDO2", "NOMBRE COMPLETO", "GENERO", "ESTADO CIVIL",
        "CIUDAD CLIENTE", "DIRECCION", "TELEFONO",
        "FECHA NACIMIENTO", "CORREO ELECTRONICO", "OBSERVACIÓN",
        "POLIZA MAESTRA", "NÚMERO CERTIFICADO", "FECHA VIGENCIA", "MES VIGENCIA", "ANO VIGENCIA",
        "FECHA EXPIRACIÓN", "DÍAS VIGENCIA", "DÍAS EXTRA", "USO VEHÍCULO", "ASEGURADORA", "PLAN",
        "SEGURO DEDUCIBLE", "CANAL", "CONCESIONARIO", "VENDEDOR", "NÚMERO IDENTIFICACIÓN VENDEDOR",
        "AGENCIA", "ORIGEN DE VENTA", "FORMA PAGO", "MESES PAGO", "MARCA", "MODELO", "MOTOR", "CHASIS",
        "COLOR", "AÑO", "TIPO PLACA", "PLACA", "ACCESORIOS", "ESTADO VEHÍCULO",
        "BENEFICIARIO ACREEDOR", "VALOR ASEGURADO", "VALOR FINANCIADO", "PRIMA VEHICULOS",
        "IMPUESTO VEHÍCULOS SUPER DE BANCOS", "IMPUESTO VEHÍCULOS SEGURO CAMPESINO",
        "IMPUESTO VEHÍCULOS EMISIÓN", "IMPUESTO VEHÍCULOS IVA", "PRIMA TOTAL VEHÍCULOS",
        "CUOTA MENSUAL VEHÍCULOS", "PRIMA DESGRAVAMEN", "IMPUESTO DESGRAVAMEN SUPER DE BANCOS",
        "IMPUESTO DESGRAVAMEN SEGURO CAMPESINO", "IMPUESTO DESGRAVAMEN EMISIÓN", "IMPUESTO DESGRAVAMEN IVA",
        "PRIMA TOTAL DESGRAVAMEN", "CUOTA MENSUAL DESGRAVAMEN", "TIPO PRIMA", "TIPO DESGRAVAMEN",
        "TOTAL PAGAR", "CUOTA MENSUAL", "DÉBITO (MEDIO DE PAGO)",
        "FECHA PAGO", "TASA NOMINAL", "COMISIÓN PRIMA VEHÍCULOS", "COMISION CANAL",
        "COMISION LIDERSEG", "COMISION INSURANCE", "COMISIÓN TOTAL",
        "VALOR MARKUP", "ESTADO PÓLIZA", "USUARIO CREADOR PÓLIZA", "NÚMERO IDENTIFICACIÓN CREADOR",
        "NÚMERO PÓLIZA VEHÍCULOS", "NÚMERO ENDOSO VEHÍCULOS", "NÚMERO FACTURA VEHÍCULOS"
    ] 
    # Añadir las columnas que falten con NaN
    for col in columnas_ordenadas:
        if col not in df.columns:
            df[col] = pd.NA

    return df[columnas_ordenadas]

def set_df_original(df):
    st.session_state["df_original"] = df

def get_df_original():
    return st.session_state.get("df_original", pd.DataFrame())
# --- APP STREAMLIT ---
st.set_page_config(page_title="Cotizador Crediprime")
st.title("Cotizador Crediprime")
#st.write(st.secrets)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds_info = dict(st.secrets["google"])   # conviértelo a un dict estándar

# 2) Reemplaza los literales "\\n" por saltos reales "\n"
creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

# 3) Crea las credenciales
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key("13hY8la9Xke5-wu3vmdB-tNKtY5D6ud4FZrJG2_HtKd8")
sh = client.open_by_key("13hY8la9Xke5-wu3vmdB-tNKtY5D6ud4FZrJG2_HtKd8")
# Asegúrate de que exista la hoja
try:
    hoja = spreadsheet.worksheet("asegurados_insurance")
except gspread.WorksheetNotFound:
    hoja = spreadsheet.add_worksheet("asegurados_insurance", rows="2000", cols="200")

# ————— 2) Carga inicial de la hoja como DataFrame “original” —————
@st.cache_data(ttl=300)
def cargar_hoja_completa():
    # 1) Traemos todas las celdas
    datos = hoja.get_all_values()
    cols  = datos[0]
    rows  = datos[1:]

    # 2) DataFrame y limpieza de filas sin ID
    df = pd.DataFrame(rows, columns=cols).dropna(
        how="all", subset=["ID INSURATLAN"]
    )

    # 3) Conversión robusta a numérico:
    #    - pd.to_numeric() parsea "50009.0"→50009.0
    #    - errors="coerce" convierte valores no numéricos en NaN
    #    - luego astype(int) convierte los floats *válidos* a ints
    df["ID INSURATLAN"] = (
        pd.to_numeric(df["ID INSURATLAN"], errors="coerce")
          .astype(int)
    )

    return df

# Uso:

df_original = cargar_hoja_completa()

# ————— 3) Función para persistir cambios (reescribe toda la hoja) —————
def persistir_en_sheet(df: pd.DataFrame):
    # Formateo de fechas a string
    for c in df.select_dtypes(include=["datetime64", "datetime64[ns]"]):
        df[c] = df[c].dt.strftime("%Y-%m-%d")

    # Reemplaza NaN/NaT con cadenas vacías
    df = df.fillna("").astype(str)

    # Prepara la matriz de valores (incluyendo cabecera)
    values = [df.columns.tolist()] + df.values.tolist()

    # Limpia la hoja y sube todo
    hoja.clear()
    hoja.update(values)
    
df_sheet = cargar_hoja_completa()
# 2) Normalizo encabezados: quito espacios y pongo todo en mayúsculas
df_sheet.columns = df_sheet.columns.str.strip().str.upper()

# 3) Si no existe en sesión, lo guardo
if "df_original" not in st.session_state:
    st.session_state["df_original"] = df_sheet

# 1) Define las pestañas y la sesión
tabs = ["📂 Carga / Descarga", "🔍 Buscar / Editar"]
if "active_tab" not in st.session_state:
    st.session_state.active_tab = tabs[1]

# El radio con key="active_tab" mantiene siempre la selección
active = st.radio(
    "Selecciona sección:",
    options=tabs,
    key="active_tab",
    horizontal=True
)

# ————— Pestaña 1 —————
if active == tabs[0]:
    st.header("1️⃣ Carga de Bases")   
    # ————— 4) Uploader de nueva base + merge —————
    archivo = st.file_uploader("1️⃣ Carga la base nueva (.xlsx)", type=["xlsx"])
    if archivo:
        # 1) Leemos la base nueva
        df_nueva = pd.read_excel(archivo)
    
        # 2) Traemos la base original de sesión (la misma que usas para persistir)
        df_original = get_df_original()
        df_nueva["IDENTIFICACION"] = df_nueva["IDENTIFICACION"].astype(str).str.strip()
        df_original["NÚMERO IDENTIFICACIÓN"] = (
            df_original["NÚMERO IDENTIFICACIÓN"]
              .astype(str)
              .str.strip()
        )
    
        
    
    
        # 3) Hacemos merge usando la columna correcta de df_original
        df_nueva = df_nueva.merge(
            df_original[['ID INSURATLAN','NÚMERO IDENTIFICACIÓN']],
            left_on='IDENTIFICACION',            # de tu archivo de entrada
            right_on='NÚMERO IDENTIFICACIÓN',    # la que ya está en df_original
            how='left'
        )
        st.write(df_nueva)
        #df_nueva = df_nueva.drop(columns=['NÚMERO IDENTIFICACIÓN_y']) \
        #               .rename(columns={'NÚMERO IDENTIFICACIÓN_x':'NÚMERO IDENTIFICACIÓN'})
    
        # 4) Ahora calculamos, sólo se crearán IDs donde `ID INSURATLAN` sea NaN
        df_calc  = calcular_cotizacion(df_nueva)
        df_orden = reorganizar_columnas_salida(df_calc)
    
        # 5) Fusionamos con la original y eliminamos duplicados por ID
        combinado = pd.concat([df_original, df_orden], ignore_index=True)
        combinado = combinado.drop_duplicates(subset=["ID INSURATLAN"], keep="last")
    
        # 6) Persistimos y mostramos
        set_df_original(combinado)
        persistir_en_sheet(combinado)
    
        st.success("✅ Base original actualizada con la nueva carga")
        st.dataframe(combinado)

    # ————— 5) Uploader de respuestas de póliza —————
    uploaded_resp = st.file_uploader("2️⃣ Sube respuesta de aseguradora", type=["xlsx"])
    if uploaded_resp:
        df_resp = pd.read_excel(uploaded_resp)
        df_resp = df_resp.set_index("ID INSURATLAN").copy()
    
        # Actualiza sólo póliza y factura
        for col in ["NÚMERO PÓLIZA VEHÍCULOS", "NÚMERO FACTURA VEHÍCULOS"]:
            if col in df_resp.columns:
                idxs = df_original["ID INSURATLAN"].isin(df_resp.index)
                df_original.loc[idxs, col] = df_original.loc[idxs, "ID INSURATLAN"].map(df_resp[col])
    
        # Persiste cambios
        persistir_en_sheet(df_original)
        st.success("✅ Pólizas y facturas actualizadas")
        st.dataframe(df_original)
    df_to_download = st.session_state.get("df_original", pd.DataFrame())
    # Si tienes datos, ofrécelos
    if not df_to_download.empty:
        # Opción Excel
        buffer = io.BytesIO()
        df_to_download.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            label="📥 Descargar base completa (Excel)",
            data=buffer,
            file_name="base_insurprime.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
        # Opción CSV (descomenta si la prefieres)
        # csv = df_to_download.to_csv(index=False).encode("utf-8")
        # st.download_button(
        #     label="📥 Descargar base completa (CSV)",
        #     data=csv,
        #     file_name="base_insurprime.csv",
        #     mime="text/csv"
        # )
    else:
        st.info("La base está vacía; no hay nada para descargar.")
    
        
else:
    st.header("🔍 Buscar y Editar Asegurados")

    # ——— Filtros en un expander ———
    with st.expander("🔎 Filtros de Búsqueda", expanded=True):
        col1, col2 = st.columns(2)
        buscar_id     = col1.text_input("ID INSURATLAN")
        buscar_poliza = col2.text_input("Número de Póliza")
        buscar_cedula = col1.text_input("Número de Cédula")
        buscar_nombre = col2.text_input("Nombre Completo (o parte)")

    # ——— Aplicar máscara ———
    EDITABLE_COLS = [
        "TELEFONO",
        "CORREO ELECTRONICO",
        "OBSERVACIÓN",
        "ESTADO PÓLIZA",
        "NÚMERO FACTURA VEHÍCULOS"
    ]
    df_original = st.session_state["df_original"]
    mask = pd.Series(True, index=df_original.index)
    if buscar_id:
        mask &= df_original["ID INSURATLAN"].astype(str) == buscar_id.strip()
    if buscar_poliza:
        mask &= df_original["NÚMERO PÓLIZA VEHÍCULOS"].astype(str) == buscar_poliza.strip()
    if buscar_cedula:
        mask &= df_original["NÚMERO IDENTIFICACIÓN"].astype(str) == buscar_cedula.strip()
    if buscar_nombre:
        mask &= df_original["NOMBRE COMPLETO"].str.contains(buscar_nombre.strip(), case=False, na=False)
    df_filtrado = df_original[mask]

    # ——— Sin resultados ———
    if df_filtrado.empty:
        st.warning("No se encontró ningún asegurado con esos criterios.")
        st.stop()

    # ——— Mostrar y organizar detalles vs edición ———
    registro = df_filtrado.iloc[0]
    st.markdown("### Detalles del Asegurado")
    left, right = st.columns([1, 2])

    # Columna izquierda: detalles estáticos
    with left:
        st.info(f"**Nombre:** {registro['NOMBRE COMPLETO']}")
        st.info(f"**ID:** {registro['ID INSURATLAN']}")
        st.info(f"**Cédula:** {registro['NÚMERO IDENTIFICACIÓN']}")
        st.info(f"**Póliza:** {registro['NÚMERO PÓLIZA VEHÍCULOS']}")

    with right:
        st.subheader("✏️ Editar Campos")
        # Usamos un formulario para agrupar los inputs
        with st.form("editar_aseg_form"):
            telefono        = st.text_input("Teléfono", registro["TELEFONO"])
            correo          = st.text_input("Correo Electrónico", registro["CORREO ELECTRONICO"])
            observacion     = st.text_area("Observación", registro["OBSERVACIÓN"])
            estado_poliza   = st.selectbox(
                "Estado de Póliza",
                options=["POLIZA CREADA", "EN PROCESO", "CERRADA", "RECHAZADA"],
                index=["POLIZA CREADA","EN PROCESO","CERRADA","RECHAZADA"].index(registro["ESTADO PÓLIZA"])
            )
            num_factura     = st.text_input("Número Factura Vehículos", registro["NÚMERO FACTURA VEHÍCULOS"])
            submitted = st.form_submit_button("💾 Guardar Cambios")

        if submitted:
            # Actualizamos df_original y Sheets
            mask_upd = df_original["ID INSURATLAN"] == registro["ID INSURATLAN"]
            df_original.loc[mask_upd, "TELEFONO"]               = telefono
            df_original.loc[mask_upd, "CORREO ELECTRONICO"]      = correo
            df_original.loc[mask_upd, "OBSERVACIÓN"]             = observacion
            df_original.loc[mask_upd, "ESTADO PÓLIZA"]           = estado_poliza
            df_original.loc[mask_upd, "NÚMERO FACTURA VEHÍCULOS"] = num_factura

            st.session_state["df_original"] = df_original
            persistir_en_sheet(df_original)
            st.success("✅ Cambios guardados en Google Sheets")
            # Mostrar los nuevos datos
            registro_act = df_original[mask_upd].iloc[0]
            st.dataframe(registro_act.to_frame().T)

    
    
