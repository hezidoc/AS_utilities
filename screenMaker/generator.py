import json
import os
from components import generar_componentes

def capitalize_first(s):
    if not s:
        return ""
    return s[0].upper() + s[1:]

def generar_proyecto(json_path="entrada.json", output_dir="screen_output"):
    if not os.path.exists(json_path):
        print(f"❌ Error: No se encuentra el archivo {json_path}")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    package_base = data.get("package", "com.example.default")
    screens = data.get("screens", [])
    
    # 1. Invoca tu components.py para estructurar los elementos base
    generar_componentes(package_base, output_dir)
    
    # Configuración de directorios de destino
    screens_dir = os.path.join(output_dir, "screens")
    viewmodels_dir = os.path.join(output_dir, "viewmodel")
    os.makedirs(screens_dir, exist_ok=True)
    os.makedirs(viewmodels_dir, exist_ok=True)
    
    vm_instantiations = []
    nav_destinations = []
    main_screen_buttons = []
    
    for item in screens:
        screen_name = item["name"]
        base_name = screen_name.replace("Screen", "")
        vm_name = f"{base_name}ViewModel"
        vm_var_name = f"{base_name.lower()}ViewModel"
        
        vm_instantiations.append(f"    val {vm_var_name}: {vm_name} = viewModel()")
        nav_destinations.append(f'            composable("{screen_name}") {{ {screen_name}(Modifier, {vm_var_name}) }}')
        
        main_screen_buttons.append(
            f'        Button(\n'
            f'            onClick = {{ navController.navigate("{screen_name}") }},\n'
            f'            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)\n'
            f'        ) {{\n'
            f'            Text("Ir a {base_name} Screen")\n'
            f'        }}'
        )
        
        # ---------------------------------------------------------------------
        # GENERACIÓN DEL VIEWMODEL INDIVIDUAL
        # ---------------------------------------------------------------------
        vm_states = []
        vm_functions = []
        
        for field in item.get("TextFieldList", []):
            field_cap = capitalize_first(field)
            vm_states.append(f'    var {field} by mutableStateOf(""); private set')
            vm_functions.append(
                f'    fun on{field_cap}Changed(nuevoTexto: String) {{\n'
                f'        {field} = nuevoTexto\n'
                f'    }}'
            )
            
        rb_data = item.get("RadioButton", {})
        if rb_data:
            rb_name = rb_data.get("name", "options")
            singular_rb = rb_name[:-1] if rb_name.endswith('s') else rb_name
            singular_rb_cap = capitalize_first(singular_rb)
            
            vm_states.append(f'    var selected{singular_rb_cap} by mutableStateOf(""); private set')
            vm_functions.append(
                f'    fun on{singular_rb_cap}Changed(newOption: String) {{\n'
                f'        selected{singular_rb_cap} = newOption\n'
                f'    }}'
            )
            
        vm_body = "\n\n".join(vm_states) + "\n\n" + "\n\n".join(vm_functions)
        
        viewmodel_template = f"""package {package_base}.viewmodel

import androidx.compose.runtime.setValue
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel

class {vm_name} : ViewModel() {{
{vm_body}
}}
"""
        with open(os.path.join(viewmodels_dir, f"{vm_name}.kt"), "w", encoding="utf-8") as f:
            f.write(viewmodel_template)
        
# ---------------------------------------------------------------------
        # GENERACIÓN DE LA SCREEN INDIVIDUAL (CON BOTÓN DE ACCIÓN Y MYLOG)
        # ---------------------------------------------------------------------
        ui_components = []
        title_spaced = " ".join([capitalize_first(w) for w in screen_name.replace("Screen", " Screen").split()])
        ui_components.append(f'        Header1("{title_spaced}")')
        
        # 1. Añadir TextFields a la UI
        for field in item.get("TextFieldList", []):
            field_cap = capitalize_first(field)
            ui_components.append(
                f'        DefaultOutlinedTextField(\n'
                f'            texto = viewModel.{field},\n'
                f'            onTextoChange = {{ viewModel.on{field_cap}Changed(it) }},\n'
                f'            label = "{field_cap}"\n'
                f'        )'
            )
            
        # 2. Añadir RadioButton a la UI (si existe)
        rb_data = item.get("RadioButton", {})
        singular_rb_cap = ""
        if rb_data:
            rb_options = ", ".join([f'"{opt}"' for opt in rb_data.get("options", [])])
            rb_name = rb_data.get("name", "options")
            singular_rb = rb_name[:-1] if rb_name.endswith('s') else rb_name
            singular_rb_cap = capitalize_first(singular_rb)
            comp_radio = "RadioHorizontal" if rb_data.get("orientacion") == "horizontal" else "RadioVertical"
            
            ui_components.append(
                f'        {comp_radio}(\n'
                f'            options = listOf({rb_options}),\n'
                f'            seleccionada = viewModel.selected{singular_rb_cap},\n'
                f'            onOpcionSelected = {{ viewModel.on{singular_rb_cap}Changed(it) }}\n'
                f'        )'
            )

        # 3. Construcción dinámica del mensaje para el Log
        log_parts = []
        for field in item.get("TextFieldList", []):
            log_parts.append(f'{field}=${{viewModel.{field}}}')
        if rb_data and singular_rb_cap:
            log_parts.append(f'seleccionado=${{viewModel.selected{singular_rb_cap}}}')
        
        log_message = ", ".join(log_parts)

        # 4. Añadir el Botón de Acción que ejecuta el MyLog
        ui_components.append(
            f'        Spacer(modifier = Modifier.height(16.dp))\n\n'
            f'        Button(\n'
            f'            onClick = {{\n'
            f'                MyLog.d("Valores capturados -> {log_message}")\n'
            f'            }},\n'
            f'            modifier = Modifier.fillMaxWidth()\n'
            f'        ) {{\n'
            f'            Text("Mostrar Valores")\n'
            f'        }}'
        )
            
        ui_body = "\n\n".join(ui_components)
        
        # Plantilla final del archivo .kt de la Screen
        screen_template = f"""package {package_base}.screens

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import {package_base}.components.*
import {package_base}.util.MyLog
import {package_base}.viewmodel.{vm_name}

@SuppressWarnings("SpellCheckingInspection")
@Composable
fun {screen_name}(
    modifier: Modifier = Modifier,
    viewModel: {vm_name}
) {{
    DefaultColumn(modifier = modifier) {{
{ui_body}
    }}
}}
"""
        with open(os.path.join(screens_dir, f"{screen_name}.kt"), "w", encoding="utf-8") as f:
            f.write(screen_template)
    # ---------------------------------------------------------------------
    # GENERACIÓN DE MAINSCREEN.KT
    # ---------------------------------------------------------------------
    buttons_block = "\n\n".join(main_screen_buttons)
    mainscreen_template = f"""package {package_base}.screens

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import {package_base}.components.DefaultColumn
import {package_base}.components.Header1

@Composable
fun MainScreen(
    navController: NavController,
    modifier: Modifier = Modifier
) {{
    DefaultColumn(modifier = modifier) {{
        Header1("Main Screen")
        
{buttons_block}
    }}
}}
"""
    with open(os.path.join(screens_dir, "MainScreen.kt"), "w", encoding="utf-8") as f:
        f.write(mainscreen_template)

    # ---------------------------------------------------------------------
    # GENERACIÓN DE MAINACTIVITY.KT (CON REFIX DE SNACKBARSTATE)
    # ---------------------------------------------------------------------
    vm_instantiations_str = "\n".join(vm_instantiations)
    nav_destinations_str = "\n".join(nav_destinations)
    
    mainactivity_template = f"""package {package_base}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import {package_base}.components.BottomNavigationBar
import {package_base}.screens.*
import {package_base}.viewmodel.*

class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContent {{
            MainApp()
        }}
    }}
}}

@Composable
fun MainApp() {{
    val navController = rememberNavController()
    val snackbarHostState = remember {{ SnackbarHostState() }}
    
{vm_instantiations_str}

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {{
            BottomNavigationBar(
                onNavigate = {{ ruta ->
                    navController.navigate(ruta) {{
                        popUpTo(navController.graph.startDestinationId) {{
                            inclusive = false
                        }}
                        launchSingleTop = true
                    }}
                }}
            )
        }},
        snackbarHost = {{
            SnackbarHost(
                snackbarHostState,
                modifier = Modifier.padding(bottom = 120.dp)
            )
        }}
    ) {{ innerPadding ->
        NavHost(
            navController = navController,
            startDestination = "MainScreen",
            modifier = Modifier.padding(innerPadding)
        ) {{
            composable("MainScreen") {{ MainScreen(navController, Modifier) }}
            
{nav_destinations_str}
        }}
    }}
}}
"""
    with open(os.path.join(output_dir, "MainActivity.kt"), "w", encoding="utf-8") as f:
        f.write(mainactivity_template)
    print("✔ El proyecto limpio sin LoginScreen se ha generado con éxito en 'output/'")

if __name__ == "__main__":
    generar_proyecto()