#!/usr/bin/env python3.13
# -*- coding: utf-8 -*-

"""
PHPファイル内の関数アノテーションを解析するスクリプト

使い方: python analyze_annotations.py [ディレクトリパス] [--exclude フォルダ1 フォルダ2 ...]
例: python analyze_annotations.py /Your/Directory/Path --exclude Hoge Fuga
"""

import os
import sys
import re
import json
import glob
import argparse
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm


def find_php_files(directory, exclude_dirs=None, limit=None):
    """
    指定されたディレクトリ内のPHPファイルを再帰的に検索する
    
    Args:
        directory (str): 検索対象のディレクトリパス
        exclude_dirs (list): 除外するディレクトリのリスト
        limit (int, optional): 検索結果の最大数
        
    Returns:
        list: 見つかったPHPファイルのパスのリスト
    """
    if exclude_dirs is None:
        exclude_dirs = []
    
    # 絶対パスに変換
    directory = os.path.abspath(directory)
    exclude_dirs = [os.path.join(directory, d) if not os.path.isabs(d) else d for d in exclude_dirs]
    
    # 除外パターンを作成
    exclude_patterns = [f"{d}/**" for d in exclude_dirs]
    
    # すべてのPHPファイルを検索
    all_files = glob.glob(f"{directory}/**/*.php", recursive=True)
    
    # 除外パターンに一致するファイルを除外
    filtered_files = []
    for file_path in all_files:
        exclude_file = False
        for pattern in exclude_patterns:
            if file_path.startswith(pattern.replace("/**", "")):
                exclude_file = True
                break
        if not exclude_file:
            filtered_files.append(file_path)
    
    # 制限がある場合は適用
    if limit is not None and limit > 0:
        filtered_files = filtered_files[:limit]
    
    return filtered_files


def analyze_file(file_path):
    """PHPファイル内の関数とそのアノテーションを解析する"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"ファイルを読み込めませんでした: {file_path} - {e}")
        return [], []

    # 関数定義を検出するための正規表現
    # public/private/protected/static などの修飾子にも対応
    function_pattern = re.compile(
        r'(?:public|private|protected|static|\s)*\s+function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]*))?'
    )
    
    # ドキュメントコメントを検出するための正規表現
    doc_comment_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
    
    # 行ごとに分割して解析
    lines = content.split('\n')
    functions_with_annotation = []
    functions_without_annotation = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # ドキュメントコメントを探す
        doc_comment = None
        if '/**' in line:
            comment_start = i
            while i < len(lines) and '*/' not in lines[i]:
                i += 1
            if i < len(lines):
                doc_comment = '\n'.join(lines[comment_start:i+1])
        
        # 関数定義を探す
        if 'function' in line:
            function_match = function_pattern.search(line)
            if function_match:
                function_name = function_match.group(1)
                params_str = function_match.group(2)
                return_type = function_match.group(3).strip() if function_match.group(3) else None
                
                # パラメータに型指定があるか確認
                has_param_type = False
                if params_str:
                    # 型指定のパターン: 型名 $変数名
                    param_type_pattern = re.compile(r'(\w+(?:\|?\w+)*)\s+\$\w+')
                    has_param_type = bool(param_type_pattern.search(params_str))
                
                # 関数の情報を収集
                function_info = {
                    'file': file_path,
                    'name': function_name,
                    'params': params_str,
                    'return_type': return_type,
                    'has_param_annotation': False,
                    'has_return_annotation': False,
                    'has_other_annotation': False,
                    'has_param_type': has_param_type,
                    'has_return_type': bool(return_type)
                }
                
                # アノテーションの判定
                has_annotation = False
                
                # ドキュメントコメントがあるか確認
                if doc_comment:
                    function_info['has_param_annotation'] = '@param' in doc_comment
                    function_info['has_return_annotation'] = '@return' in doc_comment
                    
                    # その他のアノテーションタグを検出（@see, @throws, @deprecated など）
                    other_tags = ['@see', '@throws', '@deprecated', '@since', '@author', '@version', '@todo']
                    for tag in other_tags:
                        if tag in doc_comment:
                            function_info['has_other_annotation'] = True
                            break
                    
                    has_annotation = True
                
                # PHP 7以降の型宣言があればアノテーションありとみなす
                if function_info['has_param_type'] or function_info['has_return_type']:
                    has_annotation = True
                
                # 判定結果に基づいて分類
                if has_annotation:
                    functions_with_annotation.append(function_info)
                else:
                    functions_without_annotation.append(function_info)
        
        i += 1
    
    return functions_with_annotation, functions_without_annotation


def parse_arguments():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description='PHPファイル内の関数アノテーションを解析するスクリプト')
    parser.add_argument('directory', nargs='?', default=os.getcwd(),
                        help='検索対象のディレクトリパス（デフォルト: カレントディレクトリ）')
    parser.add_argument('--exclude', '-e', nargs='+', default=[],
                        help='除外するディレクトリのリスト（例: vendor tests）')
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='分析するファイル数の上限')
    return parser.parse_args()


def main():
    """メイン関数"""
    # コマンドライン引数を解析
    args = parse_arguments()
    directory = args.directory
    exclude_dirs = args.exclude
    limit = args.limit
    
    print(f"PHPファイルを検索中: {directory}")
    if exclude_dirs:
        print(f"除外ディレクトリ: {', '.join(exclude_dirs)}")
    if limit:
        print(f"ファイル数制限: {limit}")
    
    php_files = find_php_files(directory, exclude_dirs, limit)
    total_files = len(php_files)
    print(f"合計 {total_files} 個のPHPファイルが見つかりました。")
    
    if total_files == 0:
        print("PHPファイルが見つかりませんでした。")
        return
    
    print("関数のアノテーションを解析中...")
    
    # 並列処理で解析を高速化
    all_with_annotation = []
    all_without_annotation = []
    
    with ProcessPoolExecutor() as executor:
        results = list(tqdm(executor.map(analyze_file, php_files), total=total_files))
    
    for with_annotation, without_annotation in results:
        all_with_annotation.extend(with_annotation)
        all_without_annotation.extend(without_annotation)
    
    # 結果を集計
    total_with_annotation = len(all_with_annotation)
    total_without_annotation = len(all_without_annotation)
    total_functions = total_with_annotation + total_without_annotation
    
    if total_functions == 0:
        print("関数が見つかりませんでした。")
        return
    
    # 結果を表示
    print("\n解析結果:")
    print(f"アノテーションあり: {total_with_annotation} 関数 ({total_with_annotation / total_functions * 100:.2f}%)")
    print(f"アノテーションなし: {total_without_annotation} 関数 ({total_without_annotation / total_functions * 100:.2f}%)")
    print(f"合計: {total_functions} 関数")
    
    # アノテーションがない関数の例を表示
    print("\nアノテーションがない関数の例 (最大10件):")
    for i, function in enumerate(all_without_annotation[:10]):
        print(f"- {function['name']} ({function['file']})")
        if function['params']:
            print(f"  パラメータ: {function['params']}")
        if function['return_type']:
            print(f"  戻り値の型: {function['return_type']}")
    
    # 詳細な結果をJSONファイルに保存
    results = {
        'summary': {
            'with_annotation': total_with_annotation,
            'without_annotation': total_without_annotation,
            'total': total_functions
        },
        'functions': {
            'with_annotation': all_with_annotation,
            'without_annotation': all_without_annotation
        }
    }
    
    output_file = os.path.join(os.getcwd(), 'annotation_analysis_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細な結果が保存されました: {output_file}")
    
    # ファイル別の統計情報
    files_stats = {}
    for function in all_with_annotation + all_without_annotation:
        file_path = function['file']
        if file_path not in files_stats:
            files_stats[file_path] = {'with_annotation': 0, 'without_annotation': 0}
        
        if function in all_with_annotation:
            files_stats[file_path]['with_annotation'] += 1
        else:
            files_stats[file_path]['without_annotation'] += 1
    
    # アノテーションが最も不足しているファイルを表示
    print("\nアノテーションが最も不足しているファイル (最大5件):")
    sorted_files = sorted(
        files_stats.items(),
        key=lambda x: x[1]['without_annotation'],
        reverse=True
    )
    
    for file_path, stats in sorted_files[:5]:
        total = stats['with_annotation'] + stats['without_annotation']
        percentage = stats['without_annotation'] / total * 100 if total > 0 else 0
        print(f"- {file_path}: {stats['without_annotation']}/{total} 関数にアノテーションがありません ({percentage:.2f}%)")


if __name__ == "__main__":
    main()
