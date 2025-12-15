# discord_db.py
import mysql.connector
import requests
import datetime
import os
from datetime import datetime, timedelta
from django.conf import settings

def get_discord_connection():
    return mysql.connector.connect(
        host="mysql-voiliersremi.alwaysdata.net",
        user="431257",
        password="F3nnf4qz97@12",
        database="voiliersremi_discords"
    )

class Users:
    @staticmethod
    def get_user_level(discord_id):
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT level FROM users WHERE discord_id = %s", (discord_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result['level'] if result else None
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    @staticmethod
    def get_user_vies(discord_id):
        """
        Récupère le nombre de vies (vagues_free) de l'utilisateur.
        """
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT `vagues_free` FROM users WHERE `discord_id` = %s", (discord_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result['vagues_free'] if result else None
        except Exception as e:
            print(f"Erreur get_user_vies: {e}")
            return None
    
    @staticmethod
    def get_dernier_reset(discord_id):
        """
        Récupère la date du reset
        """
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT `dernier_reset_free` FROM users WHERE `discord_id` = %s", (discord_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and 'dernier_reset_free' in result and result['dernier_reset_free']:
                return result['dernier_reset_free']
            else:
                print("Aucune date de reset trouvée")
                return None
        except Exception as e:
            print(f"Erreur get_dernier_reset: {e}")
            return None
    
    @staticmethod
    def get_user_niveau(discord_id):
        """
        Détermine le niveau de l'utilisateur en fonction du pourcentage d'activité
        Retourne un dictionnaire avec les informations formatées pour le template
        """
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Compter le nombre total de cours
            cursor.execute("SELECT COUNT(*) as total_cours FROM cours")
            total_cours = cursor.fetchone()['total_cours']
            
            # Compter le nombre de QCM validés par l'utilisateur
            cursor.execute("""
                SELECT COUNT(DISTINCT q.cours_id) as qcm_valides 
                FROM qcm q
                INNER JOIN utilisateur_qcm uq ON q.id = uq.qcm_id
                WHERE uq.discord_id = %s AND uq.est_valide = 1
            """, (discord_id,))
            qcm_valides = cursor.fetchone()['qcm_valides']
            
            cursor.close()
            conn.close()
            
            if total_cours > 0:
                pourcentage = (qcm_valides / total_cours) * 100
                
                if pourcentage < 25:
                    nom_niveau = "Débutant"
                    niveau_classe = "debutant"
                elif pourcentage < 50:
                    nom_niveau = "Intermédiaire"
                    niveau_classe = "intermediaire"
                elif pourcentage < 75:
                    nom_niveau = "Avancé"
                    niveau_classe = "avance"
                else:
                    nom_niveau = "Expert"
                    niveau_classe = "expert"
                    
                return {
                    'niveau_classe': niveau_classe,
                    'nom_niveau': nom_niveau,
                    'pourcentage': round(pourcentage, 2),
                    'cours_completes': qcm_valides,
                    'cours_total': total_cours
                }
            else:
                return {
                    'niveau_classe': "debutant",
                    'nom_niveau': "Débutant",
                    'pourcentage': 0.0,
                    'cours_completes': 0,
                    'cours_total': 0
                }
            
        except Exception as e:
            print(f"Erreur get_user_niveau: {e}")
            return {
                'niveau_classe': "debutant",
                'nom_niveau': "Débutant",
                'pourcentage': 0.0,
                'cours_completes': 0,
                'cours_total': 0
            }

    @staticmethod
    def is_premium(discord_id):
        """Vérifie si un utilisateur a un compte premium valide."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT `Type_compte`, `premium_start_date`, `premium_end_date`
                FROM users 
                WHERE discord_id = %s
            """, (discord_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and user['Type_compte'] in ['standard', 'premium'] and user['premium_end_date']:
                now = datetime.now()
                return user['premium_end_date'] >= now
            return False
        except Exception as e:
            print(f"Erreur is_premium: {e}")
            return False
        
    @staticmethod
    def get_completed_courses(discord_id):
        """Récupère les cours terminés par un utilisateur."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT c.cours_id, c.titre , MAX(s.date_activite) as date_validation
                FROM suivi s
                JOIN cours c ON s.cours_id = c.cours_id
                WHERE s.discord_id = %s AND s.etat = 'termine'
                GROUP BY c.cours_id,c.titre
            """, (discord_id,))
            courses = cursor.fetchall()
            cursor.close()
            conn.close()
            print(f"DEBUG - Completed courses for {discord_id}: {courses}") 
            return courses
        except Exception as e:
            print(f"Erreur get_completed_courses: {e}")
            return []
        
    @staticmethod
    def is_course_completed(discord_id, cours_id):
        """Vérifie si un cours spécifique est terminé."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*) as completed
                FROM suivi
                WHERE discord_id = %s AND cours_id = %s AND etat = 'terminé'
            """, (discord_id, cours_id))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result['completed'] > 0 if result else False
        except Exception as e:
            print(f"Erreur is_course_completed: {e}")
            return False

def get_discord_server_stats():
    """
    Récupère les statistiques du serveur Discord via l'API
    """
    # Remplacez par vos informations
    GUILD_ID = "1183066709343612979"  # ID de votre serveur Discord
    BOT_TOKEN = "MTI5ODM5NTIyOTA3MzcwNzA2OA.GMBLzd.HA-V4CImIf1f64g9YyDrE8P1PPDkHeZSFz6WLs" # Token de votre bot Discord
    
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}"
    }
    
    try:
        # Récupérer les informations du serveur
        response = requests.get(
            f"https://discord.com/api/v9/guilds/{GUILD_ID}?with_counts=true",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "online_count": data.get("approximate_presence_count", 0),
                "member_count": data.get("approximate_member_count", 0)
            }
        else:
            print(f"Erreur API Discord: {response.status_code}")
            return {"online_count": 0, "member_count": 0}
            
    except Exception as e:
        print(f"Erreur lors de la récupération des stats Discord: {e}")
        return {"online_count": 0, "member_count": 0}
    
   

class Resources:
    @staticmethod
    def get_themes():
        """Récupère tous les thèmes disponibles dans la table cours."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT DISTINCT thematique_id as id FROM cours ORDER BY thematique_id")
            themes = cursor.fetchall()
            cursor.close()
            conn.close()
            return themes
        except Exception as e:
            print(f"Erreur get_themes: {e}")
            return []

    @staticmethod
    def get_courses_by_theme(theme_id):
        """Récupère les cours d'un thème spécifique."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT cours_id as id, titre as nom
                FROM cours
                WHERE thematique_id = %s
                ORDER BY titre
            """, (theme_id,))
            courses = cursor.fetchall()
            cursor.close()
            conn.close()
            return courses
        except Exception as e:
            print(f"Erreur get_courses_by_theme: {e}")
            return []

    @staticmethod
    def get_media_by_filters(theme_id=None, course_id=None):
        """Récupère les médias en fonction des filtres thème et/ou cours."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT m.media_id as id, m.url, m.type,
                       c.titre as cours_nom, c.thematique_id as theme_nom
                FROM media m
                INNER JOIN chapitres ch ON m.media_id = ch.media_id
                INNER JOIN cours c ON ch.cours_id = c.cours_id
                WHERE 1=1
            """
            params = []

            if theme_id and theme_id != 'all':
                query += " AND c.thematique_id = %s"
                params.append(theme_id)

            if course_id and course_id != 'all':
                query += " AND c.cours_id = %s"
                params.append(course_id)

            query += " ORDER BY c.titre"

            cursor.execute(query, params)
            media = cursor.fetchall()
            cursor.close()
            conn.close()

            return media
        except Exception as e:
            print(f"Erreur get_media_by_filters: {e}")
            return []


class History:
    
    @staticmethod
    def get_activity_history(discord_id, activity_type=None, status=None, days=30):
        """
        Récupère et filtre l'historique des activités d'un utilisateur.
        """
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    s.suivi_id,
                    s.discord_id,
                    s.cours_id,
                    s.chapitre_id,
                    s.qcm_id,
                    s.exercice_id,
                    s.type_activite,
                    s.etat,
                    s.date_activite,
                    s.score,
                    CASE s.type_activite
                        WHEN 'cours' THEN ch.titre
                        WHEN 'qcm' THEN q.question
                        WHEN 'exercice' THEN e.instruction
                        ELSE NULL
                    END AS titre_activite
                FROM suivi s
                LEFT JOIN chapitres ch ON s.chapitre_id = ch.chapitres_id
                LEFT JOIN qcm q ON s.qcm_id = q.id
                LEFT JOIN exercices e ON s.exercice_id = e.ex_id
                WHERE s.discord_id = %s
            """
            params = [discord_id]

            if activity_type:
                query += " AND s.type_activite = %s"
                params.append(activity_type)

            if status:
                query += " AND s.etat = %s"
                params.append(status)

            if days:
                query += " AND s.date_activite >= DATE_SUB(CURDATE(), INTERVAL %s DAY)"
                params.append(days)

            query += " ORDER BY s.date_activite DESC"

            cursor.execute(query, params)
            history = cursor.fetchall()
            cursor.close()
            conn.close()

            return history

        except Exception as e:
            print(f"Erreur get_activity_history: {e}")
            return []
    
    @staticmethod
    def get_activity_stats(discord_id, days=30):
        """Récupère les statistiques d'activités pour un utilisateur."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN etat = 'terminé' THEN 1 ELSE 0 END) as reussi,
                    SUM(CASE WHEN etat = 'en cours' THEN 1 ELSE 0 END) as en_cours,
                    SUM(CASE WHEN etat = 'échoué' THEN 1 ELSE 0 END) as echoue
                FROM suivi
                WHERE discord_id = %s AND date_activite >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (discord_id, days))
            stats = cursor.fetchone()

            cursor.execute("""
                SELECT
                    MONTH(date_activite) as mois,
                    COUNT(*) as total,
                    SUM(CASE WHEN etat = 'terminé' THEN 1 ELSE 0 END) as reussi,
                    SUM(CASE WHEN etat = 'en cours' THEN 1 ELSE 0 END) as en_cours,
                    SUM(CASE WHEN etat = 'échoué' THEN 1 ELSE 0 END) as echoue
                FROM suivi
                WHERE discord_id = %s AND date_activite >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY MONTH(date_activite)
                ORDER BY MONTH(date_activite)
            """, (discord_id,))
            monthly_stats = cursor.fetchall()

            cursor.close()
            conn.close()

            return {
                'total': stats['total'] if stats else 0,
                'reussi': stats['reussi'] if stats else 0,
                'en_cours': stats['en_cours'] if stats else 0,
                'echoue': stats['echoue'] if stats else 0,
                'monthly_stats': monthly_stats if monthly_stats else []
            }
        except Exception as e:
            print(f"Erreur get_activity_stats: {e}")
            return {
                'total': 0,
                'reussi': 0,
                'en_cours': 0,
                'echoue': 0,
                'monthly_stats': []
            }
          
    
class Certificate:

    @staticmethod
    def generate_certificate(discord_id, cours_id):
        """Génère un certificat pour un cours réussi."""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.discord_id, u.username as discord_username,
                       c.cours_id, c.titre as cours_titre,
                       s.date_activite as date_validation
                FROM users u
                JOIN suivi s ON u.discord_id = s.discord_id
                JOIN cours c ON s.cours_id = c.cours_id
                WHERE u.discord_id = %s AND c.cours_id = %s AND s.etat = 'terminé'
                ORDER BY s.date_activite DESC
                LIMIT 1
            """, (discord_id, cours_id))
            data = cursor.fetchone()
            cursor.close()
            conn.close()

            if not data:
                print("DEBUG: Aucune donnée trouvée pour la génération du certificat")
                return None

            # Imports pour la génération du PDF
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

            # Créer un dossier pour les certificats s'il n'existe pas
            cert_dir = os.path.join(settings.BASE_DIR, 'certificats')
            if not os.path.exists(cert_dir):
                os.makedirs(cert_dir)

            # Créer le PDF
            filename = f"certificat_{discord_id}_{cours_id}.pdf"
            filepath = os.path.join(cert_dir, filename)

            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Ajouter le contenu du certificat
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1  # Centré
            )
            
            story.append(Paragraph("CERTIFICAT DE RÉUSSITE", title_style))
            story.append(Spacer(1, 20))
            
            content_style = ParagraphStyle(
                'CustomContent',
                parent=styles['BodyText'],
                fontSize=14,
                spaceAfter=12,
                alignment=1  # Centré
            )
            
            story.append(Paragraph(f"Ceci certifie que {data['discord_username']} a complété avec succès le cours:", content_style))
            story.append(Paragraph(f"« {data['cours_titre']} »", content_style))
            story.append(Spacer(1, 20))
            
            date_str = data['date_validation'].strftime("%d/%m/%Y")
            story.append(Paragraph(f"Date de validation: {date_str}", content_style))
            
            doc.build(story)
            print(f"DEBUG: PDF généré avec succès: {filepath}")
            return filepath

        except ImportError as e:
            print(f"DEBUG: Erreur d'importation - ReportLab non installé: {e}")
            return None
        except Exception as e:
            print(f"DEBUG: Erreur lors de la création du PDF: {e}")
            return None
 
    @staticmethod
    def debug_premium(discord_id):
        """Méthode de debug pour vérifier les données premium"""
        try:
            conn = get_discord_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT Type_compte, premium_start_date, premium_end_date,
                       CURDATE() as today,
                       DATEDIFF(premium_end_date, CURDATE()) as days_left
                FROM users 
                WHERE discord_id = %s
            """, (discord_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return user
        except Exception as e:
            return {'error': str(e)}