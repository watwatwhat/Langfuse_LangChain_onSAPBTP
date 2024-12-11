# LangChain と Generative AI Hub SDK

Generative AI Hub SDK を介して LangChain ベースのアプリケーションを設定および使用する方法について説明します。
<br>
このアプリケーションは、下記のブログの内容に準拠します。ご参照ください。
<br>
[SAP BTP上でLangChainアプリケーションを開発・実行・監視する](https://community.sap.com/t5/technology-blogs-by-sap/sap-btp%E4%B8%8A%E3%81%A7langchain%E3%82%A2%E3%83%97%E3%83%AA%E3%82%B1%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3%E3%82%92%E9%96%8B%E7%99%BA-%E5%AE%9F%E8%A1%8C-%E7%9B%A3%E8%A6%96%E3%81%99%E3%82%8B/ba-p/13960786)

## セットアップ
1. SAP AI Launchpadを介して、Generative AI Hub に LLMをセットアップする
    - 詳細な手順は上記ブログを参照
    - ブログ中ではチャットモデルのみをデプロイしていますが、同様にembeddingモデル(text-embedding-ada-002)もデプロイしてください
2. ルートディレクトリの `.env` ファイルを編集し、SAP AI Coreのインスタンスへのアクセス情報を設定する。
    - SAP BTP Cockpit -> Instance and Subscriptions から該当のインスタンスを選択
    - サービスキーを作成し、その内容として記載された内容から下記を記述する
    
```
AICORE_AUTH_URL="<SAP AI Core インスタンスの認証URL>"
AICORE_CLIENT_ID="<SAP AI Core インスタンスのOAuthクライアントID>"
AICORE_CLIENT_SECRET="<SAP AI Core インスタンスのOAuthクライアントシークレット>"
AICORE_BASE_URL="<SAP AI Core インスタンスのBase URL>"
AICORE_RESOURCE_GROUP="<SAP AI Core インスタンスのリソースグループ デフォルトでは default>"

EMBEDDING_MODEL_DEPLOYMENT_ID="<EmbeddingモデルのデプロイメントID>"
EMBEDDING_MODEL_API_VERSION="<Embeddingモデルのバージョン>"
CHAT_MODEL_DEPLOYMENT_ID="<ChatモデルのデプロイメントID>"
CHAT_MODEL_API_VERSION="<Chatモデルのバージョン>"
```

## デプロイ
1. 手順は上記ブログを参照

