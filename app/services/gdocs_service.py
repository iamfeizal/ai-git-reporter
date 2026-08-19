import os
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.state import ContentCluster, ReportState
from app.core.logger import logger

SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

class GDocsService:
    def __init__(self):
        try:
            self.creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            self.docs_service = build('docs', 'v1', credentials=self.creds)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
        except Exception as e:
            logger.warning(f"GDocsService initialization failed: {e}")
            self.docs_service = None
            self.drive_service = None

    def create_template_document(self, title: str = "AI Reporter Master Template") -> str:
        """
        Creates a new Google Doc formatted as a template with placeholders.
        Returns the Document ID.
        """
        if not self.docs_service:
            raise Exception("Google Docs API client not initialized. Check credentials.json.")

        # Create blank document
        doc = self.docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')

        # Build template content
        requests = [
            {"insertText": {"location": {"index": 1}, "text": "Laporan Aktivitas Pengembangan\n"}},
            {"updateParagraphStyle": {"range": {"startIndex": 1, "endIndex": 31}, "paragraphStyle": {"namedStyleType": "HEADING_1"}, "fields": "namedStyleType"}},
            
            {"insertText": {"location": {"index": 32}, "text": "Bulan: {{MONTH_YEAR}}\n\n"}},
            
            {"insertText": {"location": {"index": 55}, "text": "Executive Summary\n"}},
            {"updateParagraphStyle": {"range": {"startIndex": 55, "endIndex": 73}, "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}},
            
            {"insertText": {"location": {"index": 74}, "text": "{{EXEC_SUMMARY}}\n\n"}},
            
            {"insertText": {"location": {"index": 92}, "text": "Rincian Pengembangan\n"}},
            {"updateParagraphStyle": {"range": {"startIndex": 92, "endIndex": 113}, "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}},
            
            {"insertText": {"location": {"index": 114}, "text": "{{CONTENT_START}}\n"}},
        ]

        self.docs_service.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests}).execute()
        
        return doc_id

    def copy_template(self, template_id: str, new_title: str) -> str:
        """Copies an existing Google Doc and returns the new Document ID."""
        if not self.drive_service:
            raise Exception("Google Drive API client not initialized.")
        
        body = {'name': new_title}
        copied_file = self.drive_service.files().copy(fileId=template_id, body=body).execute()
        return copied_file.get('id')

    def generate_report_from_template(self, template_id: str, report_data: ReportState) -> str:
        """
        Main pipeline to generate a final report from a template.
        1. Copy template
        2. Replace static placeholders (MONTH_YEAR, EXEC_SUMMARY)
        3. Insert clusters at {{CONTENT_START}} using index-tracked insertion
        4. Highlight visual placeholders
        Returns the Document URL.
        """
        month_year = report_data.get("month_year", "Unknown Month")
        doc_title = f"Laporan Bulanan IT - {month_year}"
        
        # 1. Copy Template
        new_doc_id = self.copy_template(template_id, doc_title)
        
        # 2. Prepare Requests for Placeholder Replacement
        requests = []
        
        requests.append({
            "replaceAllText": {
                "containsText": {"text": "{{MONTH_YEAR}}", "matchCase": True},
                "replaceText": month_year
            }
        })
        
        exec_summary = report_data.get("executive_summary", "")
        requests.append({
            "replaceAllText": {
                "containsText": {"text": "{{EXEC_SUMMARY}}", "matchCase": True},
                "replaceText": exec_summary
            }
        })

        # Send replacements first to stabilize indices
        self.docs_service.documents().batchUpdate(
            documentId=new_doc_id, body={'requests': requests}).execute()

        # 3. Insert Clusters
        doc = self.docs_service.documents().get(documentId=new_doc_id).execute()
        
        # Find {{CONTENT_START}}
        content_start_index = -1
        for element in doc.get('body').get('content'):
            if 'paragraph' in element:
                for pe in element.get('paragraph').get('elements'):
                    if 'textRun' in pe:
                        content = pe.get('textRun').get('content')
                        if '{{CONTENT_START}}' in content:
                            content_start_index = pe.get('startIndex')
                            break
                if content_start_index != -1:
                    break
        
        if content_start_index == -1:
            # Fallback to appending at the end if placeholder is missing
            content_start_index = doc.get('body').get('content')[-1].get('endIndex') - 1
            
        requests = []
        current_index = content_start_index
        
        # Remove the placeholder text
        if content_start_index != -1:
            requests.append({
                "deleteContentRange": {
                    "range": {
                        "startIndex": current_index,
                        "endIndex": current_index + len("{{CONTENT_START}}\n")
                    }
                }
            })

        final_clusters = report_data.get("final_clusters", [])
        system_clusters = [c for c in final_clusters if c.category_level_1 == "SYSTEM_APP"]
        service_clusters = [c for c in final_clusters if c.category_level_1 == "SERVICE_APP"]
        
        def insert_text(text: str, style: str = "NORMAL_TEXT", highlight: bool = False):
            nonlocal current_index
            text = text + "\n"
            length = len(text)
            
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text
                }
            })
            
            if style != "NORMAL_TEXT":
                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": current_index, "endIndex": current_index + length},
                        "paragraphStyle": {"namedStyleType": style},
                        "fields": "namedStyleType"
                    }
                })
                
            if highlight:
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": current_index, "endIndex": current_index + length - 1},
                        "textStyle": {
                            "backgroundColor": {
                                "color": {"rgbColor": {"red": 1.0, "green": 0.9, "blue": 0.6}} # Light yellow
                            }
                        },
                        "fields": "backgroundColor"
                    }
                })
                
            current_index += length
            
        def insert_bullets(items: List[str]):
            nonlocal current_index
            if not items: return
            
            start_bullet_index = current_index
            for item in items:
                text = f"{item}\n"
                length = len(text)
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": text
                    }
                })
                current_index += length
                
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": start_bullet_index, "endIndex": current_index},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })

        if system_clusters:
            insert_text("1. Perbaikan & Pengembangan Sistem Aplikasi", "HEADING_2")
            for c in system_clusters:
                insert_text(c.cluster_title, "HEADING_3")
                insert_text(c.business_narrative, "NORMAL_TEXT")
                
                if c.requires_visual and c.visual_placeholder_note:
                    ph_text = f"[GAMBAR/CODE: {c.visual_placeholder_note}]"
                    insert_text(ph_text, "NORMAL_TEXT", highlight=True)
                
                if c.commit_ids:
                    insert_bullets([f"Commit: {cid}" for cid in c.commit_ids])
                
                insert_text("", "NORMAL_TEXT") # Empty line
                
        if service_clusters:
            insert_text("2. Pemeliharaan Layanan & Infrastruktur Aplikasi", "HEADING_2")
            for c in service_clusters:
                insert_text(c.cluster_title, "HEADING_3")
                insert_text(c.business_narrative, "NORMAL_TEXT")
                
                if c.requires_visual and c.visual_placeholder_note:
                    ph_text = f"[GAMBAR/CODE: {c.visual_placeholder_note}]"
                    insert_text(ph_text, "NORMAL_TEXT", highlight=True)
                
                if c.commit_ids:
                    insert_bullets([f"Commit: {cid}" for cid in c.commit_ids])
                    
                insert_text("", "NORMAL_TEXT")

        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=new_doc_id, body={'requests': requests}).execute()
            
        # Give anyone with the link view access (optional, but good for returning the URL)
        try:
            self.drive_service.permissions().create(
                fileId=new_doc_id,
                body={'type': 'anyone', 'role': 'writer'},
                fields='id'
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to set document permissions: {e}")

        return f"https://docs.google.com/document/d/{new_doc_id}/edit"