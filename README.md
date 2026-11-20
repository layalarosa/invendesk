# Invendesk

**Invendesk** es una aplicación de escritorio para gestionar las operaciones básicas de un pequeño negocio: inventario, clientes, ventas y reportes. Está desarrollada en Python con Tkinter y guarda la información localmente en una base de datos SQLite.

## Funcionalidades

- **Inventario:** crear, editar, buscar y eliminar productos; consultar alertas de stock bajo o agotado; exportar productos a CSV.
- **Importación desde Excel:** importar archivos `.xlsx` o `.xlsm`, descargar una plantilla y, opcionalmente, actualizar productos existentes por código.
- **Clientes:** mantener nombre, teléfono, correo, dirección y notas; buscar, editar y exportar información de actividad en reportes.
- **Ventas:** registrar ventas para un cliente o de mostrador, agregar artículos al carrito, validar existencias y consultar el historial con el detalle de cada venta.
- **Reportes:** revisar ingresos y productos vendidos por período, valores del inventario, productos con stock bajo y compras por cliente; exportar los reportes disponibles a CSV.
- **Acceso local:** crear el primer usuario al iniciar la aplicación, iniciar sesión y cambiar la contraseña.

## Requisitos

- Windows 10 o posterior para el ejecutable y el flujo de empaquetado incluidos.
- Python 3.10 o posterior para ejecutar desde el código fuente.
- Tkinter, normalmente incluido con la distribución de Python para Windows.
- `openpyxl` para importar y generar plantillas de Excel.
- PyInstaller para construir el ejecutable.
- Inno Setup, opcional, para generar un instalador de Windows.

## Inicio rápido: ejecutar desde el código fuente

Abre una terminal en la carpeta del proyecto y ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install openpyxl
py app.py
```

Si PowerShell no permite activar el entorno virtual, puedes ejecutar los comandos usando el intérprete del entorno directamente:

```powershell
.\.venv\Scripts\python.exe -m pip install openpyxl
.\.venv\Scripts\python.exe app.py
```

En el primer inicio, crea el usuario y la contraseña desde la pantalla de acceso. La contraseña debe tener al menos seis caracteres.

## Crear el ejecutable

El repositorio incluye un script de compilación para generar `dist\Invendesk.exe`:

```powershell
py -m pip install openpyxl pyinstaller
.\build.bat
```

El ejecutable generado es de un solo archivo y no requiere que Python esté instalado en el equipo donde se ejecuta.

### Crear un instalador (opcional)

1. Instala [Inno Setup](https://jrsoftware.org/isinfo.php).
2. Ejecuta `build.bat`.
3. Abre `Setup.iss` con Inno Setup y compílalo.

El instalador se generará en la carpeta `installer` como `InvendeskSetup-1.0.0.exe`.

## Importar productos desde Excel

Desde **Inventario → Importar Excel**, selecciona un archivo `.xlsx` o `.xlsm`. La aplicación busca encabezados reconocibles en las primeras filas. **Código** y **Nombre** son obligatorios; también puedes incluir categoría, descripción, precio de costo, precio de venta, stock y stock mínimo.

Algunos encabezados aceptados incluyen:

| Campo | Ejemplos |
|---|---|
| Código | `Código`, `SKU`, `Clave` |
| Nombre | `Nombre`, `Producto` |
| Categoría | `Categoría`, `Grupo`, `Departamento` |
| Descripción | `Descripción`, `Detalle`, `Nota` |
| Precio de costo | `Precio de costo`, `Costo`, `Precio de compra` |
| Precio de venta | `Precio de venta`, `Precio`, `PVP` |
| Stock | `Stock`, `Existencia`, `Cantidad` |
| Stock mínimo | `Stock mínimo`, `Stock de alerta`, `Mínimo` |

Puedes descargar una plantilla desde el diálogo de importación. Los productos con código existente se omiten por defecto; marca **Actualizar productos que ya existen (por código)** para actualizar sus datos.

## Datos y copias de seguridad

La base de datos se crea automáticamente como `invendesk.db` en:

```text
%APPDATA%\Invendesk\invendesk.db
```

La carpeta de datos se mantiene separada del ejecutable, por lo que reinstalar o actualizar la aplicación no debería reemplazar la base de datos. Para respaldar la información, cierra Invendesk y copia ese archivo a una ubicación segura. Para restaurar una copia, reemplaza el archivo con la aplicación cerrada.

La base de datos contiene usuarios, productos, clientes, ventas y sus líneas de detalle. La aplicación está diseñada para uso local y no sincroniza datos entre equipos.

## Estructura del proyecto

```text
.
├── app.py                 # Inicio de la aplicación, acceso y navegación
├── auth.py                # Creación de usuarios y autenticación
├── db.py                  # Esquema y acceso a SQLite
├── excel_import.py        # Importación y plantilla de Excel
├── ui.py                  # Componentes y utilidades comunes de interfaz
├── validation.py          # Validación de datos
├── screens/
│   ├── inventory.py       # Inventario e importación/exportación
│   ├── sales.py           # Registro e historial de ventas
│   ├── clients.py         # Gestión de clientes
│   └── reports.py         # Reportes y exportaciones CSV
├── requirements.txt       # Dependencias del proyecto
├── Invendesk.spec         # Configuración de PyInstaller
├── build.bat              # Generación del ejecutable
└── Setup.iss              # Configuración de Inno Setup
```

## Limitaciones y notas

- Los archivos CSV se generan con codificación UTF-8 con BOM para facilitar su apertura en hojas de cálculo.
- Los datos se almacenan en el equipo local; no hay sincronización, servidor ni multiusuario en red.
- No se incluye una suite de pruebas automatizadas en el repositorio.
