# PHP関数アノテーション分析ツール

このツールは、PHPコードベース内の関数アノテーションを分析し、アノテーションが定義されている関数とされていない関数を数えるためのものです。

## 環境設定

`.python-version`ファイルが既に設定されています。また、仕様上の制約から仮想環境を使用する必要があります。

```bash
# pyenvがインストールされていない場合
brew install pyenv

# Python 3.13.4をインストール
pyenv install 3.13.4

# プロジェクトディレクトリに移動
cd ~/workspace/function_mix_count

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate
```

## 機能

- PHPファイルを再帰的に検索
- 関数定義とドキュメントコメントを解析
- `@param`と`@return`アノテーションの有無を確認
- 並列処理による高速な解析
- 詳細な統計情報の出力
- 結果のJSON形式での保存
- 特定のディレクトリを除外する機能
- 分析するファイル数の上限を設定する機能

## 必要なライブラリ

仮想環境を有効化した後、以下のライブラリをインストールしてください：

```bash
# 仮想環境が有効な状態で実行してください
pip install --require-hashes -r requirements.txt
```

`requirements.txt` は推移的依存まで含めてバージョンとハッシュを完全固定したロックファイルです（`--require-hashes` により改ざんされたパッケージや想定外のバージョンはインストールが拒否されます）。直接手で編集しないでください。

### 依存パッケージを追加・更新する場合

直接依存は `requirements.in` に記載し、[uv](https://docs.astral.sh/uv/) で `requirements.txt` を再生成します。

```bash
# requirements.in を編集した後、ロックファイルを再生成
uv pip compile requirements.in --python-version 3.13 --universal --generate-hashes -o requirements.txt

# 既存の固定を外して最新（脆弱性修正版）へ更新する場合は --upgrade を付ける
uv pip compile requirements.in --python-version 3.13 --universal --generate-hashes --upgrade -o requirements.txt
```

## 使い方

仮想環境を有効化した状態で実行してください：

```bash
# 基本的な使い方
python analyze_annotations.py [ディレクトリパス]

# 除外ディレクトリを指定する場合
python analyze_annotations.py [ディレクトリパス] --exclude vendor tests

# ファイル数の上限を指定する場合
python analyze_annotations.py [ディレクトリパス] --limit 1000
```

例：
```bash
# cake28ディレクトリを分析し、vendorとtestsディレクトリを除外
python analyze_annotations.py /Your/Directory/Path --exclude Hoge Fuga
```

### オプション

| オプション | 短縮形 | 説明 |
|------------|------|------|
| `--exclude` | `-e` | 除外するディレクトリのリスト |
| `--limit` | `-l` | 分析するファイル数の上限 |

ディレクトリパスを指定しない場合は、スクリプトが置かれているディレクトリが対象となります。

## 出力内容

1. 検索したPHPファイル数
2. アノテーションあり/なしの関数数と割合
3. アノテーションがない関数の例（最大10件）
4. アノテーションが最も不足しているファイル（最大5件）
5. 詳細な結果をJSONファイルに保存（`annotation_analysis_results.json`）

## 使用例

```bash
# プロジェクトディレクトリに移動
cd ~/workspace/function_mix_count

# 仮想環境を有効化
source venv/bin/activate

# スクリプトを実行
python analyze_annotations.py /Your/Directory/Path 

# vendorとtestsディレクトリを除外して実行
python analyze_annotations.py /Your/Directory/Path --exclude Hoge Fuga 

# ファイル数を500に制限して実行
python analyze_annotations.py /Your/Directory/Path --limit 500
```

上記のコマンドを実行すると、ランサーズのコードベース全体を分析し、関数アノテーションの状況を確認できます。

## 結果の解釈

- **アノテーションあり**: `@param`または`@return`アノテーションが定義されている関数 または PHP 7以降の型宣言が定義されている関数
- **アノテーションなし**: ドキュメントコメントがないか、あってもアノテーションが定義されていない関数

## 注意事項

- 大規模なコードベースでは解析に時間がかかる場合があります
- エンコーディングの問題があるファイルは自動的にスキップされます
- 特殊な関数定義パターンは検出できない場合があります
