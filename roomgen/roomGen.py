import argparse
import os

"""
DATA EXAMPLE

Coche
    STR matricula
    STR modelo
    STR color
    STR fechaEntrada

vehiculo
    INT id_cliente
    STR matricula
    STR marca
    STR modelo
    STR color

cliente
    STR nombre
    STR apellido
    STR dni
"""

def main():
    parser = argparse.ArgumentParser(description="Generador de código Room")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Ejecuta el programa en modo test"
    )

    args = parser.parse_args()

    if args.test:
        print("Modo TEST activado")
    else:
        print("Modo normal")
        roomGenerator()



def roomGenerator():
    package = input("Introduce package: ").strip()

    # Limpia "package " si el usuario lo escribe
    if package.startswith("package "):
        package = package.replace("package ", "").strip()

    dbname = input("Introduce nombre de base de datos: ").strip().capitalize()

    ruta = "data.txt"  # input("Introduce la ruta del archivo de entidades: ").strip()
    entidades = solicitar_entidades_desde_archivo(ruta)

    entityList = list(entidades.keys())

    #  Archivos generales (UNA SOLA VEZ) 
    createFile(f"{dbname}Database.kt", generarDatabase(package, dbname, entityList))
    createFile("app.build.gradle.kts", generarBuildGradleApp(package))
    createFile("top.build.gradle.kts", generarBuildGradleTop())
    createFile("MainActivity.kt", generarMainActivity(package, dbname, entityList[0]))
    createFile(f"{dbname}Repository.kt", generarRepository(package, dbname, entityList[0]))


    #  Archivos por entidad 
    for entity in entityList:
        campos = entidades[entity]

        createFile(f"{entity}Dao.kt", generarDAO(package, entity,campos))
        createFile(f"{entity}.kt", generarEntity(package, entity, campos))
        createFile(f"{entity}ViewModel.kt", generarViewModel(package, dbname, entity,campos))



    




def createFile(fileName, content):
    # 1. Definimos el nombre de la carpeta
    folder = "room_code_output"
    
    # 2. Si la carpeta no existe, la creamos
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Combinamos la carpeta con el nombre del archivo (ej: "output/LibroDao.kt")
    filePath = os.path.join(folder, fileName)
    
    try:
        with open(filePath, "w", encoding="utf-8") as file:
            file.write(content.strip())
        print(f"✅ Archivo '{filePath}' generado con éxito.")
    except Exception as e:
        print(f"❌ Error al crear el archivo: {e}")

def solicitar_entidades_desde_archivo(ruta_archivo):
    entidades = {}
    entidad_actual = None

    with open(ruta_archivo, "r", encoding="utf-8") as file:
        for linea in file:
            linea = linea.rstrip()

            # Línea vacía → se ignora
            if not linea:
                continue

            # Entidad (sin indentación)
            if not linea.startswith((" ", "\t")):
                entidad_actual = linea.capitalize()
                entidades[entidad_actual] = []
            else:
                # Campo de la entidad
                partes = linea.strip().split(maxsplit=1)
                if len(partes) == 2 and entidad_actual:
                    tipo, nombre = partes
                    entidades[entidad_actual].append({
                        "tipo": tipo,
                        "nombre": nombre
                    })

    return entidades


#def solicitar_entidades():
#    entidades = []
#    while True:
#        nombre = input("Introduce el nombre de la entidad (o ENTER para finalizar): ").strip()
#        if nombre == "":
#            break
#        entidades.append(nombre.capitalize())
#    return entidades


##############################################
################## GENERADORES ###############
##############################################



def generarEntity(package, entityName, campos):
    # Mapeo de tipos del archivo a tipos Kotlin
    tipo_map = {
        "STR": "String",
        "INT": "Int",
        "DOUBLE": "Double",
        "FLOAT": "Float",
        "BOOL": "Boolean"
    }

    atributos = []

    for campo in campos:
        tipo_kotlin = tipo_map.get(campo["tipo"], "String")
        nombre = campo["nombre"]

        atributos.append(f"    val {nombre}: {tipo_kotlin}")

    atributos_str = ",\n".join(atributos)

    return f'''
package {package}

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "{entityName.lower()}")
data class {entityName}(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
{atributos_str}
)
'''.strip()

    
def generarDAO(package, entityName, campos):
    entityLower = entityName.lower()

    # Elegir el primer campo que no sea 'id' para el filtro
    campoFiltro = next((c for c in campos if c["nombre"].lower() != "id"), None)
    if campoFiltro:
        nombreFiltro = campoFiltro["nombre"]
    else:
        nombreFiltro = None  # No se genera filtrado si no hay campo

    filtroQuery = ""
    if nombreFiltro:
        filtroQuery = f'''
    @Query("""
        SELECT * FROM {entityLower}
        WHERE (:valor IS NULL OR {nombreFiltro} LIKE '%' || :valor || '%')
    """)
    fun filtrar{entityName}s(valor: String?): Flow<List<{entityName}>>'''

    # Query deleteById
    deleteByIdQuery = f'''
    @Query("DELETE FROM {entityLower} WHERE id = :id")
    suspend fun deleteById(id: Int)'''

    return f'''
package {package}.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Delete
import androidx.room.Update
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface {entityName}Dao {{

    @Insert
    suspend fun insert({entityLower}: {entityName})

    @Update
    suspend fun update({entityLower}: {entityName})

    @Delete
    suspend fun delete({entityLower}: {entityName})

    @Query("SELECT * FROM {entityLower}")
    fun getAll(): Flow<List<{entityName}>>

    @Query("SELECT * FROM {entityLower} WHERE id = :id")
    fun getById(id: Int): Flow<{entityName}>

{filtroQuery}

{deleteByIdQuery}
}}
'''.strip()






def generarDatabase(package, databaseName, entities):

    entities_str = ", ".join(f"{e}::class" for e in entities)
    dao_methods = "\n".join(
        f"    abstract fun {e.lower()}Dao(): {e}Dao"
        for e in entities
    )

    return f'''
package {package}

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [{entities_str}],
    version = 1,
    exportSchema = false
)
abstract class {databaseName}Database : RoomDatabase() {{

{dao_methods}

    companion object {{
        @Volatile
        private var INSTANCE: {databaseName}Database? = null

        fun getDatabase(context: Context): {databaseName}Database {{
            return INSTANCE ?: synchronized(this) {{
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    {databaseName}Database::class.java,
                    "{databaseName.lower()}_database"
                ).build()
                INSTANCE = instance
                instance
            }}
        }}
    }}
}}
'''.strip()

def generarViewModel(package, dbName, entity, campos):
    """
    Genera un ViewModel tipo Compose con StateFlow y mutableStateOf
    Campos: lista de dict {"tipo": "STR", "nombre": "matricula"}
    """
    entityLower = entity.lower()

    # Campos que no sean PK
    camposForm = [c for c in campos if c["nombre"].lower() != "id"]

    # Variables mutableStateOf
    varsMutable = "\n    ".join(
        f'var {c["nombre"]} by mutableStateOf("")\n        private set'
        for c in camposForm
    )

    # Funciones onCampoChanged
    funcsOnChanged = "\n\n    ".join(
        f'fun on{c["nombre"].capitalize()}Changed(nuevoTexto: String) {{ {c["nombre"]} = nuevoTexto }}'
        for c in camposForm
    )

    # Creación de entidad en guardar/editar
    camposParams = ",\n                    ".join(
        f'{c["nombre"]} = {c["nombre"]}.trim()'
        for c in camposForm
    )

    return f'''
package {package}.ui.shared

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class {entity}ViewModel(
    private val repositorio: {dbName}Repository
) : ViewModel() {{

    private val _{entityLower}Filtrados = MutableStateFlow<List<{entity}>>(emptyList())
    val {entityLower}Filtrados: StateFlow<List<{entity}>> = _{entityLower}Filtrados

    {varsMutable}

    var errorMensaje by mutableStateOf<String?>(null)
        private set

    init {{
        viewModelScope.launch {{
            repositorio.todosLos{entity}s.collect {{ lista ->
                _{entityLower}Filtrados.value = lista
            }}
        }}
    }}

    fun guardar{entity}(onSuccess: () -> Unit) {{
        viewModelScope.launch {{
            try {{
                val nuevo = {entity}(
                    {camposParams}
                )
                repositorio.insertar{entity}(nuevo)
                onSuccess()
                limpiarFormulario()
            }} catch (e: Exception) {{
                errorMensaje = "Error al guardar: ${{e.message}}"
            }}
        }}
    }}

    fun editar{entity}(id: Int, onSuccess: () -> Unit) {{
        viewModelScope.launch {{
            try {{
                val actualizado = {entity}(
                    id = id,
                    {camposParams}
                )
                repositorio.actualizar{entity}(actualizado)
                onSuccess()
                limpiarFormulario()
            }} catch (e: Exception) {{
                errorMensaje = "Error al editar: ${{e.message}}"
            }}
        }}
    }}

    private fun limpiarFormulario() {{
        {"; ".join(f'{c["nombre"]} = ""' for c in camposForm)}

        errorMensaje = null
    }}

    {funcsOnChanged}
}}
'''.strip()


def generarBuildGradleTop():
    return'''
plugins {
    id("com.google.devtools.ksp") version "2.0.21-1.0.27" apply false
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
}
    '''
def generarBuildGradleApp(package):

    projectPath = package.replace("package ","")
    print("Este es un tu path " + projectPath)

    return'''
plugins {{
    id("com.google.devtools.ksp")
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}}

android {{
    namespace = "{0}"
    compileSdk {{
        version = release(36)
    }}

    defaultConfig {{
        applicationId = "{0}"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
    }}
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }}
    kotlinOptions {{
        jvmTarget = "11"
    }}
    buildFeatures {{
        compose = true
    }}
}}

dependencies {{
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")
    val room_version = "2.8.3"
    implementation("androidx.room:room-runtime:$room_version")
    ksp("androidx.room:room-compiler:$room_version")
    annotationProcessor("androidx.room:room-compiler:$room_version")

    implementation("androidx.room:room-ktx:$room_version")
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    debugImplementation(libs.androidx.compose.ui.tooling)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}}
    '''.format(projectPath)


def generarRepository(package, dbName, entity):
    entityLower = entity.lower()
    return f'''
package {package}.data

import kotlinx.coroutines.flow.Flow

class {dbName}Repository(private val dao: {entity}Dao) {{

    val todosLos{entity}s: Flow<List<{entity}>> = dao.getAll()

    suspend fun insertar{entity}({entityLower}: {entity}) {{
        dao.insert({entityLower})
    }}

    suspend fun get{entity}byId(id: Int): Flow<{entity}> {{
        return dao.getById(id)
    }}

    suspend fun eliminar{entity}({entityLower}: {entity}) {{
        dao.delete({entityLower})
    }}

    suspend fun actualizar{entity}({entityLower}: {entity}) {{
        dao.update({entityLower})
    }}

    // Borrar por ID directamente
    suspend fun eliminarPorId(id: Int) {{
        dao.deleteById(id)
    }}

    // Ejemplo de filtrado simple (puedes ajustar según tus DAOs)
    fun filtrar{entity}s(filterValue: String?): Flow<List<{entity}>> =
        dao.filtrar{entity}s(filterValue)
}}
'''.strip()




def generarMainActivity(package, dbName, entity):
    entityLower = entity.lower()
    return f'''
package {package}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import {package}.data.{entity}Repository
import {package}.ui.theme.{dbName}Theme
import {package}.ui.shared.{entity}ViewModel
import {package}.ui.ventanas.VentanaEditar
import {package}.ui.ventanas.VentanaVer
import {package}.ui.ventanas.VentanaCrear

class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {{
            {dbName}Theme {{
                Scaffold(modifier = Modifier.fillMaxSize()) {{ innerPadding ->
                    gestorVentanas(Modifier.padding(innerPadding))
                }}
            }}
        }}
    }}
}}

@Composable
fun gestorVentanas(modifier: Modifier) {{
    val context = LocalContext.current

    val repositorio = {entity}Repository({dbName}Database.getDatabase(context).{entityLower}Dao())

    val factory = object : androidx.lifecycle.ViewModelProvider.Factory {{
        override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {{
            return {entity}ViewModel(repositorio) as T
        }}
    }}

    val {entityLower}ViewModel: {entity}ViewModel = viewModel(factory = factory)

    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = "ver") {{

        composable(
            route = "editar/{{id}}",
            arguments = listOf(
                navArgument("id") {{ type = NavType.IntType }}
            )
        ) {{ backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: 0
            VentanaEditar(navController, modifier, {entityLower}ViewModel, id)
        }}

        composable("ver") {{ VentanaVer(navController, modifier, {entityLower}ViewModel) }}
        composable("crear") {{ VentanaCrear(navController, modifier, {entityLower}ViewModel) }}
    }}
}}
'''.strip()




if __name__ == "__main__":
    main()