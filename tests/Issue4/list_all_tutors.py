"""
==============================================================================
SCRIPT DE INSPECCIÓN RÁPIDA: VER TODOS LOS TUTORES
==============================================================================
Muestra el ID, Nombre, Email, Años de Experiencia y Fechas de Creación 
de todos los tutores en la DB.

INSTRUCCIONES:
1. Asegúrate de tener datos de tutores (ejecuta 'create_test_data.py').
2. Ajusta la importación a la ruta de tu app si es necesario.
3. Ejecutar: python list_all_tutors.py
==============================================================================
"""

import os
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar el modelo Tutor
from accounts.models import Tutor 

def print_header(text):
    """Imprime un header visual."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def list_all_tutors():
    """Recupera y muestra la información de todos los tutores."""
    
    print_header("REPORTE DE TODOS LOS TUTORES")
    
    # Usamos select_related('user') para obtener los datos del User en una sola consulta
    tutores = Tutor.objects.all().select_related('user').order_by('id')
    
    if not tutores:
        print("🛑 No se encontraron tutores en la base de datos.")
        return

    for tutor in tutores:
        # Información del Tutor (desde el modelo User)
        tutor_username = tutor.user.username
        tutor_full_name = tutor.user.get_full_name()
        tutor_email = tutor.user.email
        
        # Se imprime la información completa
        print(f"ID Tutor: {tutor.id}")
        print(f"  Usuario: {tutor_username}")
        print(f"  Nombre Completo: {tutor_full_name}")
        print(f"  Email: {tutor_email}")
        print(f"  Años Experiencia: {tutor.experience_years}")
        print(f"  Fecha Creación: {tutor.created_at}")
        
        # Se muestra la biografía, truncada si es muy larga
        bio_snippet = tutor.bio[:70].strip()
        print(f"  Bio: {bio_snippet}...") 
        print("-" * 50)


if __name__ == '__main__':
    list_all_tutors()
