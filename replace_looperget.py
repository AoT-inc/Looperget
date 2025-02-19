#!/usr/bin/env python3

import os
import sys

# 변경할 최상위 경로
BASE_DIR = "/Users/gwansuk/Documents/GitHub/Looperget"

# 치환할 (old -> new) 단어 쌍들
REPLACEMENTS = [
    ("LOOPERGET", "LOOPERGET"),

]

def replace_in_file(file_path):
    """파일 내부 텍스트에서 REPLACEMENTS에 있는 단어들을 치환."""
    # 파일을 열 때 인코딩 문제 처리: 
    #  - 'utf-8'로 열되, 에러 있으면 무시하거나 대체(replace)하려면 errors='replace' 사용 가능
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f" [WARN] Cannot read file (skip): {file_path} - {e}")
        return

    original = content
    # 순차적으로 치환
    for old_word, new_word in REPLACEMENTS:
        content = content.replace(old_word, new_word)

    # 변경이 생겼다면 다시 쓰기
    if content != original:
        try:
            with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)
            print(f" [INFO] Updated text in: {file_path}")
        except Exception as e:
            print(f" [ERROR] Cannot write file: {file_path} - {e}")

def rename_path_if_needed(path):
    """
    경로(파일 or 폴더 이름)에 REPLACEMENTS에 해당하는 단어가 있다면
    새 이름으로 rename.
    """
    dir_name = os.path.dirname(path)
    base_name = os.path.basename(path)

    new_base_name = base_name
    for old_word, new_word in REPLACEMENTS:
        new_base_name = new_base_name.replace(old_word, new_word)

    # 바뀐 게 없다면 그냥 둠
    if new_base_name == base_name:
        return path

    new_path = os.path.join(dir_name, new_base_name)
    # 충돌 방지를 위해, rename 전에 존재 여부 확인
    if os.path.exists(new_path):
        print(f" [WARN] {new_path} already exists. Skipping rename.")
        return path

    try:
        os.rename(path, new_path)
        print(f" [INFO] Renamed: {path} -> {new_path}")
        return new_path
    except Exception as e:
        print(f" [ERROR] Rename failed: {path} -> {new_path}. Error: {e}")
        return path

def main():
    # 1) 파일 내용 치환
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            replace_in_file(file_path)

    # 2) 파일/폴더명 치환 (하위 -> 상위 순으로 rename)
    #    os.walk()는 기본적으로 top-down이므로, 디렉터리를 역순으로 처리하려면 별도 로직이 필요.
    #    여기서는 먼저 파일을 rename -> 디렉터리를 rename 하는 순서로.
    
    # (A) 파일 rename
    for root, dirs, files in os.walk(BASE_DIR, topdown=False):
        for file in files:
            old_path = os.path.join(root, file)
            new_path = rename_path_if_needed(old_path)

        # (B) 디렉터리 rename
        # dir 리스트를 수정해주면 하위 디렉터리 탐색 시 경로가 꼬일 수 있으므로,
        # 우선 목록을 복사 후 순회
        for d in dirs:
            dir_path = os.path.join(root, d)
            renamed_dir = rename_path_if_needed(dir_path)

    print("\n[DONE] Finished replacement process.")

if __name__ == "__main__":
    # 인자로 경로를 받고 싶다면, sys.argv 사용
    # if len(sys.argv) > 1:
    #     BASE_DIR = sys.argv[1]
    main()