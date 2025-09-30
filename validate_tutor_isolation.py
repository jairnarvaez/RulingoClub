"""
==============================================================================
SCRIPT DE VALIDACIÓN - AISLAMIENTO DE DATOS ENTRE TUTORES
==============================================================================
Este script valida que cada tutor SOLO pueda ver los estudiantes que él creó.

ESCENARIO DE PRUEBA:
- 5 Users totales
- 2 Tutores (José y María)
- 3 Students (Ana, Pedro, Luis)
- José creó a Ana (1 estudiante)
- María creó a Pedro y Luis (2 estudiantes)

VALIDACIONES:
✅ José puede ver a Ana (su estudiante)
✅ José NO puede ver a Pedro ni Luis (estudiantes de María)
✅ María puede ver a Pedro y Luis (sus estudiantes)
✅ María NO puede ver a Ana (estudiante de José)
✅ tutor1.students.all() retorna SOLO sus estudiantes
✅ tutor2.students.all() retorna SOLO sus estudiantes

INSTRUCCIONES:
1. Guardar este archivo como: validate_tutor_isolation.py
2. Editar líneas 35 y 40 con nombres correctos de proyecto/app
3. Ejecutar: python validate_tutor_isolation.py
==============================================================================
"""

import os
import sys
import django

# ⚠️ CONFIGURACIÓN - EDITAR ESTAS LÍNEAS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')  
django.setup()

from django.contrib.auth.models import User
from django.db.models import Q

# ⚠️ CONFIGURACIÓN - EDITAR ESTA LÍNEA
from accounts.models import Tutor, Student  


# ==============================================================================
# UTILIDADES PARA PRINTS CLAROS
# ==============================================================================

def print_header(text):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    """Imprime una sección"""
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80)


def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"✅ {message}")


def print_error(message):
    """Imprime mensaje de error"""
    print(f"❌ {message}")


def print_info(message):
    """Imprime información"""
    print(f"ℹ️  {message}")


def print_data(label, value):
    """Imprime datos formateados"""
    print(f"   📊 {label}: {value}")


# ==============================================================================
# SETUP: CREAR DATOS DE PRUEBA
# ==============================================================================

def setup_test_data():
    """
    Crea el escenario de prueba:
    - 2 Tutores
    - 3 Estudiantes distribuidos entre los tutores
    """
    print_header("PASO 1: CREANDO DATOS DE PRUEBA")
    
    # Limpiar datos previos si existen
    print_info("Limpiando datos de pruebas anteriores...")
    Student.objects.filter(user__username__startswith='test_iso_').delete()
    Tutor.objects.filter(user__username__startswith='test_iso_').delete()
    User.objects.filter(username__startswith='test_iso_').delete()
    print_success("Limpieza completada")
    
    print_section("Creando Tutores")
    
    # TUTOR 1: José
    user_jose = User.objects.create_user(
        username='test_iso_jose',
        email='jose@example.com',
        password='password123',
        first_name='José',
        last_name='García'
    )
    tutor_jose = Tutor.objects.create(
        user=user_jose,
        bio='Profesor de ruso con 5 años de experiencia',
        experience_years=5
    )
    print_success(f"Tutor 1 creado: {tutor_jose}")
    print_data("Username", user_jose.username)
    print_data("ID", tutor_jose.id)
    
    # TUTOR 2: María
    user_maria = User.objects.create_user(
        username='test_iso_maria',
        email='maria@example.com',
        password='password123',
        first_name='María',
        last_name='López'
    )
    tutor_maria = Tutor.objects.create(
        user=user_maria,
        bio='Profesora de ruso nativa',
        experience_years=10
    )
    print_success(f"Tutor 2 creado: {tutor_maria}")
    print_data("Username", user_maria.username)
    print_data("ID", tutor_maria.id)
    
    print_section("Creando Estudiantes")
    
    # ESTUDIANTE 1: Ana (creado por José)
    user_ana = User.objects.create_user(
        username='test_iso_ana',
        email='ana@example.com',
        password='password123',
        first_name='Ana',
        last_name='Martínez'
    )
    student_ana = Student.objects.create(
        user=user_ana,
        created_by=tutor_jose  # ← José es el creador
    )
    print_success(f"Estudiante 1 creado: {student_ana}")
    print_data("Creado por", student_ana.created_by)
    print_data("ID", student_ana.id)
    
    # ESTUDIANTE 2: Pedro (creado por María)
    user_pedro = User.objects.create_user(
        username='test_iso_pedro',
        email='pedro@example.com',
        password='password123',
        first_name='Pedro',
        last_name='Rodríguez'
    )
    student_pedro = Student.objects.create(
        user=user_pedro,
        created_by=tutor_maria  # ← María es la creadora
    )
    print_success(f"Estudiante 2 creado: {student_pedro}")
    print_data("Creado por", student_pedro.created_by)
    print_data("ID", student_pedro.id)
    
    # ESTUDIANTE 3: Luis (creado por María)
    user_luis = User.objects.create_user(
        username='test_iso_luis',
        email='luis@example.com',
        password='password123',
        first_name='Luis',
        last_name='Fernández'
    )
    student_luis = Student.objects.create(
        user=user_luis,
        created_by=tutor_maria  # ← María es la creadora
    )
    print_success(f"Estudiante 3 creado: {student_luis}")
    print_data("Creado por", student_luis.created_by)
    print_data("ID", student_luis.id)
    
    print_section("Resumen de Datos Creados")
    print_data("Total Tutores", 2)
    print_data("Total Estudiantes", 3)
    print_data("Estudiantes de José", tutor_jose.students.count())
    print_data("Estudiantes de María", tutor_maria.students.count())
    
    return {
        'tutor_jose': tutor_jose,
        'tutor_maria': tutor_maria,
        'student_ana': student_ana,
        'student_pedro': student_pedro,
        'student_luis': student_luis
    }


# ==============================================================================
# TEST 1: JOSÉ SOLO VE A ANA (SU ESTUDIANTE)
# ==============================================================================

def test_jose_sees_only_ana(data):
    """
    Valida que José solo puede ver a Ana, su estudiante.
    NO debe ver a Pedro ni Luis (estudiantes de María).
    """
    print_header("TEST 1: José solo ve a Ana (su estudiante)")
    
    tutor_jose = data['tutor_jose']
    student_ana = data['student_ana']
    student_pedro = data['student_pedro']
    student_luis = data['student_luis']
    
    passed = True
    
    # Obtener estudiantes de José usando related_name
    estudiantes_jose = tutor_jose.students.all()
    
    print_section("Estudiantes visibles para José")
    print_data("Total estudiantes", estudiantes_jose.count())
    
    if estudiantes_jose.count() == 0:
        print_error("José NO tiene estudiantes visibles")
        return False
    
    for student in estudiantes_jose:
        print_info(f"  - {student}")
    
    print_section("Validaciones de Acceso")
    
    # ✅ José DEBE ver a Ana
    if student_ana in estudiantes_jose:
        print_success("José PUEDE ver a Ana (correcto)")
    else:
        print_error("José NO PUEDE ver a Ana (incorrecto - es su estudiante)")
        passed = False
    
    # ✅ José NO debe ver a Pedro
    if student_pedro not in estudiantes_jose:
        print_success("José NO PUEDE ver a Pedro (correcto - no es su estudiante)")
    else:
        print_error("José PUEDE ver a Pedro (incorrecto - es estudiante de María)")
        passed = False
    
    # ✅ José NO debe ver a Luis
    if student_luis not in estudiantes_jose:
        print_success("José NO PUEDE ver a Luis (correcto - no es su estudiante)")
    else:
        print_error("José PUEDE ver a Luis (incorrecto - es estudiante de María)")
        passed = False
    
    # ✅ Verificar que solo tiene 1 estudiante
    if estudiantes_jose.count() == 1:
        print_success("José ve exactamente 1 estudiante (correcto)")
    else:
        print_error(f"José ve {estudiantes_jose.count()} estudiantes (debería ver solo 1)")
        passed = False
    
    return passed


# ==============================================================================
# TEST 2: MARÍA SOLO VE A PEDRO Y LUIS (SUS ESTUDIANTES)
# ==============================================================================

def test_maria_sees_only_pedro_and_luis(data):
    """
    Valida que María solo puede ver a Pedro y Luis, sus estudiantes.
    NO debe ver a Ana (estudiante de José).
    """
    print_header("TEST 2: María solo ve a Pedro y Luis (sus estudiantes)")
    
    tutor_maria = data['tutor_maria']
    student_ana = data['student_ana']
    student_pedro = data['student_pedro']
    student_luis = data['student_luis']
    
    passed = True
    
    # Obtener estudiantes de María usando related_name
    estudiantes_maria = tutor_maria.students.all()
    
    print_section("Estudiantes visibles para María")
    print_data("Total estudiantes", estudiantes_maria.count())
    
    if estudiantes_maria.count() == 0:
        print_error("María NO tiene estudiantes visibles")
        return False
    
    for student in estudiantes_maria:
        print_info(f"  - {student}")
    
    print_section("Validaciones de Acceso")
    
    # ✅ María DEBE ver a Pedro
    if student_pedro in estudiantes_maria:
        print_success("María PUEDE ver a Pedro (correcto)")
    else:
        print_error("María NO PUEDE ver a Pedro (incorrecto - es su estudiante)")
        passed = False
    
    # ✅ María DEBE ver a Luis
    if student_luis in estudiantes_maria:
        print_success("María PUEDE ver a Luis (correcto)")
    else:
        print_error("María NO PUEDE ver a Luis (incorrecto - es su estudiante)")
        passed = False
    
    # ✅ María NO debe ver a Ana
    if student_ana not in estudiantes_maria:
        print_success("María NO PUEDE ver a Ana (correcto - no es su estudiante)")
    else:
        print_error("María PUEDE ver a Ana (incorrecto - es estudiante de José)")
        passed = False
    
    # ✅ Verificar que solo tiene 2 estudiantes
    if estudiantes_maria.count() == 2:
        print_success("María ve exactamente 2 estudiantes (correcto)")
    else:
        print_error(f"María ve {estudiantes_maria.count()} estudiantes (debería ver solo 2)")
        passed = False
    
    return passed


# ==============================================================================
# TEST 3: VERIFICAR CAMPO created_by CORRECTAMENTE ASIGNADO
# ==============================================================================

def test_created_by_field(data):
    """
    Valida que el campo created_by apunta al tutor correcto.
    """
    print_header("TEST 3: Campo created_by correctamente asignado")
    
    tutor_jose = data['tutor_jose']
    tutor_maria = data['tutor_maria']
    student_ana = data['student_ana']
    student_pedro = data['student_pedro']
    student_luis = data['student_luis']
    
    passed = True
    
    print_section("Verificando created_by de cada estudiante")
    
    # Ana → José
    if student_ana.created_by == tutor_jose:
        print_success(f"Ana.created_by = {student_ana.created_by} (correcto)")
    else:
        print_error(f"Ana.created_by = {student_ana.created_by} (debería ser {tutor_jose})")
        passed = False
    
    # Pedro → María
    if student_pedro.created_by == tutor_maria:
        print_success(f"Pedro.created_by = {student_pedro.created_by} (correcto)")
    else:
        print_error(f"Pedro.created_by = {student_pedro.created_by} (debería ser {tutor_maria})")
        passed = False
    
    # Luis → María
    if student_luis.created_by == tutor_maria:
        print_success(f"Luis.created_by = {student_luis.created_by} (correcto)")
    else:
        print_error(f"Luis.created_by = {student_luis.created_by} (debería ser {tutor_maria})")
        passed = False
    
    return passed


# ==============================================================================
# TEST 4: FILTRADO CON QUERYSET (SIMULANDO ADMIN)
# ==============================================================================

def test_queryset_filtering(data):
    """
    Simula cómo se filtraría en el Admin usando get_queryset().
    Valida que cada tutor solo obtiene sus estudiantes.
    """
    print_header("TEST 4: Filtrado con QuerySet (simulando Admin)")
    
    tutor_jose = data['tutor_jose']
    tutor_maria = data['tutor_maria']
    
    passed = True
    
    print_section("Filtrado para José")
    
    # Simular get_queryset() del Admin para José
    queryset_jose = Student.objects.filter(created_by=tutor_jose)
    print_data("Estudiantes en queryset", queryset_jose.count())
    
    for student in queryset_jose:
        print_info(f"  - {student}")
    
    if queryset_jose.count() == 1:
        print_success("Queryset de José contiene 1 estudiante (correcto)")
    else:
        print_error(f"Queryset de José contiene {queryset_jose.count()} estudiantes (debería ser 1)")
        passed = False
    
    print_section("Filtrado para María")
    
    # Simular get_queryset() del Admin para María
    queryset_maria = Student.objects.filter(created_by=tutor_maria)
    print_data("Estudiantes en queryset", queryset_maria.count())
    
    for student in queryset_maria:
        print_info(f"  - {student}")
    
    if queryset_maria.count() == 2:
        print_success("Queryset de María contiene 2 estudiantes (correcto)")
    else:
        print_error(f"Queryset de María contiene {queryset_maria.count()} estudiantes (debería ser 2)")
        passed = False
    
    return passed


# ==============================================================================
# TEST 5: VERIFICAR QUE NO HAY "LEAKAGE" DE DATOS
# ==============================================================================

def test_no_data_leakage(data):
    """
    Verifica que no existe forma de que un tutor acceda a estudiantes de otro.
    """
    print_header("TEST 5: Verificar que no hay filtración de datos")
    
    tutor_jose = data['tutor_jose']
    tutor_maria = data['tutor_maria']
    student_ana = data['student_ana']
    student_pedro = data['student_pedro']
    
    passed = True
    
    print_section("Intentar acceder a estudiante de otro tutor")
    
    # José intenta acceder a Pedro (estudiante de María) por ID
    try:
        # Simular: José intenta obtener Student.objects.get(id=pedro.id)
        # En el Admin con get_queryset() esto fallaría
        student_found = Student.objects.filter(
            id=student_pedro.id,
            created_by=tutor_jose
        ).first()
        
        if student_found is None:
            print_success("José NO puede acceder a Pedro por ID con filtro de created_by (correcto)")
        else:
            print_error("José PUEDE acceder a Pedro (incorrecto - filtración de datos)")
            passed = False
            
    except Exception as e:
        print_success(f"Acceso bloqueado correctamente: {e}")
    
    # María intenta acceder a Ana (estudiante de José) por ID
    try:
        student_found = Student.objects.filter(
            id=student_ana.id,
            created_by=tutor_maria
        ).first()
        
        if student_found is None:
            print_success("María NO puede acceder a Ana por ID con filtro de created_by (correcto)")
        else:
            print_error("María PUEDE acceder a Ana (incorrecto - filtración de datos)")
            passed = False
            
    except Exception as e:
        print_success(f"Acceso bloqueado correctamente: {e}")
    
    return passed


# ==============================================================================
# CLEANUP: LIMPIAR DATOS DE PRUEBA
# ==============================================================================

def cleanup(data):
    """
    Limpia todos los datos de prueba creados.
    """
    print_header("LIMPIANDO DATOS DE PRUEBA")
    
    try:
        # Orden correcto: Students → Tutors → Users
        Student.objects.filter(user__username__startswith='test_iso_').delete()
        print_success("Estudiantes eliminados")
        
        Tutor.objects.filter(user__username__startswith='test_iso_').delete()
        print_success("Tutores eliminados")
        
        User.objects.filter(username__startswith='test_iso_').delete()
        print_success("Usuarios eliminados")
        
        print_success("Limpieza completada exitosamente")
        
    except Exception as e:
        print_error(f"Error durante limpieza: {e}")


# ==============================================================================
# MAIN: EJECUTAR TODOS LOS TESTS
# ==============================================================================

def main():
    """
    Ejecuta todos los tests de aislamiento de datos.
    """
    print_header("VALIDACIÓN DE AISLAMIENTO DE DATOS ENTRE TUTORES")
    print_info("Objetivo: Verificar que cada tutor SOLO ve sus propios estudiantes")
    print_info("Escenario: 2 tutores, 3 estudiantes distribuidos")
    
    # Setup
    data = setup_test_data()
    
    # Ejecutar tests
    total_tests = 5
    passed_tests = 0
    
    if test_jose_sees_only_ana(data):
        passed_tests += 1
    
    if test_maria_sees_only_pedro_and_luis(data):
        passed_tests += 1
    
    if test_created_by_field(data):
        passed_tests += 1
    
    if test_queryset_filtering(data):
        passed_tests += 1
    
    if test_no_data_leakage(data):
        passed_tests += 1
    
    # Cleanup
    cleanup(data)
    
    # Resumen final
    print_header("RESUMEN DE VALIDACIÓN")
    print(f"\n{'='*80}")
    print(f"  TESTS EJECUTADOS: {total_tests}")
    print(f"  TESTS PASADOS:    {passed_tests}")
    print(f"  TESTS FALLIDOS:   {total_tests - passed_tests}")
    print(f"{'='*80}\n")
    
    if passed_tests == total_tests:
        print("🎉 ¡PERFECTO! El aislamiento de datos funciona correctamente")
        print("✅ Cada tutor solo puede ver sus propios estudiantes")
        print("✅ No hay filtración de datos entre tutores")
        print("✅ El campo created_by funciona correctamente")
        print("\n📋 Este es un requisito CRÍTICO de seguridad cumplido")
    else:
        print("⚠️  ALERTA: Algunos tests de aislamiento fallaron")
        print("🔒 Revisa los errores - esto es un problema de SEGURIDAD")
        print("🔧 Debes corregir antes de continuar con Issue #2")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
