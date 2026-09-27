import imaplib
import email
from email.header import decode_header
from pathlib import Path
import re

class EmailReceiver:
    """郵件接收與處理類"""

    def __init__(self, imap_server, username, password):
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mail = None

    def connect(self):
        """連接郵箱"""
        self.mail = imaplib.IMAP4_SSL(self.imap_server)
        self.mail.login(self.username, self.password)
        print("郵箱連接成功")

    def list_folders(self):
        """列出所有文件夾"""
        _, folders = self.mail.list()
        for folder in folders:
            print(folder.decode())

    def select_folder(self, folder="INBOX"):
        """選擇文件夾"""
        status, messages = self.mail.select(folder)
        if status == 'OK':
            print(f"已選擇文件夾: {folder}")
            return int(messages[0])
        else:
            raise Exception(f"無法選擇文件夾: {folder}")

    def fetch_unread_emails(self, folder="INBOX", limit=None):
        """獲取未讀郵件"""
        total = self.select_folder(folder)

        # 搜索未讀郵件
        _, message_numbers = self.mail.search(None, 'UNSEEN')

        email_ids = message_numbers[0].split()
        if limit:
            email_ids = email_ids[-limit:]

        emails = []
        for num in email_ids:
            _, msg_data = self.mail.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            email_info = self._parse_email(email_message)
            email_info['id'] = num.decode()
            emails.append(email_info)

        print(f"獲取 {len(emails)} 封未讀郵件")
        return emails

    def search_emails(self, criteria, folder="INBOX"):
        """
        搜索郵件

        Args:
            criteria: 搜索條件字典
                {'from': 'sender@example.com'}
                {'subject': '關鍵字'}
                {'since': '01-Jan-2024'}
                {'before': '31-Jan-2024'}
        """
        self.select_folder(folder)

        # 構建搜索條件
        search_args = []
        for key, value in criteria.items():
            if key == 'from':
                search_args.extend(['FROM', value])
            elif key == 'subject':
                search_args.extend(['SUBJECT', value])
            elif key == 'since':
                search_args.extend(['SINCE', value])
            elif key == 'before':
                search_args.extend(['BEFORE', value])
            elif key == 'unseen':
                search_args.append('UNSEEN')

        _, message_numbers = self.mail.search(None, *search_args)

        emails = []
        for num in message_numbers[0].split():
            _, msg_data = self.mail.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            email_info = self._parse_email(email_message)
            email_info['id'] = num.decode()
            emails.append(email_info)

        return emails

    def _parse_email(self, email_message):
        """解析郵件內容"""
        # 解析主旨
        subject = self._decode_header(email_message['Subject'])

        # 解析發件人
        from_addr = self._parse_address(email_message['From'])

        # 解析收件人
        to_addr = self._parse_address(email_message['To'])

        # 解析日期
        date = email_message['Date']

        # 解析內容
        body_text = ""
        body_html = ""
        attachments = []

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body_text = self._get_payload(part)

                elif content_type == "text/html" and "attachment" not in content_disposition:
                    body_html = self._get_payload(part)

                elif "attachment" in content_disposition or "filename" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': self._decode_header(filename),
                            'content_type': content_type,
                            'data': part.get_payload(decode=True)
                        })
        else:
            body_text = self._get_payload(email_message)

        return {
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date,
            'body_text': body_text,
            'body_html': body_html,
            'attachments': attachments,
            'headers': dict(email_message.items())
        }

    def _decode_header(self, header_value):
        """解碼郵件頭"""
        if not header_value:
            return ""

        decoded_parts = decode_header(header_value)
        result = []

        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or 'utf-8', errors='replace'))
            else:
                result.append(part)

        return "".join(result)

    def _parse_address(self, address_str):
        """解析郵件地址"""
        from email.utils import parseaddr
        name, addr = parseaddr(address_str)
        return {
            'name': self._decode_header(name),
            'email': addr
        }

    def _get_payload(self, part):
        """獲取郵件內容"""
        payload = part.get_payload(decode=True)
        if payload:
            charset = part.get_content_charset() or 'utf-8'
            return payload.decode(charset, errors='replace')
        return ""

    def download_attachments(self, email_info, download_dir="attachments"):
        """下載郵件附件"""
        download_path = Path(download_dir)
        download_path.mkdir(exist_ok=True)

        saved_files = []

        for attachment in email_info['attachments']:
            # 清理文件名
            filename = re.sub(r'[\\/:*?"<>|]', '_', attachment['filename'])
            file_path = download_path / filename

            # 處理重名
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                file_path = download_path / f"{stem}_{counter}{original_path.suffix}"
                counter += 1

            with open(file_path, 'wb') as f:
                f.write(attachment['data'])

            saved_files.append({
                'filename': attachment['filename'],
                'path': file_path,
                'size': len(attachment['data'])
            })

            print(f"附件已下載: {file_path}")

        return saved_files

    def mark_as_read(self, email_id):
        """標記郵件為已讀"""
        self.mail.store(email_id.encode(), '+FLAGS', '\\Seen')
        print(f"已標記為已讀: {email_id}")

    def move_to_folder(self, email_id, target_folder):
        """移動郵件到指定文件夾"""
        # 複製到目標文件夾
        self.mail.copy(email_id.encode(), target_folder)
        # 標記為刪除（從原文件夾移除）
        self.mail.store(email_id.encode(), '+FLAGS', '\\Deleted')
        print(f"已移動到: {target_folder}")

    def delete_email(self, email_id):
        """刪除郵件"""
        self.mail.store(email_id.encode(), '+FLAGS', '\\Deleted')
        self.mail.expunge()
        print(f"已刪除郵件: {email_id}")

    def disconnect(self):
        """斷開連接"""
        if self.mail:
            self.mail.close()
            self.mail.logout()
            print("郵箱連接已關閉")

# 使用示例
if __name__ == "__main__":
    receiver = EmailReceiver(
        imap_server="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_app_password"
    )

    receiver.connect()

    # 列出文件夾
    # receiver.list_folders()

    # 獲取未讀郵件
    unread_emails = receiver.fetch_unread_emails(limit=10)

    for email_info in unread_emails:
        print(f"\n{'='*50}")
        print(f"主旨: {email_info['subject']}")
        print(f"發件人: {email_info['from']['name']} <{email_info['from']['email']}>")
        print(f"日期: {email_info['date']}")
        print(f"附件數: {len(email_info['attachments'])}")

        # 自動下載附件
        if email_info['attachments']:
            files = receiver.download_attachments(
                email_info,
                "downloads/email_attachments"
            )
            print(f"已下載 {len(files)} 個附件")

        # 根據條件移動郵件
        if "發票" in email_info['subject']:
            receiver.move_to_folder(email_info['id'], "Invoices")
        elif "報告" in email_info['subject']:
            receiver.download_attachments(email_info, "reports/downloads")
            receiver.mark_as_read(email_info['id'])

    receiver.disconnect()