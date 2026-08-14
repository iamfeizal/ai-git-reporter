from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

class GDocsService:
    def __init__(self):
        # Autentikasi menggunakan file credentials.json
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.docs_service = build('docs', 'v1', credentials=self.creds)

    def insert_text_and_style(self, text: str, style: str = "NORMAL_TEXT"):
        """Fungsi pembantu untuk menyisipkan teks di bagian paling atas dokumen (index 1)"""
        requests = []
        # 1. Sisipkan teks
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": text + "\n"
            }
        })
        # 2. Terapkan style (Heading 1, 2, 3, atau Normal)
        if style != "NORMAL_TEXT":
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": 1, "endIndex": len(text) + 1},
                    "paragraphStyle": {"namedStyleType": style},
                    "fields": "namedStyleType"
                }
            })
        return requests

    def write_report_to_docs(self, clusters: list, target_doc_id: str):
        """Menerjemahkan Pydantic final_clusters menjadi perintah Batch Update Google Docs"""
        all_requests = []
        
        # Pisahkan cluster berdasarkan kategori
        system_clusters = [c for c in clusters if c.category_level_1 == "SYSTEM_APP"]
        service_clusters = [c for c in clusters if c.category_level_1 == "SERVICE_APP"]

        # Karena kita menyisipkan di Index 1, kita harus membangun dokumen dari BAWAH ke ATAS (Reversed)
        
        # --- BAGIAN 2: SERVICE APP ---
        if service_clusters:
            for cluster in reversed(service_clusters):
                if cluster.requires_visual:
                    placeholder = f"[GAMBAR/CODE: {cluster.visual_placeholder_note}]"
                    all_requests.extend(self.insert_text_and_style(placeholder, "NORMAL_TEXT"))
                
                all_requests.extend(self.insert_text_and_style(cluster.business_narrative, "NORMAL_TEXT"))
                all_requests.extend(self.insert_text_and_style(cluster.cluster_title, "HEADING_3"))
            
            all_requests.extend(self.insert_text_and_style("2. Pemeliharaan Layanan & Infrastruktur", "HEADING_2"))

        # --- BAGIAN 1: SYSTEM APP ---
        if system_clusters:
            for cluster in reversed(system_clusters):
                if cluster.requires_visual:
                    placeholder = f"[GAMBAR/CODE: {cluster.visual_placeholder_note}]"
                    all_requests.extend(self.insert_text_and_style(placeholder, "NORMAL_TEXT"))
                
                all_requests.extend(self.insert_text_and_style(cluster.business_narrative, "NORMAL_TEXT"))
                all_requests.extend(self.insert_text_and_style(cluster.cluster_title, "HEADING_3"))
            
            all_requests.extend(self.insert_text_and_style("1. Perbaikan & Pengembangan Sistem", "HEADING_2"))

        # --- JUDUL UTAMA DOKUMEN ---
        all_requests.extend(self.insert_text_and_style("Laporan Aktivitas Pengembangan", "HEADING_1"))

        # Eksekusi semua perintah sekaligus ke Google Docs
        if all_requests:
            self.docs_service.documents().batchUpdate(
                documentId=target_doc_id, 
                body={'requests': all_requests}
            ).execute()