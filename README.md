# terminal-japanese-input-pad（日本語入力パッド）

Windows Terminal の窓のすぐ下に、日本語を打つための入力窓を常設する小さな道具です。
A small always-on input box docked under Windows Terminal, for typing Japanese without the IME candidate window covering what you type.

個人が作った道具です。Anthropic・Microsoft・Google とは関係ありません。

## なぜ作ったか

Windows Terminal で Claude Code などの対話型のコマンドラインツールを使うと、日本語入力（IME）の予測候補・変換候補の窓が、打っている文字の上に重なって読めないことがあります。
原因は Windows Terminal の不具合です（[microsoft/terminal#20318](https://github.com/microsoft/terminal/issues/20318)）。直し（[microsoft/terminal#20627](https://github.com/microsoft/terminal/pull/20627)）は 2026-09-01 に Windows Terminal の開発版へ入りましたが、2026-10-01 時点で配布されている Stable（1.24.11911.0）・Preview（1.25.1912.0）にはまだ入っていません（Canary には入っています）。利用者の側の設定では直せません。参考：[anthropics/claude-code#70955](https://github.com/anthropics/claude-code/issues/70955)

この道具は、Windows Terminal の直しが届くまでのつなぎです。直しの入った版が配られたら、要らなくなるかもしれません。

この道具は、Windows Terminal の窓のすぐ下に普通の Windows の入力窓を置きます。そこで打てば、候補の窓は文字の位置に正しく出て、重なりません。打ち終わって Enter を押すと、文が元の窓へ貼り付けられ、そのまま送信されます。

## できること

- Windows Terminal の窓の下に、同じ横幅でくっつく。窓を動かす・幅を変えるとついてくる。最小化すると一緒に隠れる
- 下に場所が無いときは、Windows Terminal の窓の高さを自動で縮める（最大化されていれば元に戻してから縮める）
- **Enter**＝貼り付けて送信／**Ctrl+Enter**＝貼り付けだけ／**Shift+Enter**＝改行／**Esc**＝元の窓へ戻る（書きかけは残る）
- **Ctrl+Shift+J**＝入力窓と元の窓を行き来する。入力窓をしまっているときは出し直す
- **Tab**（Windows Terminal が前にあるとき）＝入力窓へ飛ぶ（v0.5.0）。Ctrl・Shift・Alt・Win を押しているときと、入力窓をしまっているときは、ふつうの Tab として届く
- 上の線をつかんで上下に動かすと、入力窓の高さが変わる（覚えておく）
- **Ctrl+ホイール**または右クリックで、文字の大きさを変える（覚えておく）
- ファイルや画像を落とすと、その場所（フルパス）が入る（[tkinterdnd2](https://pypi.org/project/tkinterdnd2/) が入っているとき）
- 右クリック →「入力窓をしまう」でしまう
- 日本語入力で確定したハイフンやドットなどの半角の記号が tkinter で落ちる不具合を、確定文字列（`WM_IME_COMPOSITION` の `GCS_RESULTSTR`）を直接受け取ることで避けている

## 動く環境

- Windows 10 / 11
- Windows Terminal
- Python 3.10 以降（3.13 で確認）。tkinter は Python に同梱
- 任意：`pip install tkinterdnd2`（ファイルを落とす機能を使うとき）
- 日本語入力は Google 日本語入力で確かめています。Microsoft IME・ATOK では確かめていません

## 使い方

```
pythonw input_pad.pyw
```

二重起動はしません。終了は、入力窓の中で右クリック →「日本語入力パッドを終了する」。

Windows にログインしたときに自動で立ち上げたいときは、`pythonw.exe` で `input_pad.pyw` を開くショートカットを、スタートアップフォルダ（`Win+R` → `shell:startup`）に置いてください。

## 設定（任意）

`input_pad.pyw` と同じフォルダに `config.json` を置くと、既定値を変えられます。文字の大きさと入力窓の高さは、操作すると自動でここに書かれます。

```json
{
  "hotkey_modifiers": ["ctrl", "shift"],
  "hotkey_key": "J",
  "font_family": "BIZ UDゴシック",
  "font_size": 14,
  "pad_lines": 3,
  "tab_jump": true,
  "pad_height": 120
}
```

## 記録（ログ）

`logs\input_pad_YYYYMMDD.log` に動きの記録を残します。打った文の中身は残さず、文字数だけを残します。ただし、送り先の窓の題名（Windows Terminal のタブの名前）は記録に残ります。

## 既知の制限

- 送るときにクリップボードを使います（送った文がクリップボードに残ります）
- 送る先は、Windows Terminal の窓でいま開いているタブです
- 画面のスクリーンショット道具で「アクティブな窓」を撮ると、入力窓を選んでいるときは入力窓だけが撮れます（別の窓のため）
- Tab で入力窓へ飛ぶため、Windows Terminal の中では Tab で候補を確定する操作（Claude Code の / のコマンドやファイル名の候補など）が使えません。使いたいときは `config.json` に `"tab_jump": false` と書いてください。Windows Terminal に直接日本語を打っていて、変換中に Tab で予測候補を選ぶ操作も入力窓へ飛ぶ動きになります

## ライセンス

MIT License（`LICENSE` を参照）
