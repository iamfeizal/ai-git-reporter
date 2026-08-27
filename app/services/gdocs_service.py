import os
import re
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.state import SubClusterNarrationOutput, ContextCluster, ServiceSubDomain, ReportState
from app.core.logger import logger

SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")


class GDocsService:
    def __init__(self):
        try:
            self.creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            self.docs_service = build('docs', 'v1', credentials=self.creds)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
        except Exception as e:
            logger.warning(f"GDocsService initialization failed: {e}")
            self.docs_service = None
            self.drive_service = None

    def create_template_document(self, title: str = "AI Reporter Master Template (Super App)") -> str:
        """
        Creates a new Google Doc formatted as a template with standard styles and placeholders.
        Returns the Document ID.
        """
        if not self.docs_service:
            raise Exception("Google Docs API client not initialized. Check credentials.json.")

        doc = self.docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')

        requests = [
            {"insertText": {"location": {"index": 1}, "text": "Laporan Aktivitas Pengembangan Super App\n"}},
            {"updateParagraphStyle": {
                "range": {"startIndex": 1, "endIndex": 41},
                "paragraphStyle": {"namedStyleType": "HEADING_1"},
                "fields": "namedStyleType"
            }},
            {"insertText": {"location": {"index": 42}, "text": "Bulan: {{MONTH_YEAR}}\n\n"}},
            {"insertText": {"location": {"index": 65}, "text": "Ringkasan Eksekutif (Executive Summary)\n"}},
            {"updateParagraphStyle": {
                "range": {"startIndex": 65, "endIndex": 105},
                "paragraphStyle": {"namedStyleType": "HEADING_2"},
                "fields": "namedStyleType"
            }},
            {"insertText": {"location": {"index": 106}, "text": "{{EXEC_SUMMARY}}\n\n"}},
            {"insertText": {"location": {"index": 124}, "text": "{{CONTENT_START}}\n"}},
        ]

        self.docs_service.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests}
        ).execute()

        return doc_id

    def copy_template(self, template_id: str, new_title: str) -> str:
        """Copies an existing Google Doc and returns the new Document ID."""
        if not self.drive_service:
            raise Exception("Google Drive API client not initialized.")

        body = {'name': new_title}
        copied_file = self.drive_service.files().copy(fileId=template_id, body=body).execute()
        new_doc_id = copied_file.get('id')

        # Make document viewable/editable by anyone with the link
        try:
            self.drive_service.permissions().create(
                fileId=new_doc_id,
                body={'type': 'anyone', 'role': 'writer'},
                fields='id'
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to set document permissions: {e}")

        return new_doc_id

    def init_report_document(
        self,
        template_id: Optional[str],
        month_year: str,
        exec_summary: str,
        mode: str = "direct"
    ) -> tuple[str, str]:
        """
        Initializes the document: copies or creates template, replaces {{MONTH_YEAR}} and {{EXEC_SUMMARY}}.
        Returns (doc_id, doc_url).
        """
        if not self.docs_service:
            raise Exception("Google Docs API client not initialized.")

        if not template_id:
            template_id = self.create_template_document()

        doc_title = f"Laporan Bulanan IT Super App - {month_year or 'Bulan Berjalan'}"
        if mode == "copy":
            doc_id = self.copy_template(template_id, doc_title)
        else:
            doc_id = template_id

        # Replace placeholders
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": "{{MONTH_YEAR}}", "matchCase": True},
                    "replaceText": month_year or ""
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{EXEC_SUMMARY}}", "matchCase": True},
                    "replaceText": exec_summary or ""
                }
            }
        ]

        self.docs_service.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests}
        ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return doc_id, doc_url

    def append_subcluster_section(
        self,
        doc_id: str,
        h2_title: Optional[str],
        h3_title: Optional[str],
        h4_title: Optional[str],
        narration_output: SubClusterNarrationOutput,
    ) -> None:
        """
        Appends a sub-cluster's headings, balanced narration (with monospace formatting for code/functions),
        visual placeholder, and commit bullet points to the end of the Google Doc.
        """
        if not self.docs_service:
            logger.warning("Docs service not ready, skipping append.")
            return

        doc = self.docs_service.documents().get(documentId=doc_id).execute()
        body_content = doc.get('body', {}).get('content', [])
        if not body_content:
            return

        # Find insert location (just before the trailing newline)
        current_index = body_content[-1].get('endIndex', 1) - 1
        if current_index < 1:
            current_index = 1

        requests = []

        def add_styled_text(text: str, style: str = "NORMAL_TEXT", bold: bool = False, italic: bool = False):
            nonlocal current_index
            text_with_nl = text + "\n"
            length = len(text_with_nl)
            
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text_with_nl
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

            if bold or italic:
                text_style = {}
                fields = []
                if bold:
                    text_style["bold"] = True
                    fields.append("bold")
                if italic:
                    text_style["italic"] = True
                    fields.append("italic")
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": current_index, "endIndex": current_index + length - 1},
                        "textStyle": text_style,
                        "fields": ",".join(fields)
                    }
                })

            current_index += length

        def add_narration_with_formatting(narrative: str):
            """
            Parses inline code (`func()`) and bold (**term**) in narrative text
            and applies monospace font and bold weights in Google Docs.
            """
            nonlocal current_index
            paragraphs = narrative.split("\n\n")
            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue

                # Strip markers for raw text insertion, but track spans for formatting
                # We will process tokens: `code` and **bold**
                # Pattern to split by `...` or **...**
                token_pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*)")
                parts = token_pattern.split(p_clean)

                p_start_index = current_index
                full_inserted_text = ""

                formatting_ranges = [] # list of (start_offset, end_offset, style_type)

                for part in parts:
                    if part.startswith("`") and part.endswith("`") and len(part) > 1:
                        plain_part = part[1:-1]
                        start_offset = len(full_inserted_text)
                        full_inserted_text += plain_part
                        end_offset = len(full_inserted_text)
                        formatting_ranges.append((start_offset, end_offset, "CODE"))
                    elif part.startswith("**") and part.endswith("**") and len(part) > 3:
                        plain_part = part[2:-2]
                        start_offset = len(full_inserted_text)
                        full_inserted_text += plain_part
                        end_offset = len(full_inserted_text)
                        formatting_ranges.append((start_offset, end_offset, "BOLD"))
                    else:
                        full_inserted_text += part

                full_inserted_text += "\n\n"
                length = len(full_inserted_text)

                requests.append({
                    "insertText": {
                        "location": {"index": p_start_index},
                        "text": full_inserted_text
                    }
                })
                requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": p_start_index, "endIndex": p_start_index + length},
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        "fields": "namedStyleType"
                    }
                })

                # Apply inline styling for code and bold
                for start_off, end_off, style_type in formatting_ranges:
                    if start_off >= end_off:
                        continue
                    abs_start = p_start_index + start_off
                    abs_end = p_start_index + end_off
                    if style_type == "CODE":
                        requests.append({
                            "updateTextStyle": {
                                "range": {"startIndex": abs_start, "endIndex": abs_end},
                                "textStyle": {
                                    "weightedFontFamily": {"fontFamily": "Consolas"},
                                    "backgroundColor": {"color": {"rgbColor": {"red": 0.94, "green": 0.94, "blue": 0.96}}}
                                },
                                "fields": "weightedFontFamily,backgroundColor"
                            }
                        })
                    elif style_type == "BOLD":
                        requests.append({
                            "updateTextStyle": {
                                "range": {"startIndex": abs_start, "endIndex": abs_end},
                                "textStyle": {"bold": True},
                                "fields": "bold"
                            }
                        })

                current_index += length

        def add_highlight_box(note: str):
            nonlocal current_index
            box_text = f"[TAMBAHKAN GAMBAR/DOKUMENTASI - Keterangan: {note}]\n\n"
            length = len(box_text)

            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": box_text
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": current_index, "endIndex": current_index + length - 2},
                    "textStyle": {
                        "backgroundColor": {"color": {"rgbColor": {"red": 1.0, "green": 0.92, "blue": 0.65}}},
                        "italic": True,
                        "bold": True,
                    },
                    "fields": "backgroundColor,italic,bold"
                }
            })
            current_index += length

        def add_bullet_commits(commit_ids: List[str]):
            nonlocal current_index
            if not commit_ids:
                return
            start_bullet_index = current_index
            for cid in commit_ids:
                c_text = f"Git Commit: {cid}\n"
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": c_text
                    }
                })
                current_index += len(c_text)

            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": start_bullet_index, "endIndex": current_index},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })
            # Trailing blank line
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": "\n"
                }
            })
            current_index += 1

        # Build content requests
        if h2_title:
            add_styled_text(h2_title, "HEADING_2")
        if h3_title:
            add_styled_text(h3_title, "HEADING_3")
        if h4_title:
            add_styled_text(h4_title, "HEADING_4")

        # Sub-cluster title as bold intro
        add_styled_text(narration_output.sub_cluster_title, "NORMAL_TEXT", bold=True)

        # Main balanced narration
        add_narration_with_formatting(narration_output.business_narrative)

        # Visual placeholder if required
        if narration_output.requires_visual and narration_output.visual_placeholder_note:
            add_highlight_box(narration_output.visual_placeholder_note)

        # Commit IDs
        if narration_output.commit_ids:
            add_bullet_commits(narration_output.commit_ids)

        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=doc_id, body={'requests': requests}
            ).execute()

    def generate_report_from_template(self, template_id: str, report_data: ReportState, mode: str = "direct") -> str:
        """
        Legacy fallback / bulk generator.
        """
        month_year = report_data.get("month_year", "Unknown Month")
        exec_summary = report_data.get("executive_summary", "")

        doc_id, doc_url = self.init_report_document(template_id, month_year, exec_summary, mode=mode)

        final_narratives = report_data.get("final_narratives", [])
        for item in final_narratives:
            self.append_subcluster_section(
                doc_id=doc_id,
                h2_title=None,
                h3_title=None,
                h4_title=f"{item.cluster_title or 'Cluster'} - {item.sub_cluster_title}",
                narration_output=item
            )

        return doc_url