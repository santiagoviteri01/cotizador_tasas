import streamlit as st
import pandas as pd
import numpy as np
import io

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
    
    return ""
# --- FUNCION PRINCIPAL DE COTIZACION ---
def calcular_cotizacion(df):
    
    df = df.copy()
    df = df.reset_index(drop=True)
    df["ID INSURATLAN"] = df.index + 5000
    
    # FECH: igual a FECHA LIQ EN ARQUIVO (asegúrate que esa columna exista en tu archivo)
    df["FECH"] = df["FECHA LIQ EN ARQUIVO"]
    
    # TIPO IDENTIFICACION basado en NUMERO IDENTIFICACION
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
    
    df["TIPO IDENTIFICACION"] = df["NUMERO IDENTIFICACION"].apply(tipo_identificacion)
    
    # NOMBRE1, NOMBRE2, APELLIDO1, APELLIDO2 desde ASEGURADO
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
    
    nombres_df = df["ASEGURADO"].apply(dividir_nombres)
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
    df["COMISION_LIDERSEG"] = df["COMISION_TOTAL"] * 0.4
    df["COMISION_CANAL"] = df["COMISION_TOTAL"] * 0.4
    df["COMISION_INSURANCE"] = df["COMISION_TOTAL"] * 0.2
    df["VALOR_MARKUP"] = df["VALOR TOTAL ASEGURADO"] * df["TEC"] * df["MARK_UP_%"]

    # Prima vehículos solo si tasa es válida
    df["PRIMA_VEHICULOS"] = np.where(
        df["TASA_SEGURA_VALIDA"],
        df["VALOR TOTAL ASEGURADO"] * df["TASA SEGURO"],
        np.nan
    )

    # Impuestos
    df["IMP_SUPER"] = df["PRIMA_VEHICULOS"] * 0.035
    df["IMP_CAMPESINO"] = df["PRIMA_VEHICULOS"] * 0.005
    df["DERECHO_EMISION"] = np.where(
        df["ASEGURADORA"].str.upper().str.contains("ZURICH"),
        0.45,
        df["PRIMA_VEHICULOS"].apply(lambda x: derecho_emision(x) if pd.notnull(x) else np.nan)
    )
    df["SUBTOTAL"] = df["PRIMA_VEHICULOS"] + df["IMP_SUPER"] + df["IMP_CAMPESINO"] + df["DERECHO_EMISION"]
    df["IVA"] = df["SUBTOTAL"] * 0.15
    df["TOTAL"] = df["SUBTOTAL"] + df["IVA"]
    df["PLAN"] = df.apply(asignar_plan, axis=1)
    df["TIPO IDENTIFICACION"] = df["NUMERO IDENTIFICACION"].apply(tipo_identificacion)


    return df

# --- APP STREAMLIT ---
st.set_page_config(page_title="Cotizador Crediprime", page_icon="📊")
st.title("📊 Cotizador Técnico de Seguros - Crediprime")

archivo = st.file_uploader("Carga la base de entrada (.xlsx)", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    resultado = calcular_cotizacion(df)
    st.success("✅ Cálculos completados")
    st.dataframe(resultado.head(50))
    # Suponiendo que ya tienes tu DataFrame llamado 'resultado'
    if not resultado.empty:
        # Crear buffer de memoria
        output = io.BytesIO()
    
        # Exportar el DataFrame al buffer
        resultado.to_excel(output, index=False, engine='openpyxl')
    
        # Mover el puntero al inicio del archivo
        output.seek(0)
    
        # Mostrar botón de descarga
        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name="resultado_cotizacion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No hay resultados para descargar.")

