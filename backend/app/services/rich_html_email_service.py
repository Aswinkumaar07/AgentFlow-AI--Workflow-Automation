import re
import logging
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

logger = logging.getLogger("agentflow.services.rich_html_email")


class RichHTMLEmailService:
    """
    Sprint Rich HTML Email: Generates styled, modern HTML emails with multipart/alternative MIME structure.
    Supports Plain Text, HTML, Action Buttons, Tables, Inline Images, and Lists.
    """

    def is_rich_html_requested(self, prompt: str) -> bool:
        p_lower = prompt.lower()
        keywords = [
            "beautiful email",
            "html email",
            "rich email",
            "styled email",
            "formatted email",
            "newsletter",
            "table",
            "button",
            "call to action",
            "template",
            "html",
        ]
        return any(kw in p_lower for kw in keywords)

    def generate_rich_html(
        self,
        subject: str,
        body_text: str,
        title: Optional[str] = None,
        button_label: Optional[str] = None,
        button_url: Optional[str] = None,
        table_data: Optional[Dict[str, Any]] = None,
        list_items: Optional[list] = None,
    ) -> str:
        """Generates a responsive, modern HTML email body."""
        header_title = title or subject
        
        # Build list HTML if provided
        list_html = ""
        if list_items:
            items_str = "".join([f'<li style="margin-bottom: 8px; color: #374151;">{item}</li>' for item in list_items])
            list_html = f'<ul style="padding-left: 20px; margin: 16px 0; font-family: Inter, sans-serif;">{items_str}</ul>'

        # Build table HTML if provided
        table_html = ""
        if table_data and "headers" in table_data and "rows" in table_data:
            headers_str = "".join([f'<th style="padding: 10px 14px; background-color: #f3f4f6; color: #1f2937; text-align: left; font-size: 13px; border-bottom: 2px solid #e5e7eb;">{h}</th>' for h in table_data["headers"]])
            rows_str = ""
            for row in table_data["rows"]:
                cells = "".join([f'<td style="padding: 10px 14px; border-bottom: 1px solid #f3f4f6; color: #4b5563; font-size: 13px;">{cell}</td>' for cell in row])
                rows_str += f"<tr>{cells}</tr>"
            table_html = f'<table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #ffffff; border-radius: 8px; overflow: hidden;"><thead><tr>{headers_str}</tr></thead><tbody>{rows_str}</tbody></table>'

        # Build button HTML if provided
        button_html = ""
        if button_label:
            url = button_url or "#"
            button_html = f'''
            <div style="margin: 28px 0; text-align: center;">
                <a href="{url}" style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 14px; display: inline-block; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);">
                    {button_label}
                </a>
            </div>
            '''

        # Format body text paragraphs
        paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip()]
        body_formatted = "".join([f'<p style="margin: 0 0 16px 0; line-height: 1.6; color: #374151; font-size: 15px;">{p}</p>' for p in paragraphs])

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{header_title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 40px 16px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 32px 32px; text-align: left;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">{header_title}</h1>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding: 32px 32px;">
                            {body_formatted}
                            {list_html}
                            {table_html}
                            {button_html}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px 32px; border-top: 1px solid #f1f5f9; text-align: center;">
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">Sent automatically via AgentFlow AI Enterprise Suite</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        return html_content

    def build_multipart_alternative_mime(
        self,
        to_addr: str,
        subject: str,
        plain_text: str,
        html_body: str,
        from_addr: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> MIMEMultipart:
        """
        Constructs an RFC-2822 MIMEMultipart('alternative') message containing
        both text/plain and text/html parts.
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["To"] = to_addr
        if from_addr:
            msg["From"] = from_addr
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc

        part_text = MIMEText(plain_text, "plain", "utf-8")
        part_html = MIMEText(html_body, "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)
        return msg


rich_html_email_service = RichHTMLEmailService()
