import requests
import json
from typing import Optional, Tuple

class DestinationService:
    def __init__(self, vcap_services: dict):
        # parameter
        self.vcap_services = vcap_services
        
        self.xsuaa_credentials = vcap_services["destination"][0]["credentials"]
        self.destination_service_url = vcap_services["destination"][0]["credentials"]["uri"]
        self.access_token: Optional[str] = None

    def get_xsuaa_token(self) -> str:
        """
        XSUAAからアクセストークンを取得する
        """
        url = self.xsuaa_credentials["url"] + "/oauth/token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.xsuaa_credentials["clientid"],
            'client_secret': self.xsuaa_credentials["clientsecret"]
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()  # エラーチェック

        self.access_token = response.json()["access_token"]
        return self.access_token

    def get_destination_url_and_header(self, destination_name: str) -> Tuple[str, dict]:
        """
        Destinationサービスから指定のDestinationのURLとヘッダーを取得する
        """
        if not self.access_token:
            self.get_xsuaa_token()

        url = self.destination_service_url + "/destination-configuration/v1/destinations/" + destination_name
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # エラーチェック
        
        destination_config = response.json()
        destination_url = destination_config["destinationConfiguration"]["URL"]
        
        destination_header = {
            "Content-Type": "application/json"
        }
        
        if "authTokens" in destination_config:  # authTokensが存在する場合
            print("================== AUTH TOKEN ==================")
            print(destination_config)
            auth_token = destination_config["authTokens"][0]  # 最初のトークンを使用
            destination_header[auth_token["http_header"]["key"]] = auth_token["http_header"]["value"]
        
        return destination_url, destination_header