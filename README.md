# Invendesk

Aplicación de escritorio para la operación diaria de pequeños negocios. Invendesk centraliza el inventario, el registro de ventas, la información de clientes y reportes operativos en una interfaz local para Windows.

La aplicación está construida con Python y Tkinter. Los datos se conservan en una base de datos SQLite en el perfil del usuario; no requiere servidor ni conexión a Internet para las funciones principales.

## Contenido

- [Capacidades](#capacidades)
- [Plataforma y tecnología](#plataforma-y-tecnología)
- [Ejecución desde el código fuente](#ejecución-desde-el-código-fuente)
- [Compilación y distribución](#compilación-y-distribución)
- [Importación de productos](#importación-de-productos)
- [Almacenamiento y respaldo](#almacenamiento-y-respaldo)
- [Arquitectura del proyecto](#arquitectura-del-proyecto)
- [Alcance y consideraciones](#alcance-y-consideraciones)

## Capacidades

| Área | Operaciones |
|---|---|
| **Inventario** | Alta, edición, búsqueda y eliminación de productos; control de stock mínimo; importación desde Excel y exportación a CSV. |
| **Ventas** | Registro de ventas de mostrador o asociadas a un cliente; carrito con validación de existencias; historial y detalle por venta. |
| **Clientes** | Administración de datos de contacto y notas; búsqueda y reportes agregados de compras. |
| **Reportes** | Ingresos y artículos vendidos por período; valoración del inventario; alertas de stock; actividad de clientes; exportaciones CSV. |
| **Acceso** | Creación inicial de usuario, inicio de sesión y cambio de contraseña. |

## Plataforma y tecnología

- **Plataforma de distribución:** Windows 10 o posterior.
- **Ejecución desde código:** Python 3.10 o posterior y Tkinter.
- **Persistencia:** SQLite, con creación automática del esquema al iniciar.
- **Excel:** `openpyxl` para importar productos y generar plantillas.
- **Empaquetado:** PyInstaller; Inno Setup es opcional para generar el instalador.

## Ejecución desde el código fuente

Desde PowerShell, en el directorio del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py app.py
```

Si no se activa el entorno virtual, utiliza su intérprete directamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

En la primera ejecución, Invendesk solicitará crear el usuario inicial. La contraseña debe tener al menos seis caracteres.

## Compilación y distribución

Para generar el ejecutable independiente `dist\Invendesk.exe`:

```powershell
py -m pip install openpyxl pyinstaller
.\build.bat
```

El script `build.bat` ejecuta la configuración de `Invendesk.spec` y produce un ejecutable de un solo archivo, sin ventana de consola. El equipo de destino no necesita tener Python instalado.

### Instalador de Windows

1. Instala [Inno Setup](https://jrsoftware.org/isinfo.php).
2. Ejecuta `build.bat`.
3. Abre `Setup.iss` con Inno Setup y compila el instalador.

La configuración actual genera `installer\InvendeskSetup-1.0.0.exe`.

## Importación de productos

En **Inventario → Importar Excel**, selecciona un archivo `.xlsx` o `.xlsm`. Invendesk busca encabezados reconocibles en las primeras 15 filas y permite descargar una plantilla desde el mismo diálogo.

Cada fila de producto debe incluir **Código**, **Nombre** y un **Precio de venta válido**. Categoría, descripción, precio de costo, stock y stock mínimo son opcionales; los campos numéricos opcionales vacíos se interpretan como cero. Los códigos se normalizan a mayúsculas.

| Campo | Encabezados reconocidos (ejemplos) |
|---|---|
| Código | `Código`, `SKU`, `Clave` |
| Nombre | `Nombre`, `Producto` |
| Categoría | `Categoría`, `Grupo`, `Departamento` |
| Descripción | `Descripción`, `Detalle`, `Nota` |
| Precio de costo | `Precio de costo`, `Costo`, `Precio de compra` |
| Precio de venta | `Precio de venta`, `Precio`, `PVP` |
| Stock | `Stock`, `Existencia`, `Cantidad` |
| Stock mínimo | `Stock mínimo`, `Stock de alerta`, `Mínimo` |

Por defecto, las filas con un código ya existente se reportan como errores y no actualizan el producto. La opción **Actualizar productos que ya existen (por código)** activa la actualización de los datos del producto, incluido el stock.

## Almacenamiento y respaldo

En Windows, la base de datos se guarda en:

```text
%APPDATA%\Invendesk\invendesk.db
```

Si `APPDATA` no está definido, la aplicación utiliza `~/.invendesk/invendesk.db`. El directorio de datos es independiente de la ubicación del ejecutable.

Para realizar una copia de seguridad o restaurarla:

1. Cierra Invendesk.
2. Copia o reemplaza `invendesk.db` desde la carpeta de datos.
3. Inicia la aplicación nuevamente.

La base de datos contiene usuarios, productos, clientes, ventas y líneas de venta. Mantén las copias de respaldo en una ubicación con controles de acceso apropiados.

## Arquitectura del proyecto

La interfaz se organiza por áreas funcionales en `screens/`. `db.py` centraliza la conexión y el esquema de SQLite; `validation.py` reúne validaciones compartidas y `excel_import.py` implementa la importación y creación de plantillas.

```text
.
├── app.py                  # Inicio, autenticación visual y navegación
├── auth.py                 # Creación de usuarios y verificación de contraseñas
├── db.py                   # Esquema, rutas de datos y conexión SQLite
├── validation.py           # Validación y normalización de entradas
├── excel_import.py         # Importación de productos y plantilla Excel
├── ui.py                   # Utilidades compartidas de interfaz
├── screens/
│   ├── inventory.py        # Inventario
│   ├── sales.py            # Ventas e historial
│   ├── clients.py          # Clientes
│   └── reports.py          # Reportes y exportaciones
├── requirements.txt        # Dependencias Python
├── Invendesk.spec          # Configuración de PyInstaller
├── build.bat               # Compilación del ejecutable
└── Setup.iss               # Configuración del instalador
```

## Alcance y consideraciones

- Invendesk es una aplicación local: no incluye sincronización, servicio remoto ni modo multiusuario en red.
- La autenticación es propia de la aplicación. Las contraseñas se almacenan mediante PBKDF2-HMAC-SHA256 con salt; el archivo SQLite **no está cifrado**.
- La solución no implementa roles ni permisos diferenciados entre usuarios.
- Las exportaciones CSV usan UTF-8 con BOM para mejorar la compatibilidad con hojas de cálculo.
- El repositorio no incluye una suite de pruebas automatizadas.
