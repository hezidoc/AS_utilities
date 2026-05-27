import os

def generar_componentes(package_base, output_dir="output"):
    """Genera los archivos Kotlin de los componentes base con el package especificado"""
    components_dir = os.path.join(output_dir, "components")
    os.makedirs(components_dir, exist_ok=True)
    
    # 1. RadioHorizontal.kt (¡Nuevo!)
    radio_horizontal = f"""package {package_base}.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * [RadioButton] de selección horizontal.
 *
 * Este componente sigue el patrón de "State Hoisting", el componente solo recibe ordenes, no sabe el estado
 * delega el estado al llamador, esto para facilita la reutilización y las pruebas.
 */
@Composable
fun RadioHorizontal(
    options: List<String>,
    seleccionada: String,
    onOpcionSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {{
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically
    ) {{
        options.forEach {{ opcion ->
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.clickable {{ onOpcionSelected(opcion) }}
            ) {{
                RadioButton(
                    selected = (opcion == seleccionada),
                    onClick = {{ onOpcionSelected(opcion) }}
                )
                Text(
                    text = opcion,
                    style = MaterialTheme.typography.bodyMedium
                )
            }}
            Spacer(modifier = Modifier.width(8.dp))
        }}
    }}
}}
"""
    with open(os.path.join(components_dir, "RadioHorizontal.kt"), "w", encoding="utf-8") as f:
        f.write(radio_horizontal)

# 1.5. RadioVertical.kt (¡Nuevo!)
    radio_vertical = f"""package {package_base}.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * [RadioButton] de selección vertical.
 *
 * Este componente sigue el patrón de "State Hoisting", el componente solo recibe ordenes, no sabe el estado
 * delega el estado al llamador, esto para facilita la reutilización y las pruebas.
 */
@Composable
fun RadioVertical(
    options: List<String>,
    seleccionada: String,
    onOpcionSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {{
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.Start
    ) {{
        options.forEach {{ opcion ->
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.clickable {{ onOpcionSelected(opcion) }}
            ) {{
                RadioButton(
                    selected = (opcion == seleccionada),
                    onClick = {{ onOpcionSelected(opcion) }}
                )
                Text(
                    text = opcion,
                    style = MaterialTheme.typography.bodyMedium
                )
            }}
            Spacer(modifier = Modifier.height(4.dp))
        }}
    }}
}}
"""
    with open(os.path.join(components_dir, "RadioVertical.kt"), "w", encoding="utf-8") as f:
        f.write(radio_vertical)

    # 2. BottomNavigationBar.kt
    bottom_nav = f"""package {package_base}.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun BottomNavigationBar(
    onNavigate: (String) -> Unit
) {{
    BottomAppBar(
        containerColor = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.primary
    ) {{
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {{
            IconButton(onClick = {{ onNavigate("MainScreen") }}) {{
                Icon(Icons.Default.Home, contentDescription = "Inicio", modifier = Modifier.size(30.dp))
            }}
            IconButton(onClick = {{ }}) {{
                Icon(Icons.Default.Visibility, contentDescription = "Ver", modifier = Modifier.size(30.dp))
            }}
            IconButton(onClick = {{ }}) {{
                Icon(Icons.Default.Add, contentDescription = "Insertar", modifier = Modifier.size(30.dp))
            }}
            IconButton(onClick = {{ }}) {{
                Icon(Icons.Default.Delete, contentDescription = "Eliminar", modifier = Modifier.size(30.dp))
            }}
        }}
    }}
}}
"""
    with open(os.path.join(components_dir, "BottomNavigationBar.kt"), "w", encoding="utf-8") as f:
        f.write(bottom_nav)

    # 3. DefaultColumn.kt
    default_column = f"""package {package_base}.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun DefaultColumn(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {{
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Top,
        content = content
    )
}}
"""
    with open(os.path.join(components_dir, "DefaultColumn.kt"), "w", encoding="utf-8") as f:
        f.write(default_column)

    # 4. DefaultOutlinedTextField.kt
    default_tf = f"""package {package_base}.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun DefaultOutlinedTextField(
    texto: String,
    onTextoChange: (String) -> Unit,
    label: String = "placeholder"
) {{
    OutlinedTextField(
        value = texto,
        onValueChange = onTextoChange,
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        label = {{ Text(label) }},
        singleLine = true
    )
}}
"""
    with open(os.path.join(components_dir, "DefaultOutlinedTextField.kt"), "w", encoding="utf-8") as f:
        f.write(default_tf)

    # 5. Headers.kt
    headers = f"""package {package_base}.components

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.FontWeight

@Composable
fun Header1(
    text: String
) {{
    Text(
        text = text,
        style = MaterialTheme.typography.titleLarge.copy(
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )
    )
}}

@Composable
fun Header2(
    text: String
) {{
    Text(
        text = text,
        style = MaterialTheme.typography.titleMedium.copy(
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.secondary
        )
    )
}}
"""
    with open(os.path.join(components_dir, "Headers.kt"), "w", encoding="utf-8") as f:
        f.write(headers)
    print("✔ Todos los componentes base (incluyendo RadioHorizontal) han sido actualizados.")



# ---------------------------------------------------------------------
    # GENERACIÓN DE LA CARPETA UTIL Y MYLOG.KT
    # ---------------------------------------------------------------------
    util_dir = os.path.join(output_dir, "util")
    os.makedirs(util_dir, exist_ok=True)

    mylog_content = f"""package {package_base}.util

import android.util.Log

/**
 * Es una forma global de llamar a un log, asi podemos estandarizar el mensaje.
 * Aseguramos que todos los logs tengan un [MyApp]
 * También informa desde que función se esta realizando el log.
 */
object MyLog {{
    private const val PREFIX = "[MyApp] "

    private fun caller(): String {{
        val trace = Throwable().stackTrace

        // Buscamos el primer elemento que NO sea de librerías del sistema ni de esta clase
        val frame = trace.firstOrNull {{ el ->
            val cn = el.className
            !cn.startsWith("android.") &&
                    !cn.startsWith("com.android.") &&
                    !cn.startsWith("androidx.") &&
                    !cn.startsWith("kotlin.") &&
                    !cn.startsWith("java.") &&
                    !cn.startsWith("kotlinx.") &&
                    !cn.contains("MyLog") // Evitamos que el log se apunte a sí mismo
        }}

        val file = frame?.fileName ?: "Unknown.kt"
        val line = frame?.lineNumber ?: -1

        // Mantenemos este formato porque es el que permite hacer CLICK en el Logcat
        return "($file:$line)"
    }}

    fun d(message: String) {{
        Log.d(caller(), PREFIX + message)
    }}

    fun e(message: String, throwable: Throwable? = null) {{
        Log.e(caller(), PREFIX + message, throwable)
    }}
}}
"""

    with open(os.path.join(util_dir, "MyLog.kt"), "w", encoding="utf-8") as f:
        f.write(mylog_content)
        
    print("✔ Carpeta 'util' y archivo 'MyLog.kt' generados correctamente.")