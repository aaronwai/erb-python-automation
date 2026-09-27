import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

class EmailAutomation:
    """電子郵件自動化類"""

    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_simple_email(self, to_email, subject, body):
        """發送純文本郵件"""
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        self._send(msg, to_email)

    def send_html_email(self, to_email, subject, html_content,
                        text_content=None):
        """發送 HTML 格式郵件"""
        msg = MIMEMultipart('alternative')
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject

        # 同時添加純文本版本（兼容性）
        if text_content is None:
            text_content = "請使用支持 HTML 的郵件客戶端查看此郵件。"

        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        self._send(msg, to_email)

    def send_email_with_attachment(self, to_email, subject, body,
                                   attachments):
        """
        發送帶附件的郵件

        Args:
            attachments: 文件路徑列表或 (文件名, 文件路徑) 元組列表
        """
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 添加附件
        for attachment in attachments:
            if isinstance(attachment, tuple):
                filename, file_path = attachment
            else:
                file_path = attachment
                filename = Path(file_path).name

            mime_attachment = self._create_attachment(file_path, filename)
            msg.attach(mime_attachment)

        self._send(msg, to_email)

    def _create_attachment(self, file_path, filename=None):
        """創建郵件附件"""
        path = Path(file_path)

        if filename is None:
            filename = path.name

        # 處理中文文件名
        from email.header import Header
        encoded_filename = Header(filename, 'utf-8').encode()

        # 根據文件類型選擇 MIME 類型
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(path))

        if mime_type:
            main_type, sub_type = mime_type.split('/')
        else:
            main_type, sub_type = 'application', 'octet-stream'

        with open(path, 'rb') as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())

        encoders.encode_base64(attachment)

        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{encoded_filename}"'
        )

        return attachment

    def _send(self, msg, to_email):
        """執行發送"""
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port,
                              context=context) as server:
            server.login(self.username, self.password)
            server.sendmail(self.username, to_email, msg.as_string())

        print(f"郵件已發送至: {to_email}")

    def send_batch_emails(self, recipients, template_func,
                          use_threading=False):
        """
        批量發送個性化郵件

        Args:
            recipients: 收件人列表，每個元素為字典
            template_func: 生成個性化內容的函數
            use_threading: 是否使用多執行緒加速
        """
        success_count = 0
        failed_recipients = []

        if use_threading:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for recipient in recipients:
                    future = executor.submit(
                        self._send_single_email,
                        recipient,
                        template_func
                    )
                    futures.append((recipient, future))

                for recipient, future in futures:
                    try:
                        if future.result():
                            success_count += 1
                        else:
                            failed_recipients.append(recipient)
                    except Exception as e:
                        print(f"發送失敗 ({recipient['email']}): {str(e)}")
                        failed_recipients.append(recipient)
        else:
            for recipient in recipients:
                try:
                    if self._send_single_email(recipient, template_func):
                        success_count += 1
                    else:
                        failed_recipients.append(recipient)
                except Exception as e:
                    print(f"發送失敗 ({recipient['email']}): {str(e)}")
                    failed_recipients.append(recipient)

        print(f"\n批量發送完成: {success_count}/{len(recipients)} 成功")
        if failed_recipients:
            print(f"失敗列表: {[r['email'] for r in failed_recipients]}")

        return success_count, failed_recipients

    def _send_single_email(self, recipient, template_func):
        """發送單封郵件"""
        try:
            subject, body = template_func(recipient)
            self.send_simple_email(recipient['email'], subject, body)
            return True
        except Exception as e:
            print(f"發送異常: {str(e)}")
            return False

# 使用示例
if __name__ == "__main__":
    email = EmailAutomation(
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        username="your_email@gmail.com",
        password="your_app_password"  # 需使用應用程式密碼
    )

    # 發送簡單郵件
    email.send_simple_email(
        to_email="recipient@example.com",
        subject="自動化測試郵件",
        body="這是由 Python 自動化腳本發送的郵件。"
    )

    # 發送 HTML 郵件
    html_content = """
    <html>
        <body>
            <h1 style="color: #333;">自動化報告</h1>
            <p>您好，</p>
            <p>這是<strong>自動生成</strong>的 HTML 郵件。</p>
            <table border="1" style="border-collapse: collapse;">
                <tr><th>項目</th><th>狀態</th></tr>
                <tr><td>數據抓取</td><td style="color: green;">成功</td></tr>
                <tr><td>報告生成</td><td style="color: green;">成功</td></tr>
            </table>
        </body>
    </html>
    """

    email.send_html_email(
        to_email="recipient@example.com",
        subject="HTML 測試郵件",
        html_content=html_content
    )

    # 發送帶附件的郵件
    email.send_email_with_attachment(
        to_email="recipient@example.com",
        subject="月度報告",
        body="請查閱附件中的月度報告。",
        attachments=[
            "reports/monthly_report.xlsx",
            ("備註.txt", "notes/important_notes.txt")
        ]
    )

    # 批量發送個性化郵件
    customers = [
        {"name": "張先生", "email": "zhang@example.com",
         "order_id": "ORD001", "amount": 1500},
        {"name": "李女士", "email": "li@example.com",
         "order_id": "ORD002", "amount": 2800},
        {"name": "王小姐", "email": "wang@example.com",
         "order_id": "ORD003", "amount": 950},
    ]

    def generate_invoice_email(customer):
        subject = f"訂單確認 - {customer['order_id']}"
        body = f"""
尊敬的 {customer['name']}，

感謝您的訂購！

訂單詳情：
- 訂單編號: {customer['order_id']}
- 訂單金額: HK$ {customer['amount']}
- 訂單日期: {datetime.now().strftime('%Y-%m-%d')}

如有問題請聯繫客服。

此郵件由自動化系統發送，請勿回覆。
        """
        return subject, body

    email.send_batch_emails(customers, generate_invoice_email)