import streamlit as st
import pandas as pd
import numpy as np
import io

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

# Validación de tasa seguro
def validar_tasa_seguro(row, aseguradora):
    valor = row["VALOR TOTAL ASEGURADO"]
    tasa_seguro = row["TASA SEGURO"]
    if pd.isna(valor) or pd.isna(tasa_seguro):
        return False
    tasa_seguro = round(tasa_seguro, 4)

    if aseguradora == "MAPFRE":
        tipo = clasificar_tipo_vehiculo_mapfre_por_tasa(row.get("CIUDAD", ""), tasa_seguro)
        st.write(tipo)
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

# --- FUNCION PRINCIPAL DE COTIZACION ---
def calcular_cotizacion(df, aseguradora):
    df = df.copy()
    df["VALOR TOTAL ASEGURADO"] = pd.to_numeric(df["VALOR TOTAL ASEGURADO"], errors='coerce')
    df["TASA APLICADA"] = pd.to_numeric(df["TASA APLICADA"], errors='coerce')
    df["TASA SEGURO"] = pd.to_numeric(df["TASA SEGURO"], errors='coerce')

    if aseguradora == "MAPFRE":
        df["TEC"] = df["TASA SEGURO"]
        df["MARK_UP_%"] = df.apply(obtener_mark_up_mapfre, axis=1)
        com_pct = 0.23
    elif aseguradora == "AIG":
        df["TEC"] = df["TASA SEGURO"]
        df["MARK_UP_%"] = 0.0
        com_pct = 0.25
    elif aseguradora == "ZURICH":
        df["TEC"] = df["TASA SEGURO"]
        df["MARK_UP_%"] = 0.10 if np.isclose(df["TASA APLICADA"], df["TASA SEGURO"]).all() else 0.0
        com_pct = 0.24
    else:
        st.error("Aseguradora no reconocida")
        return df

    df["TASA_SEGURA_VALIDA"] = df.apply(lambda row: validar_tasa_seguro(row, aseguradora), axis=1)

    df["PRIMA_TECNICA"] = df["VALOR TOTAL ASEGURADO"] * df["TEC"]
    df["COMISION_TOTAL"] = df["PRIMA_TECNICA"] * com_pct
    df["COMISION_LIDERSEG"] = df["COMISION_TOTAL"] * 0.4
    df["COMISION_CANAL"] = df["COMISION_TOTAL"] * 0.4
    df["COMISION_INSURANCE"] = df["COMISION_TOTAL"] * 0.2
    df["VALOR_MARKUP"] = df["VALOR TOTAL ASEGURADO"] * df["TEC"] * df["MARK_UP_%"]

    df["PRIMA_VEHICULOS"] = np.where(
        df["TASA_SEGURA_VALIDA"],
        df["VALOR TOTAL ASEGURADO"] * df["TASA SEGURO"],
        np.nan
    )
    
    # Impuestos solo si la PRIMA_VEHICULOS es válida
    df["IMP_SUPER"] = df["PRIMA_VEHICULOS"] * 0.035
    df["IMP_CAMPESINO"] = df["PRIMA_VEHICULOS"] * 0.005
    df["DERECHO_EMISION"] = df["PRIMA_VEHICULOS"].apply(lambda x: derecho_emision(x) if pd.notnull(x) else np.nan)
    
    df["SUBTOTAL"] = df["PRIMA_VEHICULOS"] + df["IMP_SUPER"] + df["IMP_CAMPESINO"] + df["DERECHO_EMISION"]
    df["IVA"] = df["SUBTOTAL"] * 0.15
    df["TOTAL"] = df["SUBTOTAL"] + df["IVA"]

    return df

# --- APP STREAMLIT ---
st.set_page_config(page_title="Cotizador Crediprime", page_icon="📊")
st.title("📊 Cotizador Técnico de Seguros - Crediprime")

archivo = st.file_uploader("Carga la base de entrada (.xlsx)", type=["xlsx"])
aseguradora = st.selectbox("Selecciona la aseguradora", ["MAPFRE", "AIG", "ZURICH"])

if archivo:
    df = pd.read_excel(archivo)
    resultado = calcular_cotizacion(df, aseguradora)
    st.success("✅ Cálculos completados para " + aseguradora)
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

