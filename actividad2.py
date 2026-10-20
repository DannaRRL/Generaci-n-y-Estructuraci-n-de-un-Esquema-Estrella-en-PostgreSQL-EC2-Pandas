
import pandas as pd
import numpy as np

# ==========================================
# PRÁCTICA 2: ESQUEMA ESTRELLA CON PANDAS
# ==========================================

# Simulación de datos de un sistema OLTP
np.random.seed(101)

n = 500

df_operativo = pd.DataFrame({
    'id_transaccion': range(1000, 1000 + n),
    'fecha_hora': pd.date_range(
        start='2026-01-01',
        periods=n,
        freq='h'
    ),
    'cliente_nombre': np.random.choice(
        ['Juan Pérez', 'María Gómez', 'Carlos Ruiz'], n
    ),
    'cliente_ciudad': np.random.choice(
        ['Puebla', 'CDMX', 'Guadalajara'], n
    ),
    'producto_nombre': np.random.choice(
        ['Laptop Dell', 'Mouse Logi', 'Monitor LG'], n
    ),
    'categoria_prod': np.random.choice(
        ['Cómputo', 'Accesorios', 'Pantallas'], n
    ),
    'precio_unitario': np.random.choice(
        [15000.0, 350.0, 4500.0], n
    ),
    'cantidad': np.random.randint(1, 5, n)
})

print("\n==========================================")
print("1. DATOS OPERATIVOS (OLTP)")
print("==========================================")
print(df_operativo.head())
print(f"\nTotal de transacciones: {len(df_operativo)}")


# ==========================================
# 2. DIMENSIÓN CLIENTE
# ==========================================

dim_cliente = df_operativo[
    ['cliente_nombre', 'cliente_ciudad']
].drop_duplicates().reset_index(drop=True)

# Generación de llave subrogada
dim_cliente['id_cliente_sk'] = dim_cliente.index + 1

# Organización de columnas
dim_cliente = dim_cliente[
    ['id_cliente_sk', 'cliente_nombre', 'cliente_ciudad']
]

print("\n==========================================")
print("2. DIMENSIÓN CLIENTE (DIM_CLIENTE)")
print("==========================================")
print(dim_cliente.head(10))
print(f"\nTotal de clientes: {len(dim_cliente)}")


# ==========================================
# 3. DIMENSIÓN PRODUCTO
# ==========================================

dim_producto = df_operativo[
    ['producto_nombre', 'categoria_prod', 'precio_unitario']
].drop_duplicates().reset_index(drop=True)

# Generación de llave subrogada
dim_producto['id_producto_sk'] = dim_producto.index + 1

dim_producto = dim_producto[
    [
        'id_producto_sk',
        'producto_nombre',
        'categoria_prod',
        'precio_unitario'
    ]
]

print("\n==========================================")
print("3. DIMENSIÓN PRODUCTO (DIM_PRODUCTO)")
print("==========================================")
print(dim_producto.head(10))
print(f"\nTotal de productos: {len(dim_producto)}")


# ==========================================
# 4. DIMENSIÓN TIEMPO
# ==========================================

dim_tiempo = pd.DataFrame({
    'fecha_completa': df_operativo[
        'fecha_hora'
    ].dt.date.unique()
})

dim_tiempo['fecha_completa'] = pd.to_datetime(
    dim_tiempo['fecha_completa']
)

# Llave subrogada basada en la fecha
dim_tiempo['id_tiempo_sk'] = (
    dim_tiempo['fecha_completa']
    .dt.strftime('%Y%m%d')
    .astype(int)
)

dim_tiempo['anio'] = dim_tiempo['fecha_completa'].dt.year
dim_tiempo['mes'] = dim_tiempo['fecha_completa'].dt.month
dim_tiempo['dia'] = dim_tiempo['fecha_completa'].dt.day

# NUEVOS ATRIBUTOS SOLICITADOS EN LA PRÁCTICA
dim_tiempo['dia_semana'] = (
    dim_tiempo['fecha_completa'].dt.day_name()
)

dim_tiempo['es_fin_semana'] = (
    dim_tiempo['fecha_completa'].dt.dayofweek >= 5
)

dim_tiempo = dim_tiempo[
    [
        'id_tiempo_sk',
        'fecha_completa',
        'anio',
        'mes',
        'dia',
        'dia_semana',
        'es_fin_semana'
    ]
]

print("\n==========================================")
print("4. DIMENSIÓN TIEMPO (DIM_TIEMPO)")
print("==========================================")
print(dim_tiempo.head(10))
print(f"\nTotal de fechas: {len(dim_tiempo)}")


# ==========================================
# 5. CONSTRUCCIÓN DE TABLA DE HECHOS
# ==========================================

# Relacionar transacciones con clientes
fact_ventas = df_operativo.merge(
    dim_cliente,
    on=['cliente_nombre', 'cliente_ciudad'],
    how='left',
    validate='many_to_one'
)

# Relacionar transacciones con productos
fact_ventas = fact_ventas.merge(
    dim_producto,
    on=[
        'producto_nombre',
        'categoria_prod',
        'precio_unitario'
    ],
    how='left',
    validate='many_to_one'
)

# Preparar fecha para relacionar con Dim_Tiempo
fact_ventas['fecha_completa'] = pd.to_datetime(
    fact_ventas['fecha_hora'].dt.date
)

# Relacionar transacciones con fechas
fact_ventas = fact_ventas.merge(
    dim_tiempo,
    on='fecha_completa',
    how='left',
    validate='many_to_one'
)

# Calcular monto total de cada venta
fact_ventas['monto_total'] = (
    fact_ventas['cantidad'] *
    fact_ventas['precio_unitario']
)

# Seleccionar columnas finales de Fact_Ventas
fact_table = fact_ventas[
    [
        'id_transaccion',
        'id_cliente_sk',
        'id_producto_sk',
        'id_tiempo_sk',
        'cantidad',
        'monto_total'
    ]
].copy()

print("\n==========================================")
print("5. TABLA DE HECHOS (FACT_VENTAS)")
print("==========================================")
print(fact_table.head(10))
print(f"\nTotal de ventas: {len(fact_table)}")


# ==========================================
# 6. VALIDACIÓN DE RESULTADOS
# ==========================================

print("\n==========================================")
print("6. VALIDACIÓN DEL ESQUEMA ESTRELLA")
print("==========================================")

try:
    if len(fact_table) != n:
        raise ValueError(
            "El número de transacciones cambió durante los cruces."
        )

    if fact_table.isnull().any().any():
        raise ValueError(
            "Se encontraron valores nulos en la tabla de hechos."
        )

    if fact_table['id_transaccion'].duplicated().any():
        raise ValueError(
            "Existen transacciones duplicadas."
        )

    print("Validación correcta.")
    print("No hay transacciones duplicadas.")
    print("No hay valores nulos en Fact_Ventas.")

except ValueError as error:
    print(f"Error de validación: {error}")
    raise


# ==========================================
# 7. ESTADÍSTICAS DE VENTAS
# ==========================================

print("\n==========================================")
print("7. ESTADÍSTICAS GENERALES")
print("==========================================")

print(f"Cantidad total vendida: {fact_table['cantidad'].sum()}")

print(
    f"Monto total de ventas: "
    f"${fact_table['monto_total'].sum():,.2f}"
)

print(
    f"Promedio por transacción: "
    f"${fact_table['monto_total'].mean():,.2f}"
)


# ==========================================
# 8. EXPORTACIÓN DE TABLAS
# ==========================================

# Guardar las cuatro tablas como archivos CSV
dim_cliente.to_csv('dim_cliente.csv', index=False)
dim_producto.to_csv('dim_producto.csv', index=False)
dim_tiempo.to_csv('dim_tiempo.csv', index=False)
fact_table.to_csv('fact_ventas.csv', index=False)

print("\n==========================================")
print("8. EXPORTACIÓN COMPLETADA")
print("==========================================")

print("Archivo generado: dim_cliente.csv")
print("Archivo generado: dim_producto.csv")
print("Archivo generado: dim_tiempo.csv")
print("Archivo generado: fact_ventas.csv")

print("\nPRÁCTICA 2 FINALIZADA CORRECTAMENTE")
