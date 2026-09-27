import requests
import json
import time
from urllib.parse import urljoin
from typing import Dict, List, Any

class APIAutomation:
    """API 自動化測試與調用類"""
    def __init__(self, base_url, auth_token=None, timeout=30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}'
            })

    def call_api(self, endpoint, method='GET', data=None,
                 params=None, expected_status=None, headers=None):
        """
        調用 API 並驗證響應
        Args:
            endpoint: API 端點路徑
            method: HTTP 方法
            data: 請求數據
            params: URL 參數
            expected_status: 預期狀態碼
            headers: 本次請求專屬 header
        """
        url = urljoin(self.base_url, endpoint)
        merged_headers = {**self.session.headers}
        if headers:
            merged_headers.update(headers)

        # 執行請求
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=merged_headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                if data is not None:
                    merged_headers["Content-Type"] = "application/json"
                response = self.session.post(url, json=data, params=params, headers=merged_headers, timeout=self.timeout)
            elif method.upper() == 'PUT':
                if data is not None:
                    merged_headers["Content-Type"] = "application/json"
                response = self.session.put(url, json=data, params=params, headers=merged_headers, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, headers=merged_headers, timeout=self.timeout)
            else:
                raise ValueError(f"不支援的方法: {method}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"網路請求異常: {str(e)}")

        # 驗證狀態碼
        if expected_status and response.status_code != expected_status:
            raise AssertionError(
                f"狀態碼不匹配: 預期 {expected_status}, "
                f"實際 {response.status_code}"
            )
        # 嘗試解析 JSON
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = response.text
        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'data': result,
            'response_time': response.elapsed.total_seconds()
        }

    def batch_api_calls(self, endpoints: List[Dict]) -> List[Dict]:
        """
        批量調用 API
        Args:
            endpoints: 端點配置列表
                [
                    {
                        'endpoint': '/api/users',
                        'method': 'GET',
                        'params': {'page': 1}
                    },
                    ...
                ]
        """
        results = []
        for config in endpoints:
            print(f"\n調用: {config['method']} {config['endpoint']}")
            try:
                result = self.call_api(
                    endpoint=config['endpoint'],
                    method=config.get('method', 'GET'),
                    data=config.get('data'),
                    params=config.get('params'),
                    expected_status=config.get('expected_status'),
                    headers=config.get('headers')
                )
                results.append({
                    'success': True,
                    'config': config,
                    'result': result
                })
                print(f"成功: 狀態碼 {result['status_code']}, "
                      f"耗時 {result['response_time']:.3f}s")
            except Exception as e:
                results.append({
                    'success': False,
                    'config': config,
                    'error': str(e)
                })
                print(f"失敗: {str(e)}")
            # 請求間延遲
            time.sleep(config.get('delay', 0.5))
        return results

    def api_test_suite(self, test_cases: List[Dict]) -> tuple[int, int, List[Dict]]:
        """
        API 測試套件
        Args:
            test_cases: 測試用例列表
        """
        passed = 0
        failed = 0
        test_report = []
        print("=" * 60)
        print("開始 API 測試套件")
        print("=" * 60)
        for i, test in enumerate(test_cases, 1):
            test_name = test['name']
            print(f"\n測試 {i}/{len(test_cases)}: {test_name}")
            case_result = {
                "name": test_name,
                "passed": False,
                "error": None,
                "response": None
            }
            try:
                result = self.call_api(
                    endpoint=test['endpoint'],
                    method=test.get('method', 'GET'),
                    data=test.get('data'),
                    params=test.get('params'),
                    expected_status=test.get('expected_status'),
                    headers=test.get('headers')
                )
                case_result["response"] = result
                # 執行斷言
                assertions = test.get('assertions', [])
                for assertion in assertions:
                    self._run_assertion(result, assertion)
                print(f"  ✓ 通過")
                passed += 1
                case_result["passed"] = True
            except AssertionError as e:
                msg = f"斷言失敗: {str(e)}"
                print(f"  ✗ {msg}")
                failed += 1
                case_result["error"] = msg
            except Exception as e:
                msg = f"異常: {str(e)}"
                print(f"  ✗ {msg}")
                failed += 1
                case_result["error"] = msg
            test_report.append(case_result)
        print("\n" + "=" * 60)
        print(f"測試完成: {passed} 通過, {failed} 失敗")
        print("=" * 60)
        return passed, failed, test_report

    def _run_assertion(self, result, assertion):
        """執行單個斷言"""
        assert_type = assertion['type']
        if assert_type == 'status_code':
            assert result['status_code'] == assertion['expected'], \
                f"狀態碼 {result['status_code']} != {assertion['expected']}"
        elif assert_type == 'contains':
            value = self._get_nested_value(result['data'], assertion['path'])
            assert assertion['expected'] in str(value), \
                f"值 {value} 不包含 {assertion['expected']}"
        elif assert_type == 'equals':
            value = self._get_nested_value(result['data'], assertion['path'])
            assert value == assertion['expected'], \
                f"值 {value} != {assertion['expected']}"
        elif assert_type == 'exists':
            value = self._get_nested_value(result['data'], assertion['path'])
            assert value is not None, f"路徑 {assertion['path']} 不存在"
        else:
            raise ValueError(f"不支援的斷言類型: {assert_type}")

    def _get_nested_value(self, data, path):
        """獲取嵌套字典/列表值，支持 0,1 數字索引"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list):
                if key.isdigit():
                    idx = int(key)
                    value = value[idx] if idx < len(value) else None
                else:
                    value = None
            else:
                value = None
            if value is None:
                break
        return value

# 使用示例
if __name__ == "__main__":
    # 初始化 API 客戶端
    api = APIAutomation(
        base_url="https://jsonplaceholder.typicode.com",
        auth_token=None  # 公開 API 無需認證
    )
    # 單個 API 調用
    result = api.call_api(
        endpoint="/posts/1",
        method="GET",
        expected_status=200
    )
    print(f"文章標題: {result['data']['title']}")
    # 批量調用
    endpoints = [
        {'endpoint': '/posts/1', 'method': 'GET'},
        {'endpoint': '/posts/2', 'method': 'GET'},
        {'endpoint': '/users/1', 'method': 'GET'},
    ]
    batch_results = api.batch_api_calls(endpoints)
    # 測試套件
    test_cases = [
        {
            'name': '獲取文章列表',
            'endpoint': '/posts',
            'method': 'GET',
            'assertions': [
                {'type': 'status_code', 'expected': 200}
            ]
        },
        {
            'name': '創建新文章',
            'endpoint': '/posts',
            'method': 'POST',
            'data': {
                'title': '測試文章',
                'body': '這是內容',
                'userId': 1
            },
            'assertions': [
                {'type': 'status_code', 'expected': 201},
                {'type': 'equals', 'path': 'title', 'expected': '測試文章'}
            ]
        },
        {
            'name': '獲取特定文章',
            'endpoint': '/posts/1',
            'method': 'GET',
            'assertions': [
                {'type': 'status_code', 'expected': 200},
                {'type': 'equals', 'path': 'id', 'expected': 1}
            ]
        }
    ]
    passed, failed, report = api.api_test_suite(test_cases)
