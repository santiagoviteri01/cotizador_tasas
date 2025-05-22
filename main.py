import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from google.oauth2.service_account import Credentials

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
def actualizar_datos_poliza(df_base, df_respuesta):
    df_base = df_base.copy()
    df_respuesta = df_respuesta.copy()
    df_base.set_index("CÉDULA", inplace=True)
    df_respuesta.set_index("CÉDULA", inplace=True)

    for col in ["NÚMERO PÓLIZA VEHÍCULOS", "NÚMERO FACTURA VEHÍCULOS"]:
        if col in df_respuesta.columns:
            df_base.update(df_respuesta[[col]])

    df_base.reset_index(inplace=True)
    return df_base
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
    df["TEC"] = df["TASA SEGURO"]
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
# --- APP STREAMLIT ---
st.set_page_config(page_title="Cotizador Crediprime")
st.title("Cotizador Crediprime")
google_creds_dict = st.secrets["general"]
creds = Credentials.from_service_account_info(google_creds_dict)
client = gspread.authorize(creds)

archivo = st.file_uploader("Carga la base de entrada (.xlsx)", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    resultado = calcular_cotizacion(df)
    df_ordenado = reorganizar_columnas_salida(resultado)
    st.success("✅ Cálculos completados")
    st.dataframe(df_ordenado.head(50))

    # 📤 Escribir a Google Sheets
    sh = client.open_by_key("13hY8la9Xke5-wu3vmdB-tNKtY5D6ud4FZrJG2_HtKd8")
    try:
        hoja_asegurados = sh.worksheet("asegurados_insurance")
    except:
        hoja_asegurados = sh.add_worksheet(title="asegurados_insurance", rows="1000", cols="50")

    hoja_asegurados.clear()
    hoja_asegurados.update([df_ordenado.columns.values.tolist()] + df_ordenado.values.tolist())

    # 📥 Descarga local
    if not df_ordenado.empty:
        output = io.BytesIO()
        df_ordenado.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name="resultado_cotizacion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No hay resultados para descargar.")
        
uploaded_file = st.file_uploader("Sube archivo de aseguradora", type=["xlsx"])
if uploaded_file:
    df_respuesta = pd.read_excel(uploaded_file)
    df_actualizada = actualizar_datos_poliza(df_original, df_respuesta)
    st.success("✅ Registros actualizados")
    st.dataframe(df_actualizada)

