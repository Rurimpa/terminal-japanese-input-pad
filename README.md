# terminal-japanese-input-pad（日本語入力パッド）

Windows Terminal の窓のすぐ下に、日本語を打つための入力窓を常設する小さな道具です。
A small always-on input box docked under Windows Terminal, for typing Japanese without the IME candidate window covering what you type.

個人が作った道具です。Anthropic・Microsoft・Google とは関係ありません。

## すぐ使う（3手）

1. **Python を入れる**（入っていれば飛ばす）：PowerShell かコマンドプロンプトで `winget install Python.Python.3.13`。または https://www.python.org/downloads/ から入れる
2. **ファイルを取る**：このページ上の緑の **Code** → **Download ZIP** で落とし、好きな場所に展開する
3. **`start_input_pad.bat` を2回クリック**する。Windows Terminal の窓の下に入力窓が出ます

あとは入力窓で日本語を打って **Enter** で送信。Windows Terminal で **Tab** を押すと入力窓へ飛びます。
終わるときは、入力窓の中で右クリック →「日本語入力パッドを終了する」。

ログインしたときに自動で立ち上げたいときは、`start_input_pad.bat` のショートカットを、スタートアップフォルダ（`Win+R` → `shell:startup`）に置いてください。

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
- **Ctrl+C**（入力窓の中で、文字を選んでいないとき）＝元の窓へ Ctrl+C を送り、Claude Code・Codex の動きを止める（v0.7.0）。文字を選んでいるときはふつうのコピー
- Windows Terminal の窓ごとに入力窓が1つずつ出る（Claude Code と Codex を別の窓で開いているときなど・v0.8.0）。書きかけの文は入力窓ごとに別々に残り、窓を閉じるとその入力窓も消える
- **↑・↓・Enter**（入力窓が空のとき）＝元の窓へ送る（v0.10.0）。Claude Code の選ぶ画面（フォルダを信用するか・許可の質問・/model など）を、入力窓にいたまま選べる。文字があるときや日本語の変換中は、入力窓の中で働く
- **Win＋矢印**（入力窓が選ばれているとき）＝Windows Terminal の窓を寄せる（v0.9.1）。↑＝画面いっぱい／←→＝左半分・右半分／↓＝寄せる前の位置。左右半分から↑↓で上下4分の1。どれも下に入力窓の分を空ける。Windows のスナップ補助（残り半分に置く窓を選ぶ画面）は出ない
- **Tab**（Windows Terminal が前にあるとき）＝入力窓へ飛ぶ（v0.5.0）。Ctrl・Shift・Alt・Win を押しているときと、入力窓をしまっているときは、ふつうの Tab として届く
- 入力窓を出しているときに Windows Terminal を選ぶ（クリック・Alt+Tab など）と、自動で入力窓へ移る（v0.6.0）。入力窓から **Esc** で戻ったときは移らないので、Claude Code の許可の質問に答えたり、Esc で止めたりできる。Tab などで入力窓へ戻ると、また移るようになる
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

## 使い方（コマンドで起動するとき）

```
pythonw input_pad.pyw
```

二重起動はしません（2つ目は何もせずに終わります）。

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
  "auto_focus": true,
  "pad_height": 120
}
```

## 記録（ログ）

`logs\input_pad_YYYYMMDD.log` に動きの記録を残します。打った文の中身は残さず、文字数だけを残します。ただし、送り先の窓の題名（Windows Terminal のタブの名前）は記録に残ります。また、自動で入力窓へ移る働きのために、切り替えた窓の種類名（例 `Chrome_WidgetWin_1`。窓の題名ではありません）も記録に残ります。

## 既知の制限

- 送るときにクリップボードを使います（送った文がクリップボードに残ります）
- 送る先は、Windows Terminal の窓でいま開いているタブです
- 画面のスクリーンショット道具で「アクティブな窓」を撮ると、入力窓を選んでいるときは入力窓だけが撮れます（別の窓のため）
- Tab で入力窓へ飛ぶため、Windows Terminal の中では Tab で候補を確定する操作（Claude Code の / のコマンドやファイル名の候補など）が使えません。使いたいときは `config.json` に `"tab_jump": false` と書いてください。Windows Terminal に直接日本語を打っていて、変換中に Tab で予測候補を選ぶ操作も入力窓へ飛ぶ動きになります

## ライセンス

MIT License（`LICENSE` を参照）。自由に使い、直し、組み込んでかまいません。そのときは、作者名（Rurimpa）とこの置き場のアドレスを残してください。MIT ライセンスそのものが、`LICENSE` に書かれた作者の表示を、写したものすべてに残すことを求めています。

作者：Rurimpa（https://github.com/Rurimpa）
