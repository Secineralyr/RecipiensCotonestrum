# Recipiens Cotonestrum

コトネストルムを受け取る者。

これはdream用絵文字モデレーションツール(サーバー)です。Cotonestrumを動かすために必要となります。

## 実行方法

### 前提条件

misskeyサーバーの管理用apiを叩けることが前提です。サーバーは以下の権限を持つapiキーが必須です。

- 「アカウントを見る(read:account)」
- 「絵文字を見る(read:admin:emoji)」
- 「絵文字ログを見る(read:admin:emoji-log)」

また、これはdocker composeで動作します。なのでdockerが必須です

### step1: .envを作る

.env_templateをコピーし、.envを作成してください。サーバーの設定は.envで行います。

#### .env設定項目

- HOST
リッスンするホストアドレス
- PORT
リッスンするポート番号
- DATA_DIRPATH
データが保存されるディレクトリ名
- DBPATH
データベースファイル名
- MISSKEY_HOST
misskeyのアドレス。必要であればポートも記載する
- MISSKEY_TOKEN
misskeyのapiトークン
- NO_SSL
(テスト環境用) misskeyのapi接続でSSLを使用するかどうか (1=true, 0=false)
- IS_DOCKER
(docker用) この変数名が定義されている場合サーバーに起動がDocker経由であることを知らせます

### step2: 起動する

docker compose upをしてください。

```
docker compose up -d
```

## 開発用

こちらは開発用に開発環境を整えるためにする手順です。

### step1: venvを作成する

```
python -m venv .venv
```

作成後、各環境に合わせてアクティベートを行ってください。

### step2: ライブラリをインストールする

```
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### step3: .envを作成する

上記を参照

### step4: 起動する

```
python src/main.py
```

### テスト方法

```
python -m unittest
```
