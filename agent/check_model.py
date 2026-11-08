"""交互式 DeepSeek 连接测试；不保存密钥，不访问数据库。"""
import getpass
import json
import sys
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    if not sys.stdin.isatty():
        print('请在 Mac 终端中直接运行此命令。')
        return 1
    try:
        key = getpass.getpass('请粘贴 DeepSeek API Key（输入不显示），然后回车：').strip()
        if not key or any(c.isspace() for c in key):
            print('密钥为空或包含空白，请重新运行并粘贴完整密钥。')
            return 1
        key.encode('ascii')
        payload = {
            'model': 'deepseek-flash',
            'messages': [{'role': 'user', 'content': '这是接口连接测试。请只回复：连接成功'}],
            'thinking': {'type': 'disabled'},
            'max_tokens': 64,
            'stream': False,
        }
        request = urllib.request.Request(
            'https://api.deepseek.com/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
            method='POST',
        )
        print('正在发送一次短文本测试请求，请稍候（最长等待约 45 秒）……')
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=45) as response:
            result = json.load(response)
        content = result['choices'][0]['message']['content']
        if not isinstance(content, str) or not content.strip():
            print('接口已响应，但没有返回文本；请把这条提示告诉我。')
            return 1
        print('API 连接测试通过。')
        print('模型回复：', content.replace(key, '[已隐藏密钥]'))
        usage = result.get('usage', {})
        for field, label in [('prompt_tokens', '输入 token'), ('completion_tokens', '输出 token')]:
            if isinstance(usage.get(field), int):
                print(f'{label}：{usage[field]}')
        print('本次未连接 MySQL，未读取项目数据，未保存密钥。')
        return 0
    except urllib.error.HTTPError as exc:
        messages = {400: '请求参数未被接受。', 401: '密钥未通过验证，请检查是否复制完整。',
                    402: '账户可用余额不足，请检查充值是否到账。', 429: '请求受限，请稍后重试。'}
        print(f'接口返回 HTTP {exc.code}：' + messages.get(exc.code, '服务暂不可用或请求被拒绝。'))
        return 1
    except (urllib.error.URLError, TimeoutError):
        print('网络或证书连接失败/超时。请将此提示告诉我，无需发送密钥。')
        return 1
    except (KeyboardInterrupt, EOFError):
        print('\n已取消。')
        return 1
    except (ValueError, KeyError, IndexError, TypeError):
        print('密钥格式或接口响应格式不符合预期。请将此提示告诉我，无需发送密钥。')
        return 1


if __name__ == '__main__':
    sys.exit(main())
