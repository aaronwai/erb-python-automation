from string import Template
from pathlib import Path
import json

class EmailTemplateSystem:
    """郵件模板系統"""

    def __init__(self, template_dir="email_templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """載入所有模板"""
        for template_file in self.template_dir.glob("*.json"):
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                self.templates[template_data['name']] = template_data

    def create_template(self, name, subject_template, body_template,
                       html_template=None, variables=None):
        """創建新模板"""
        template_data = {
            'name': name,
            'subject_template': subject_template,
            'body_template': body_template,
            'html_template': html_template,
            'variables': variables or []
        }

        template_file = self.template_dir / f"{name}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)

        self.templates[name] = template_data
        print(f"模板已創建: {name}")

    def render_template(self, template_name, variables):
        """渲染模板"""
        if template_name not in self.templates:
            raise ValueError(f"模板不存在: {template_name}")

        template = self.templates[template_name]

        # 使用 string.Template 進行變數替換
        subject = Template(template['subject_template']).safe_substitute(variables)
        body = Template(template['body_template']).safe_substitute(variables)

        html = None
        if template.get('html_template'):
            html = Template(template['html_template']).safe_substitute(variables)

        return subject, body, html

    def list_templates(self):
        """列出所有模板"""
        print("可用模板:")
        for name, template in self.templates.items():
            print(f"  - {name}: {', '.join(template.get('variables', []))}")

# 使用示例
if __name__ == "__main__":
    template_system = EmailTemplateSystem()

    # 創建模板
    template_system.create_template(
        name="welcome_email",
        subject_template="歡迎加入 $company_name, $user_name！",
        body_template="""
您好 $user_name，

歡迎加入 $company_name！您的帳號已創建成功。

登入資訊：
- 用戶名: $username
- 臨時密碼: $temp_password
- 登入網址: $login_url

請在首次登入後立即修改密碼。

如有問題，請聯繫: $support_email
        """,
        html_template="""
<html>
<body>
    <h1>歡迎加入 $company_name！</h1>
    <p>您好 <strong>$user_name</strong>，</p>
    <p>您的帳號已創建成功。</p>
    <div style="background: #f5f5f5; padding: 15px;">
        <p><strong>登入資訊：</strong></p>
        <ul>
            <li>用戶名: $username</li>
            <li>臨時密碼: <code>$temp_password</code></li>
            <li>登入網址: <a href="$login_url">點擊登入</a></li>
        </ul>
    </div>
</body>
</html>
        """,
        variables=["user_name", "company_name", "username",
                  "temp_password", "login_url", "support_email"]
    )

    # 渲染模板
    variables = {
        "user_name": "張偉明",
        "company_name": "科技有限公司",
        "username": "zhang.wm",
        "temp_password": "Temp@123456",
        "login_url": "https://portal.example.com",
        "support_email": "support@example.com"
    }

    subject, body, html = template_system.render_template("welcome_email", variables)
    print(f"主旨: {subject}")
    print(f"內容: {body[:100]}...")