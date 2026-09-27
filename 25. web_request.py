import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path

class NetworkAutomation:
    """網絡自動化類"""
    def __init__(self, timeout=30, max_retries=3):
        self.session = requests.Session()
        self.timeout = timeout
        # 重試策略：預設不重試POST/PUT等非冪等請求
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        # 預設請求頭
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br'
        })

    def get(self, url, params=None, headers=None, **kwargs):
        """安全的 GET 請求"""
        try:
            merged_headers = {**self.session.headers}
            if headers:
                merged_headers.update(headers)
            response = self.session.get(
                url,
                params=params,
                headers=merged_headers,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"GET 請求失敗: {url}")
            print(f"錯誤: {str(e)}")
            return None

    def post(self, url, data=None, json_data=None, headers=None, **kwargs):
        """安全的 POST 請求"""
        try:
            merged_headers = {**self.session.headers}
            if headers:
                merged_headers.update(headers)
            if json_data:
                # 只有不存在時才設定Content-Type，避免覆蓋自訂header
                if "Content-Type" not in merged_headers:
                    merged_headers['Content-Type'] = 'application/json'
                response = self.session.post(
                    url,
                    json=json_data,
                    headers=merged_headers,
                    timeout=self.timeout,
                    **kwargs
                )
            else:
                response = self.session.post(
                    url,
                    data=data,
                    headers=merged_headers,
                    timeout=self.timeout,** kwargs
                )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"POST 請求失敗: {url}")
            print(f"錯誤: {str(e)}")
            return None

    def put(self, url, data=None, json_data=None, headers=None, **kwargs):
        """PUT 請求"""
        try:
            merged_headers = {**self.session.headers}
            if headers:
                merged_headers.update(headers)
            if json_data:
                if "Content-Type" not in merged_headers:
                    merged_headers['Content-Type'] = 'application/json'
                response = self.session.put(url, json=json_data, headers=merged_headers, timeout=self.timeout, **kwargs)
            else:
                response = self.session.put(url, data=data, headers=merged_headers, timeout=self.timeout,** kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"PUT 請求失敗: {str(e)}")
            return None

    def delete(self, url, headers=None, **kwargs):
        """DELETE 請求"""
        try:
            merged_headers = {**self.session.headers}
            if headers:
                merged_headers.update(headers)
            response = self.session.delete(url, headers=merged_headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"DELETE 請求失敗: {str(e)}")
            return None

    def download_file(self, url, save_path, chunk_size=8192, headers=None,
                      progress_callback=None):
        """
        下載大文件
        Args:
            progress_callback: 進度回調函數，接收 (downloaded, total) 參數
        """
        try:
            merged_headers = {**self.session.headers}
            if headers:
                merged_headers.update(headers)
            response = self.session.get(url, stream=True, headers=merged_headers, timeout=self.timeout)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)
            print(f"文件已下載: {save_path} ({self._format_size(downloaded)})")
            return save_path
        except requests.exceptions.RequestException as e:
            print(f"下載網絡錯誤: {str(e)}")
            return None
        except IOError as e:
            print(f"文件寫入錯誤: {str(e)}")
            return None

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def upload_file(self, url, file_path, field_name='file',
                    extra_data=None, headers=None, timeout=None):
        """上傳文件"""
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"上傳失敗，文件不存在: {path}")
                return None
            merged_headers = {**self.session.headers}
            if headers:
                merged_headers.update(headers)
            use_timeout = timeout or self.timeout
            with open(path, 'rb') as f:
                files = {field_name: (path.name, f, 'application/octet-stream')}
                response = self.session.post(
                    url,
                    files=files,
                    data=extra_data,
                    headers=merged_headers,
                    timeout=use_timeout
                )
                response.raise_for_status()
                return response
        except requests.exceptions.RequestException as e:
            print(f"上傳請求失敗: {str(e)}")
            return None
        except IOError as e:
            print(f"讀取上傳文件失敗: {str(e)}")
            return None

# 使用示例
if __name__ == "__main__":
    net = NetworkAutomation()
    # GET 請求
    response = net.get("https://api.github.com/users/github")
    if response:
        data = response.json()
        print(f"用戶: {data['login']}")
        print(f"公開倉庫: {data['public_repos']}")
        print(f"追隨者: {data['followers']}")
    # POST 請求
    response = net.post(
        "https://httpbin.org/post",
        json_data={
            "name": "測試",
            "value": 123
        }
    )
    if response:
        print(f"POST 響應: {response.json()['json']}")
    # 下載文件
    def show_progress(downloaded, total):
        percent = (downloaded / total) * 100
        print(f"\r下載進度: {percent:.1f}% ({downloaded}/{total})", end="")
    net.download_file(
        "https://example.com/large_file.zip",
        "downloads/file.zip",
        progress_callback=show_progress
    )
    # 上傳文件
    # net.upload_file(
    #     "https://httpbin.org/post",
    #     "document.pdf",
    #     extra_data={"description": "測試上傳"}
    # )
