from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core.paginator import Paginator
from .db_routers import Users, get_discord_server_stats, Resources, History, get_discord_connection
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from django.utils.timezone import now
import os
from django.conf import settings
from datetime import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


def get_user_context(request):
    """
    Fonction utilitaire pour récupérer le contexte utilisateur commun à toutes les vues
    """
    user_info = request.session.get('user_info', None)
    user_id = user_info.get('id') if user_info else None
    
    is_premium = Users.is_premium(user_id) if user_id else False
    
    return {
        'user_info': user_info,
        'user_is_premium': is_premium 
    }

def board_view(request):
    context = get_user_context(request)
    user_info = context['user_info']
  
    if user_info:
        niveau_utilisateur = Users.get_user_niveau(user_info['id'])
        vies_utilisateur = Users.get_user_vies(user_info['id'])
        dernier_reset = Users.get_dernier_reset(user_info['id'])
        discord_stats = get_discord_server_stats()

        context.update({
            'niveau_utilisateur': niveau_utilisateur,
            'vies_utilisateur': vies_utilisateur,
            'dernier_reset': dernier_reset,
            'discord_stats': discord_stats,
        })
    
    return render(request, 'board.html', context)

def learn_view(request):
    context = get_user_context(request)
    user_info = context['user_info']
    
    selected_theme = request.GET.get('theme', 'all')
    selected_course = request.GET.get('course', 'all')
    page_number = request.GET.get('page', 1)

    themes = Resources.get_themes()
    courses = []
    if selected_theme and selected_theme != 'all':
        courses = Resources.get_courses_by_theme(selected_theme)

    media_list = Resources.get_media_by_filters(
        theme_id=selected_theme if selected_theme != 'all' else None,
        course_id=selected_course if selected_course != 'all' else None
    )

    paginator = Paginator(media_list, 10)
    page_obj = paginator.get_page(page_number)

    context.update({
        'themes': themes,
        'courses': courses,
        'resources': page_obj,
        'selected_theme': selected_theme,
        'selected_course': selected_course,
    })

    return render(request, 'learn.html', context)

def doc_view(request):
    context = get_user_context(request)
    return render(request, 'doc.html', context)

def history_view(request):
    context = get_user_context(request)
    user_info = context['user_info']
    user_id = user_info.get('id') if user_info else None

    activity_type = request.GET.get('activity_type', None)
    status = request.GET.get('status', None)
    days = int(request.GET.get('days', 30))

    history = History.get_activity_history(user_id, activity_type, status, days)
    stats = History.get_activity_stats(user_id, days)

    if stats['total'] > 0:
        stats['success_rate'] = (stats['reussi'] / stats['total']) * 100
        stats['failed_rate'] = 100 - stats['success_rate']
    else:
        stats['success_rate'] = 0
        stats['failed_rate'] = 0

    qcm_count = sum(1 for activity in history if activity.get('type_activite') == 'qcm')
    exercice_count = sum(1 for activity in history if activity.get('type_activite') == 'exercice')
    completed_courses = Users.get_completed_courses(user_id) if user_id else []

    context.update({
        'history': history,
        'stats': stats,
        'selected_activity_type': activity_type,
        'selected_status': status,
        'selected_days': days,
        'qcm_count': qcm_count,
        'exercice_count': exercice_count,
        'completed_courses': completed_courses,
    })

    return render(request, 'history.html', context)

def account_view(request):
    context = get_user_context(request)
    user_info = context['user_info']
    user_id = user_info.get('id') if user_info else None
    
    # Récupérer les informations détaillées de l'utilisateur depuis la base
    user_details = None
    if user_id:
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT Type_compte, premium_start_date, premium_end_date,
                       DATEDIFF(premium_end_date, CURDATE()) as jours_restants
                FROM users 
                WHERE discord_id = %s
            """, (user_id,))
            user_details = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Erreur récupération détails utilisateur: {e}")
    
    completed_courses = Users.get_completed_courses(user_id) if user_id else []
    
    context.update({
        'completed_courses': completed_courses,
        'user_details': user_details
    })
    
    return render(request, 'account.html', context)

def home_view(request):
    context = get_user_context(request)
    return render(request, 'home.html', context)

def generate_certificate(request, cours_id):
    context = get_user_context(request)
    user_info = context['user_info']
    user_id = user_info.get('id') if user_info else None
    
    if not user_id:
        return redirect('account')
    
    # Vérifier le type de compte
    if not context.get('user_is_premium'):
        return redirect('account')
    
    # Vérifier si le cours est complété
    if not Users.is_course_completed(user_id, cours_id):
        return redirect('account')
    
    # Récupérer les données du cours et de l'utilisateur
    conn = get_discord_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            u.discord_id, 
            u.pseudo as discord_username,
            c.cours_id, 
            c.titre as cours_titre,
            c.thematique_id,
            s.date_activite as date_validation,
            (SELECT COUNT(*) FROM chapitres WHERE cours_id = c.cours_id) as nombre_chapitres
        FROM users u
        JOIN suivi s ON u.discord_id = s.discord_id
        JOIN cours c ON s.cours_id = c.cours_id
        WHERE u.discord_id = %s AND c.cours_id = %s AND s.etat = 'terminé'
        ORDER BY s.date_activite DESC
        LIMIT 1
    """, (user_id, cours_id))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not data:
        return redirect('account')
    
     # Gestion robuste de thematique_id
    thematique_id = data.get('thematique_id', 0)  # Valeur par défaut si la clé n'existe pas
    
    # Option 2: Si vous avez une correspondance entre les IDs et les noms de thématiques
    # vous pouvez créer un mapping ici
    thematique_mapping = {
        1: "Navigation",
        2: "Météorologie",
        3: "Sécurité",
        # Ajoutez d'autres mappings selon vos besoins
    }
    thematique_nom = thematique_mapping.get(data['thematique_id'], f"Thématique {data['thematique_id']}")
    
    # Préparer le contexte pour le template
    context = {
        'discord_username': data['discord_username'],
        'cours_titre': data['cours_titre'],
        'thematique_nom': thematique_nom,
        'date_validation': data['date_validation'].strftime("%d/%m/%Y"),
        'delivree_le': now().strftime("%d/%m/%Y"),
        'nombre_chapitres': data['nombre_chapitres'],
        'certificat_id': f"CERT-{user_id}-{cours_id}-{datetime.now().strftime('%Y%m%d')}"
    }
    
    # Rendre le template HTML
    html_string = render_to_string('certificate.html', context)
    
    # Convertir HTML en PDF
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_file)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF')
    
    # Retourner le PDF en réponse
    pdf_file.seek(0)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificat_{data["cours_titre"].replace(" ", "_")}.pdf"'
    return response

def premium_view(request):
    """
    Vue pour afficher la page premium.
    """
    context = get_user_context(request)
    user_info = context['user_info']
    user_id = user_info.get('id') if user_info else None
    
    if user_id:
        # Récupérer les détails de l'abonnement
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT Type_compte, premium_start_date, premium_end_date,
                       DATEDIFF(premium_end_date, CURDATE()) as jours_restants
                FROM users 
                WHERE discord_id = %s
            """, (user_id,))
            subscription_details = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            subscription_details = None
            print(f"Erreur récupération détails abonnement: {e}")
        
        context.update({
            'subscription_details': subscription_details
        })
    
    return render(request, 'premium.html', context)



    
