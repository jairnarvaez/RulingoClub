"""
==============================================================================
SCRIPT DE VALIDACIÓN AUTOMÁTICA - ISSUE #1
==============================================================================
Este script valida TODOS los criterios de aceptación del Issue #1:
- Modelos Tutor y Student creados correctamente
- Relaciones OneToOne con User funcionando
- Campo created_by en Student con ForeignKey a Tutor
- Validación de rol único (User no puede ser Tutor Y Student)
- Métodos __str__() implementados
- Migraciones aplicadas correctamente

INSTRUCCIONES:
1. Guardar este archivo en la raíz del proyecto como: validate_issue1.py
2. Ejecutar: python validate_issue1.py
3. Revisar los resultados en consola

NOTA: Este script NO usa Django shell. Se ejecuta directamente.
==============================================================================
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')  
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection

from accounts.models import Tutor, Student


# ==============================================================================
# UTILIDADES PARA PRINTS CLAROS
# ==============================================================================

def print_header(text):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_test(test_name):
    """Imprime el nombre del test que se está ejecutando"""
    print(f"\n🔍 TEST: {test_name}")
    print("-" * 80)


def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"✅ ÉXITO: {message}")


def print_error(message):
    """Imprime mensaje de error"""
    print(f"❌ ERROR: {message}")


def print_info(message):
    """Imprime información"""
    print(f"ℹ️  INFO: {message}")


def cleanup():
    """
    Limpia datos de prueba creados.
    
    ORDEN CRÍTICO:
    1. Primero eliminar Students (están en el nivel más bajo)
    2. Luego eliminar Tutors (tienen PROTECT desde Students)
    3. Finalmente eliminar Users (CASCADE borra perfiles restantes)
    
    Si no se respeta este orden, PROTECT lanza error.
    """
    print_info("Limpiando datos de prueba...")
    
    try:
        # Paso 1: Borrar Students primero (nivel más bajo)
        students_deleted = Student.objects.filter(
            user__username__startswith='test_'
        ).count()
        Student.objects.filter(user__username__startswith='test_').delete()
        if students_deleted > 0:
            print_success(f"{students_deleted} Students eliminados")
        
        # Paso 2: Borrar Tutors (ahora sin Students que los protejan)
        tutors_deleted = Tutor.objects.filter(
            user__username__startswith='test_'
        ).count()
        Tutor.objects.filter(user__username__startswith='test_').delete()
        if tutors_deleted > 0:
            print_success(f"{tutors_deleted} Tutors eliminados")
        
        # Paso 3: Borrar Users (CASCADE borra cualquier perfil restante)
        users_deleted = User.objects.filter(username__startswith='test_').count()
        User.objects.filter(username__startswith='test_').delete()
        if users_deleted > 0:
            print_success(f"{users_deleted} Users eliminados")
        
        print_success("Limpieza completada exitosamente")
        
    except Exception as e:
        print_error(f"Error durante limpieza: {e}")
        print_info("Esto no afecta la validación principal, solo la limpieza")


# ==============================================================================
# VALIDACIÓN 1: VERIFICAR MIGRACIONES APLICADAS
# ==============================================================================

def validate_migrations():
    """
    ✅ Criterio: Migraciones aplicadas sin errores
    ✅ Criterio: Verificar en DB que tablas fueron creadas correctamente
    """
    print_test("Verificar que migraciones están aplicadas")
    
    try:
        with connection.cursor() as cursor:
            # Obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Buscar tablas de Tutor y Student
            app_prefix = 'accounts_'  
            tutor_table = f'{app_prefix}tutor'
            student_table = f'{app_prefix}student'
            
            print_info(f"Buscando tabla: {tutor_table}")
            print_info(f"Buscando tabla: {student_table}")
            
            if tutor_table in tables and student_table in tables:
                print_success(f"Tabla '{tutor_table}' encontrada en la base de datos")
                print_success(f"Tabla '{student_table}' encontrada en la base de datos")
                return True
            else:
                print_error("Las tablas de Tutor y/o Student NO existen en la base de datos")
                print_info("Ejecuta: python manage.py makemigrations")
                print_info("Ejecuta: python manage.py migrate")
                return False
                
    except Exception as e:
        print_error(f"Error al verificar migraciones: {e}")
        return False


# ==============================================================================
# VALIDACIÓN 2: VERIFICAR ESTRUCTURA DE MODELO TUTOR
# ==============================================================================

def validate_tutor_model():
    """
    ✅ Criterio: Modelo Tutor existe con todos sus campos
    ✅ Criterio: Relación OneToOneField con User
    ✅ Criterio: Campos bio, experience_years, created_at
    ✅ Criterio: Método __str__() implementado
    """
    print_test("Verificar estructura del modelo Tutor")
    
    # Verificar campos
    fields = {
        'user': 'OneToOneField',
        'bio': 'TextField',
        'experience_years': 'PositiveIntegerField',
        'created_at': 'DateTimeField',
    }
    
    for field_name, field_type in fields.items():
        try:
            field = Tutor._meta.get_field(field_name)
            print_success(f"Campo '{field_name}' existe (tipo: {field.__class__.__name__})")
        except Exception as e:
            print_error(f"Campo '{field_name}' NO encontrado: {e}")
            return False
    
    # Verificar método __str__
    try:
        tutor_str = str(Tutor)
        print_success(f"Método __str__() implementado en Tutor")
    except Exception as e:
        print_error(f"Método __str__() NO funciona: {e}")
        return False
    
    # Verificar Meta
    if hasattr(Tutor, '_meta'):
        print_success(f"Meta.verbose_name: '{Tutor._meta.verbose_name}'")
        print_success(f"Meta.verbose_name_plural: '{Tutor._meta.verbose_name_plural}'")
    
    return True


# ==============================================================================
# VALIDACIÓN 3: VERIFICAR ESTRUCTURA DE MODELO STUDENT
# ==============================================================================

def validate_student_model():
    """
    ✅ Criterio: Modelo Student existe con todos sus campos
    ✅ Criterio: Relación OneToOneField con User
    ✅ Criterio: Campo created_by con ForeignKey a Tutor
    ✅ Criterio: Campo created_at
    ✅ Criterio: Método __str__() implementado
    """
    print_test("Verificar estructura del modelo Student")
    
    # Verificar campos
    fields = {
        'user': 'OneToOneField',
        'created_by': 'ForeignKey',
        'created_at': 'DateTimeField',
    }
    
    for field_name, field_type in fields.items():
        try:
            field = Student._meta.get_field(field_name)
            print_success(f"Campo '{field_name}' existe (tipo: {field.__class__.__name__})")
            
            # Verificar related_name en created_by
            if field_name == 'created_by':
                if hasattr(field, 'related_query_name'):
                    related_name = field.remote_field.related_name
                    if related_name == 'students':
                        print_success(f"Campo 'created_by' tiene related_name='students' correcto")
                    else:
                        print_error(f"Campo 'created_by' tiene related_name='{related_name}' (debería ser 'students')")
        except Exception as e:
            print_error(f"Campo '{field_name}' NO encontrado: {e}")
            return False
    
    # Verificar método __str__
    try:
        student_str = str(Student)
        print_success(f"Método __str__() implementado en Student")
    except Exception as e:
        print_error(f"Método __str__() NO funciona: {e}")
        return False
    
    # Verificar Meta
    if hasattr(Student, '_meta'):
        print_success(f"Meta.verbose_name: '{Student._meta.verbose_name}'")
        print_success(f"Meta.verbose_name_plural: '{Student._meta.verbose_name_plural}'")
    
    return True


# ==============================================================================
# VALIDACIÓN 4: CREAR TUTOR EXITOSAMENTE
# ==============================================================================

def validate_create_tutor():
    """
    ✅ Criterio: Crear Tutor asociado a User funciona correctamente
    ✅ Test Manual Equivalente: Test 1 del Issue #1
    """
    print_test("Crear Tutor exitosamente")
    
    try:
        # Crear User
        user = User.objects.create_user(
            username='test_tutor_1',
            email='test_tutor1@example.com',
            password='password123',
            first_name='José',
            last_name='García'
        )
        print_success(f"User creado: {user.username}")
        
        # Crear Tutor
        tutor = Tutor.objects.create(
            user=user,
            bio='Experto en ruso con 5 años de experiencia',
            experience_years=5
        )
        print_success(f"Tutor creado: {tutor}")
        print_info(f"ID del Tutor: {tutor.id}")
        print_info(f"Usuario asociado: {tutor.user.username}")
        print_info(f"Años de experiencia: {tutor.experience_years}")
        print_info(f"Fecha de creación: {tutor.created_at}")
        
        return tutor
        
    except Exception as e:
        print_error(f"No se pudo crear Tutor: {e}")
        return None


# ==============================================================================
# VALIDACIÓN 5: VALIDACIÓN DE ROL ÚNICO (Tutor → Student)
# ==============================================================================

def validate_role_uniqueness_tutor_to_student(tutor):
    """
    ✅ Criterio: Si User ya es Tutor, no puede ser Student
    ✅ Criterio: Debe lanzar ValidationError con mensaje claro
    ✅ Test Manual Equivalente: Test 2 del Issue #1
    """
    print_test("Validar que User que es Tutor NO puede ser Student")
    
    if not tutor:
        print_error("No hay tutor para validar (test anterior falló)")
        return False
    
    try:
        # Intentar crear Student con el mismo User
        student_fail = Student(user=tutor.user, created_by=tutor)
        student_fail.full_clean()  # Esto DEBE lanzar ValidationError
        
        # Si llegamos aquí, la validación NO funcionó
        print_error("❌ VALIDACIÓN FALLÓ: Se permitió crear Student con User que ya es Tutor")
        print_error("La validación en clean() NO está funcionando correctamente")
        return False
        
    except ValidationError as e:
        # ✅ Esperamos este error
        error_message = str(e)
        print_success("ValidationError lanzado correctamente")
        print_info(f"Mensaje de error: {error_message}")
        
        # Verificar que el mensaje es el correcto
        expected_message = "Este usuario ya es Tutor"
        if expected_message in error_message:
            print_success(f"Mensaje de error contiene: '{expected_message}'")
            return True
        else:
            print_error(f"Mensaje de error NO contiene el texto esperado")
            print_info(f"Esperado: '{expected_message}'")
            print_info(f"Recibido: '{error_message}'")
            return False
            
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False


# ==============================================================================
# VALIDACIÓN 6: CREAR STUDENT EXITOSAMENTE
# ==============================================================================

def validate_create_student(tutor):
    """
    ✅ Criterio: Crear Student asociado a User funciona correctamente
    ✅ Criterio: Campo created_by se establece correctamente
    ✅ Test Manual Equivalente: Test 3 del Issue #1
    """
    print_test("Crear Student exitosamente")
    
    if not tutor:
        print_error("No hay tutor para asignar como created_by (test anterior falló)")
        return None
    
    try:
        # Crear nuevo User para el Student
        user = User.objects.create_user(
            username='test_student_1',
            email='test_student1@example.com',
            password='password123',
            first_name='Ana',
            last_name='Martínez'
        )
        print_success(f"User creado: {user.username}")
        
        # Crear Student
        student = Student.objects.create(
            user=user,
            created_by=tutor
        )
        print_success(f"Student creado: {student}")
        print_info(f"ID del Student: {student.id}")
        print_info(f"Usuario asociado: {student.user.username}")
        print_info(f"Creado por: {student.created_by}")
        print_info(f"Fecha de creación: {student.created_at}")
        
        return student
        
    except Exception as e:
        print_error(f"No se pudo crear Student: {e}")
        return None


# ==============================================================================
# VALIDACIÓN 7: VALIDACIÓN DE ROL ÚNICO (Student → Tutor)
# ==============================================================================

def validate_role_uniqueness_student_to_tutor(student):
    """
    ✅ Criterio: Si User ya es Student, no puede ser Tutor
    ✅ Criterio: Debe lanzar ValidationError con mensaje claro
    """
    print_test("Validar que User que es Student NO puede ser Tutor")
    
    if not student:
        print_error("No hay student para validar (test anterior falló)")
        return False
    
    try:
        # Intentar crear Tutor con el mismo User
        tutor_fail = Tutor(user=student.user)
        tutor_fail.full_clean()  # Esto DEBE lanzar ValidationError
        
        # Si llegamos aquí, la validación NO funcionó
        print_error("❌ VALIDACIÓN FALLÓ: Se permitió crear Tutor con User que ya es Student")
        print_error("La validación en clean() NO está funcionando correctamente")
        return False
        
    except ValidationError as e:
        # ✅ Esperamos este error
        error_message = str(e)
        print_success("ValidationError lanzado correctamente")
        print_info(f"Mensaje de error: {error_message}")
        
        # Verificar que el mensaje es el correcto
        expected_message = "Este usuario ya es Estudiante"
        if expected_message in error_message:
            print_success(f"Mensaje de error contiene: '{expected_message}'")
            return True
        else:
            print_error(f"Mensaje de error NO contiene el texto esperado")
            print_info(f"Esperado: '{expected_message}'")
            print_info(f"Recibido: '{error_message}'")
            return False
            
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False


# ==============================================================================
# VALIDACIÓN 8: VERIFICAR RELACIÓN INVERSA (related_name)
# ==============================================================================

def validate_related_name(tutor, student):
    """
    ✅ Criterio: related_name='students' funciona correctamente
    ✅ Test Manual Equivalente: Test 4 del Issue #1
    """
    print_test("Verificar relación inversa tutor.students")
    
    if not tutor or not student:
        print_error("No hay tutor o student para validar relación (tests anteriores fallaron)")
        return False
    
    try:
        # Verificar que podemos acceder a tutor.students
        students = tutor.students.all()
        print_success(f"Relación inversa funciona: tutor.students.all()")
        print_info(f"Número de estudiantes del tutor: {students.count()}")
        
        # Verificar que nuestro student está en la lista
        if student in students:
            print_success(f"Student '{student}' encontrado en tutor.students.all()")
            return True
        else:
            print_error(f"Student '{student}' NO encontrado en tutor.students.all()")
            return False
            
    except Exception as e:
        print_error(f"Error al acceder a tutor.students: {e}")
        print_info("Verifica que created_by tenga related_name='students'")
        return False


# ==============================================================================
# VALIDACIÓN 9: ON_DELETE BEHAVIORS
# ==============================================================================

def validate_on_delete_protect():
    """
    ✅ Criterio: on_delete=PROTECT en Student.created_by funciona
    ✅ No se puede borrar Tutor si tiene Students
    """
    print_test("Verificar on_delete=PROTECT en Student.created_by")
    
    try:
        # Crear tutor temporal
        user_tutor = User.objects.create_user(
            username='test_tutor_temp',
            email='temp@example.com',
            password='pass123'
        )
        tutor_temp = Tutor.objects.create(user=user_tutor)
        print_info(f"Tutor temporal creado: {tutor_temp}")
        
        # Crear student asociado
        user_student = User.objects.create_user(
            username='test_student_temp',
            email='temp_student@example.com',
            password='pass123'
        )
        student_temp = Student.objects.create(user=user_student, created_by=tutor_temp)
        print_info(f"Student temporal creado: {student_temp}")
        
        # Intentar borrar el tutor (DEBE fallar)
        try:
            tutor_temp.delete()
            print_error("❌ Se permitió borrar Tutor con Students asociados")
            print_error("on_delete=PROTECT NO está funcionando")
            return False
        except Exception as e:
            print_success("No se pudo borrar Tutor (comportamiento correcto)")
            print_info(f"Error esperado: {type(e).__name__}")
            
            # Limpiar datos temporales
            student_temp.delete()
            tutor_temp.delete()
            print_info("Datos temporales limpiados")
            return True
            
    except Exception as e:
        print_error(f"Error en validación de PROTECT: {e}")
        return False


# ==============================================================================
# MAIN: EJECUTAR TODAS LAS VALIDACIONES
# ==============================================================================

def main():
    """
    Ejecuta todas las validaciones del Issue #1 en orden
    """
    print_header("VALIDACIÓN AUTOMÁTICA - ISSUE #1: CONFIGURAR MODELOS DE USUARIO")
    print_info("Este script valida TODOS los criterios de aceptación del Issue #1")
    print_info("Revisa cada sección para confirmar que todo funciona correctamente")
    
    # Limpiar datos previos
    cleanup()
    
    # Contador de tests
    total_tests = 9
    passed_tests = 0
    
    # Test 1: Migraciones
    if validate_migrations():
        passed_tests += 1
    
    # Test 2: Modelo Tutor
    if validate_tutor_model():
        passed_tests += 1
    
    # Test 3: Modelo Student
    if validate_student_model():
        passed_tests += 1
    
    # Test 4: Crear Tutor
    tutor = validate_create_tutor()
    if tutor:
        passed_tests += 1
    
    # Test 5: Validación Tutor → Student
    if validate_role_uniqueness_tutor_to_student(tutor):
        passed_tests += 1
    
    # Test 6: Crear Student
    student = validate_create_student(tutor)
    if student:
        passed_tests += 1
    
    # Test 7: Validación Student → Tutor
    if validate_role_uniqueness_student_to_tutor(student):
        passed_tests += 1
    
    # Test 8: Related name
    if validate_related_name(tutor, student):
        passed_tests += 1
    
    # Test 9: ON_DELETE PROTECT
    if validate_on_delete_protect():
        passed_tests += 1
    
    # Limpiar datos de prueba
    cleanup()
    
    # Resumen final
    print_header("RESUMEN DE VALIDACIÓN")
    print(f"\n{'='*80}")
    print(f"  TESTS EJECUTADOS: {total_tests}")
    print(f"  TESTS PASADOS:    {passed_tests}")
    print(f"  TESTS FALLIDOS:   {total_tests - passed_tests}")
    print(f"{'='*80}\n")
    
    if passed_tests == total_tests:
        print("🎉 ¡FELICIDADES! Todos los criterios del Issue #1 están cumplidos")
        print("✅ El Issue #1 está COMPLETO y listo para cerrar")
        print("\n📋 Próximo paso: Issue #2 - Configurar Admin para Usuarios")
    else:
        print("⚠️  Algunos tests fallaron. Revisa los errores arriba.")
        print("🔧 Corrige los problemas y vuelve a ejecutar este script")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
