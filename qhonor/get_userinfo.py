import requests
import re
import json
import os


def extract_script_values(html_content):
    """从HTML内容中提取所需的JavaScript变量值"""
    jdy_access_token = re.search(r'window\.jdy_access_token\s*=\s*"([^"]+)"', html_content).group(1)
    jdy_access_type = re.search(r'window\.jdy_access_type\s*=\s*"([^"]+)"', html_content).group(1)
    jdy_access_id = re.search(r'window\.jdy_access_id\s*=\s*"([^"]+)"', html_content).group(1)
    app_id = re.search(r'appId:\s*"([^"]+)"', html_content).group(1)
    entry_id = re.search(r'entryId:\s*"([^"]+)"', html_content).group(1)

    return {
        'jdy_access_token': jdy_access_token,
        'jdy_access_type': jdy_access_type,
        'jdy_access_id': jdy_access_id,
        'app_id': app_id,
        'entry_id': entry_id,
    }


def get_user_info():
    session = requests.Session()

    # 第1步：请求基础URL获取token和ID
    base_url = "https://rvl4jxgu5s.jiandaoyun.com/dash/6a5779b4d76fe22fba914ff1"
    response = session.get(base_url)

    if response.status_code != 200:
        print(f"基础URL请求失败，状态码: {response.status_code}")
        return None

    extracted_values = extract_script_values(response.text)
    print("提取基础变量:", extracted_values)

    # 第2步：发送密码验证请求
    password_url = f"{base_url}/password"
    password_data = {
        "publicPwd": "******",
        "fx_access_token": extracted_values['jdy_access_token'],
        "fx_access_type": extracted_values['jdy_access_type'],
    }

    password_response = session.post(password_url, json=password_data)

    if password_response.status_code != 200:
        print(f"密码验证请求失败，状态码: {password_response.status_code}")
        return None

    print("密码验证响应:", password_response.text)
    print("密码验证获取的cookies:", session.cookies.get_dict())

    # 第3步：获取数据（分页请求），只保留姓名和金额两个字段
    data_url = "https://rvl4jxgu5s.jiandaoyun.com/_/data_process/data/dash/list"

    NAME_FIELD = "f_1784117718128"   # 姓名
    AMOUNT_FIELD = "f_1784117720295"  # 金额

    all_data = []
    skip = 0
    limit = 100
    has_more_data = True

    while has_more_data:
        print(f"正在获取数据，skip={skip}, limit={limit}")

        data_payload = {
            "widgetId": "_widget_1784117700354",
            "appId": extracted_values['app_id'],
            "entryId": extracted_values['entry_id'],
            "skip": skip,
            "limit": limit,
            # 只请求需要的字段，减少不必要的数据量
            "fields": {NAME_FIELD: True, AMOUNT_FIELD: True},
            "showAllFields": False,
            "sort": [],
            "filter": {},
            "hasCount": False,
            "fx_access_token": extracted_values['jdy_access_token'],
            "fx_access_type": extracted_values['jdy_access_type'],
        }

        data_response = session.post(data_url, json=data_payload)

        if data_response.status_code != 200:
            print(f"数据请求失败，状态码: {data_response.status_code}")
            break

        response_data = data_response.json()

        if 'data' in response_data:
            current_data = response_data['data']
            if isinstance(current_data, list) and len(current_data) > 0:
                # 只提取姓名和金额两个字段，简化输出结构
                for item in current_data:
                    all_data.append({
                        "姓名": item.get(NAME_FIELD),
                        "金额": item.get(AMOUNT_FIELD),
                    })
                print(f"已获取 {len(current_data)} 条数据，累计 {len(all_data)} 条")

                if len(current_data) < limit:
                    has_more_data = False
                else:
                    skip += limit
            else:
                print("本次请求未返回数据，结束请求")
                has_more_data = False
        else:
            print("返回数据格式不符合预期，结束请求")
            has_more_data = False

    return {"data": all_data}


def save_to_file(data, filename="/www/wwwroot/pub.qfamily.cn/cert/user_info.json"):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {file_path}")


def main():
    print("开始获取数据...")
    user_data = get_user_info()

    if user_data:
        print(f"成功获取 {len(user_data['data'])} 条数据")
        save_to_file(user_data)
    else:
        print("获取数据失败")


if __name__ == "__main__":
    main()
